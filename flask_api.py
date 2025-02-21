from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for temperature data
temperature_data = []

REGISTERED_DEVICES = {}  # Store discovered devices
SELECTED_DEVICE = None  # Store user's selected MAC address

@app.route("/register_devices", methods=["POST"])
def register_devices():
    global REGISTERED_DEVICES
    devices = request.json

    REGISTERED_DEVICES = {device["mac"]: device["name"] for device in devices}
    return jsonify({"message": "Devices registered", "devices": REGISTERED_DEVICES}), 200

@app.route("/get_devices", methods=["GET"])
def get_devices():
    return jsonify(REGISTERED_DEVICES), 200

@app.route("/select_device", methods=["POST"])
def select_device():
    global SELECTED_DEVICE
    data = request.json
    mac_address = data.get("mac")

    if mac_address in REGISTERED_DEVICES:
        SELECTED_DEVICE = mac_address
        return jsonify({"message": f"Device {mac_address} selected"}), 200
    else:
        return jsonify({"error": "MAC address not found"}), 400

@app.route("/get_selected_device", methods=["GET"])
def get_selected_device():
    if SELECTED_DEVICE:
        return jsonify({"selected_mac": SELECTED_DEVICE}), 200
    return jsonify({"error": "No device selected"}), 400

# Endpoint to receive temperature data from ble_scan.py
@app.route('/temperature', methods=['POST'])
def receive_temperature():
    data = request.json
    if 'device_id' in data and 'temperature' in data:
        temperature_data.append({
            "device_id": data['device_id'],
            "temperature": data['temperature']
        })
        return jsonify({"status": "success"}), 200
    return jsonify({"status": "error", "message": "Invalid data"}), 400

# Endpoint for Dash app to fetch the latest temperature data
@app.route('/latest-temperature', methods=['GET'])
def get_latest_temperature():
    if temperature_data:
        return jsonify(temperature_data[-1])  # Return the latest data
    return jsonify({"status": "error", "message": "No data available"}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000, debug=True)
