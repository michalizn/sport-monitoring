
# Sport Monitoring App

## Overview

The Sport Monitoring App is a powerful tool designed to help athletes and fitness enthusiasts track and analyze their outdoor activities. By leveraging GPS data from GPX files from Mapy.cz mobile app, the app provides detailed insights into various metrics such as distance, speed, elevation, and more. The app offers an intuitive interface to visualize routes, elevation profiles, and speed variations, making it easier to monitor performance and progress.

![Sport Monitoring App](https://github.com/michalizn/sport-monitoring/blob/main/assets/app.png)

## Features

- **Route Visualization**: Display your route on an interactive map.
- **Elevation Profile**: View the elevation changes throughout your route.
- **Speed Profile**: Analyze your speed variations over the distance covered.
- **Activity Metrics**: Get detailed metrics including total distance, highest speed, lowest speed, average speed, total time, top elevation, lowest elevation, and calories burned.
- **Pause Handling**: Automatically exclude significant pauses from the total time calculation for more accurate tracking.

## Trace Information

- **Total Distance**: The total distance covered during the activity.
- **Highest Speed**: The highest speed achieved.
- **Lowest Speed**: The lowest speed recorded.
- **Average Speed**: The average speed over the entire route.
- **Total Time**: The total duration of the activity, formatted as `hh:mm:ss`.
- **Top Elevation**: The highest elevation point reached.
- **Lowest Elevation**: The lowest elevation point.
- **Calories Burned**: An estimate of the calories burned based on average cyclist metrics.

## Usage

1. **Select Route and Activity**: Choose a GPX file from the dropdown menu to load your route.
2. **View Trace Details**: The map and graphs will update to show your selected route, elevation profile, and speed profile.
3. **Analyze Metrics**: Detailed metrics will be displayed in the "Trace Information" section for easy analysis of your performance.

## Calculation of burned calories based on your personal information

![Settings](https://github.com/michalizn/sport-monitoring/blob/main/assets/settings.png)

## Installation

To run the Sport Monitoring App locally:

### Unix/MacOS
```bash
# Clone the repository
git clone https://github.com/michalizn/sport-monitoring

# Get to the app directory
cd sport-monitoring

# Create a new Python environment
python3 -m venv env

# Activate the virtual environment (Unix/MacOS)
source env/bin/activate

# Install the required packages
pip3 install -r environment/requirements.txt

# Run app locally
python3 index.py
```
### Windows
```bash
# Clone the repository
git clone https://github.com/michalizn/sport-monitoring

# Get to the app directory
cd sport-monitoring

# Create a new Python environment
python3 -m venv env

# Activate the virtual environment (Windows)
.\env\Scripts\activate

# Install the required packages
pip3 install -r environment/requirements.txt

# Run app locally
python3 index.py
```

## Contributing

We welcome contributions to enhance the Sport Monitoring App. If you have any ideas or improvements, please feel free to submit a pull request or open an issue on GitHub.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
