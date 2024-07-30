from dash import html, dcc
from dash.dependencies import Input, Output
# Connect to main app.py file
from app import app
# Connect to app pages
from pages import overview, about, settings
# Connect the navbar to the index
from components import navbar
# Make a server
server = app.server
# Define the navbar
nav = navbar.Navbar()
# Define the index page layout
app.layout = html.Div([
    dcc.Store(id='store_weight', storage_type='local', data='weight_value'),
    dcc.Store(id='store_height', storage_type='local', data='height_value'),
    dcc.Store(id='store_age', storage_type='local', data='age_value'),
    dcc.Store(id='store_sex', storage_type='local', data='sex_value'),
    dcc.Location(id='url', refresh=False),
    nav, 
    html.Div(id='page-content', children=[]), 
])

@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/overview':
        return overview.layout
    if pathname == '/settings':
        return settings.layout
    if pathname == '/about':
        return about.layout
    else:
        return overview.layout

if __name__ == '__main__':
    app.run_server(debug=True)