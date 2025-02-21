import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import requests
from datetime import datetime, timedelta
import json
import os

# Ensure the json folder exists
if not os.path.exists('json'):
    os.makedirs('json')
    print("Created 'json' directory.")

# Default names for specific MAC addresses
default_names = {
    'F0:82:C0:B9:C9:08': 'SensEver HSI-BLE'
}

# Function to load preferred names from a file
def load_preferred_names(file_path):
    try:
        with open(file_path, 'r') as file:
            preferred_names = json.load(file)
            # Merge default names with preferred names
            return {**default_names, **preferred_names}
    except FileNotFoundError:
        print(f"File {file_path} not found. Returning default names.")
        return default_names
    except json.JSONDecodeError:
        print(f"Error decoding JSON from {file_path}. Returning default names.")
        return default_names

# Function to save preferred names to a file
def save_preferred_names(file_path, preferred_names):
    with open(file_path, 'w') as file:
        json.dump(preferred_names, file)
        print(f"Saved preferred names to {file_path}")

# File path for the preferred names dictionary
preferred_names_file = 'json/preferred_names.json'

# Load the preferred names dictionary from the file
preferred_names = load_preferred_names(preferred_names_file)

# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])

color_options = [
    {'label': 'Black', 'value': '#000000'},
    {'label': 'Red', 'value': '#FF0000'},
    {'label': 'Green', 'value': '#008000'},
    {'label': 'Blue', 'value': '#0000FF'},
    {'label': 'White', 'value': '#FFFFFF'},
    {'label': 'Yellow', 'value': '#FFFF00'}
]

# Default color for chart if invalid color is provided
DEFAULT_COLOR = '#0000FF'

# Sidebar layout
sidebar = html.Div([
    html.H4("Customize Chart", className="mb-3"),
    html.Label("Select Device:"),
    dcc.Dropdown(id='device-dropdown', options=[], value=None),
    html.Br(),
    html.Label("Chart Time Range (minutes)"),
    dcc.Slider(id='chart-time-slider', min=5, max=65, step=15, value=20,
               marks={i: f"{i} min" for i in range(5, 66, 15)}),
    html.Br(),
    html.Label("Select Chart Color:"),
    dcc.Dropdown(
        id="chart-color", 
        options=color_options,
        value='#0000FF'
    ),
    html.Br(),
    html.Label("Temperature Warning Threshold (°C):"),
    dcc.Input(id="threshold", type="number", value=75, step=1),
    html.Br(),
    html.Label("Select Threshold Line Color:"),
    dcc.Dropdown(
        id="threshold-color",
        options=color_options,
        value='#FF0000'
    ),
    html.Br()
], style={"width": "300px", "padding": "20px", "position": "fixed", "left": 0, "top": 0, "bottom": 0, "backgroundColor": "#747c7c", "overflowY": "auto"})

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Img(src='/assets/TEG_logo.png', style={'height': '50px', 'float': 'right', 'position': 'absolute', 'right': '20px', 'top': '20px'}), width={"size": 1}),
        html.Div(style={"height": "60px"}),
    ], className="align-items-center mt-3 d-flex"),
    dbc.Row([
        dbc.Col(html.Div([sidebar], id="sidebar-container"), width=3),
        dbc.Col(html.H1("TEGnology Sensors Monitoring"), className="text-center", width={"size": 6, "offset": 1}),
    ], className="align-items-center mt-3 d-flex"),
    # Real-time Temperature Display
    dbc.Row([dbc.Col(html.Div(id='temperature-display', className="text-center"), width={"size": 6, "offset": 4})]),
    # Spacer
    dbc.Row([dbc.Col(html.Div(style={"height": "30px"}))]),
    # Real-time Chart
    dbc.Row([dbc.Col(dcc.Graph(id="temperature-graph"), width={"size": 8, "offset": 3})]),
    # Interval component for updates
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),
    # Store temperature data
    dcc.Store(id='temperature-data-store', data={'temperature_data': []}),
    # Store device options
    dcc.Store(id='device-options-store', data=[]),
    # Store preferred names
    dcc.Store(id='preferred-names-store', data=preferred_names),
    html.Div([
        html.Label("Enter Preferred Name:"),
        dcc.Input(id='preferred-name-input', type='text', value='', className="text-center"),
        html.Button('Update Name', id='update-name-button', n_clicks=0),
        html.Div(id='update-name-output', className="text-center")
    ], style={'margin-top': '20px'})
], fluid=True, style={"position": "fixed", "top": 0, "bottom": 0, "backgroundColor": '#f0f0f0'})

# Callback to prompt the user to update the name when a device is selected
@app.callback(
    Output('preferred-name-input', 'value'),
    Input('device-dropdown', 'value')
)
def prompt_update_name(device_id):
    if device_id:
        return ""
    return dash.no_update

