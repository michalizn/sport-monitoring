import gpxpy
import dash
from dash import Input, Output, State
from dash import dcc, html
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import os
import re
import glob
from app import app
from plotly.subplots import make_subplots
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.point import Point
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import requests
import xml.etree.ElementTree as ET

dash.register_page(__name__, path='/')

# Function to parse GPX file
def parse_gpx(file_path):
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
    
    latitudes = []
    longitudes = []
    times = []
    elevations = []
    
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                latitudes.append(point.latitude)
                longitudes.append(point.longitude)
                times.append(point.time)
                elevations.append(point.elevation)
    
    return latitudes, longitudes, times, elevations

# Haversine formula to calculate distance between two points
def haversine(lat1, lon1, lat2, lon2):
    from math import radians, sin, cos, sqrt, asin
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of Earth in kilometers
    return c * r * 1000  # Return in meters

def rename_gpx():
    # Regular expression to match the <time> tag
    time_regex = re.compile(r'<time>(.*?)</time>')
    loc_regex = re.compile(r'<trkpt\s+lat="([+-]?\d+\.\d+)"\s+lon="([+-]?\d+\.\d+)">')

    # Iterate over all files in the directory
    for filename in os.listdir(gpx_folder):
        if filename.endswith(".gpx"):
            filepath = os.path.join(gpx_folder, filename)
                
            # Open and read the file
            with open(filepath, 'r') as file:
                content = file.read()

                # Search for the first occurrence of the time tag
                time_match = time_regex.search(content)
                loc_match = loc_regex.search(content)

                if time_match and loc_match:
                    time_str = time_match.group(1)  # Extract the time string
                    lat = loc_match.group(1)
                    lon = loc_match.group(2)

                    # Format the time string as YYYYMMDDHHMMSS
                    formatted_time = time_str.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')

                    # Construct the new filename
                    new_filename = f"{formatted_time}.gpx"
                    new_filepath = os.path.join(gpx_folder, new_filename)

                    # Rename the file
                    os.rename(filepath, new_filepath)
                    print(f"Renamed '{filename}' to '{new_filename}'")
                else:
                    print(f"No time tag found in '{filename}'")

# Smooth speed data using rolling average
def smooth_speed_data(speeds, window_size=5):
    speed_series = pd.Series(speeds)
    smoothed_speeds = speed_series.rolling(window=window_size, center=True).mean().fillna(method='bfill').fillna(method='ffill')
    return smoothed_speeds.tolist()

def calculate_metrics(latitudes, longitudes, times, elevations, pause_threshold_minutes=1):
    speeds = []
    distances = []
    total_distance = 0
    total_time_seconds = 0
    
    pause_threshold_seconds = pause_threshold_minutes * 60
    
    for i in range(1, len(times)):
        lat1, lon1, time1, ele1 = latitudes[i-1], longitudes[i-1], times[i-1], elevations[i-1]
        lat2, lon2, time2, ele2 = latitudes[i], longitudes[i], times[i], elevations[i]
        
        distance = haversine(lat1, lon1, lat2, lon2)
        time_diff = (time2 - time1).total_seconds()
        
        if time_diff > pause_threshold_seconds:
            continue  # Skip this segment if the pause is significant
        
        if time_diff > 0:
            speed = (distance / time_diff) * 3.6  # Convert to km/h
        else:
            speed = 0
        
        speeds.append(speed)
        distances.append(total_distance + distance)
        total_distance += distance
        total_time_seconds += time_diff

    smoothed_speeds = smooth_speed_data(speeds)

    highest_speed = max(smoothed_speeds) if smoothed_speeds else 0
    lowest_speed = min(smoothed_speeds) if smoothed_speeds else 0
    average_speed = sum(smoothed_speeds) / len(smoothed_speeds) if smoothed_speeds else 0
    top_elevation = max(elevations)
    lowest_elevation = min(elevations)
    
    metrics = {
        'highest_speed': highest_speed,
        'lowest_speed': lowest_speed,
        'average_speed': average_speed,
        'total_time_seconds': total_time_seconds,
        'top_elevation': top_elevation,
        'lowest_elevation': lowest_elevation,
        'total_distance': total_distance / 1000,  # Convert to km
    }
    
    return speeds, distances, metrics

