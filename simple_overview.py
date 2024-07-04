import gpxpy
import dash
from dash import dcc, html
import plotly.graph_objs as go
from math import radians, cos, sin, asin, sqrt
from datetime import datetime
import numpy as np
import pandas as pd

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
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a)) 
    r = 6371  # Radius of Earth in kilometers
    return c * r * 1000  # Return in meters

# Function to calculate speeds, distances, and other metrics
def calculate_metrics(latitudes, longitudes, times, elevations):
    speeds = []
    distances = []
    total_distance = 0
    
    for i in range(1, len(times)):
        lat1, lon1, time1, ele1 = latitudes[i-1], longitudes[i-1], times[i-1], elevations[i-1]
        lat2, lon2, time2, ele2 = latitudes[i], longitudes[i], times[i], elevations[i]
        
        distance = haversine(lat1, lon1, lat2, lon2)
        time_diff = (time2 - time1).total_seconds()
        
        if time_diff > 0:
            speed = (distance / time_diff) * 3.6  # Convert to km/h
        else:
            speed = 0
        
        speeds.append(speed)
        distances.append(total_distance + distance)
        total_distance += distance
    
    highest_speed = max(speeds)
    lowest_speed = min(speeds)
    average_speed = sum(speeds) / len(speeds)
    total_time = (times[-1] - times[0]).total_seconds() / 3600  # in hours
    top_elevation = max(elevations)
    lowest_elevation = min(elevations)
    
    # Rough estimation of calories burned (based on an average cyclist)
    weight_kg = 80  # Average weight
    met_value = 12.0  # MET value for moderate cycling
    calories_burned = weight_kg * met_value * total_time
    
    metrics = {
        'highest_speed': highest_speed,
        'lowest_speed': lowest_speed,
        'average_speed': average_speed,
        'total_time': total_time,
        'top_elevation': top_elevation,
        'lowest_elevation': lowest_elevation,
        'total_distance': total_distance / 1000,  # Convert to km
        'calories_burned': calories_burned
    }
    
    return speeds, distances, metrics

# Smooth speed data using rolling average
def smooth_speed_data(speeds, window_size=5):
    speed_series = pd.Series(speeds)
    smoothed_speeds = speed_series.rolling(window=window_size, center=True).mean().fillna(method='bfill').fillna(method='ffill')
    return smoothed_speeds.tolist()

# Parse GPX file
latitudes, longitudes, times, elevations = parse_gpx(r'/home/baranekm/Downloads/Trip at Vlčnovská - Uherský Brod.gpx')

# Calculate speeds, distances, and metrics
speeds, distances, metrics = calculate_metrics(latitudes, longitudes, times, elevations)

# Distance in kilometers
distances_kilometers = [dist / 1000 for dist in distances]

# Smooth speed data
smoothed_speeds = smooth_speed_data(speeds)

# Normalize speeds for color scaling
speeds_normalized = (np.array(speeds) - min(speeds)) / (max(speeds) - min(speeds))

# Create Dash app
app = dash.Dash(__name__)

# Create Scattermapbox figure with color based on speed
map_fig = go.Figure(go.Scattermapbox(
    lat=latitudes[1:],  # skip the first point for speed calculation
    lon=longitudes[1:],  # skip the first point for speed calculation
    mode='markers+lines',
    marker=go.scattermapbox.Marker(
        size=7,
        color=speeds_normalized,
        colorscale='turbo',  # Color scale can be changed
        colorbar=dict(title='Speed (km/h)')
    ),
    line=go.scattermapbox.Line(
        width=2,
        color='blue'
    ),
    text=[f'Speed: {speed:.2f} km/h' for speed in speeds],
    hoverinfo='text'
))

