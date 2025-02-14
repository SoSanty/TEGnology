from flask import Flask, request, jsonify

app = Flask(__name__)

# In-memory storage for temperature data
temperature_data = []

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
