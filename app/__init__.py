from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from database import Database
import fitdecode
import gzip
import os
import gpxpy
import json
import tcxparser
import xmltodict

db = SQLAlchemy()

def create_app():

    # Flask stuff
    app = Flask(__name__)

    # Configure and initialize the database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
    db.init_app(app)

    with app.app_context():
        from .routes import main  # import main from the routes file
        app.register_blueprint(main)  # register main in app

    UPLOAD_FOLDER = 'uploads'  # Define the directory where the activity files will be saved.
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER  # Define the directory where flask will save the uploaded files.
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Define the directory size in bytes.

    return app

DECOMPRESSED_ACTIVITY_FILES_FOLDER = 'decompressed_activity_files'  # Define the directory where decompressed files will
# be saved.

# Define constants
METER_TO_MILE = 0.000621371
MPS_TO_MPH = 2.23694
METER_TO_FOOT = 3.28084

# Ensure the upload and decompressed activities directories exists in the same directory of this program and if not,
# create them.
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DECOMPRESSED_ACTIVITY_FILES_FOLDER, exist_ok=True)

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


def convert_activity_csv_to_db():
    """
    This function creates an instance of the Database class (defined in database.py), drops(deletes) any existing
    database(Database.DATABASE_NAME), then creates a table(Database.TABLE_NAME) in the defined database
    (Database.DATABASE_NAME) with the defined columns(defined in the Database.convert_csv_to_df() method).
    :return: None
    """
    db = Database()
    db.drop_table(db.DATABASE_NAME)
    db.create_db_table(db.DATABASE_NAME, db.TABLE_NAME, db.convert_csv_to_df())


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


def plot_speed_vs_distance(speed_list, distance_list):
    """
    This function prepares the data to be plotted using Plotly. It takes two lists as parameters, converts them to
    Pandas dataframes, converts them to a figure, and finally converts the figure to an HTML div string. The speed list
     is plotted on the Y-Axis and the distance is plotted on the X-Axis.
    :param speed_list: (List of floats) The moving speed at any given time in the activity.
    :param distance_list: (List of floats) The distance at any given time of the activity.
    :return: The figure converted to an HTML div string.
    """
    # print(f'speed_list length is: {len(speed_list)}')
    # print(f'distance_list length is: {len(distance_list)}')

    if len(speed_list) == 0:
        print(f'elevation_list is empty. Returning from plot_speed_vs_distance()')
        return

    if len(distance_list) == 0:
        print(f'distance_list is empty. Returning from plot_speed_vs_distance()')
        return

    speed_data = {
        'Activity Speed(MPH)': speed_list,
        'Distance(Miles)': distance_list
    }
    speed_df = pd.DataFrame(speed_data)
    speed_fig = px.line(
        speed_df,
        x='Distance(Miles)',
        y='Activity Speed(MPH)',
        title='Speed vs Distance',
        # line_shape='spline' # This is supposed to smooth out the line.
    )
    speed_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))
    return speed_fig.to_html(full_html=False)


def plot_elevation_vs_distance(elevation_list, distance_list):
    """
    This function prepares the data to be plotted using Plotly. It takes two lists as parameters, converts them to
    Pandas dataframes, converts them to a figure, and finally converts the figure to an HTML div string. The elevation
    list is plotted on the Y-Axis and the distance is plotted on the X-Axis.
    :param elevation_list: (List of floats) The elevation at any given time in the activity.
    :param distance_list: (List of floats) The distance at any given time of the activity.
    :return: The figure converted to an HTML div string.
    """
    # print(f'elevation_list length is: {len(elevation_list)} and distance_list is: {len(distance_list)}')
    # print(f'elevation_list is: \n{elevation_list}')
    # print(f'distance_list is: \n{distance_list}')
    # print(f'type(distance_list) is: {type(distance_list[10])}')
    # print(f'type(elevation_list) is: {type(elevation_list[10])}')
    # for point in elevation_list:
    #     print(round(point, 1))

    if len(elevation_list) == 0:
        print(f'elevation_list is empty. Returning from plot_elevation_vs_distance()')
        return

    if len(distance_list) == 0:
        print(f'distance_list is empty. Returning from plot_elevation_vs_distance()')
        return

    elevation_data = {
        'Activity Elevation(Feet)': elevation_list,
        'Distance(Miles)': distance_list
    }
    elevation_df = pd.DataFrame(elevation_data)
    elevation_fig = px.line(
        elevation_df,
        x='Distance(Miles)',
        y='Activity Elevation(Feet)',
        title='Elevation vs Distance',
        # line_shape='spline' # This is supposed to smooth out the line.
    )
    # elevation_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))
    return elevation_fig.to_html(full_html=False)


