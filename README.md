# Tracking Listening Habits
Web Automation with Python and Selenium of the website `https://bandcamp.com/`

## Utils folder
This folder contents the class `BandLeader`, used to:
- Initialize a headless browser and navigate to bandcamp
- Keep a list of available tracks
- Support finding more track
- Play, pause, and skip tracks
- Collects structured information about the currently playing track
- Keep a 'database' of tracks
- Save and restore that 'database' to and from disk

## Requirements
Have a look at the `requirements.txt` file to see the required libraries in order to run this code, also, `Firefox` web browser is a requirement

To install the requirements at once, simply type in your terminal: `pip install -r requirements.txt`

## Run code
In the `main.py` file you can see a simple code to initialize the `BandLeader` class with the default `csv_path` parameter
