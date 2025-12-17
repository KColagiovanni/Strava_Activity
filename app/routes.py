from flask import Blueprint, render_template, request, jsonify, session
from app.models import Activity, db
from sqlalchemy.sql.operators import ilike_op
from app.database import Database
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
import plotly
from fitparse import FitFile
import gzip
import os
import gpxpy
import tcxparser
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
from config import Config
import pytz
from app import create_app
from sqlalchemy.exc import OperationalError

main = Blueprint('main', __name__)

# Define constants
METER_TO_MILE = 0.000621371
MPS_TO_MPH = 2.23694
METER_TO_FOOT = 3.28084

# Ensure the decompressed activities directory exists in the same directory of this program and if not, create it.
os.makedirs(Config.DECOMPRESSED_ACTIVITY_FILES_FOLDER, exist_ok=True)


def convert_activity_csv_to_db():
    """
    This function creates an instance of the Database class (defined in database.py), drops(deletes) any existing
    database(Database.DATABASE_NAME), then creates a table(Database.TABLE_NAME) in the defined database
    (Database.DATABASE_NAME) with the defined columns(defined in the Database.convert_csv_to_df() method).
    :return: None
    """
    db = Database()
    db.drop_table(Config.DATABASE_NAME)
    db.create_db_tables(Config.DATABASE_NAME, Config.ACTIVITY_TABLE_NAME, db.convert_csv_to_df())
    db.convert_json()


def convert_time_to_seconds(seconds, minutes, hours):
    """
    Convert elapsed time to seconds. Given seconds, minutes, and hours as parameters, this function converts elapsed
    time to seconds.
    :param seconds: (int) The amount of seconds in the elapsed time.
    :param minutes: (int) The amount of minutes in the elapsed time.
    :param hours: (int) The amount of hours in the elapsed time.
    :return: (int) The elapsed time in seconds.
    """
    if hours == '' or hours is None:
        hours = '00'
    if minutes == '' or minutes is None:
        minutes = '00'
    if seconds == '' or seconds is None:
        seconds = '00'

    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def split_time_string(time):
    """
    Returns the hour, minute, and second individually of a given time. Ex. If HH:MM:SS is passed as a parameters, [HH,
    MM, SS] will be returned.
    :param: (str) Time in HH:MM:SS or MM:SS format.
    :return: (list) [hour, minute, second]
    """
    if len(time) == 5:
        return_list = ['00'] # If the time is less than an hour, the hour will be 00
        time_split = time.split(':')
        return_list.append(time_split[0])
        return_list.append(time_split[1])
        return return_list
    else:
        return time.split(':')


def convert_meter_to_mile(meter):
    """
    Converts meters to miles using the convertion factor constant defined at the top of the program. If there is a comma
    (Ex. 1,842), it will be removed because it would not be able to be converted to a float.
    :param meter: (str) distance in meters.
    :return: (float) distance in miles.
    """
    if type(meter) == str:
        meter = meter.replace(',', '')  # Remove the comma from values so it can be converted to float.
        meter = float(meter)
    return round(meter * METER_TO_MILE, 2)


def convert_meters_to_feet(meter):
    """
    Converts meters to feet using the convertion factor constant defined at the top of the program.
    :param meter: (float) elevation in meters.
    :return: (float) elevation in feet.
    """
    return meter * METER_TO_FOOT


def convert_meters_per_second_to_miles_per_hour(meters_per_second):
    """
    Convert meters per second to miles per hour using the convertion factor constant defined at the top of the program,
    then rounds the result two decimal places after the decimal.
    :param meters_per_second: (float) speed in meters pere second.
    :return: (float) speed in miles per hour.
    """
    return round(meters_per_second * MPS_TO_MPH, 2)


def convert_celsius_to_fahrenheit(temp):
    """
    Converts the provided temperature from Celsius to Fahrenheit.
    :param temp: (float) the temperature in Celsius.
    :return: (float) the temperature in Fahrenheit.
    """
    return (temp * (9/5)) + 32


def generate_plot(data, title, yaxis_title, xaxis_title):
    """
    This function prepares the data to be plotted using Plotly. It takes a dictionary of the X and Y data, converts them
    to a figure, and finally converts the figure to JSON format. The main data is plotted on the Y-Axis and the distance
    or time is plotted on the X-Axis.
    :param data: (dict) The data for the x and y axes.
    :param title: (str) The title of the chart.
    :param yaxis_title: (str) The title of the y-axis.
    :param xaxis_title: (str) The title of the x-axis.
    :return: A JSON object with the plot figure data.
    """
    fig = go.Figure()
    fig.add_trace(go.Line(x=data['x'], y=data['y'], mode='lines', name=title))
    fig.update_layout(title=title, yaxis_title=yaxis_title, xaxis_title=xaxis_title)
    if xaxis_title == 'Time':
        fig.update_layout(xaxis=dict(dtick=len(data['x']) / 8))
    return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)


def calculate_speed(trackpoints):
    """
    Calculate the moving speed using the GPS coordinates(a.k.a. trackpoints).
    :param trackpoints: (list) The longitude and latitude points of the GPS activity.
    :return speed_list: (list) A list of the speed for each datapoint.
    """
    speed_list = []

    for i in range(1, len(trackpoints)):
        t1, lat1, lon1 = trackpoints[i - 1]
        t2, lat2, lon2 = trackpoints[i]

        # Calculate time difference in seconds
        time_diff = (t2 - t1).total_seconds()

        if time_diff > 0:
            # Calculate distance in meters
            distance = geodesic((lat1, lon1), (lat2, lon2)).meters
            speed = distance / time_diff  # meters per second (m/s)
            speed_list.append(convert_meters_per_second_to_miles_per_hour(speed))

    return speed_list


def parse_tcx(filepath):
    """
    Parses the trackpoints from the tcx activity file.
    :param filepath: (str) The decompressed_activity_files/ path with the filename of the file being parsed.
    :return trackpoints: (list) The longitude and latitude points of the GPS activity.
    """
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Namespaces in TCX files
    ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}

    trackpoints = []
    for tp in root.findall('.//tcx:Trackpoint', ns):
        tcx_time = tp.find('tcx:Time', ns)
        position = tp.find('tcx:Position', ns)

        if tcx_time is not None and position is not None:
            timestamp = datetime.fromisoformat(tcx_time.text.replace("Z", "+00:00"))
            lat = float(position.find('tcx:LatitudeDegrees', ns).text)
            lon = float(position.find('tcx:LongitudeDegrees', ns).text)

            trackpoints.append((timestamp, lat, lon))

    return trackpoints


def decompress_gz_file(input_file_path_and_name):
    """
    Decompress a .gz file. The file passed will be decompressed and the decompressed version will be saved in a
    directory within the directory where this program is located.
    :param input_file_path_and_name: (str) The filepath from where this program is running and the filename.
    :return: None
    """
    filename = input_file_path_and_name.split('/')[-1]
    filepath = input_file_path_and_name.split('/')[:-1]
    if 'gz' in input_file_path_and_name:
        output_file_name = filename.split('.gz')[0]
        # print(f'input_file from decompress_gz_file is: {input_file_path_and_name}')
        # print(f'output_file from decompress_gz_file is: {output_file_name}')
        with gzip.open(input_file_path_and_name, 'rb') as f_in:
            with open(f'{Config.DECOMPRESSED_ACTIVITY_FILES_FOLDER}/{output_file_name}', 'wb') as f_out:
            # with open(output_file, 'wb') as f_out:
                    f_out.write(f_in.read())
    else:
        print(f'There is no compressed file named {filename} in {filepath}')

