import bluetooth

def get_bluetooth_device_mac():
    print("Scanning for nearby Bluetooth devices...")
    nearby_devices = bluetooth.discover_devices(lookup_names=True)

    if len(nearby_devices) == 0:
        print("No devices found.")
        return None

    print(f"Found {len(nearby_devices)} device(s).")
    for idx, (addr, name) in enumerate(nearby_devices, start=1):
        print(f"{idx}: {name} ({addr})")

    # Automatically select the first device (or customize as needed)
    selected_device = nearby_devices[0]
    print(f"Automatically selected device: {selected_device[1]} ({selected_device[0]})")
    return selected_device[0]

def connect_bluetooth_device(mac_address):
    port = 1  # You may need to adjust this depending on your sensor

    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((mac_address, port))

        print("Connected to Bluetooth device!")
        data = sock.recv(1024)  # Adjust buffer size
        print(f"Received data: {data}")

        sock.close()
    except bluetooth.btcommon.BluetoothError as err:
        print(f"Failed to connect: {err}")

# Automatically discover device and connect
mac_address = get_bluetooth_device_mac()
if mac_address:
    connect_bluetooth_device(mac_address)
else:
    print("No devices to connect to.")
