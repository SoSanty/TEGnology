import asyncio
import requests
from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData
from bleak import BleakScanner

# Flask API endpoint
API_URL = "http://localhost:5000/temperature"

# Function to scan and display available devices
async def list_available_devices():
    devices = await BleakScanner.discover()
    print("Available BLE Devices:")
    for idx, device in enumerate(devices):
        print(f"{idx + 1}. {device.address} - {device.name}")
    
    try:
        selected_index = int(input("Enter the number of the sensor you want to monitor: ")) - 1
        selected_device = devices[selected_index]
        print(f"Selected Device: {selected_device.address} - {selected_device.name}")
        return selected_device.address
    except (ValueError, IndexError):
        print("Invalid selection. Exiting.")
        return None

# Callback function for BLE device data
def ble_signal_callback(device: BLEDevice, advertisement_data: AdvertisementData, target_mac_address):
    if device.address != target_mac_address:
        return

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
async def ble_scan(target_mac_address):
    scanner = BleakScanner(lambda device, adv_data: ble_signal_callback(device, adv_data, target_mac_address))

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

# Main function
async def main():
    selected_mac_address = await list_available_devices()
    if selected_mac_address:
        await ble_scan(selected_mac_address)

# Run the main function
asyncio.run(main())
