import dash
from dash import dcc, html
from dash.dependencies import Output, Input, State
import dash_bootstrap_components as dbc
import plotly.graph_objs as go
import pandas as pd
import requests
from datetime import datetime, timedelta


# Initialize Dash app with Bootstrap theme
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])

# Store temperature data
temperature_data = pd.DataFrame(columns=["time", "temperature"])

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Industrial Temperature Monitoring", className="text-center mt-4"), width=12)
    ]),

    # Real-time Temperature Display
    dbc.Row([
        dbc.Col(html.Div(id='temperature-display', className="display-4 text-center mt-3"), width=12)
    ]),

    # Customization Options
    dbc.Row([
        dbc.Col([
            html.Label("Select Chart Color:"),
            dcc.Dropdown(
                id="chart-color",
                options=[
                    {"label": "Blue", "value": "blue"},
                    {"label": "Red", "value": "red"},
                    {"label": "Green", "value": "green"},
                    {"label": "Orange", "value": "orange"}
                ],
                value="blue"
            ),
            html.Label("Temperature Threshold (°C):"),
            dcc.Input(id="threshold", type="number", value=75, step=1),
        ], width=4)
    ], className="mt-3"),

    # Real-time Chart
    dbc.Row([
        dbc.Col(dcc.Graph(id="temperature-graph"), width=12)
    ]),

    # Interval component for updates
    dcc.Interval(
        id='interval-component',
        interval=5000,  # Update every 5 seconds
        n_intervals=0
    )
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
                template="plotly_dark"
            )

            return display_text, fig

        else:
            return "No temperature data available.", go.Figure()

    except requests.RequestException:
        return "Error fetching data from API.", go.Figure()

if __name__ == '__main__':
    app.run_server(debug=True)
