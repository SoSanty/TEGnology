import dash
from dash import dcc, html
from dash.dependencies import Output, Input
import requests

# Initialize Dash app
app = dash.Dash(__name__)

# App layout
app.layout = html.Div([
    html.H1("Real-Time Temperature Monitoring", style={'textAlign': 'center'}),
    html.Div(id='temperature-display', style={
        'fontSize': '48px', 'textAlign': 'center', 'marginTop': '20px'
    }),
    dcc.Interval(
        id='interval-component',
        interval=5*1000,  # Update every 5 seconds
        n_intervals=0
    )
])

# Callback to fetch and update temperature data
@app.callback(
    Output('temperature-display', 'children'),
    [Input('interval-component', 'n_intervals')]
)
def update_temperature(n):
    try:
        response = requests.get("http://localhost:5000/latest-temperature", timeout=1)
        if response.status_code == 200:
            data = response.json()
            return f"Device: {data['device_id']} - Temperature: {data['temperature']}°C"
        else:
            return "No temperature data available."
    except requests.RequestException:
        return "Error fetching data from API."

if __name__ == '__main__':
    app.run_server(debug=True)
