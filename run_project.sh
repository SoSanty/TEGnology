#!/bin/bash

# Update package list and install dependencies
echo "Updating system and installing necessary packages..."
sudo apt-get update -y
sudo apt-get install -y python3-pip python3-dev python3-venv libbluetooth-dev

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

# Run the Flask API in the background
echo "Starting Flask API..."
nohup python3 flask_api.py > flask_api.log 2>&1 &

# Run the BLE Scanner in the background
echo "Starting BLE Scanner..."
nohup python3 ble_scan.py > ble_scan.log 2>&1 &

# Run the Dash App
echo "Starting Dash App..."
python3 dash_app.py
