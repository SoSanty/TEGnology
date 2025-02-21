import asyncio
import httpx
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak import BleakScanner
import requests

# Flask API endpoint
DEVICES_API_URL = "http://localhost:9000/register_devices"  # For sending MAC addresses
TEMP_API_URL = "http://localhost:9000/temperature"

# Global variable to store scanned devices
scanned_devices = {}
scanned_devices_lock = asyncio.Lock()

# Callback function for BLE device data
async def ble_signal_callback(device: BLEDevice, advertisement_data: AdvertisementData):
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
                async with httpx.AsyncClient() as client:
                    try:
                        await client.post(TEMP_API_URL, json=payload, timeout=1)
                    except httpx.RequestError as e:
                        print(f"Error sending data to API: {e}")
        async with scanned_devices_lock:
            scanned_devices[device.address] = device.name

    except Exception as e:
        print(f"Error processing data for {device.address}: {e}")

# BLE Scanning function
async def ble_scan():
    scanner = BleakScanner()
    scanner.register_detection_callback(ble_signal_callback)

    try:
        await scanner.start()
        while True:  # Keep scanning indefinitely
            await asyncio.sleep(10)  # Adjust scan frequency
            await send_devices_to_flask()
    finally:
        await scanner.stop()

# Send discovered devices to Flask API
async def send_devices_to_flask():
    async with scanned_devices_lock:
        device_list = [{"mac": mac, "name": name} for mac, name in scanned_devices.items()]
    
    try:
        response = requests.post(DEVICES_API_URL, json=device_list)
        print(f"Sent device list to Flask API. Response: {response.status_code}")
    except Exception as e:
        print(f"Error sending device list: {e}")

async def main():
    await ble_scan()  # Start scanning

asyncio.run(main())