def modify_tcx_file(file_name):
    """
    This function opens the .tcx file and removes the first line which was causing an issue. The first line was xml
    specific. TCX files are basically xml files, but for some reason the tcx parser would throw an error when trying to
    parse the tcx file. The original file is read into a list, all if it except for the first line. The list is then
    written back to the original file, overriding the original content.
    :param file_name: (str) The name of tcx the file to be parsed.
    :return: None.
    """

    # Open the file and read it to a list named "lines".
    with open(file_name, 'r') as f:
        lines = f.readlines()

    # Delete the first line of the list "lines".
    del lines[0]

    # Write the modified list back to the file.
    with open(file_name, 'w') as f:
        f.writelines(lines)


def get_activity_tcx_file(activity_id, filepath):
    """
    Decompress the tcx activity file and parse all the needed data for displaying and graphing stats, then save the
    data in the data_dict and return it.
    :param activity_id: (str) The activity id of the tcx activity.
    :param filepath: (str) The filepath of uploads folder, where activity files are stored.
    :return data_dict: (dict) A dictionary of info for the tcx activity graphs.
    """

    data_dict = {}
    activity_dict = {}
    speed_list = []
    file_is_found = False

    activity_data = db.session.get(Activity, activity_id)
    activity_type = activity_data.activity_type
    filename = activity_data.filename.split("/")[-1]
    sub_dir = activity_data.filename.split("/")[0]
    input_file_path = f'{filepath}/{sub_dir}'

    # Linear search for file
    for file in os.listdir(input_file_path):
        if file == filename:
            file_is_found = True
            filepath = os.path.join(input_file_path, file)
            decompress_gz_file(filepath)
            break  # Stop searching once the file is found.

    if file_is_found:
        xml_filename = Config.DECOMPRESSED_ACTIVITY_FILES_FOLDER + '/' + filepath.split('/')[-1].split('.gz')[0]
        modify_tcx_file(xml_filename)
        with open(xml_filename, 'r') as f:
            tcx = tcxparser.TCXParser(f)

            # Get activity data points
            altitude_list = [int(convert_meters_to_feet(alt_point)) for alt_point in tcx.altitude_points()]
            distance_list = [float(convert_meter_to_mile(value)) for value in tcx.distance_values()]
            time_list = tcx.time_values()
            hr_list = tcx.hr_values()
            position_list = tcx.position_values()
            cadence_list = tcx.cadence_values()
            power_list = tcx.power_values()

            # Make all the other lists the same length as the time_list by appending their last data point to the list
            # repeatedly until it is the same length as the time_list.
            if len(time_list) > 0:

                # Check if the altitude list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                while len(altitude_list) < len(time_list):
                    if len(altitude_list) > 0:
                        altitude_list.append(altitude_list[-1])
                    else:
                        altitude_list.append(0)

                activity_dict['elevation'] = {'x': distance_list, 'y': altitude_list}

                # Check if the distance list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                while len(distance_list) < len(time_list):
                    if len(distance_list) > 0:
                        distance_list.append(distance_list[-1])
                    else:
                        distance_list.append(0)

                # Create the speed list
                tcx_file = xml_filename
                trackpoints = parse_tcx(tcx_file)
                # data_dict['trackpoints'] = trackpoints
                speed_list = calculate_speed(trackpoints)

                while len(speed_list) < len(time_list):
                    if len(speed_list) > 0:
                        speed_list.append(speed_list[-1])
                    else:
                        speed_list.append(0)

                if activity_type in Config.INDOOR_ACTIVITIES:
                    activity_dict['speed_indoor'] = {'x': time_list, 'y': speed_list}
                else:
                    activity_dict['speed'] = {'x': distance_list, 'y': speed_list}

                # Check if the heartrate list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                while len(hr_list) < len(time_list):
                    if len(hr_list) > 0:
                        hr_list.append(hr_list[-1])
                    else:
                        hr_list.append(0)

                if activity_type in Config.INDOOR_ACTIVITIES:
                    activity_dict['heart_rate_indoor'] = {'x': time_list, 'y': hr_list}
                else:
                    activity_dict['heart_rate'] = {'x': distance_list, 'y': hr_list}

                # Check if the position list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                while len(position_list) < len(time_list):
                    if len(position_list) > 0:
                        position_list.append(position_list[-1])
                    else:
                        position_list.append(0)

                # Check if the cadence list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                while len(cadence_list) < len(time_list):
                    if len(cadence_list) > 0:
                        cadence_list.append(cadence_list[-1])
                    else:
                        cadence_list.append(0)

                if activity_type in Config.INDOOR_ACTIVITIES:
                    activity_dict['cadence_indoor'] = {'x': time_list, 'y': cadence_list}
                else:
                    activity_dict['cadence'] = {'x': distance_list, 'y': cadence_list}

                # Check if the power list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                while len(power_list) < len(time_list):
                    if len(power_list) > 0:
                        power_list.append(power_list[-1])
                    else:
                        power_list.append(0)

            if activity_type in Config.INDOOR_ACTIVITIES:
                activity_dict['power_indoor'] = {'x': time_list, 'y': power_list}
            else:
                activity_dict['power'] = {'x': distance_list, 'y': power_list}

            if 'heart_rate' in activity_dict and np.average(hr_list) > 0:
                data_dict['heart_rate'] = generate_plot(
                    activity_dict['heart_rate'],
                    'Heart Rate',
                    'BPM',
                    'Distance'
                )

            if 'heart_rate_indoor' in activity_dict and np.average(hr_list) > 0:
                data_dict['heart_rate'] = generate_plot(
                    activity_dict['heart_rate_indoor'],
                    'Heart Rate',
                    'BPM',
                    'Time'
                )

            if 'speed' in activity_dict and np.average(speed_list) > 0:
                data_dict['speed'] = generate_plot(
                    activity_dict['speed'],
                    'Speed',
                    'MPH',
                    'Distance'
                )

            if 'speed_indoor' in activity_dict and np.average(speed_list) > 0:
                data_dict['speed'] = generate_plot(
                    activity_dict['speed_indoor'],
                    'Speed',
                    'MPH',
                    'Time'
                )

            if np.average(altitude_list) > 0:
                data_dict['elevation'] = generate_plot(
                    activity_dict['elevation'],
                    'Elevation',
                    'Feet',
                    'Distance'
                )

            if 'cadence' in activity_dict and np.average(cadence_list) > 0:
                data_dict['cadence'] = generate_plot(
                    activity_dict['cadence'],
                    'Cadence',
                    'RPM',
                    'Distance'
                )

            if 'cadence_indoor' in activity_dict and np.average(cadence_list) > 0:
                data_dict['cadence'] = generate_plot(
                    activity_dict['cadence_indoor'],
                    'Cadence',
                    'RPM',
                    'Time'
                )

            if 'power' in activity_dict and np.average(power_list) > 0:
                data_dict['power'] = generate_plot(
                    activity_dict['power'],
                    'Power',
                    'Watts',
                    'Distance'
                )

            if 'power_indoor' in activity_dict and np.average(power_list) > 0:
                data_dict['power'] = generate_plot(
                    activity_dict['power_indoor'],
                    'Power',
                    'Watts',
                    'Time'
                )

            return data_dict

    else:
        print('The file was not found. :-(')

