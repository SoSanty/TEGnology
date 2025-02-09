import bluetooth
import bluetooth_utils as bluetooth_utils

BluetoothSocket = bluetooth.BluetoothSocket
RFCOMM = bluetooth.RFCOMM

def setup_bluetooth():
    # Initialize Bluetooth server
    server_socket = bluetooth_utils.BluetoothSocket(bluetooth_utils.RFCOMM)
    server_socket.bind(("", 1))  # Bind to any available Bluetooth port
    server_socket.listen(1)
    print("Waiting for Bluetooth connection...")
    
    # Accept an incoming connection from the Bluetooth sensor
    client_socket, address = server_socket.accept()
    print(f"Connected to {address}")
    return client_socket

def receive_temperature(client_socket):
    # Receive temperature data from Bluetooth sensor
    data = client_socket.recv(1024).decode().strip()
    return data
