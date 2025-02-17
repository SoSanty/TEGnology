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
    html.Label("Chart Time Range (minutes)"),
    dcc.Slider(id='chart-time-slider', min=5, max=60, step=5, value=20,
               marks={i: f"{i} min" for i in range(5, 61, 5)}),
    html.Br(),
    html.Label("Select Chart Color:"),
    dcc.Dropdown(id="chart-color", options=[
        {"label": "Blue", "value": "blue"},
        {"label": "Red", "value": "red"},
        {"label": "Green", "value": "green"},
        {"label": "Orange", "value": "orange"}
    ], value="blue"),
    html.Br(),
    html.Label("Temperature Warning Threshold (°C):"),
    dcc.Input(id="threshold", type="number", value=75, step=1),
    html.Br(),
    html.Br()
], style={"width": "300px", "padding": "20px", "position": "fixed", "top": 0, "bottom": 0, "backgroundColor": "#f8f9fa", "overflowY": "auto"})

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.Div([sidebar], id="sidebar-container"), width=3),
        dbc.Col(html.H1("SensEver HSI-BLE", id='main-title'), className="text-center", width={"size": 6, "offset": 1}),
    ], className="align-items-center mt-3 d-flex"),

    # Real-time Temperature Display
    dbc.Row([dbc.Col(html.Div(id='temperature-display', className="display-4 text-center mt-3"), width={"size": 9, "offset": 3})]),

    # Real-time Chart
    dbc.Row([dbc.Col(dcc.Graph(id="temperature-graph"), width={"size": 9, "offset": 3})]),

    # Interval component for updates
    dcc.Interval(id='interval-component', interval=5000, n_intervals=0),

    # Store temperature data
    dcc.Store(id='temperature-data-store', data={'temperature_data': []}),

], fluid=True)

# Callback to fetch and update temperature data
@app.callback(
    [Output('temperature-display', 'children'),
     Output('temperature-graph', 'figure'),
     Output('temperature-data-store', 'data')],
    [Input('interval-component', 'n_intervals'),
     Input('chart-color', 'value'),
     Input('threshold', 'value'),
     State('temperature-data-store', 'data')]
)
def update_temperature(n, color, threshold, stored_data):
    if stored_data is None:
        stored_data = {'temperature_data': []}
    try:
        response = requests.get("http://localhost:9000/latest-temperature", timeout=1)
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
            cutoff_time = current_time - timedelta(minutes=20)
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
            df['temperature'] = df['temperature'].astype(float) 

            # Plot the data
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=df['time'],
                y=df['temperature'].to_list(),
                mode="lines+markers",
                line=dict(color=color),
                name="Temperature"
            ))

            # Add threshold line
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
                template="plotly_white"
            )

            return display_text, fig, stored_data

        else:
            return "No temperature data available.", go.Figure(), stored_data

    except requests.RequestException:
        return "Error fetching data from API.", go.Figure(), stored_data


if __name__ == '__main__':
    app.run_server(debug=True)