def load_data(file_path):
    # Parse GPX file and calculate metrics
    latitudes, longitudes, times, elevations = parse_gpx(file_path)
    speeds, distances, metrics = calculate_metrics(latitudes, longitudes, times, elevations)
    distances_kilometers = [dist / 1000 for dist in distances]
    smoothed_speeds = smooth_speed_data(speeds)
    speeds_normalized = (np.array(speeds) - min(speeds)) / (max(speeds) - min(speeds))
    
    return {
        'latitudes': latitudes,
        'longitudes': longitudes,
        'times': times,
        'distances_kilometers': distances_kilometers,
        'elevations': elevations,
        'smoothed_speeds': smoothed_speeds,
        'speeds_normalized': speeds_normalized,
        'metrics': metrics
    }

# Create the map layout
map_layout = go.Layout(
    mapbox_style='open-street-map',
    hovermode='closest',
    showlegend=False,
)

# Create the figure and add the scatter mapbox trace
map_figure = go.Figure(data=[go.Scattermapbox()], layout=map_layout)

# Global variables to store data
data_cache = {}
prev_selected_file = None

# Get list of GPX files
gpx_folder = os.path.dirname(os.path.abspath(__file__)).replace('pages', 'data')
rename_gpx()
gpx_files = [f for f in os.listdir(gpx_folder) if f.endswith('.gpx')]

# App layout
layout = html.Div([
    dbc.Container([
        dbc.Row([
            dbc.Col([
                html.Div([], style={'textAlign': 'center'}),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.Label('Select route and activity', style={'fontSize':30, 'textAlign':'center'}),
                        html.Div([
                            html.Div([
                                dcc.Dropdown(
                                    id='gpx-dropdown',
                                    options=[
                                        {'label': f'Data Set: {file_name}', 'value': file_path}
                                        for file_name, file_path in zip(
                                            [os.path.basename(file_path) for file_path in glob.glob(os.path.join(gpx_folder, '*.gpx'))],
                                            glob.glob(os.path.join(gpx_folder, '*.gpx'))
                                        )
                                    ],
                                    placeholder="Select a GPX file",
                                    clearable=True,
                                    searchable=True,
                                    persistence=True,
                                ),
                            ], style={'width': '50%', 'margin-right': '10px'}),
                            html.Div([
                                dcc.Dropdown(
                                    id='activity-dropdown',
                                    options=['Running', 'Cycling', 'Walking'],
                                    placeholder="Select an activity",
                                    persistence=True,
                                ),
                            ], style={'width': '50%', 'margin-right': '10px'}),
                        ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '10px', 'flex': '1'}),
                    ]),
                ], style={'background': 'linear-gradient(to top, rgb(255, 255, 255) 0%, rgb(64, 64, 64) 100%)'}),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Trace details:"),
                    dbc.CardBody([
                        html.Div([
                            html.Div([
                                dcc.Graph(id='combined-graph', style={'flex': '1', 'height': '200px'}),
                            ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px', 'flex': '1'}),
                            html.Div([
                                dcc.Graph(id='gpx-map', figure=map_figure, className='map', style={'flex': '1', 'height': '400px'}),
                            ], style={'flex': '1'}),
                        ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '10px', 'flex': '1'}),
                    ]),
                ]),
            ]),
        ]),
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader("Trace Information", style={'fontSize':30, 'textAlign':'left', 'color': 'black'}),
                    dbc.CardBody([
                        html.Div(id='metrics-output', style={'padding': '10px'})
                    ]),
                ], style={'background': 'linear-gradient(to top, rgb(64, 64, 64) 0%, rgb(255, 255, 255) 100%)'}),
            ]),
        ]),
    ])
], style={'background': 'linear-gradient(to top, rgb(255, 255, 255) 0%, rgb(64, 64, 64) 100%)'})