def plot_heart_rate_vs_distance(heart_rate_list, distance_list):
    """
    This function prepares the data to be plotted using Plotly. It takes two lists as parameters, converts them to
    Pandas dataframes, converts them to a figure, and finally converts the figure to an HTML div string. The heart rate
    list is plotted on the Y-Axis and the distance is plotted on the X-Axis.
    :param heart_rate_list: (List of ints) The heart rate, in beats per minutes, at any given time in the activity.
    :param distance_list: (List of floats) The distance at any given time of the activity.
    :return: The figure converted to an HTML div string.
    """
    # print(f'heart_rate_list is: \n{heart_rate_list}')
    # print(f'distance_list is: \n{distance_list}')
    # print(f'type(distance_list) is: {type(distance_list[10])}')
    # print(f'type(heart_rate_list) is: {type(heart_rate_list[10])}')

    if len(heart_rate_list) == 0:
        print(f'heart_rate_list is empty. Returning from plot_heart_rate_vs_distance()')
        return

    if len(distance_list) == 0:
        print(f'distance_list is empty. Returning from plot_heart_rate_vs_distance()')
        return

    heart_rate_data = {
        'Heart Rate(BPM)': heart_rate_list,
        'Distance(Miles)': distance_list
    }
    heart_rate_df = pd.DataFrame(heart_rate_data)
    # print(f'heart_rate_df is: {heart_rate_df}')
    heart_rate_fig = px.line(
        heart_rate_df,
        x='Distance(Miles)',
        y='Heart Rate(BPM)',
        title='Heart Rate vs Distance',
        # line_shape='spline' # This is supposed to smooth out the line.
    )
    heart_rate_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))
    return heart_rate_fig.to_html(full_html=False)


def decompress_gz_file(input_file_path_and_name):
    """
    Decompress a .gz file. The file passed will be decompressed and the decompressed version will be saved in a
    directory within the directory where this program is located.
    :param input_file_path_and_name: (str) The filepath from where this program is running and the filename.
    :return: None
    """
    #TODO: handle the case where a file is passed to this function that is not a .gz file.
    output_file_name = input_file_path_and_name.split('/')[-1].split('.gz')[0]
    # print(f'input_file from decompress_gz_file is: {input_file_path_and_name}')
    # print(f'output_file from decompress_gz_file is: {output_file_name}')
    with gzip.open(input_file_path_and_name, 'rb') as f_in:
        with open(f'{DECOMPRESSED_ACTIVITY_FILES_FOLDER}/{output_file_name}', 'wb') as f_out:
        # with open(output_file, 'wb') as f_out:
                f_out.write(f_in.read())