def get_activity_gpx_file(activity_id, filepath):
    """
    Parse the gpx file and extract all the needed data for displaying and graphing stats, then save the data in the
    data_dict and return it.
    :param activity_id: (datatype: str) The activity_id of the activity associated with the .gpx file.
    :param filepath: (datatype: str) The filepath to the .gpx file.
    :return: data_dict: (datatype: dict) A dictionary with the data to be plotted.
    """
    data_dict = {}
    activity_dict = {}

    activity_data = db.session.get(Activity, activity_id)
    activity_type = activity_data.activity_type

    filename = f'{activity_id}.gpx'
    input_file_path = f'{filepath}/activities/{filename}'

    with open(input_file_path, 'r') as f:
        gpx = gpxpy.parse(f)

    for track in gpx.tracks:
        for segment in track.segments:

            # start_time = segment.points[0].time
            elapsed_time = 0
            time_list = []
            speed_list = []
            distance_list = []
            hr_list = []
            total_distance = 0

            for data_point in range(0, len(segment.points)):
                point1 = segment.points[data_point - 1]
                point2 = segment.points[data_point]

                try:
                    hr_list.append(
                        [int(el.text) for el in segment.points[data_point].extensions[0] if 'hr' in el.tag][0]
                    )
                except IndexError as e:
                    message = f'No heart rate data was found.'

                if data_point == 0:
                    distance = 0
                else:
                    # Calculate distance, in meters, between the current GPS point and the previous using haversine
                    # formula
                    distance = point1.distance_2d(point2)

                # Calculate overall distance, in meters, between the current GPS point and the starting point using
                # haversine formula, then convert it from meters to miles.
                total_distance += distance
                distance_list.append(convert_meter_to_mile(total_distance))

                # Calculate time difference between two points
                time_diff = point2.time - point1.time

                # Calculate speed in m/s and then convert it to mi/h
                if time_diff.total_seconds() > 0:
                    speed_list.append(convert_meters_per_second_to_miles_per_hour(distance / time_diff.total_seconds()))
                    elapsed_time += time_diff.total_seconds()
                else:
                    speed_list.append(0)

                time_list.append(str(timedelta(seconds=elapsed_time)))

            if activity_type in Config.INDOOR_ACTIVITIES:
                activity_dict['heart_rate_indoor'] = {'x': time_list, 'y': hr_list}
            else:
                activity_dict['heart_rate'] = {'x': distance_list, 'y': hr_list}

            if np.average(hr_list) > 0:
                if 'heart_rate_indoor' in activity_dict:
                    data_dict['heart_rate'] = generate_plot(
                        activity_dict['heart_rate_indoor'],
                        'Heart Rate',
                        'BPM',
                        'Time'
                    )

                if 'heart_rate' in activity_dict:
                    data_dict['heart_rate'] = generate_plot(
                        activity_dict['heart_rate'],
                        'Heart Rate',
                        'BPM',
                        'Distance'
                    )

            if activity_type in Config.INDOOR_ACTIVITIES:
                activity_dict['speed_indoor'] = {'x': time_list, 'y': speed_list}
            else:
                activity_dict['speed'] = {'x': distance_list, 'y': speed_list}

            if np.average(speed_list) > 0:
                if 'speed_indoor' in activity_dict:
                    data_dict['speed'] = generate_plot(
                        activity_dict['speed_indoor'],
                        'Speed',
                        'MPH',
                        'Time'
                    )
                if 'speed' in activity_dict:
                    data_dict['speed'] = generate_plot(
                        activity_dict['speed'],
                        'Speed',
                        'MPH',
                        'Distance'
                    )

            activity_dict['elevation'] = {
                'x': distance_list,
                'y': [convert_meters_to_feet(point.elevation) for point in segment.points]
            }

            if activity_type not in Config.INDOOR_ACTIVITIES:
                data_dict['elevation'] = generate_plot(
                    activity_dict['elevation'],
                    'Elevation',
                    'Feet',
                    'Distance'
                )

    return data_dict

