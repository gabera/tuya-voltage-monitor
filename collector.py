import os
import tinytuya
from typing import List, Dict, Optional
from datetime import datetime


class TuyaCollector:
    def __init__(self):
        self.client_id = os.getenv('TUYA_CLIENT_ID')
        self.client_secret = os.getenv('TUYA_CLIENT_SECRET')
        self.region = os.getenv('TUYA_REGION', 'us')

        device_ids_str = os.getenv('DEVICE_IDS', '')
        self.device_ids = [d.strip() for d in device_ids_str.split(',') if d.strip()]

        if not self.client_id or not self.client_secret:
            raise ValueError("TUYA_CLIENT_ID and TUYA_CLIENT_SECRET must be set")

        if not self.device_ids:
            raise ValueError("DEVICE_IDS must be set (comma-separated list)")

        # Initialize Tuya Cloud connection
        self.cloud = tinytuya.Cloud(
            apiRegion=self.region,
            apiKey=self.client_id,
            apiSecret=self.client_secret
        )

        print(f"✓ Tuya collector initialized for {len(self.device_ids)} device(s)")

    def collect_all_devices(self) -> List[Dict]:
        """Collect voltage data from all configured devices"""
        readings = []

        for device_id in self.device_ids:
            reading = self.collect_device(device_id)
            if reading:
                readings.append(reading)

        return readings

    def collect_device(self, device_id: str) -> Optional[Dict]:
        """Collect data from a single device"""
        try:
            # Get device status
            status = self.cloud.getstatus(device_id)

            if not status or 'result' not in status:
                print(f"✗ No data returned for device {device_id}")
                return None

            # Parse the result
            result = status['result']

            # Tuya energy monitors typically report:
            # - voltage (in 0.1V units, e.g., 2200 = 220.0V)
            # - current (in mA)
            # - power (in 0.1W units)

            reading = {
                'device_id': device_id,
                'voltage': None,
                'current': None,
                'power': None
            }

            # Parse voltage, current, and power from the result
            for item in result:
                code = item.get('code', '')
                value = item.get('value')

                if code == 'voltage' or code == 'cur_voltage':
                    # Convert from 0.1V to V
                    reading['voltage'] = value / 10.0 if value else None
                elif code == 'current' or code == 'cur_current':
                    # Convert from mA to A
                    reading['current'] = value / 1000.0 if value else None
                elif code == 'power' or code == 'cur_power':
                    # Convert from 0.1W to W
                    reading['power'] = value / 10.0 if value else None

            if reading['voltage'] is None:
                print(f"✗ No voltage data found for device {device_id}")
                print(f"  Available data: {result}")
                return None

            print(f"✓ {device_id}: {reading['voltage']:.1f}V", end="")
            if reading['current']:
                print(f", {reading['current']:.3f}A", end="")
            if reading['power']:
                print(f", {reading['power']:.1f}W", end="")
            print()

            return reading

        except Exception as e:
            print(f"✗ Error collecting from device {device_id}: {e}")
            return None

    def test_connection(self) -> bool:
        """Test if we can connect to Tuya cloud and access devices"""
        try:
            devices = self.cloud.getdevices()
            if devices:
                print(f"✓ Successfully connected to Tuya Cloud")
                print(f"  Found {len(devices)} device(s) in your account")

                # Show configured devices
                print(f"\n  Configured devices to monitor:")
                for device_id in self.device_ids:
                    print(f"    - {device_id}")

                return True
            else:
                print("✗ Connected but no devices found")
                return False
        except Exception as e:
            print(f"✗ Connection test failed: {e}")
            return False