def get_activity_tcx_file(activity_id, filepath):
    """

    :param activity_id:
    :param filepath:
    :return:
    """
    # print('In get_activity_tcx_file()')

    data_dict = {}
    speed_list = []
    distance_list = []
    time_list = []
    altitude_list = []
    position_list = []
    hr_list = []
    file_is_found = False

    # print(f'activity_id is: {activity_id}')
    activity_data = db.session.get(Activity, activity_id)
    # print(f'activity_data.filename is: {activity_data.filename}')
    filename = activity_data.filename.split("/")[-1]
    sub_dir = activity_data.filename.split("/")[0]
    # print(f'filename from get_activity_tcx_file() is: {filename}')
    input_file_path = f'{filepath}/{sub_dir}'
    # print(f'input_file_path from get_activity_tcx_file() is: {input_file_path}')
    # output_file = f'{activity_data.filename.split("/")[1].split(".")[0]}.tcx'

    for file in os.listdir(input_file_path):
        # if file.split('.')[-2] == 'tcx':
        #     print(f'file is: {file}')
        if file == filename:
            file_is_found = True
            filepath = os.path.join(input_file_path, file)
            # print(f'filepath from get_activity_tcx_file() is: {filepath}')
            decompress_gz_file(filepath)
            break  # Stop searching once the file is found.

    if file_is_found:
        with open(DECOMPRESSED_ACTIVITY_FILES_FOLDER + '/' + filepath.split('/')[-1].split('.gz')[0], 'r') as f:
            xml_string = f.read().strip()  # Strip leading/trailing whitespace

        #     # ~~~~~~~~~~ Testing this to see if it works ~~~~~~~~~~
        #     f.readline()
        #     xml_list = f.readlines()
        #     xml_string = ''.join(xml_list)
        #     # tcx = tcxparser.TCXParser(xml_string)
        #
        #     # print('filename head is:')
        #     # os.system(f'head {filepath}{filename}')
        #
        # tcx = tcxparser.TCXParser(xml_string)
            xml_dict = xmltodict.parse(xml_string)
        #
        # # Show activity data points
        # print(tcx.altitude_points())
        # print(tcx.distance_values())
        # print(tcx.time_values())
        # print(tcx.cadence_values())
        # print(tcx.hr_values())
        # print(tcx.position_values())
        # print(tcx.power_values())
        #
        # # ~~~~~~~~~~ End Test ~~~~~~~~~~

            # print(f'xml_dict is: {xml_dict}')
            # for value in range(len(xml_dict)):
            #     print(value)
            #['@xmlns', '@xmlns:xsi', '@xsi:schemaLocation', 'Activities', 'Author']
            # print(f'xml_dict.keys() is: {xml_dict.keys()}')
            # print(f'xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"] length is: {len(xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"])})')
            # print(f'xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"] keys are: {xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"].keys()})')
            # print(f'xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"]["Lap"] length is: {len(xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"]["Lap"])}')
            # print(f'xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"]["Lap"] is: {xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"]["Lap"]}')
            for activity in xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"]["Lap"]:
                # print(f'activity["Track"].keys() is: {activity["Track"].keys()}')
                try:
                    base = activity["Track"]["Trackpoint"]
                except TypeError as e:
                    print(e)
                    print(f'activity["Track"].keys() is: {activity["Track"].keys()}')
                # print(base)
                for data_point in base:

                    # Time data point was taken
                    # print(f'Time: {data_point["Time"]}')
                    time_list.append(data_point["Time"])

                    # Position values of the data point
                    try:
                        position_list.append(
                            (data_point["Position"]["LatitudeDegrees"], data_point["Position"]["LongitudeDegrees"])
                        )
                        # print(f'Longitude: {data_point["Position"]["LatitudeDegrees"]}')
                        # print(f'Longitude: {data_point["Position"]["LongitudeDegrees"]}')
                    except KeyError:
                        # print(f'No Positional Data is available!')
                        # print(f'No Positional Data is available! Appending {position_list[-1]}')
                        position_list.append(position_list[-1])

                    # Elevation value of the data point
                    try:
                        altitude_list.append(float(data_point["AltitudeMeters"]))
                        # print(f'Elevation: {data_point["AltitudeMeters"]}')
                    except KeyError:
                        # print(f'No Altitude Data is available!')
                        # print(f'No Altitude Data is available! Appending {altitude_list[-1]}')
                        altitude_list.append(altitude_list[-1])

                    # Distance value of the data point
                    try:
                        # print(f'float(data_point["DistanceMeters"]) is: {float(data_point["DistanceMeters"])}')
                        # print(f'float(distance_list[-1]) is: {float(distance_list[-1])}')
                        if len(distance_list) > 0:

                            # Handle GPS errors. **It was observed in one activity that distance jumped from 9656.46
                            # meters to 8051.73 meters (diff of 1604.73 meters) from one data point to the next.**
                            if float(distance_list[-1]) > float(data_point["DistanceMeters"]):
                                diff = abs(float(data_point["DistanceMeters"]) - float(distance_list[-1]))
                                # print(f'Distance: {data_point["DistanceMeters"]} ---> Diff {diff}')
                                distance_list.append(float(data_point["DistanceMeters"]) + diff)
                            else:
                                # print(f'Distance: {data_point["DistanceMeters"]}')
                                distance_list.append(float(data_point["DistanceMeters"]))
                        else:
                            distance_list.append(float(data_point["DistanceMeters"]))

                    except KeyError:
                        # print(f'No Distance Data is available!')
                        print(f'No Distance Data is available! Appending {distance_list[-1]}')
                        distance_list.append(distance_list[-1])

                    # Heart rate value of the data pont
                    try:
                        hr_list.append(data_point["HeartRateBpm"]["Value"])
                        # print(f'HR: {data_point["HeartRateBpm"]["Value"]}')
                    except KeyError:
                        # print('No Heart Rate Data is available!')
                        if len(hr_list) > 0:
                            # print(f'No Heart Rate Data is available! Appending {hr_list[-1]}')
                            hr_list.append(hr_list[-1])
                        else:
                            # print('No Heart Rate Data is available! Appending 0.')
                            hr_list.append(0)

                    # number_of_laps = len(activity)
                # print(f'number of laps is: {number_of_laps}')
                # for lap_num in range(number_of_laps - 1):
                #     for data_point in range(len(activity["Track"][lap_num]["Trackpoint"])):
                #         base = activity["Track"][lap_num]["Trackpoint"][data_point]
                #         print(f'base.keys() is: {base.keys()}')
                #         # print(f'base is: {base}')
                #         print(f'base length is: {len(base)}')
                #         # print(f'Base length is: {len(base)}')
                #         # print(f'Lap Number: {lap_num + 1}')
                #         # print(f'Time is: {base["Time"]}')
                #         time_list.append(base["Time"])
                #         # print(f'Position is: {(base["Position"]["LatitudeDegrees"], base["Position"]["LongitudeDegrees"])}')
                #         if 'Position' in base:
                #             position_list.append(
                #                 (base["Position"]["LatitudeDegrees"], base["Position"]["LongitudeDegrees"]))
                #         # print(f'Altitude is: {base["AltitudeMeters"]} Meters')
                #         # print(f'Altitude type is: {type(base["AltitudeMeters"])}')
                #         if 'AltitudeMeters' in base:
                #             altitude_list.append(float(base["AltitudeMeters"]))
                #         # print(f'Distance is: {base["DistanceMeters"]} Meters')
                #         if 'DistanceMeters' in base:
                #             distance_list.append(base["DistanceMeters"])
                #
                #         if 'HeartRateBpm' in base:
                #             # print(f'HR is: {base["HeartRateBpm"]["Value"]}bpm')
                #             hr_list.append(base["HeartRateBpm"]["Value"])
                #     print('------------------------------------------------------------------')

        # print(f'first distance point is: {distance_list[0]}')
        altitude_list = [int(convert_meters_to_feet(alt_point)) for alt_point in altitude_list]
        distance_list = [float(convert_meter_to_mile(value)) for value in distance_list]
        time_list = [str(value) for value in time_list]
        hr_list = [int(value) for value in hr_list]
        position_list = [tuple(value) for value in position_list]

        for i in range(1, len(distance_list) - 1):
            hour1 = time_list[i - 1].split(":")[-3][-2:]
            min1 = time_list[i - 1].split(":")[-2]
            sec1 = time_list[i - 1].split(":")[-1][0:2]
            hour2 = time_list[i].split(":")[-3][-2:]
            min2 = time_list[i].split(":")[-2]
            sec2 = time_list[i].split(":")[-1][0:2]

            point1 = datetime.strptime(f'{hour1}:{min1}:{sec1}', '%H:%M:%S')
            point2 = datetime.strptime(f'{hour2}:{min2}:{sec2}', '%H:%M:%S')

            # Calculate the time, in hours, between data points (To later be converted to MPH)
            time_delta = (point2 - point1).total_seconds() / 3600

            try:
                speed = (distance_list[i] - distance_list[i - 1])/time_delta
            except ZeroDivisionError:
                speed_list.append(speed_list[-1])
            else:
                speed_list.append(speed)


        while len(speed_list) < len(distance_list):
            speed_list.append(speed_list[-1])

        # Show activity data points
        # print(altitude_list)
        # print(distance_list)
        # print(time_list)
        # # print(cadence_list)
        # print(hr_list)
        # print(position_list)
        # # print(power_list)
        # print(speed_list)

        # print(f'Length of speed list: {len(speed_list)}')
        # print(f'length of altitude list: {len(altitude_list)}')
        # print(f'length of distance list: {len(distance_list)}')
        # print(f'length of time list: {len(time_list)}')
        # print(f'length of heart rate list: {len(hr_list)}')
        # print(f'length of position list: {len(position_list)}')

        # Plot Speed vs Distance
        data_dict['speed'] = plot_speed_vs_distance(speed_list, distance_list)

        # Plot Elevation vs Distance
        data_dict['elevation'] = plot_elevation_vs_distance(altitude_list, distance_list)

        # Plot Heart Rate vs Distance
        data_dict['heart rate'] = plot_heart_rate_vs_distance(hr_list, distance_list)

        return data_dict
    else:
        print('The file was not found. :-(')

