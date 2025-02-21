import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import requests
from datetime import datetime, timedelta

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
], style={"width": "300px", "padding": "20px", "position": "fixed", "top": 0, "bottom": 0, "backgroundColor": "#f8f9fa", "overflowY": "auto"})

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Div([sidebar], id="sidebar-container"), width=3),
        dbc.Col(html.H1("SensEver HSI-BLE"), className="text-center", width={"size": 6, "offset": 1}),
    ], className="align-items-center mt-3 d-flex"),

    # Real-time Temperature Display
    dbc.Row([dbc.Col(html.Div(id='temperature-display', className="display-4 text-center mt-3"), width={"size": 9, "offset": 3})]),

    # Spacer
    dbc.Row([dbc.Col(html.Div(style={"height": "30px"}))]),

    # Real-time Chart
    dbc.Row([dbc.Col(dcc.Graph(id="temperature-graph"), width={"size": 9, "offset": 3})]),

    # Interval component for updates
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),

    # Store temperature data
    dcc.Store(id='temperature-data-store', data={'temperature_data': []}),

], fluid=True)

# Callback to update device dropdown options
@app.callback(
    Output('device-dropdown', 'options'),
    Input('interval-component', 'n_intervals')
)

def update_device_dropdown(n_intervals):
    try:
        response = requests.get("http://localhost:5000/get-devices", timeout=5)
        if response.status_code == 200:
            devices = response.json()
            options = [{"label": device["label"], "value": device["value"]} for device in devices]
            return options
        else:
            return []
    except requests.RequestException as e:
        print(f"Error fetching scanned devices: {e}")
        return []

# Callback to fetch and update temperature data
@app.callback(
    [Output('temperature-display', 'children'),
     Output('temperature-graph', 'figure'),
     Output('temperature-data-store', 'data')],
    [Input('device-dropdown', 'value'),
     Input('chart-color', 'value'),
     Input('threshold', 'value'),
     State('temperature-data-store', 'data'),
     State('chart-time-slider', 'value')]
)
def update_temperature(device_id, color, threshold, stored_data, chart_time):
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
            display_text = f"Device: {data.get('device_id', 'Unknown')} - Temperature: {data['temperature']}°C"

            # Create a DataFrame for plotting
            df = pd.DataFrame(stored_data['temperature_data'])
            if not df.empty:
                df['time'] = pd.to_datetime(df['time'])
            # Ensure 'time' is in datetime format (if needed)
            df['time'] = pd.to_datetime(df['time'])
            # Ensure 'temperature' values are correctly assigned
            if df['temperature'].dtype != float:
                df['temperature'] = df['temperature'].astype(float)
            df['temperature'] = df['temperature'].astype(float) 
            # Validate color against color_options values
            valid_colors = [option['value'] for option in color_options]
            if color not in valid_colors:
                color = '#0000FF'  # Default to blue if color is invalid

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
            return "No temperature data available.", go.Figure(), stored_data

    except requests.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return f"Error fetching data from API: {e}", go.Figure(), stored_data


if __name__ == '__main__':
    app.run_server(debug=True)
