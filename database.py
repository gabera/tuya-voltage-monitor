import os
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from typing import List, Dict, Optional


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
        """Create tables if they don't exist"""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS voltage_readings (
            id SERIAL PRIMARY KEY,
            device_id VARCHAR(100) NOT NULL,
            timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
            voltage REAL NOT NULL,
            current REAL,
            power REAL,
            created_at TIMESTAMP DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_device_timestamp
        ON voltage_readings(device_id, timestamp DESC);
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
                self.conn.commit()
            print("✓ Database schema initialized")
        except Exception as e:
            print(f"✗ Schema initialization failed: {e}")
            self.conn.rollback()
            raise

    def insert_reading(self, device_id: str, voltage: float,
                      current: Optional[float] = None,
                      power: Optional[float] = None):
        """Insert a single voltage reading"""
        insert_query = """
        INSERT INTO voltage_readings (device_id, voltage, current, power)
        VALUES (%s, %s, %s, %s)
        """

        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_query, (device_id, voltage, current, power))
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

        insert_query = """
        INSERT INTO voltage_readings (device_id, voltage, current, power)
        VALUES %s
        """

        values = [
            (r['device_id'], r['voltage'], r.get('current'), r.get('power'))
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
        SELECT device_id, timestamp, voltage, current, power
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