def get_activity_gpx_file(activity_id, filepath):
    """

    :param activity_id:
    :param filepath:
    :return:
    """
    # print('In get_activity_gpx_file()')
    data_dict = {}

    filename = f'{activity_id}.gpx'
    input_file_path = f'{filepath}/activities/{filename}'

    with open(input_file_path, 'r') as f:
        gpx = gpxpy.parse(f)

    for track in gpx.tracks:
        # print(f'track is: {track}')
        for segment in track.segments:

            start_time = segment.points[0].time
            speed_list = []
            distance_list = []
            heart_rate_list = []
            total_distance = 0

            for data_point in range(0, len(segment.points)):
                point1 = segment.points[data_point - 1]
                point2 = segment.points[data_point]
                # point3 = segment.points[data_point].extensions[0].find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')

                try:
                    heart_rate_list.append(
                        [el.text for el in segment.points[data_point].extensions[0] if 'hr' in el.tag][0]
                    )
                except IndexError as e:
                    print(f'No heart rate data was found.')
                # print(f'point3 is: {point3}')
                # print(f'HR List: {heart_rate_list}')

                # print(f'point1: {point1} | point2: {point2} | point3: {point3}')

                if data_point == 0:
                    distance = 0
                else:
                    # Calculate distance, in meters, between the current GPS point and the previous using haversine
                    # formula
                    distance = point1.distance_2d(point2)

                # print(f'distance is: {distance}')

                # Calculate overall distance, in meters, between the current GPS point and the starting point using
                # haversine formula, then convert it from meters to miles.
                # ride_distance = convert_meter_to_mile(start_point.distance_2d(point2))
                total_distance += distance
                # distance_list.append(total_distance)
                distance_list.append(convert_meter_to_mile(total_distance))

                # print(f'distance is:{distance} - total_distance is: {total_distance}')
                # Calculate time difference between two points
                time_diff = point2.time - point1.time

                # Calculate speed in m/s and , then convert it to mi/h
                if time_diff.total_seconds() > 0:
                    speed_list.append(convert_meters_per_second_to_miles_per_hour(distance / time_diff.total_seconds()))
                else:
                    speed_list.append(0)

            # Plot Speed vs Distance
            data_dict['speed'] = plot_speed_vs_distance(speed_list, distance_list)

            # Plot Elevation vs Distance
            data_dict['elevation'] = plot_elevation_vs_distance(
                [convert_meters_to_feet(point.elevation) for point in segment.points],
                distance_list
            )

            # Plot Heart Rate vs Distance
            data_dict['heart_rate'] = plot_heart_rate_vs_distance(heart_rate_list, distance_list)

            # return [elevation_graph, speed_graph]#, heart_rate_graph]
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
    # print('In get_activity_fit_file()')

    time_list = []
    distance_list = []
    altitude_list = []
    speed_list = []
    heart_rate_list = []
    cadence_list = []
    temperature_list = []
    power_list = []
    data_dict = {}

    activity_data = db.session.get(Activity, activity_id)
    activity_dir = activity_data.filename.split("/")[0]
    filename = activity_data.filename.split("/")[1]
    # print(f'filepath is: {filepath}')
    # print(f'activity_dir is: {activity_dir}')
    input_file_path = f'{filepath}/{activity_dir}'
    # print(f"filename is: {filename}")
    output_file = DECOMPRESSED_ACTIVITY_FILES_FOLDER + '/' + filename.split('.gz')[0]
    # print(f'input_file_path is: {input_file_path}')
    # print(f'output_file is: {output_file}')

    for file in os.listdir(input_file_path):
        if file == filename:
            filepath = os.path.join(input_file_path, file)
            # print(f'{filename} has been found(from get_activity_fit_file()')
            break  # Stop searching once the file is found.

    decompress_gz_file(filepath)

    with fitdecode.FitReader(output_file) as fit_file:
        for frame in fit_file:
            if isinstance(frame, fitdecode.FitDataMessage):
                if frame.name == 'record':

                    # Append activity time to the time_list
                    time = frame.get_value('timestamp')
                    time_list.append(time)

                    # Append activity distance to the distance_list
                    try:
                        distance = convert_meter_to_mile(frame.get_value('distance'))
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
                        distance_list.append(distance_list[-1])
                    else:
                        distance_list.append(distance)

                    # Append activity altitude to the altitude_list
                    try:
                        altitude = round(convert_meters_to_feet(frame.get_value('altitude')), 2)
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
                        altitude_list.append(altitude_list[-1])
                    else:
                        altitude_list.append(altitude)

                    # Append speed time to the speed_list
                    try:
                        speed = convert_meters_per_second_to_miles_per_hour(frame.get_value('speed'))
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
                        speed_list.append(speed_list[-1])
                    else:
                        speed_list.append(speed)

                    # Append activity heart_rate to the heart_rate_list
                    try:
                        heart_rate = frame.get_value('heart_rate')
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
                        if len(heart_rate_list) > 0:
                            heart_rate_list.append(heart_rate_list[-1])
                        # else:
                        #     heart_rate_list.append(0)
                    else:
                        heart_rate_list.append(heart_rate)

                    # Append activity cadence to the cadence_list
                    try:
                        cadence = frame.get_value('cadence')
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
                        if len(cadence_list) > 0:
                            if len(cadence_list) > 0:
                                cadence_list.append(cadence_list[-1])
                        else:
                            cadence_list.append(0)
                    else:
                        cadence_list.append(cadence)

                    # Append activity temperature to the temperature_list
                    try:
                        temperature = convert_celsius_to_fahrenheit(frame.get_value('temperature'))
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
                        temperature_list.append(temperature_list[-1])
                    else:
                        temperature_list.append(temperature)

                    # Append activity power to the power_list
                    try:
                        power = frame.get_value('power')
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
                        if len(power_list) > 0:
                            power_list.append(power_list[-1])
                    else:
                        power_list.append(power)

        # Plot Speed vs Distance
        data_dict['speed'] = plot_speed_vs_distance(speed_list, distance_list)

        # Plot Elevation vs Distance
        data_dict['elevation'] = plot_elevation_vs_distance(altitude_list, distance_list)

        # Plot Heart Rate vs Distance
        if len(heart_rate_list) > 0:
            data_dict['heart rate'] = plot_heart_rate_vs_distance(heart_rate_list, distance_list)

        # print('Returning a .fit file from get_activity_fit_file()')

        return data_dict

# if __name__ == '__main__':
#     app.run(
#         # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
#         debug=True,
#         host='0.0.0.0',  # Use for local debugging
#         port=5000  # Define the port to use when connecting.
#     )
