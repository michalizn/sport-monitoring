import dash
import dash_bootstrap_components as dbc
from dash import html
from app import app


dash.register_page(__name__, path='/')

# Define the layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H1("Welcome to Sport Monitoring App"),
                ], style={'textAlign': 'center'}),
            ]),
        ]),
    ]),
])

if __name__ == "__main__":
    app.run_server(debug=True)