@app.callback(
    [Output('metrics-output', 'children'),
     Output('gpx-map', 'figure'),
     Output('combined-graph', 'figure')],
    [Input('gpx-dropdown', 'value'),
     Input('combined-graph', 'hoverData'),
     Input('activity-dropdown', 'value')],
    [State('store_weight', 'data'),
     State('store_height', 'data'),
     State('store_age', 'data'),
     State('store_sex', 'data')]
)
def update_output(file_path, hoverData_plot, activity, weight, height, age, sex):
    global data_cache

    if not file_path:
        return [html.Div(), {}, {}]

    # Load data if the file path is new or if data_cache is empty
    if file_path not in data_cache:
        data_cache[file_path] = load_data(file_path)

    data = data_cache[file_path]
    
    # Format metrics
    metrics = data['metrics']
    times = data['times']
    formatted_times = [time.strftime('%Y-%m-%d %H:%M:%S %Z').replace(' Z', '') for time in times]  # Convert datetime to string
    # Combine speed and time for hover info
    hover_texts = [
        f"Speed: {speed:.2f} km/h<br>Time: {time}"
        for speed, time in zip(data['smoothed_speeds'], formatted_times)
    ]
    total_time_seconds = metrics['total_time_seconds']
    hours, minutes, seconds = int(total_time_seconds // 3600), int((total_time_seconds % 3600) // 60), int(total_time_seconds % 60)
    total_time_formatted = f"{hours:02}:{minutes:02}:{seconds:02}"
    
    map_fig = go.Figure(go.Scattermapbox(
        lat=data['latitudes'][1:],
        lon=data['longitudes'][1:],
        mode='markers+lines',
        marker=dict(size=7, color=data['speeds_normalized'], colorscale='turbo'),
        line=dict(width=2, color='blue'),
        text=hover_texts,
        hoverinfo='text'
    ))
    
    map_fig.update_layout(
        mapbox_style="open-street-map",
        mapbox=dict(
            center=go.layout.mapbox.Center(
                lat=data['latitudes'][len(data['latitudes']) // 2],
                lon=data['longitudes'][len(data['longitudes']) // 2]
            ),
            zoom=10
        ),
        margin={"r":0, "t":0, "l":0, "b":0}
    )

    # Create the combined figure with elevation and speed profiles
    elev_fig = go.Scatter(
        x=data['distances_kilometers'],
        y=data['elevations'],
        mode='lines+markers',
        line=dict(color='green'),
        marker=dict(size=5, color='green'),
        text=[f'Elevation: {ele:.2f} m' for ele in data['elevations']],
        hoverinfo='text'
    )

    speed_fig = go.Scatter(
        x=data['distances_kilometers'],
        y=data['smoothed_speeds'],
        mode='lines+markers',
        line=dict(color='red'),
        marker=dict(size=5, color='red'),
        text=[f'Speed: {speed:.2f} km/h' for speed in data['smoothed_speeds']],
        hoverinfo='text'
    )

    combined_fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.1)
    combined_fig.add_trace(elev_fig, row=1, col=1)
    combined_fig.add_trace(speed_fig, row=2, col=1)
    combined_fig.update_layout(
        xaxis=dict(range=[min(data['distances_kilometers']), max(data['distances_kilometers'])]),
        xaxis_title='Distance (km)',
        yaxis1_title='Elevation (m)',
        yaxis2_title='Speed (km/h)',
        showlegend=False,
        margin={"r":0, "t":0, "l":0, "b":0}
    )
    ## TODO add to the calculation sex information and typical times for running, walking and biking based on Strava measurements
    if not activity or not weight or not height or not age or not sex:
        calories_burned = "Please select an activity and enter your personal information in setttings menu."
    else:
        total_time = float(total_time_seconds)
        average_speed = float(metrics["average_speed"])

        # MET values for different activities
        met_values = {
            'Running': 9.8,
            'Cycling': 7.5,
            'Walking': 3.8
        }

        met_value = met_values.get(activity, 1)
        
        # Adjust MET value based on elevation gain and average speed
        elevation_gain_value = metrics["top_elevation"] - metrics["lowest_elevation"]
        
        if elevation_gain_value > 500:
            met_value += 1  # Increase MET value for high elevation gain

        if average_speed > 20:
            met_value += 1  # Increase MET value for high speed

        calories_burned = met_value * weight * (total_time/3600)

        calories_burned = f'{calories_burned:.2f} kcal'

    metrics_output = html.Div([
        html.Div([
            dbc.Card([
                dbc.CardHeader("Total Distance:"),
                dbc.CardBody(html.P(f'{metrics["total_distance"]:.2f} km', style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
            dbc.Card([
                dbc.CardHeader("Highest Speed:"),
                dbc.CardBody(html.P(f'{metrics["highest_speed"]:.2f} km/h', style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
            dbc.Card([
                dbc.CardHeader("Lowest Speed:"),
                dbc.CardBody(html.P(f'{metrics["lowest_speed"]:.2f} km/h', style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
            dbc.Card([
                dbc.CardHeader("Average Speed:"),
                dbc.CardBody(html.P(f'{metrics["average_speed"]:.2f} km/h', style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
        ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '10px', 'flex': '1'}),
        html.Div([
            dbc.Card([
                dbc.CardHeader("Total Time:"),
                dbc.CardBody(html.P(f'{total_time_formatted}', style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
            dbc.Card([
                dbc.CardHeader("Top Elevation:"),
                dbc.CardBody(html.P(f'{metrics["top_elevation"]:.2f} m', style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
            dbc.Card([
                dbc.CardHeader("Lowest Elevation:"),
                dbc.CardBody(html.P(f'{metrics["lowest_elevation"]:.2f} m', style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
            dbc.Card([
                dbc.CardHeader("Calories Burned: "),
                dbc.CardBody(html.P(calories_burned, style={'text-align': 'right', 'fontSize':20}))
            ], style={'width': '25%', 'margin-right': '10px', 'color': 'white', 'border-color': 'white', 'background': 'radial-gradient(circle at 10% 20%, rgb(0, 0, 0) 0%, rgb(64, 64, 64) 90.2%)'}),
        ], style={'display': 'flex', 'flexDirection': 'row', 'gap': '10px', 'flex': '1'})
    ], style={'display': 'flex', 'flexDirection': 'column', 'gap': '10px', 'flex': '1'})

    if hoverData_plot:
        point_index = hoverData_plot['points'][0]['pointIndex']
        lat = data['latitudes'][point_index + 1]
        lon = data['longitudes'][point_index + 1]

        # Update map figure
        map_fig.update_traces(
            marker=dict(size=[12 if i == point_index else 7 for i in range(len(data['latitudes']) - 1)])
        )
        map_fig.update_layout(
            mapbox=dict(
                center=go.layout.mapbox.Center(lat=lat, lon=lon),
                zoom=14
            )
        )

        # Update combined figure
        combined_fig.update_traces(
            marker=dict(size=[10 if i == point_index else 5 for i in range(len(data['smoothed_speeds']))])
        )

    return metrics_output, map_fig, combined_fig

# Define a callback to update the activity dropdown based on the average speed
@app.callback(
    Output('activity-dropdown', 'value'),
    Input('gpx-dropdown', 'value')
)
def update_activity_dropdown(file_path):
    if file_path:
        if file_path not in data_cache:
            data_cache[file_path] = load_data(file_path)

        data = data_cache[file_path]
        metrics = data['metrics']
        average_speed = float(metrics["average_speed"])  # in km/h
        
        # Determine activity based on average speed
        if average_speed > 17:
            return 'Cycling'
        elif 7 <= average_speed <= 17:
            return 'Running'
        else:
            return 'Walking'
    
    return None  # Default value if no file is selected

@app.callback(
    Output('gpx-dropdown', 'options'),
    [Input('gpx-dropdown', 'value')]
)
def update_options(selected_value):
    updated_options = [
        {'label': f'Data Set: {file_name}', 'value': file_path}
        for file_name, file_path in zip(
            [os.path.basename(file_path) for file_path in glob.glob(os.path.join(gpx_folder, '*.gpx'))],
            glob.glob(os.path.join(gpx_folder, '*.gpx'))
        )
    ]
    return updated_options

if __name__ == '__main__':
    app.run_server(debug=True)