def get_activity_fit_file(activity_id, filepath):
    """
    This function takes an activity_id and filepath as parameters. It searches for the .fit file associated with the
    activity_id in the specified filepath. It extracts the time, elevation, distance, speed, heart rate, cadence, and
    temperature from the file. Finally, it plots the speed, elevation, and heart rate vs distance.

    :param activity_id: (datatype: str) The activity_id of the activity associated with the .fit file.
    :param filepath: (datatype: str) The filepath to the .fit file.
    :return: data_dict: (datatype: dict) A dictionary with the data to be plotted.
    """
    time_list = []
    distance_list = []
    altitude_list = []
    speed_list = []
    hr_list = []
    cadence_list = []
    temperature_list = []
    power_list = []
    data_dict = {}
    decompress_gz_file(filepath)
    count = 0
    activity_dict = {}

    activity_data = db.session.get(Activity, activity_id)
    activity_type = activity_data.activity_type
    activity_dir = activity_data.filename.split("/")[0]
    filename = activity_data.filename.split("/")[1]
    input_file_path = f'{filepath}/{activity_dir}'
    output_file = Config.DECOMPRESSED_ACTIVITY_FILES_FOLDER + '/' + filename.split('.gz')[0]
    fitFile = FitFile(output_file)

    for file in os.listdir(input_file_path):
        if file == filename:
            filepath = os.path.join(input_file_path, file)
            break  # Stop searching once the file is found.

    # for lap in fitFile.get_messages('session'):
    #     print('Lap:')
    #     for lap_info in lap:
    #         print(f'{lap_info.name} - {lap_info.value}')

    for record in fitFile.get_messages("record"):
        for data in record:
            if data.name == 'timestamp':
                count += 1
                if count == 1:
                    initial_time = data.value
                elapsed_time = (data.value - initial_time).total_seconds()
                time_list.append(Database.convert_seconds_to_time_format(elapsed_time))

            # Append activity distance to the distance_list
            if data.name == 'distance':
                try:
                    distance = convert_meter_to_mile(data.value)
                except KeyError as e:
                    if len(distance_list) > 0:
                        distance_list.append(distance_list[-1])
                    else:
                        distance_list.append(0)
                else:
                    if distance is None:
                        distance_list.append(0)
                    else:
                        distance_list.append(distance)

            # Append activity altitude to the altitude_list
            if data.name == 'enhanced_altitude':
                try:
                    altitude = round(convert_meters_to_feet(data.value), 2)
                except KeyError as e:
                    print(f'ERROR: {e}. Skipping for now.')
                    if len(altitude_list) > 0:
                        altitude_list.append(altitude_list[-1])
                except IndexError as e:
                    print(f'ERROR: {e}. Skipping for now.')
                    if len(altitude_list) > 0:
                        altitude_list.append(altitude_list[-1])
                    else:
                        altitude_list.append(0)
                else:
                    if altitude is None:
                        altitude_list.append(0)
                    else:
                        altitude_list.append(altitude)

            # Append speed to the speed_list
            if data.name == 'enhanced_speed':
                try:
                    speed = convert_meters_per_second_to_miles_per_hour(data.value)
                except KeyError as e:
                    print(f'ERROR: {e}. Skipping for now.')
                    if len(speed_list) > 0:
                        speed_list.append(speed_list[-1])
                    else:
                        speed_list.append(0)
                else:
                    if speed is None:
                        speed_list.append(0)
                    else:
                        speed_list.append(speed)

            # Append activity heart_rate to the hr_list
            if data.name == 'heart_rate':
                try:
                    heart_rate = data.value
                except KeyError as e:
                    print(f'ERROR: {e}. Skipping for now.')
                    if len(hr_list) > 0:
                        hr_list.append(hr_list[-1])
                    else:
                        hr_list.append(0)
                else:
                    if heart_rate is None:
                        hr_list.append(0)
                    else:
                        hr_list.append(heart_rate)

            # Append activity cadence to the cadence_list
            if data.name == 'cadence':
                try:
                    cadence = data.value
                except KeyError as e:
                    print(f'ERROR: {e}. Skipping for now.')
                    if len(cadence_list) > 0:
                        cadence_list.append(cadence_list[-1])
                    else:
                        cadence_list.append(0)
                else:
                    if cadence is None:
                        cadence_list.append(0)
                    else:
                        cadence_list.append(cadence)

            # Append activity temperature to the temperature_list
            if data.name == 'temperature':
                try:
                    temperature = convert_celsius_to_fahrenheit(data.value)
                except KeyError as e:
                    print(f'ERROR: {e}. Skipping for now.')
                    if len(temperature_list) > 0:
                        temperature_list.append(temperature_list[-1])
                    else:
                        temperature_list.append(0)
                else:
                    if temperature is None:
                        temperature_list.append(0)
                    else:
                        temperature_list.append(temperature)

            # Append activity power to the power_list
            if data.name == 'power':
                try:
                    power = data.value
                except KeyError as e:
                    print(f'ERROR: {e}. Skipping for now.')
                    if len(power_list) > 0:
                        power_list.append(power_list[-1])
                    else:
                        power_list.append(0)
                else:
                    if power is None:
                        power_list.append(0)
                    else:
                        power_list.append(power)

        if len(distance_list) != count:
            distance_list.append(0)

        if len(altitude_list) != count:
            altitude_list.append(0)
        activity_dict['elevation'] = {'x': distance_list, 'y': altitude_list}

        if len(speed_list) != count:
            speed_list.append(0)
        activity_dict['speed'] = {'x': distance_list, 'y': speed_list}

        if len(hr_list) != count:
            hr_list.append(0)

        if activity_type in Config.INDOOR_ACTIVITIES:
            activity_dict['heart_rate_indoor'] = {'x': time_list, 'y': hr_list}
        else:
            activity_dict['heart_rate'] = {'x': distance_list, 'y': hr_list}

        if len(cadence_list) != count:
            cadence_list.append(0)

        if activity_type in Config.INDOOR_ACTIVITIES:
            activity_dict['cadence_indoor'] = {'x': time_list, 'y': cadence_list}
        else:
            activity_dict['cadence'] = {'x': distance_list, 'y': cadence_list}

        if len(temperature_list) != count:
            temperature_list.append(0)

        if activity_type in Config.INDOOR_ACTIVITIES:
            activity_dict['temperature_indoor'] = {'x': time_list, 'y': temperature_list}
        else:
            activity_dict['temperature'] = {'x': distance_list, 'y': temperature_list}

        if len(power_list) != count:
            power_list.append(0)

        if activity_type in Config.INDOOR_ACTIVITIES:
            activity_dict['power_indoor'] = {'x': time_list, 'y': power_list}
        else:
            activity_dict['power'] = {'x': distance_list, 'y': power_list}

    if 'speed' in activity_dict and np.average(speed_list) > 0:
        data_dict['speed'] = generate_plot(
            activity_dict['speed'],
            'Speed',
            'MPH',
            'Distance'
        )

    if 'elevation' in activity_dict and np.average(distance_list) > 0:
        data_dict['elevation'] = generate_plot(
            activity_dict['elevation'],
            'Elevation',
            'Ft',
            'Distance'
        )

    if 'heart_rate' in activity_dict and np.average(hr_list) > 0:
        data_dict['heart_rate'] = generate_plot(
            activity_dict['heart_rate'],
            'Heart Rate',
            'BPM',
            'Distance'
        )

    if 'heart_rate_indoor' in activity_dict and np.average(hr_list) > 0:
        data_dict['heart_rate'] = generate_plot(
            activity_dict['heart_rate_indoor'],
            'Heart Rate',
            'BPM',
            'Time'
        )

    if 'cadence' in activity_dict and np.average(cadence_list) > 0:
        data_dict['cadence'] = generate_plot(
            activity_dict['cadence'],
            'Cadence',
            'RPM',
            'Distance'
        )

    if 'cadence_indoor' in activity_dict and np.average(cadence_list) > 0:
        data_dict['cadence'] = generate_plot(
            activity_dict['cadence_indoor'],
            'Cadence',
            'Strokes Per Minute',
            'Time'
        )

    if 'temperature' in activity_dict and np.average(temperature_list) > 0:
        data_dict['temperature'] = generate_plot(
            activity_dict['temperature'],
            'Temperature',
            'F',
            'Distance'
        )

    if 'temperature_indoor' in activity_dict and np.average(temperature_list) > 0:
        data_dict['temperature'] = generate_plot(
            activity_dict['temperature_indoor'],
            'Temperature',
            'F',
            'Time'
        )

    if 'power' in activity_dict and np.average(power_list) > 0:
        data_dict['power'] = generate_plot(
            activity_dict['power'],
            'Power',
            'Watts',
            'Distance'
        )

    if 'power_indoor' in activity_dict and np.average(power_list) > 0:
        data_dict['power'] = generate_plot(
            activity_dict['power_indoor'],
            'Power',
            'Watts',
            'Time'
        )

    return data_dict


@main.route('/')
def index():
    """
    Function and route for the home page.
    :return: Renders the index.html page.
    """
    return render_template('index.html')


