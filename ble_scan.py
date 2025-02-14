import asyncio
import requests
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak import BleakScanner

# Flask API endpoint
API_URL = "http://localhost:9000/temperature"

# Callback function for BLE device data
def ble_signal_callback(device: BLEDevice, advertisement_data: AdvertisementData):
    try:
        if advertisement_data.manufacturer_data:
            data = next(iter(advertisement_data.manufacturer_data.values()))
            bytes_data = list(data)
            
            if len(bytes_data) != 10:
                return

            temperature = int.from_bytes([bytes_data[-2], bytes_data[-1]], byteorder='little', signed=True)
            temperature = temperature / 10.0

            if -100.0 < temperature < 200.0:
                print(f"Device ID: {device.address}, Temperature: {temperature:.1f}°C")
                
                payload = {"device_id": device.address, "temperature": temperature}
                try:
                    requests.post(API_URL, json=payload, timeout=1)
                except requests.RequestException as e:
                    print(f"Error sending data to API: {e}")

    except Exception as e:
        print(f"Error processing data for {device.address}: {e}")

# BLE scanning function
async def ble_scan():
    scanner = BleakScanner(ble_signal_callback)

    while True:
        try:
            await scanner.start()
        except Exception as e:
            print(f"Error starting scanner: {e}")

        await asyncio.sleep(30.0)

        try:
            await scanner.stop()
        except Exception as e:
            print(f"Error stopping scanner: {e}")

# Run the main function
asyncio.run(ble_scan())