# Combined callback to update device dropdown options and sensor name
@app.callback(
    [Output('device-dropdown', 'options'),
     Output('device-options-store', 'data'),
     Output('preferred-names-store', 'data'),
     Output('update-name-output', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('update-name-button', 'n_clicks')],
    [State('device-dropdown', 'value'),
     State('preferred-name-input', 'value'),
     State('device-options-store', 'data'),
     State('preferred-names-store', 'data')]
)
def update_device_and_sensor_name(n_intervals, n_clicks, device_id, preferred_name, options, preferred_names):
    ctx = dash.callback_context

    if not ctx.triggered:
        return options, options, preferred_names, ""

    trigger = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger == 'interval-component':
        try:
            response = requests.get("http://localhost:9000/get_devices", timeout=5)
            if response.status_code == 200:
                devices = response.json()

                options = [{"label": preferred_names.get(mac, default_names.get(mac, name)), "value": mac} for mac, name in devices.items()]
                return options, options, preferred_names, ""
            else:
                print(f"Failed to fetch devices from http://localhost:9000/get_devices. Status code: {response.status_code}")  # Debugging statement
                return [], [], preferred_names, ""
        except requests.RequestException as e:
            print(f"Error fetching scanned devices from http://localhost:9000/get_devices: {e}")  # Debugging statement
            return [], [], preferred_names, ""

    elif trigger == 'update-name-button' and n_clicks > 0 and device_id and preferred_name:
        # Update the sensor name in the dropdown options and preferred names dictionary
        preferred_names[device_id] = preferred_name
        save_preferred_names(preferred_names_file, preferred_names)  # Save the updated dictionary to the file
        print(f"Updated preferred name for device {device_id} to {preferred_name}. Current preferred names: {preferred_names}")  # Debugging statement
        for option in options:
            if option['value'] == device_id:
                option['label'] = preferred_name
        return options, options, preferred_names, f"Sensor name updated to: {preferred_name}"

    return options, options, preferred_names, ""

# Callback to fetch and update temperature data
@app.callback(
    [Output('temperature-display', 'children'),
     Output('temperature-graph', 'figure'),
     Output('temperature-data-store', 'data')],
    [Input('device-dropdown', 'value'),
     Input('chart-color', 'value'),
     Input('threshold', 'value'),
     State('temperature-data-store', 'data'),
     State('chart-time-slider', 'value'),
     State('preferred-names-store', 'data')]
)
def update_temperature(device_id, color, threshold, stored_data, chart_time, preferred_names):
    if stored_data is None:
        stored_data = {'temperature_data': []}
    if device_id is None:
        return "No device selected.", go.Figure(), stored_data
    try:
        response = requests.get(f"http://localhost:9000/latest-temperature?device_id={device_id}", timeout=5)
        if response.status_code == 200:
            data = response.json()
            current_time = datetime.now()

            # Create a new entry for the new data point
            new_entry = {"time": current_time, "temperature": data['temperature']}

            # Append new data point to stored_data
            stored_data['temperature_data'].append(new_entry)

            # Convert 'time' field to datetime if it's a string
            for entry in stored_data['temperature_data']:
                if isinstance(entry['time'], str):
                    entry['time'] = datetime.fromisoformat(entry['time'])

            # Keep only the last 20 minutes of data
            cutoff_time = current_time - timedelta(minutes=chart_time)
            filtered_data = [entry for entry in stored_data['temperature_data'] if entry['time'] >= cutoff_time]

            # Update stored data with the filtered data
            stored_data['temperature_data'] = filtered_data

            # Real-time Temperature Display
            device_name = preferred_names.get(device_id, default_names.get(device_id, device_id))
            display_text = f"{device_name} - Temperature: {data['temperature']}°C" 
            df = pd.DataFrame(stored_data['temperature_data'])
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
            # Ensure 'time' is in datetime format (if needed)
            df['time'] = pd.to_datetime(df['time'])
            # Ensure 'temperature' values are correctly assigned
            if df['temperature'].dtype != float:
                df['temperature'] = df['temperature'].astype(float)
            # Validate color against color_options values
            valid_colors = [option['value'] for option in color_options]
            if color not in valid_colors:
                color = '#0000FF'  # Default to blue if color is invalid
                color = DEFAULT_COLOR  # Default to blue if color is invalid
            # Plot the data
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df['temperature'].to_list(),
                mode="lines+markers",
                line=dict(color=color),
                name="Temperature"
            ))

            fig.add_trace(go.Scatter(
                x=df["time"],
                y=[threshold] * len(df["time"]),
                mode="lines",
                line=dict(color="red", dash="dash"),
                name="Threshold"
            ))

            fig.update_layout(
                title="Temperature Over Time",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                xaxis=dict(tickformat="%H:%M:%S"),
            )

            return display_text, fig, stored_data

        else:
            print(f"Error fetching data from API at URL: http://localhost:9000/latest-temperature?device_id={device_id}. Error: {e}")

    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return f"Error fetching data from API: {e}", go.Figure(), stored_data


if __name__ == '__main__':
    app.run_server(debug=True)
