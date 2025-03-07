#!/bin/bash

# Change to the directory where the script is located
cd "$(dirname "$0")"

# Update package list and install dependencies
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-dev python3-venv

# Activate virtual environment if exists, otherwise create one
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Create the Logs directory if it doesn't exist
mkdir -p logs/output
mkdir -p logs/errors

# Run the Flask API in the background and separate stdout and stderr
nohup python3 flask_api.py > Logs/output/flask_api.log 2> Logs/errors/flask_api_errors.log &

# Run the BLE Scanner in the background and separate stdout and stderr
nohup python3 ble_scan.py > Logs/output/ble_scan.log 2> Logs/errors/ble_scan_errors.log &

# Run the Dash App (stdout and stderr are combined here in the same log file)
python3 dash_app.py