@main.route('/activities', methods=['POST', 'GET'])
def activity():
    """
    Function and route for the activities page. If the request method is POST, then this function will get all the data
    from the filter options and query the database based off the filter(s) that were chosen. If the request method is
    GET, then all the data wil be queried from the database. The filters that have max and min values will be populated
    with those values from the max and min values that are stored in the database. Graphs will be generated for moving
    time, distance, average speed, max speed, and elevation gain from the selected data.

    :return: Renders the activities.html page.
    """
    activities = ''
    num_of_activities = 0
    date_format = '%Y-%m-%d'
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', Config.PER_PAGE, type=int)

    # Attempt to interact with the database by querying the activity data. Raise an error and return the error page if
    # a db does not exist.
    try:
        Activity.query.all()
    except OperationalError as e:
        db_error_message = str(e).split('(sqlite3.OperationalError)')[-1].split(':')[0]
        print(f'db_error_message: <{db_error_message}>')
        if db_error_message == ' no such table':
            error_message = 'An activities database was not found.'
        else:
            error_message = f'Some other db error was thrown: {e}'
        return render_template('error.html', error_message=error_message)

    activity_filters = session['filters'] = {
        'activity-search': request.form.get('activity-search') or '',
        'type-options': request.form.get('type-options'),
        'gear-options': request.form.get('gear-options'),
        'start-date': request.form.get('start-date'),
        'end-date': request.form.get('end-date'),
        'commute': request.form.get('commute') or None,
        'more-than-distance': request.form.get('more-than-distance'),
        'less-than-distance': request.form.get('less-than-distance'),
        'more-than-elevation-gain': request.form.get('more-than-elevation-gain'),
        'less-than-elevation-gain': request.form.get('less-than-elevation-gain'),
        'more-than-highest-elevation': request.form.get('more-than-highest-elevation'),
        'less-than-highest-elevation': request.form.get('less-than-highest-elevation'),
        'more-than-seconds': request.form.get('more-than-seconds'),
        'more-than-minutes': request.form.get('more-than-minutes'),
        'more-than-hours': request.form.get('more-than-hours'),
        'less-than-seconds': request.form.get('less-than-seconds'),
        'less-than-minutes': request.form.get('less-than-minutes'),
        'less-than-hours': request.form.get('less-than-hours'),
        'more-than-average-speed': request.form.get('more-than-average-speed'),
        'less-than-average-speed': request.form.get('less-than-average-speed'),
        'more-than-max-speed': request.form.get('more-than-max-speed'),
        'less-than-max-speed': request.form.get('less-than-max-speed')
    }
    # Config.TEXT_SEARCH = request.form.get('activity-search') or ''
    # Config.SELECTED_ACTIVITY_TYPE = request.form.get('type-options')
    # Config.SELECTED_ACTIVITY_GEAR = request.form.get('gear-options')
    # Config.START_DATE = request.form.get('start-date')
    # Config.END_DATE = request.form.get('end-date')
    # Config.COMMUTE = request.form.get('commute') or None
    # Config.MIN_DISTANCE_VALUE = request.form.get('more-than-distance')
    # Config.MAX_DISTANCE_VALUE = request.form.get('less-than-distance')
    # Config.MIN_ELEVATION_GAIN_VALUE = request.form.get('more-than-elevation-gain')
    # Config.MAX_ELEVATION_GAIN_VALUE = request.form.get('less-than-elevation-gain')
    # Config.MIN_HIGHEST_ELEVATION_VALUE = request.form.get('more-than-highest-elevation')
    # Config.MAX_HIGHEST_ELEVATION_VALUE = request.form.get('less-than-highest-elevation')
    # Config.MORE_THAN_SECONDS_VALUE = request.form.get('more-than-seconds')
    # Config.MORE_THAN_MINUTES_VALUE = request.form.get('more-than-minutes')
    # Config.MORE_THAN_HOURS_VALUE = request.form.get('more-than-hours')
    # Config.LESS_THAN_SECONDS_VALUE = request.form.get('less-than-seconds')
    # Config.LESS_THAN_MINUTES_VALUE = request.form.get('less-than-minutes')
    # Config.LESS_THAN_HOURS_VALUE = request.form.get('less-than-hours')
    # Config.MIN_AVERAGE_SPEED_VALUE = request.form.get('more-than-average-speed')
    # Config.MAX_AVERAGE_SPEED_VALUE = request.form.get('less-than-average-speed')
    # Config.MIN_MAX_SPEED_VALUE = request.form.get('more-than-max-speed')
    # Config.MAX_MAX_SPEED_VALUE = request.form.get('less-than-max-speed')

    # GET request when the page loads
    if request.method == 'GET':

        # print(f'session is: {session}')

        if 'filters' not in session:

            print('filters is not in session')
            session['filters'] = {}
        else:
            print(f'session[filters] from GET is: {session["filters"]}')

        query_string = Activity.query.order_by(Activity.start_time.desc())

        activities = query_string.limit(per_page).offset((page - 1) * per_page).all()
        num_of_activities = query_string.count()
        total_pages = (num_of_activities + per_page - 1) // per_page

    activity_date_newest = str((Activity.query.order_by(Activity.start_time.desc()).first().start_time)).split(' ')[0]
    activity_date_oldest = str((Activity.query.order_by(Activity.start_time).first().start_time)).split(' ')[0]

    # POST request when the filter form is submitted
    if request.method == 'POST':

        session['filters'] = request.form.to_dict()
        activity_filters = session.get('filters', {})

        if activity_filters['start-date'] > activity_filters['end-date']:
            print('Start date can\'t be less than end date')
            activity_filters['start-date'] = activity_filters['end-date']

        more_than_value = convert_time_to_seconds(
            activity_filters['more-than-seconds'],
            activity_filters['more-than-minutes'],
            activity_filters['more-than-hours']
        )

        less_than_value = convert_time_to_seconds(
            activity_filters['less-than-seconds'],
            activity_filters['less-than-minutes'],
            activity_filters['less-than-hours']
        )

        # print(f'session.get(filters).get(activity-search) from POST is: {session.get("filters", {}).get("activity-search")}')
        # print(f'session.get(filters) from POST is: {session.get("filters", {})}')

        filters = {}

        if Config.SELECTED_ACTIVITY_TYPE != 'All':
            filters['activity_type'] = Config.SELECTED_ACTIVITY_TYPE

        if Config.SELECTED_ACTIVITY_GEAR != 'All':
            filters['activity_gear'] = Config.SELECTED_ACTIVITY_GEAR

        if Config.COMMUTE == 'commute':
            filters['commute'] = 1

        print(f'activity_filter["end-date"] is: {activity_filters["end-date"]}')

        # Convert date string to datetime object
        datetime_object = datetime.strptime(activity_filters['end-date'], date_format)

        # Add one day to datetime object
        new_date_object = datetime_object + timedelta(days=1)

        # Convert datetime object back to string
        activity_filters['end-date'] = new_date_object.strftime(date_format)

        query_string = (
            Activity
            .query
            .filter_by(**filters)
            # .filter(ilike_op(Activity.activity_name, f'%{request.form.get("activity-search") or ""}%'))
            # .filter(ilike_op(Activity.activity_name, f'%{Config.TEXT_SEARCH}%'))
            # .filter(ilike_op(Activity.activity_name, f'%{text_search}%'))  # Original
            .filter(ilike_op(Activity.activity_name, f'%{activity_filters["activity-search"]}%'))
            # .filter(ilike_op(Activity.activity_description, f'%{Config.TEXT_SEARCH}%'))

            # Activities SQL Query
            .filter(activity_filters['start-date'] <= Activity.start_time)
            .filter(activity_filters['end-date'] >= Activity.start_time)
            .filter(activity_filters['more-than-distance'] <= Activity.distance)
            # .filter(Config.MIN_DISTANCE_VALUE <= Activity.distance)
            .filter(activity_filters['less-than-distance'] >= Activity.distance)
            .filter(activity_filters['more-than-elevation-gain'] <= Activity.elevation_gain)
            .filter(activity_filters['less-than-elevation-gain'] >= Activity.elevation_gain)
            .filter(activity_filters['more-than-highest-elevation'] <= Activity.highest_elevation)
            .filter(activity_filters['less-than-highest-elevation'] >= Activity.highest_elevation)
            .filter(more_than_value <= Activity.moving_time_seconds)
            .filter(less_than_value >= Activity.moving_time_seconds)
            .filter(activity_filters['more-than-average-speed'] <= Activity.average_speed)
            .filter(activity_filters['less-than-average-speed'] >= Activity.average_speed)
            .filter(activity_filters['more-than-max-speed'] <= Activity.max_speed)
            .filter(activity_filters['less-than-max-speed'] >= Activity.max_speed)

            # .filter(Config.START_DATE <= Activity.start_time)
            # .filter(Config.END_DATE >= Activity.start_time)
            # .filter(Config.MIN_DISTANCE_VALUE <= Activity.distance)
            # .filter(Config.MAX_DISTANCE_VALUE >= Activity.distance)
            # .filter(Config.MIN_ELEVATION_GAIN_VALUE <= Activity.elevation_gain)
            # .filter(Config.MAX_ELEVATION_GAIN_VALUE >= Activity.elevation_gain)
            # .filter(Config.MIN_HIGHEST_ELEVATION_VALUE <= Activity.highest_elevation)
            # .filter(Config.MAX_HIGHEST_ELEVATION_VALUE >= Activity.highest_elevation)
            # .filter(more_than_value <= Activity.moving_time_seconds)
            # .filter(less_than_value >= Activity.moving_time_seconds)
            # .filter(Config.MIN_AVERAGE_SPEED_VALUE <= Activity.average_speed)
            # .filter(Config.MAX_AVERAGE_SPEED_VALUE >= Activity.average_speed)
            # .filter(Config.MIN_MAX_SPEED_VALUE <= Activity.max_speed)
            # .filter(Config.MAX_MAX_SPEED_VALUE >= Activity.max_speed)

            .order_by(Activity.start_time  # Order activities by date
            # .order_by(Activity.average_speed  # Order activities by average speed
            # .order_by(Activity.max_speed  # Order activities by max speed
            # .order_by(Activity.distance  # Order activities by distance
            # .order_by(Activity.elevation_gain  # Order activities by elevation gain
            # .order_by(Activity.highest_elevation  # Order activities by highest elevation
            # .order_by(Activity.moving_time_seconds  # Order activities by moving time
            .desc())  # Show newest activities first
        )
        activities = query_string.limit(per_page).offset((page - 1) * per_page).all()

        num_of_activities = query_string.count()

        print(f'filters from POST is: {activity_filters}')

    # activity_filters = session.get('filters', {})

    total_pages = (num_of_activities + per_page - 1) // per_page

    # Display the number of activities that are being displayed.
    if num_of_activities == 0:
        num_of_activities_string = 'No Activities to Show'
    elif num_of_activities == 1:
        num_of_activities_string = 'Showing 1 Activity'
    else:
        num_of_activities_string = f'Showing {num_of_activities} Activities'

    # Get the minimum and maximum of all the activity distances for the dropdown boxes
    # min_activities_distance = (Activity.query.order_by(Activity.distance).
    #                            first().distance)
    # max_activities_distance = (Activity.query.order_by(Activity.distance.desc()).
    #                            first().distance)
    activity_filters['more-than-distance'] = (Activity.query.order_by(Activity.distance).
                               first().distance)
    activity_filters['less-than-distance'] = (Activity.query.order_by(Activity.distance.desc()).
                               first().distance)

    # Get the minimum and maximum of all the activity elevation gains for the dropdown boxes
    # min_activities_elevation_gain = (Activity.query.order_by(Activity.elevation_gain).
    #                                  first().elevation_gain)
    # max_activities_elevation_gain = (Activity.query.order_by(Activity.elevation_gain.desc()).
    #                                  first().elevation_gain)
    activity_filters['more-than-elevation-gain'] = (Activity.query.order_by(Activity.elevation_gain).
                                     first().elevation_gain)
    activity_filters['less-than-elevation-gain'] = (Activity.query.order_by(Activity.elevation_gain.desc()).
                                     first().elevation_gain)

    # Get the minimum and maximum of all the activity elevations for the dropdown boxes
    # min_activities_highest_elevation = Activity.query.order_by(Activity.highest_elevation).first().highest_elevation
    # max_activities_highest_elevation = (Activity.query.order_by(Activity.highest_elevation.desc()).
    #                                     first().highest_elevation)
    activity_filters['more-than-highest-elevation'] = Activity.query.order_by(Activity.highest_elevation).first().highest_elevation
    activity_filters['less-than-highest-elevation'] = (Activity.query.order_by(Activity.highest_elevation.desc()).
                                        first().highest_elevation)

    # Get the minimum and maximum of all the activity moving times for the dropdown boxes
    longest_moving_time_split = split_time_string(Activity.query.order_by(Activity.moving_time.desc()).
                                                  first().moving_time)
    shortest_moving_time_split = split_time_string(Activity.query.order_by(Activity.moving_time).
                                                   first().moving_time)
    activity_filters['more-than-hours'] = shortest_moving_time_split[0]
    activity_filters['more-than-minutes'] = shortest_moving_time_split[1]
    activity_filters['more-than-seconds'] = shortest_moving_time_split[2]
    activity_filters['less-than-hours'] = longest_moving_time_split[0]
    activity_filters['less-than-minutes'] = longest_moving_time_split[1]
    activity_filters['less-than-seconds'] = longest_moving_time_split[2]

    # Get the minimum and maximum of all the activity average speeds for the dropdown boxes
    activity_filters['more-than-average-speed'] = (Activity.query.order_by(Activity.average_speed).
                                    first().average_speed)
    activity_filters['less-than-average-speed'] = (Activity.query.order_by(Activity.average_speed.desc()).
                                    first().average_speed)

    # Get the minimum and maximum of all the activity max speeds for the dropdown boxes
    # min_activities_max_speed = (Activity.query.order_by(Activity.max_speed).
    #                             first().max_speed)
    # max_activities_max_speed = (Activity.query.order_by(Activity.max_speed.desc()).
    #                             first().max_speed)
    activity_filters['more-than-max-speed'] = (Activity.query.order_by(Activity.max_speed).
                                first().max_speed)
    activity_filters['less-than-max-speed'] = (Activity.query.order_by(Activity.max_speed.desc()).
                                first().max_speed)

    # Group the activity types and create a list of each activity type to be used to populate the dropdown menu options.
    activity_type_categories = (Activity.query.with_entities(Activity.activity_type).
                                group_by(Activity.activity_type).all())
    activity_type_list = [point.activity_type for point in activity_type_categories]

    # Group the activity gear and create a list of each activity gear to be used to populate the dropdown menu options.
    activity_gear_categories = (Activity.query.with_entities(Activity.activity_gear).
                                group_by(Activity.activity_gear).all())
    activity_gear_list = [gear.activity_gear for gear in activity_gear_categories]

    # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # div for activity Date vs Moving Time.
    # moving_time_data = {
    #     'Activity Moving Time': [point.moving_time_seconds for point in activities],
    #     'Activity Date': [point.start_time for point in activities]
    # }
    # moving_time_df = pd.DataFrame(moving_time_data)
    # moving_time_fig = px.line(
    #     moving_time_df,
    #     x='Activity Date',
    #     y='Activity Moving Time',
    #     title="Moving Time vs Activity Date"
    # )
    # plot_moving_time_data = moving_time_fig.to_html(full_html=False)
    #
    # # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # # div for activity Date vs Distance.
    # distance_data = {
    #     'Activity Distance': [point.distance for point in activities],
    #     'Activity Date': [point.start_time for point in activities]
    # }
    # distance_df = pd.DataFrame(distance_data)
    # distance_fig = px.line(
    #     distance_df,
    #     x='Activity Date',
    #     y='Activity Distance',
    #     title="Distance vs Activity Date"
    # )
    # plot_distance_data = distance_fig.to_html(full_html=False)
    #
    # # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # # div for activity Date vs Average Speed.
    # avg_speed_data = {
    #     'Activity Average Speed': [point.average_speed for point in activities],
    #     'Activity Date': [point.start_time for point in activities]
    # }
    # avg_speed_df = pd.DataFrame(avg_speed_data)
    # avg_speed_fig = px.line(
    #     avg_speed_df,
    #     x='Activity Date',
    #     y='Activity Average Speed',
    #     title="Average Speed vs Activity Date"
    # )
    # plot_avg_speed_data = avg_speed_fig.to_html(full_html=False)
    #
    # # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # # div for activity Date vs Max Speed.
    # max_speed_data = {
    #     'Activity Max Speed': [point.max_speed for point in activities],
    #     'Activity Date': [point.start_time for point in activities]
    # }
    # max_speed_df = pd.DataFrame(max_speed_data)
    # max_speed_fig = px.line(
    #     max_speed_df,
    #     x='Activity Date',
    #     y='Activity Max Speed',
    #     title="Max Speed vs Activity Date"
    # )
    # plot_max_speed_data = max_speed_fig.to_html(full_html=False)
    #
    # # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # # div for activity Date vs Elevation Gain.
    # elevation_gain_data = {
    #     'Activity Elevation Gain': [point.elevation_gain for point in activities],
    #     'Activity Date': [point.start_time for point in activities]
    # }
    # elevation_gain_df = pd.DataFrame(elevation_gain_data)
    # elevation_gain_fig = px.line(
    #     elevation_gain_df,
    #     x='Activity Date',
    #     y='Activity Elevation Gain',
    #     title="Elevation Gain vs Activity Date"
    # )
    # plot_elevation_gain_data = elevation_gain_fig.to_html(full_html=False)

    return render_template(
        'activities.html',
        activities=activities,
        activity_type_list=activity_type_list,
        activity_gear_list=activity_gear_list,
        start_date=activity_date_oldest,
        end_date=activity_date_newest,
        num_of_activities_string=num_of_activities_string,
        # min_activities_distance=min_activities_distance,
        # max_activities_distance=max_activities_distance,
        # min_activities_elevation_gain=min_activities_elevation_gain,
        # max_activities_elevation_gain=max_activities_elevation_gain,
        # min_activities_highest_elevation=min_activities_highest_elevation,
        # max_activities_highest_elevation=max_activities_highest_elevation,
        # longest_moving_time_split=longest_moving_time_split,
        # shortest_moving_time_split=shortest_moving_time_split,
        # min_activities_average_speed=min_activities_average_speed,
        # max_activities_average_speed=max_activities_average_speed,
        # min_activities_max_speed=min_activities_max_speed,
        # max_activities_max_speed=max_activities_max_speed,
        # plot_moving_time_data=plot_moving_time_data,
        # plot_distance_data=plot_distance_data,
        # plot_avg_speed_data=plot_avg_speed_data,
        # plot_max_speed_data=plot_max_speed_data,
        # plot_elevation_gain_data=plot_elevation_gain_data,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        num_of_activities=num_of_activities,
        # text_search=Config.TEXT_SEARCH,
        # selected_activity_type=Config.SELECTED_ACTIVITY_TYPE,
        # selected_activity_gear=Config.SELECTED_ACTIVITY_GEAR,
        # selected_start_date=Config.START_DATE,
        # selected_end_date=Config.END_DATE,
        # commute=Config.COMMUTE,
        # min_distance_value=Config.MIN_DISTANCE_VALUE,
        # max_distance_value=Config.MAX_DISTANCE_VALUE,
        # min_elevation_gain_value=Config.MIN_ELEVATION_GAIN_VALUE,
        # max_elevation_gain_value=Config.MAX_ELEVATION_GAIN_VALUE,
        # min_highest_elevation_value=Config.MIN_HIGHEST_ELEVATION_VALUE,
        # max_highest_elevation_value=Config.MAX_HIGHEST_ELEVATION_VALUE,
        # more_than_seconds_value=Config.MORE_THAN_SECONDS_VALUE,
        # more_than_minutes_value=Config.MORE_THAN_MINUTES_VALUE,
        # more_than_hours_value=Config.MORE_THAN_HOURS_VALUE,
        # less_than_seconds_value=Config.LESS_THAN_SECONDS_VALUE,
        # less_than_minutes_value=Config.LESS_THAN_MINUTES_VALUE,
        # less_than_hours_value=Config.LESS_THAN_HOURS_VALUE,
        # min_average_speed_value=Config.MIN_AVERAGE_SPEED_VALUE,
        # max_average_speed_value=Config.MAX_AVERAGE_SPEED_VALUE,
        # min_max_speed_value=Config.MIN_MAX_SPEED_VALUE,
        # max_max_speed_value=Config.MAX_MAX_SPEED_VALUE,
        activity_filters=activity_filters
    )


