import dash
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dcc
from dash import html
from app import app
from dash import Input, Output, State

dash.register_page(__name__, path='/')

# Define the layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Set your personal information", style={'fontSize':30, 'textAlign':'left', 'color': 'black'}),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                dcc.Input(id='weight-input', type='number', placeholder='Weight (kg)', persistence=True, style={'width': '25%', 'margin-right': '10px'}),
                                dcc.Input(id='height-input', type='number', placeholder='Height (cm)', persistence=True, style={'width': '25%', 'margin-right': '10px'}),
                                dcc.Input(id='age-input', type='number', placeholder='Age', persistence=True, style={'width': '25%', 'margin-right': '10px'}),
                                html.Div([
                                    dcc.Dropdown(id='sex-input', placeholder='Sex', options=['Male', 'Female'], persistence=True),
                                ], style={'width': '25%', 'margin-right': '10px'})
                            ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '10px', 'flex': '1'}),
                        ]),
                    ]),
                ]),
            ]),
        ]),
    ]),
])

@app.callback([Output('store_weight', 'data'),
               Output('store_height', 'data'),
               Output('store_age', 'data'),
               Output('store_sex', 'data')],
              [Input('weight-input','value'),
               Input('height-input','value'),
               Input('age-input','value'),
               Input('sex-input','value')],
              [State('store_weight', 'data'),
               State('store_height', 'data'),
               State('store_age', 'data'),
               State('store_sex', 'data')])
def update_slider(weight, height, age, sex, weight_data, height_data, age_data, sex_data):
    weight_data = float(weight)
    height_data = float(height)
    age_data = int(age)
    sex_data = str(sex)
    return weight_data, height_data, age_data, sex_data

if __name__ == "__main__":
    app.run_server(debug=True)