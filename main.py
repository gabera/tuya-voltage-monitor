#!/usr/bin/env python3
import os
import time
from datetime import datetime
from dotenv import load_dotenv

from collector import TuyaCollector
from database import VoltageDatabase


def main():
    """Main collection loop"""
    # Load environment variables
    load_dotenv()

    print("=" * 60)
    print("Tuya Voltage Monitor - WORKER - Data Collection Script")
    print("=" * 60)

    # Get collection interval
    interval = int(os.getenv('COLLECTION_INTERVAL', 300))
    print(f"Collection interval: {interval} seconds ({interval/60:.1f} minutes)")

    # Initialize components
    try:
        collector = TuyaCollector()
        db = VoltageDatabase()
    except Exception as e:
        print(f"\n✗ Initialization failed: {e}")
        print("\nPlease check your environment variables:")
        print("  - TUYA_CLIENT_ID")
        print("  - TUYA_CLIENT_SECRET")
        print("  - DEVICE_IDS")
        print("  - DATABASE_URL")
        return

    # Test connection
    print("\nTesting Tuya connection...")
    if not collector.test_connection():
        print("\n✗ Connection test failed. Please check your credentials.")
        return

    print("\n" + "=" * 60)
    print("Starting data collection...")
    print("Press Ctrl+C to stop")
    print("=" * 60 + "\n")

    collection_count = 0

    try:
        while True:
            collection_count += 1
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            print(f"[{timestamp}] Collection #{collection_count}")

            # Collect from all devices
            readings = collector.collect_all_devices()

            # Store in database
            if readings:
                success = db.insert_batch(readings)
                if success:
                    print(f"✓ Stored {len(readings)} reading(s)\n")
                else:
                    print(f"✗ Failed to store readings\n")
            else:
                print("✗ No readings collected\n")

            # Wait for next collection
            print(f"Next collection in {interval} seconds...")
            print("-" * 60 + "\n")
            time.sleep(interval)

    except KeyboardInterrupt:
        print("\n\n" + "=" * 60)
        print("Shutting down...")
        print(f"Total collections: {collection_count}")
        print("=" * 60)

    finally:
        db.close()


if __name__ == "__main__":
    main()
