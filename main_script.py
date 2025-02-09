import platform
import time
from bluetooth_utils import BluetoothSocket, RFCOMM
from utils.mock_gpio import MockGPIO as GPIO  # For macOS

# If you're running on Raspberry Pi, you'll use the real GPIO
if platform.system() != "Darwin":
    import RPi.GPIO as GPIO  # For Raspberry Pi GPIO

# Define a threshold for the temperature
TEMP_THRESHOLD = 30  # Example threshold for triggering the LED

# Bluetooth setup
def setup_bluetooth():
    server_socket = BluetoothSocket(RFCOMM)
    server_socket.bind(("", 1))  # Bind to any available Bluetooth port
    server_socket.listen(1)
    print("Waiting for Bluetooth connection...")
    client_socket, address = server_socket.accept()
    print(f"Connected to {address}")
    return client_socket

# GPIO setup
def setup_gpio():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(17, GPIO.OUT)  # Set GPIO pin 17 to output (LED control)

# Trigger LED based on temperature
def trigger_led(temperature):
    if temperature > TEMP_THRESHOLD:
        print("LED is ON: Temperature exceeded threshold!")
        GPIO.output(17, GPIO.HIGH)  # Turn on LED
    else:
        print("LED is OFF: Temperature is safe.")
        GPIO.output(17, GPIO.LOW)  # Turn off LED

def main():
    client_socket = setup_bluetooth()
    setup_gpio()

    try:
        while True:
            data = client_socket.recv(1024).decode().strip()  # Receive data from Bluetooth sensor
            if data:
                try:
                    temperature = float(data)
                    print(f"Received Temperature: {temperature}°C")
                    trigger_led(temperature)
                except ValueError:
                    print("Invalid data received.")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Program terminated.")
    finally:
        client_socket.close()
        GPIO.cleanup()

if __name__ == "__main__":
    main()