@main.route('/activity/<activity_id>', methods=['GET'])
def activity_info(activity_id):
    """
    This function handles when an individual activity file is displayed. It takes the activity_id as an input parameter
    and shows the activity details and shows the plotly graphs for speed and elevation and heart rate if applicable. The
    filetype is determined and the appropriate function is called to handle the filetype date.
    :param activity_id: (datatype: str)The unique id that was given to the selected activity.
    :return: The rendered individual_activity.html page and activity_data(An instance of the Activity db class) and
    activity_graph_data(dict).
    """
    # TODO: If activity is workout or something else indoor, disable speed/distance/gps data.
    activity_data = db.session.get(Activity, activity_id)
    try:
        if activity_data.filename.split(".")[-1] == 'gz':
            filetype = activity_data.filename.split(".")[-2]
        else:
            filetype = activity_data.filename.split(".")[-1]
    except AttributeError as e:
        print(f'Error: {e}')
        print('This may have happened because an associated file could not be found for this activity. Was this '
              'activity entered manually?')
        return render_template('index.html')

    # Define the upload folder path
    filepath = os.path.join(os.getcwd(), Config.UPLOAD_FOLDER)

    # Search for .gpx file associated with the provided activity ID.
    if filetype == 'gpx':
        activity_graph_data = get_activity_gpx_file(activity_id, filepath)
    elif filetype == 'fit':
        activity_graph_data = get_activity_fit_file(activity_id, filepath)
    elif filetype == 'tcx':
        activity_graph_data = get_activity_tcx_file(activity_id, filepath)
    else:
        error_message = f'The activity file({activity_data.filename.split("/")[-1]}) was not found.'
        return render_template('error.html', error_message=error_message)

    return render_template(
        'individual_activity.html',
        activity_data=activity_data,
        activity_graph_data=activity_graph_data
    )

