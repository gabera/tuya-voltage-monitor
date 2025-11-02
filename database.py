import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional

# Brazilian timezone (GMT-3)
BRT = timezone(timedelta(hours=-3))


class VoltageDatabase:
    def __init__(self):
        self.database_url = os.getenv('DATABASE_URL')
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable not set")

        self.conn = None
        self.connect()
        self.initialize_schema()

    def connect(self):
        """Connect to PostgreSQL database"""
        try:
            self.conn = psycopg2.connect(self.database_url)
            print("✓ Connected to database")
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            raise

    def initialize_schema(self):
        """Create tables if they don't exist and migrate existing tables"""
        # Create table with new schema (without current and power)
        # Timestamps are stored as naive TIMESTAMP (no timezone conversion)
        # The application handles Brazilian timezone conversion before storing
        create_table_query = """
        CREATE TABLE IF NOT EXISTS voltage_readings (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            voltage REAL NOT NULL,
            created_at TIMESTAMP NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_device_timestamp
        ON voltage_readings(device_id, timestamp DESC);
        """

        # Drop old columns if they exist
        migration_query = """
        ALTER TABLE voltage_readings
        DROP COLUMN IF EXISTS current,
        DROP COLUMN IF EXISTS power;
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
                # Run migration to drop columns if table already exists
                cur.execute(migration_query)
                self.conn.commit()
            print("✓ Database schema initialized")
        except Exception as e:
            print(f"✗ Schema initialization failed: {e}")
            self.conn.rollback()
            raise

    def insert_reading(self, device_id: str, voltage: float):
        """Insert a single voltage reading"""
        # Get current time in Brazilian timezone (naive datetime, no timezone info)
        # This stores the actual Brazilian time without offset
        brt_time = datetime.now(BRT).replace(tzinfo=None)

        insert_query = """
        INSERT INTO voltage_readings (device_id, voltage, timestamp, created_at)
        VALUES (%s, %s, %s, %s)
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_query, (device_id, voltage, brt_time, brt_time))
                self.conn.commit()
            return True
        except Exception as e:
            print(f"✗ Failed to insert reading for {device_id}: {e}")
            self.conn.rollback()
            return False

    def insert_batch(self, readings: List[Dict]):
        """Insert multiple readings at once"""
        if not readings:
            return

        # Get current time in Brazilian timezone (naive datetime, no timezone info)
        # This stores the actual Brazilian time without offset
        brt_time = datetime.now(BRT).replace(tzinfo=None)

        insert_query = """
        INSERT INTO voltage_readings (device_id, voltage, timestamp, created_at)
        VALUES %s
        """

        values = [
            (r['device_id'], r['voltage'], brt_time, brt_time)
            for r in readings
        ]

        try:
            with self.conn.cursor() as cur:
                execute_values(cur, insert_query, values)
                self.conn.commit()
            print(f"✓ Inserted {len(readings)} readings")
            return True
        except Exception as e:
            print(f"✗ Batch insert failed: {e}")
            self.conn.rollback()
            return False

    def get_recent_readings(self, device_id: Optional[str] = None,
                           limit: int = 100):
        """Retrieve recent readings"""
        query = """
        SELECT device_id, timestamp, voltage
        FROM voltage_readings
        """

        if device_id:
            query += " WHERE device_id = %s"

        query += " ORDER BY timestamp DESC LIMIT %s"

        try:
            with self.conn.cursor() as cur:
                if device_id:
                    cur.execute(query, (device_id, limit))
                else:
                    cur.execute(query, (limit,))
                return cur.fetchall()
        except Exception as e:
            print(f"✗ Query failed: {e}")
            return []

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("✓ Database connection closed")
