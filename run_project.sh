#!/bin/bash

# Activate virtual environment if exists, otherwise create one
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Run the Flask API in the background
nohup python3 flask_api.py > flask_api.log 2>&1 &

# Run the BLE Scanner in the background
nohup python3 ble_scan.py > ble_scan.log 2>&1 &

# Run the Dash App
python3 dash_app.py