@main.route('/create-db', methods=['POST', 'GET'])
def create_db():
    """
    Function and route for the create db page, where the user will create the db after selecting the directory where the
    activity data is.
    :return: Renders the create_db.html page
    """
    if request.method == 'GET':
        return render_template(
            'create_db.html',
            timezone=Config.USER_TIMEZONE
        )

    elif request.method == 'POST':
        try:
            convert_activity_csv_to_db()

        except AttributeError as e:
            if 'NoneType' in str(e):
                message = '"strava_activities.csv" has not been found!!'
            else:
                message = e

        except ValueError as e:
            if 'NaN' in str(e):
                message = 'Cannot find sufficient data!!'
            else:
                message = 'Cannot find all expected columns!!'

        else:
            message = f'File "strava_activities.csv" has been uploaded successfully!!'

        print(message)

        return render_template(
            'create_db.html',
            timezone=Config.USER_TIMEZONE,
            message=message
        )

    else:
        return render_template(
            'index.html'
        )

@main.route('/upload', methods=['POST', 'GET'])
def upload_activity():
    """
    Function and route for the upload activity page, where the user will upload activity data.
    :return: Renders the upload_activities.html page.
    """
    return render_template(
        'upload_activities.html',
        timezone=Config.USER_TIMEZONE
    )