map_fig.update_layout(
    mapbox_style="open-street-map",
    mapbox=dict(
        center=go.layout.mapbox.Center(
            lat=latitudes[len(latitudes) // 2],
            lon=longitudes[len(longitudes) // 2]
        ),
        zoom=10
    ),
    margin={"r":0,"t":0,"l":0,"b":0}
)

# Create elevation profile figure
elevation_fig = go.Figure(go.Scatter(
    x=distances_kilometers,
    y=elevations,
    mode='lines+markers',
    line=dict(color='green'),
    marker=dict(size=5, color='green'),
    text=[f'Elevation: {ele:.2f} m' for ele in elevations],
    hoverinfo='text'
))

elevation_fig.update_layout(
    xaxis=dict(
        range=[min(distances_kilometers), max(distances_kilometers)]  # Specify the range of x-axis
    ),
    xaxis_title='Distance (km)',
    yaxis_title='Elevation (m)',
    margin={"r":0,"t":0,"l":0,"b":0}
)

# Create speed profile figure
speed_fig = go.Figure(go.Scatter(
    x=distances_kilometers,
    y=smoothed_speeds,
    mode='lines+markers',
    line=dict(color='red'),
    marker=dict(size=5, color='red'),
    text=[f'Speed: {speed:.2f} km/h' for speed in smoothed_speeds],
    hoverinfo='text'
))

speed_fig.update_layout(
    xaxis=dict(
        range=[min(distances_kilometers), max(distances_kilometers)]  # Specify the range of x-axis
    ),
    xaxis_title='Distance (km)',
    yaxis_title='Speed (km/h)',
    margin={"r":0,"t":0,"l":0,"b":0}
)

# App layout
app.layout = html.Div([
    html.Div([
        dcc.Graph(id='gpx-map', figure=map_fig),
    ]),
    html.Div([
        dcc.Graph(id='elevation-profile', figure=elevation_fig),
        dcc.Graph(id='speed-profile', figure=speed_fig)
    ]),
    html.Div([
        html.H4('Trace Information'),
        html.P(f'Total Distance: {metrics["total_distance"]:.2f} km'),
        html.P(f'Highest Speed: {metrics["highest_speed"]:.2f} km/h'),
        html.P(f'Lowest Speed: {metrics["lowest_speed"]:.2f} km/h'),
        html.P(f'Average Speed: {metrics["average_speed"]:.2f} km/h'),
        html.P(f'Total Time: {metrics["total_time"]:.2f} hours'),
        html.P(f'Calories Burned: {metrics["calories_burned"]:.2f} kcal'),
        html.P(f'Top Elevation: {metrics["top_elevation"]:.2f} m'),
        html.P(f'Lowest Elevation: {metrics["lowest_elevation"]:.2f} m'),
    ])
], style={'max-width': '1200px', 'margin': '0 auto'})

# Callback to synchronize hover events between map and elevation profile
@app.callback(
    [dash.dependencies.Output('gpx-map', 'figure'),
     dash.dependencies.Output('speed-profile', 'figure')],
    [dash.dependencies.Input('elevation-profile', 'hoverData'),
     dash.dependencies.Input('speed-profile', 'hoverData')]
)
def update_map_hover(hoverData_el, hoverData_sp):
    if hoverData_el:
        point_index = hoverData_el['points'][0]['pointIndex']
        lat = latitudes[point_index + 1]  # +1 to skip the first point
        lon = longitudes[point_index + 1]
        
        map_fig.update_traces(
            marker=dict(size=[10 if i == point_index else 7 for i in range(len(latitudes)-1)])
        )
        map_fig.update_layout(
            mapbox=dict(
                center=go.layout.mapbox.Center(lat=lat, lon=lon),
                zoom=12
            )
        )

        speed_fig.update_traces(
            marker=dict(size=[10 if i == point_index else 5 for i in range(len(smoothed_speeds))])
        )
    if hoverData_sp:
        point_index = hoverData_sp['points'][0]['pointIndex']
        lat = latitudes[point_index + 1]  # +1 to skip the first point
        lon = longitudes[point_index + 1]
        
        map_fig.update_traces(
            marker=dict(size=[10 if i == point_index else 7 for i in range(len(latitudes)-1)])
        )
        map_fig.update_layout(
            mapbox=dict(
                center=go.layout.mapbox.Center(lat=lat, lon=lon),
                zoom=12
            )
        )

        speed_fig.update_traces(
            marker=dict(size=[10 if i == point_index else 5 for i in range(len(smoothed_speeds))])
        )
    return map_fig, speed_fig

# Run the app
if __name__ == '__main__':
    app.run_server(debug=True)
