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

# Store temperature data
temperature_data = pd.DataFrame(columns=["time", "temperature"])

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

], fluid=True)

# Callback to fetch and update temperature data
@app.callback(
    [Output('temperature-display', 'children'),
     Output('temperature-graph', 'figure')],
    [Input('interval-component', 'n_intervals'),
     Input('chart-color', 'value'),
     Input('threshold', 'value')]
)
def update_temperature(n, color, threshold):
    global temperature_data

    try:
        response = requests.get("http://localhost:9000/latest-temperature", timeout=1)
        print(response)
        if response.status_code == 200:
            data = response.json()
            current_time = datetime.now()

            # Add new data to the dataframe
            new_entry = pd.DataFrame({"time": [current_time], "temperature": [data['temperature']]})

            # Drop rows where temperature is NaN or empty
            new_entry = new_entry.dropna(subset=["temperature"])

            # Concatenate safely
            temperature_data = pd.concat([temperature_data, new_entry], ignore_index=True)

            # Keep only last 20 minutes of data
            cutoff_time = current_time - timedelta(minutes=20)
            temperature_data = temperature_data[temperature_data["time"] >= cutoff_time]

            # Real-time Temperature Display
            display_text = f"Device: {data['device_id']} - Temperature: {data['temperature']}°C"

            # Plot the data
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=temperature_data["time"],
                y=temperature_data["temperature"],
                mode="lines+markers",
                line=dict(color=color),
                name="Temperature"
            ))

            # Add threshold line
            fig.add_trace(go.Scatter(
                x=temperature_data["time"],
                y=[threshold] * len(temperature_data["time"]),
                mode="lines",
                line=dict(color="red", dash="dash"),
                name="Threshold"
            ))

            fig.update_layout(
                title="Temperature Over Time",
                xaxis_title="Time",
                yaxis_title="Temperature (°C)",
                xaxis=dict(tickformat="%H:%M:%S"),
                template="lux"
            )

            return display_text, fig

        else:
            return "No temperature data available.", go.Figure()

    except requests.RequestException:
        return "Error fetching data from API.", go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)