# Route to handle the file upload
@main.route('/upload-file', methods=['GET', 'POST'])
def upload_file():
    """
    Get the full path to the directory that was chosen by the user and search for a file called 'strava_activities.csv'. Write
    the relative path to the strava_activities.csv file to the transfer_data.json file. Inform the user if the file has been
    found successfully or not.
    :return: (json) a json file with a message informing the user if the strava_activities.csv file was found or not.
    """
    app = create_app()

    uploaded_files = request.files.getlist('files')
    upload_directory = request.form.get('files')

    for file in uploaded_files:

        if os.path.basename(file.filename) == Config.TARGET_FILENAME:
            save_path = os.path.join(Config.UPLOAD_FOLDER, file.filename.split('/')[1])
            file.save(save_path)
            try:
                convert_activity_csv_to_db()
            except ValueError as e:
                if 'NaN' in str(e):
                    print('Cannot find sufficient data!!')
                    return jsonify({'message': 'Cannot find sufficient data!!'}), 400
                else:
                    print('Cannot find all expected columns!!')
                    return jsonify({'message': 'Cannot find all expected columns!!'}), 400
            else:
                transfer_data = {
                    "relative_path": file.filename.split('/')[0],
                    "absolute_path": os.path.abspath(os.path.join(app.root_path, file.filename.split('/')[0]))
                }
                json_file_data = json.dumps(transfer_data, indent=1)
                with open('transfer_data.json', 'w') as outfile:
                    outfile.write(json_file_data)

                print(f'File "{file.filename}" has been uploaded successfully!!')
                return jsonify({
                    'message': f'File "{file.filename}" has been uploaded successfully!!',
                    'file_name': file.filename,
                })

    return jsonify({
        "message": f"File '{Config.TARGET_FILENAME}' not found in the selected directory."
    })


@main.route('/settings', methods=['POST', 'GET'])
def settings():
    """
    Function and route for the settings page, where the user can modify settings.
    :return: Renders the settings.html page.
    """
    timezone_list = []
    for tz in pytz.all_timezones:
        timezone_list.append(tz)

    if request.method == 'POST':
        Config.USER_TIMEZONE = request.form.get('timezone-options')

    return render_template(
        'settings.html',
        timezone_list=timezone_list,
        current_timezone_selection=Config.USER_TIMEZONE,
    )


@main.route('/calorie-calculator', methods=['POST', 'GET'])
def calorie_calculator():
    """
    Function and route for the calorie calculator page, where the user cal calculate their calorie needs.
    :return: Renders the calorie_calculator.html page.
    """

    if request.method == 'POST':
        Config.USER_AGE = int(request.form.get('age'))
        Config.USER_GENDER = request.form.get('gender-options')
        Config.USER_WEIGHT = float(request.form.get('weight'))
        Config.USER_HEIGHT = float(request.form.get('height'))
        Config.USER_ACTIVITY_LEVEL = float(request.form.get('activity-level-options'))

        if Config.USER_ACTIVITY_LEVEL == 1.2:
            user_activity_level_readable = 'user_activity_level_readable'
        elif Config.USER_ACTIVITY_LEVEL == 1.375:
            user_activity_level_readable = 'Light Activity (Light exercise 1-3 days a week)'
        elif Config.USER_ACTIVITY_LEVEL == 1.55:
            user_activity_level_readable = 'Moderately Active (Moderate Exercise 3-5 days a week)'
        elif Config.USER_ACTIVITY_LEVEL == 1.75:
            user_activity_level_readable = 'Very Active (Hard Exercise 6-7 days a week)'
        else:
            user_activity_level_readable = 'Extra Active (Very Hard Exercise Daily)'

        if Config.USER_GENDER == 'Male':
            resting_metabolic_rate = round(
                66 + (6.23 * Config.USER_WEIGHT) + (12.7 * Config.USER_HEIGHT) - (6.8 * Config.USER_AGE), 2
            )
        if Config.USER_GENDER == 'Female':
            resting_metabolic_rate = round(
                655 + (4.35 * Config.USER_WEIGHT) + (4.7 * Config.USER_HEIGHT) - (4.7 * Config.USER_AGE), 2
            )

        maintain = round(resting_metabolic_rate * Config.USER_ACTIVITY_LEVEL, 2)
        lose_fast = round(maintain - 1000, 2)
        lose_moderate = round(maintain - 500, 2)
        lose_slow = round(maintain - 250, 2)
        gain_slow = round(maintain + 250, 2)
        gain_moderate = round(maintain + 500, 2)
        gain_fast = round(maintain + 1000, 2)

        return render_template(
            'calorie_calculator.html',
            user_age=Config.USER_AGE,
            user_gender=Config.USER_GENDER,
            user_weight=Config.USER_WEIGHT,
            user_height=Config.USER_HEIGHT,
            user_activity_level=Config.USER_ACTIVITY_LEVEL,
            readable_user_activity_level=user_activity_level_readable,
            resting_metabolic_rate=resting_metabolic_rate,
            lose_fast=lose_fast,
            lose_moderate=lose_moderate,
            lose_slow=lose_slow,
            maintain=maintain,
            gain_slow=gain_slow,
            gain_moderate=gain_moderate,
            gain_fast=gain_fast
        )
    else:
        return render_template(
            'calorie_calculator.html',
            user_age = Config.USER_AGE,
            user_gender = Config.USER_GENDER,
            user_weight = Config.USER_WEIGHT,
            user_height = Config.USER_HEIGHT,
            user_activity_level = Config.USER_ACTIVITY_LEVEL
        )


@main.route('/hr-zones', methods=['POST', 'GET'])
def heart_rate_zones():
    """
    Function and route for the heart rate zone page, where the users heart rate zones will be calculated.
    :return: Renders the heart_rate_zones.html page.
    """
    if request.method == 'POST':
        Config.USER_AGE = int(request.form.get('age'))
        activity_type = request.form.get('activity-options')

        print(f'activity_type is: {activity_type}')

        # Using the Tanaka formula to calculate Max HR, which is more accurate for fit individuals.
        max_heart_rate = int(208 - (0.7 * Config.USER_AGE))  # Normal Max HR for running, hiking, walking, etc.
        if activity_type == 'cycling':
            max_heart_rate = int(208 - (0.7 * Config.USER_AGE)) - 9  # Cycling is ~5-10bpm lower because rider is seated
            # and using less muscle.
        if activity_type == 'swimming':
            max_heart_rate = int(208 - (0.7 * Config.USER_AGE)) - 14  # Swimming is ~10-15bpm lower because of the
            # horizontal position.
        if activity_type == 'rowing':
            max_heart_rate = int(208 - (0.7 * Config.USER_AGE)) - 5  # 5bpm lower because of being seated, but using
            # upper body.

        return render_template(
            'heart_rate_zones.html',
            user_age=Config.USER_AGE,
            zone1_low=int(max_heart_rate * 0.5),  # 50%
            zone1_high=int(max_heart_rate * 0.6),  # 60%
            zone2_high=int(max_heart_rate * 0.7),  # 70%
            zone3_high=int(max_heart_rate * 0.8),  # 80%
            zone4_high=int(max_heart_rate * 0.9),  # 90%
            zone5_high=max_heart_rate  # 100%
        )
    else:
        return render_template(
            'heart_rate_zones.html',
            user_age = Config.USER_AGE,
        )


@main.route('/error', methods=['POST', 'GET'])
def error(error_message):
    """
    Function and route for the upload activity page, where the user will upload activity data.
    :return: Renders the upload_activities.html page.
    """

    return render_template('error.html', error_message=error_message)
