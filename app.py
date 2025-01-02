from fileinput import filename

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.operators import ilike_op
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

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
db = SQLAlchemy(app)

# Set a path to save the uploaded files
UPLOAD_FOLDER = 'uploads'
DECOMPRESSED_ACTIVITY_FILES_FOLDER = 'decompressed_activity_files'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
TARGET_FILENAME = 'activities.csv'
METER_TO_MILE = 0.000621371
MPS_TO_MPH = 2.23694
METER_TO_FOOT = 3.28084

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DECOMPRESSED_ACTIVITY_FILES_FOLDER, exist_ok=True)

class Activity(db.Model):

    activity_id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(200), nullable=False)
    activity_description = db.Column(db.String(1000), nullable=False)
    commute = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    moving_time = db.Column(db.String(200), nullable=False)
    moving_time_seconds = db.Column(db.Integer, nullable=False)
    distance = db.Column(db.Double, default=0)
    average_speed = db.Column(db.Double, default=0)
    max_speed = db.Column(db.Double, default=0)
    elevation_gain = db.Column(db.Double, default=0, nullable=False)
    highest_elevation = db.Column(db.Double, default=0)
    activity_type = db.Column(db.String(40), nullable=False)
    activity_gear = db.Column(db.String(50), nullable=False)
    filename = db.Column(db.String(100))


    def __repr__(self):
        return '<Activity %r' % self.activity_id


    @property
    def convert_seconds_to_time_format(self):
        return str(timedelta(seconds=self.moving_time))


def convert_time_to_seconds(seconds, minutes, hours):
    if hours == '' or hours is None:
        hours = '00'
    if minutes == '' or minutes is None:
        minutes = '00'
    if seconds == '' or seconds is None:
        seconds = '00'

    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)


def split_time_string(time):
    """
    Returns the hour, minute, and second of a given time
    :param time:
    :return: hour, minute, second
    """
    if len(time) == 5:
        return_list = ['00']
        time_split = time.split(':')
        return_list.append(time_split[0])
        return_list.append(time_split[1])
        return return_list
    else:
        return time.split(':')


def convert_activity_csv_to_db():
    db = Database()
    db.drop_table(db.DATABASE_NAME)
    db.create_db_table(db.DATABASE_NAME, db.TABLE_NAME, db.convert_csv_to_df())


def convert_meter_to_mile(meter):
    if type(meter) == str:
        meter = meter.replace(',', '')  # Remove the comma from values so it can be converted to float.
        meter = float(meter)
    return round(meter * METER_TO_MILE, 2)


def convert_meters_to_feet(meter):
    return meter * METER_TO_FOOT


def convert_meters_per_second_to_miles_per_hour(meters_per_second):
    return round(meters_per_second * MPS_TO_MPH, 2)


def convert_celsius_to_fahrenheit(temp):
    return (temp * (9/5)) + 32


def plot_speed_vs_distance(speed_list, distance_list):
    """

    :param speed_list:
    :param distance_list:
    :return:
    """
    print(f'speed_list length is: {len(speed_list)}')
    print(f'distance_list length is: {len(distance_list)}')

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
        # line_shape='spline'
    )
    speed_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))
    return speed_fig.to_html(full_html=False)


def plot_elevation_vs_distance(elevation_list, distance_list):
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
        # line_shape='spline'
    )
    # elevation_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))
    return elevation_fig.to_html(full_html=False)


def plot_heart_rate_vs_distance(heart_rate_list, distance_list):
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
        # line_shape='spline'
    )
    heart_rate_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))
    return heart_rate_fig.to_html(full_html=False)


def decompress_gz_file(input_file_path_and_name):
    output_file_name = input_file_path_and_name.split('/')[-1].split('.gz')[0]
    print(f'input_file from decompress_gz_file is: {input_file_path_and_name}')
    print(f'output_file from decompress_gz_file is: {output_file_name}')
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
    print('In get_activity_tcx_file()')

    data_dict = {}
    speed_list = []
    distance_list = []
    time_list = []
    altitude_list = []
    position_list = []
    hr_list = []
    file_is_found = False

    print(f'activity_id is: {activity_id}')
    activity_data = db.session.get(Activity, activity_id)
    print(f'activity_data.filename is: {activity_data.filename}')
    filename = activity_data.filename.split("/")[-1]
    sub_dir = activity_data.filename.split("/")[0]
    print(f'filename from get_activity_tcx_file() is: {filename}')
    input_file_path = f'{filepath}/{sub_dir}'
    print(f'input_file_path from get_activity_tcx_file() is: {input_file_path}')
    # output_file = f'{activity_data.filename.split("/")[1].split(".")[0]}.tcx'

    for file in os.listdir(input_file_path):
        # if file.split('.')[-2] == 'tcx':
        #     print(f'file is: {file}')
        if file == filename:
            file_is_found = True
            filepath = os.path.join(input_file_path, file)
            print(f'filepath from get_activity_tcx_file() is: {filepath}')
            decompress_gz_file(filepath)
            break  # Stop searching once the file is found.

    if file_is_found:
        with open(DECOMPRESSED_ACTIVITY_FILES_FOLDER + '/' + filepath.split('/')[-1].split('.gz')[0], 'r') as f:
            xml_string = f.read().strip()  # Strip leading/trailing whitespace
            # tcx = tcxparser.TCXParser(xml_string)

            xml_dict = xmltodict.parse(xml_string)

            # print(f'xml_dict is: {xml_dict}')
            # for value in range(len(xml_dict)):
            #     print(value)
            #['@xmlns', '@xmlns:xsi', '@xsi:schemaLocation', 'Activities', 'Author']
            print(f'xml_dict.keys() is: {xml_dict.keys()}')
            for activity in xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"]["Lap"]:
                # print(f'activity.keys() is: {activity["Track"].keys()}')
                number_of_laps = len(activity)
                print(f'number of laps is: {number_of_laps}')
                for lap_num in range(number_of_laps - 1):
                    for data_point in range(len(activity["Track"][lap_num]["Trackpoint"])):
                        base = activity["Track"][lap_num]["Trackpoint"][data_point]
                        print(f'base.keys() is: {base.keys()}')
                        print(f'base is: {base}')
                        print(f'base length is: {len(base)}')
                        # print(f'Base length is: {len(base)}')
                        # print(f'Lap Number: {lap_num + 1}')
                        # print(f'Time is: {base["Time"]}')
                        time_list.append(base["Time"])
                        # print(f'Position is: {(base["Position"]["LatitudeDegrees"], base["Position"]["LongitudeDegrees"])}')
                        if 'Position' in base:
                            position_list.append(
                                (base["Position"]["LatitudeDegrees"], base["Position"]["LongitudeDegrees"]))
                        # print(f'Altitude is: {base["AltitudeMeters"]} Meters')
                        # print(f'Altitude type is: {type(base["AltitudeMeters"])}')
                        if 'AltitudeMeters' in base:
                            altitude_list.append(float(base["AltitudeMeters"]))
                        # print(f'Distance is: {base["DistanceMeters"]} Meters')
                        if 'DistanceMeters' in base:
                            distance_list.append(base["DistanceMeters"])

                        if 'HeartRateBpm' in base:
                            # print(f'HR is: {base["HeartRateBpm"]["Value"]}bpm')
                            hr_list.append(base["HeartRateBpm"]["Value"])
                        # print('------------------------------------------------------------------')

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

        print(f'Length of speed list: {len(speed_list)}')
        print(f'length of altitude list: {len(altitude_list)}')
        print(f'length of distance list: {len(distance_list)}')
        print(f'length of time list: {len(time_list)}')
        print(f'length of heart rate list: {len(hr_list)}')
        print(f'length of position list: {len(position_list)}')

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
    print('In get_activity_gpx_file()')
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
    print('In get_activity_fit_file()')

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
    output_file = DECOMPRESSED_ACTIVITY_FILES_FOLDER + '/' + filename.split('/')[1].split('.gz')[0]
    # print(f'input_file_path is: {input_file_path}')
    # print(f'output_file is: {output_file}')

    for file in os.listdir(input_file_path):
        if file == filename:
            filepath = os.path.join(input_file_path, file)
            print(f'{filename} has been found(from get_activity_fit_file()')
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

        print('Returning a .fit file from get_activity_fit_file()')

        return data_dict

@app.route('/')
def index():
    """
    Function and route for the home page.

    :return: Renders the index.html page.
    """
    return render_template('index.html')

@app.route('/activities', methods=['POST', 'GET'])
def activity():
    """
    Function and route for the activities page.

    :return: Renders the activities.html page.
    """
    activities = ''
    num_of_activities = 0
    filetype = Activity.filename
    print(f'filetype is: {filetype}')

    # When the filter form is submitted
    if request.method == 'POST':
        text_search = request.form.get('activity_search') or ''
        selected_activity_type = request.form.get('type-options')
        selected_activity_gear = request.form.get('gear-options')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date') or datetime.now()
        commute = request.form.get('commute') or None
        min_distance_value = request.form.get('more_than_distance')
        max_distance_value = request.form.get('less_than_distance')
        min_elevation_gain_value = request.form.get('more_than_elevation_gain')
        max_elevation_gain_value = request.form.get('less_than_elevation_gain')
        min_highest_elevation_value = request.form.get('more_than_highest_elevation')
        max_highest_elevation_value = request.form.get('less_than_highest_elevation')
        more_than_seconds_value = request.form.get('more_than_seconds')
        more_than_minutes_value = request.form.get('more_than_minutes')
        more_than_hours_value = request.form.get('more_than_hours')
        less_than_seconds_value = request.form.get('less_than_seconds')
        less_than_minutes_value = request.form.get('less_than_minutes')
        less_than_hours_value = request.form.get('less_than_hours')
        min_average_speed_value = request.form.get('more_than_average_speed')
        max_average_speed_value = request.form.get('less_than_average_speed')
        min_max_speed_value = request.form.get('more_than_max_speed')
        max_max_speed_value = request.form.get('less_than_max_speed')

        more_than_value = convert_time_to_seconds(
            more_than_seconds_value,
            more_than_minutes_value,
            more_than_hours_value
        )

        less_than_value = convert_time_to_seconds(
            less_than_seconds_value,
            less_than_minutes_value,
            less_than_hours_value
        )

        filters = {}
        if selected_activity_type != 'All':
            filters['activity_type'] = selected_activity_type

        if selected_activity_gear != 'All':
            filters['activity_gear'] = selected_activity_gear

        if commute == 'commute':
            filters['commute'] = 1

        query_string = (
            Activity
            .query
            .filter_by(**filters)
            .filter(ilike_op(Activity.activity_name, f'%{text_search}%'))
            # .filter(ilike_op(Activity.activity_description, f'%{text_search}%'))
            .filter(start_date <= Activity.start_time)
            .filter(end_date >= Activity.start_time)
            .filter(min_distance_value <= Activity.distance)
            .filter(max_distance_value >= Activity.distance)
            .filter(min_elevation_gain_value <= Activity.elevation_gain)
            .filter(max_elevation_gain_value >= Activity.elevation_gain)
            .filter(min_highest_elevation_value <= Activity.highest_elevation)
            .filter(max_highest_elevation_value >= Activity.highest_elevation)
            .filter(more_than_value <= Activity.moving_time_seconds)
            .filter(less_than_value >= Activity.moving_time_seconds)
            .filter(min_average_speed_value <= Activity.average_speed)
            .filter(max_average_speed_value >= Activity.average_speed)
            .filter(min_max_speed_value <= Activity.max_speed)
            .filter(max_max_speed_value >= Activity.max_speed)

            .order_by(Activity.start_time  # Order activities by date
            # .order_by(Activity.average_speed  # Order activities by average speed
            # .order_by(Activity.max_speed  # Order activities by max speed
            # .order_by(Activity.distance  # Order activities by distance
            # .order_by(Activity.elevation_gain  # Order activities by elevation gain
            # .order_by(Activity.highest_elevation  # Order activities by highest elevation
            # .order_by(Activity.moving_time_seconds  # Order activities by moving time
            .desc())  # Show newest activities first
        )
        activities = query_string.all()
        num_of_activities = query_string.count()

    # GET request when the page loads
    if request.method == 'GET':
        query_string = Activity.query.order_by(Activity.start_time.desc())

        activities = query_string.all()
        num_of_activities = query_string.count()

    # Display the number of activities that are being displayed.
    if num_of_activities == 0:
        num_of_activities_string = 'No Activities to Show'
    elif num_of_activities == 1:
        num_of_activities_string = 'Showing 1 Activity'
    else:
        num_of_activities_string = f'Showing {num_of_activities} Activities'

    # Get the minimum and maximum of all the activity distances for the dropdown boxes
    min_activities_distance = (Activity.query.order_by(Activity.distance).
                               first().distance)
    max_activities_distance = (Activity.query.order_by(Activity.distance.desc()).
                               first().distance)

    # Get the minimum and maximum of all the activity elevation gains for the dropdown boxes
    min_activities_elevation_gain = (Activity.query.order_by(Activity.elevation_gain).
                                     first().elevation_gain)
    max_activities_elevation_gain = (Activity.query.order_by(Activity.elevation_gain.desc()).
                                     first().elevation_gain)

    # Get the minimum and maximum of all the activity elevations for the dropdown boxes
    min_activities_highest_elevation = Activity.query.order_by(Activity.highest_elevation).first().highest_elevation
    max_activities_highest_elevation = (Activity.query.order_by(Activity.highest_elevation.desc()).
                                        first().highest_elevation)

    # Get the minimum and maximum of all the activity moving times for the dropdown boxes
    longest_moving_time_split = split_time_string(Activity.query.order_by(Activity.moving_time.desc()).
                                                  first().moving_time)
    shortest_moving_time_split = split_time_string(Activity.query.order_by(Activity.moving_time).
                                                   first().moving_time)

    # Get the minimum and maximum of all the activity average speeds for the dropdown boxes
    min_activities_average_speed = (Activity.query.order_by(Activity.average_speed).
                                    first().average_speed)
    max_activities_average_speed = (Activity.query.order_by(Activity.average_speed.desc()).
                                    first().average_speed)

    # Get the minimum and maximum of all the activity max speeds for the dropdown boxes
    min_activities_max_speed = (Activity.query.order_by(Activity.max_speed).
                                first().max_speed)
    max_activities_max_speed = (Activity.query.order_by(Activity.max_speed.desc()).
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
    moving_time_data = {
        'Activity Moving Time': [point.moving_time_seconds for point in activities],
        'Activity Date': [point.start_time for point in activities]
    }
    moving_time_df = pd.DataFrame(moving_time_data)
    moving_time_fig = px.line(
        moving_time_df,
        x='Activity Date',
        y='Activity Moving Time',
        title="Moving Time vs Activity Date"
    )
    plot_moving_time_data = moving_time_fig.to_html(full_html=False)

    # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # div for activity Date vs Distance.
    distance_data = {
        'Activity Distance': [point.distance for point in activities],
        'Activity Date': [point.start_time for point in activities]
    }
    distance_df = pd.DataFrame(distance_data)
    distance_fig = px.line(
        distance_df,
        x='Activity Date',
        y='Activity Distance',
        title="Distance vs Activity Date"
    )
    plot_distance_data = distance_fig.to_html(full_html=False)

    # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # div for activity Date vs Average Speed.
    avg_speed_data = {
        'Activity Average Speed': [point.average_speed for point in activities],
        'Activity Date': [point.start_time for point in activities]
    }
    avg_speed_df = pd.DataFrame(avg_speed_data)
    avg_speed_fig = px.line(
        avg_speed_df,
        x='Activity Date',
        y='Activity Average Speed',
        title="Average Speed vs Activity Date"
    )
    plot_avg_speed_data = avg_speed_fig.to_html(full_html=False)

    # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # div for activity Date vs Max Speed.
    max_speed_data = {
        'Activity Max Speed': [point.max_speed for point in activities],
        'Activity Date': [point.start_time for point in activities]
    }
    max_speed_df = pd.DataFrame(max_speed_data)
    max_speed_fig = px.line(
        max_speed_df,
        x='Activity Date',
        y='Activity Max Speed',
        title="Max Speed vs Activity Date"
    )
    plot_max_speed_data = max_speed_fig.to_html(full_html=False)

    # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # div for activity Date vs Elevation Gain.
    elevation_gain_data = {
        'Activity Elevation Gain': [point.elevation_gain for point in activities],
        'Activity Date': [point.start_time for point in activities]
    }
    elevation_gain_df = pd.DataFrame(elevation_gain_data)
    elevation_gain_fig = px.line(
        elevation_gain_df,
        x='Activity Date',
        y='Activity Elevation Gain',
        title="Elevation Gain vs Activity Date"
    )
    plot_elevation_gain_data = elevation_gain_fig.to_html(full_html=False)

    return render_template(
        'activities.html',
        activities=activities,
        activity_type_list=activity_type_list,
        activity_gear_list=activity_gear_list,
        num_of_activities=num_of_activities_string,
        min_activities_distance=min_activities_distance,
        max_activities_distance=max_activities_distance,
        min_activities_elevation_gain=min_activities_elevation_gain,
        max_activities_elevation_gain=max_activities_elevation_gain,
        min_activities_highest_elevation = min_activities_highest_elevation,
        max_activities_highest_elevation = max_activities_highest_elevation,
        longest_moving_time_split=longest_moving_time_split,
        shortest_moving_time_split=shortest_moving_time_split,
        min_activities_average_speed=min_activities_average_speed,
        max_activities_average_speed=max_activities_average_speed,
        min_activities_max_speed = min_activities_max_speed,
        max_activities_max_speed = max_activities_max_speed,
        plot_moving_time_data=plot_moving_time_data,
        plot_distance_data=plot_distance_data,
        plot_avg_speed_data=plot_avg_speed_data,
        plot_max_speed_data=plot_max_speed_data,
        plot_elevation_gain_data=plot_elevation_gain_data
    )

@app.route('/activity/<activity_id>', methods=['GET'])
def activity_info(activity_id):
    """
    This function handles when an individual activity file is displayed. It takes the activity_id as an input parameter
    and shows the activity details and shows the plotly graphs for speed and elevation and heart rate if applicable. The
    filetype is determined and the approate function is called to handle the filetype date.
    :param activity_id: (datatype: str)The unique id that was given to the selected activity.
    :return: The rendered individual_activity.html page and activity_data(An instance of the Activity db class) and
    activity_graph_data(dict).
    """

    activity_data = db.session.get(Activity, activity_id)
    print(f'activity_id is: {activity_id}')
    print(f'activity_data type is: {type(activity_data)}')
    print(f'activity_data.filename is: {activity_data.filename}')
    try:
        print(f'activity_data.filename.split(".")[-1] is: {activity_data.filename.split(".")[-1]}')
        if activity_data.filename.split(".")[-1] == 'gz':
            filetype = activity_data.filename.split(".")[-2]
        else:
            filetype = activity_data.filename.split(".")[-1]
    except AttributeError as e:
        print(f'Error: {e}')
        print('This may have happened because an associated file could not be found for this activity. Was this '
              'activity entered manually?')
        # return render_template('activities.html')
        return render_template('index.html')
    else:
        print(f'filetype is: {filetype}')

    # Open and load the JSON file
    with open('transfer_data.json', 'r') as openfile:
        json_file_data = json.load(openfile)
        filepath = os.path.join(os.getcwd(), json_file_data['relative_path'])
        print(f'filepath type is: {type(filepath)}')

    # Search for .gpx file associated with the provided activity ID.
    if filetype == 'gpx':
        print('Looking for a .gpx file!!')
        activity_graph_data = get_activity_gpx_file(activity_id, filepath)
    elif filetype == 'fit':
        print('Looking for a .fit file!!')
        activity_graph_data = get_activity_fit_file(activity_id, filepath)
    elif filetype == 'tcx':
        print('Looking for a .tcx file!!')
        activity_graph_data = get_activity_tcx_file(activity_id, filepath)
    else:
        raise FileNotFoundError(f'The activity file({activity_data.filename.split("/")[-1]}) was not found.')
    print(f'activity_graph_data type is: {type(activity_graph_data)}')
    # print(f'activity_graph_data is: {activity_graph_data}')
    print(f'activity_graph_data keys are: {activity_graph_data.keys()}')

    return render_template(
        'individual_activity.html',
        activity_data=activity_data,
        activity_graph_data=activity_graph_data
        # elevation=activity_graph_data[0],
        # speed=activity_graph_data[1],
        # heart_rate=activity_graph_data[2]
    )
    # else:
    #     print(f'Activity ID: {activity_id} does have an associated .gpx file')
    # finally:
    #     return render_template(
    #         'individual_activity.html',
    #         activity_data=activity_data,
    #         elevation=activity_graph_data[0],
    #         speed=activity_graph_data[1],
    #         heart_rate=activity_graph_data[2]
    #     )

# @app.route('/graph', methods=['POST'])
# def plot_data():
#     text_search = request.form.get('activity_search') or ''
#     selected_activity_type = request.form.get('type-options')
#     selected_activity_gear = request.form.get('gear-options')
#     start_date = request.form.get('start_date')
#     end_date = request.form.get('end_date') or datetime.datetime.now()
#     commute = request.form.get('commute') or None
#     min_distance_value = request.form.get('more_than_distance')
#     max_distance_value = request.form.get('less_than_distance')
#     min_elevation_gain_value = request.form.get('more_than_elevation_gain')
#     max_elevation_gain_value = request.form.get('less_than_elevation_gain')
#     min_highest_elevation_value = request.form.get('more_than_highest_elevation')
#     max_highest_elevation_value = request.form.get('less_than_highest_elevation')
#     more_than_seconds_value = request.form.get('more_than_seconds')
#     more_than_minutes_value = request.form.get('more_than_minutes')
#     more_than_hours_value = request.form.get('more_than_hours')
#     less_than_seconds_value = request.form.get('less_than_seconds')
#     less_than_minutes_value = request.form.get('less_than_minutes')
#     less_than_hours_value = request.form.get('less_than_hours')
#     min_average_speed_value = request.form.get('more_than_average_speed')
#     max_average_speed_value = request.form.get('less_than_average_speed')
#     min_max_speed_value = request.form.get('more_than_max_speed')
#     max_max_speed_value = request.form.get('less_than_max_speed')
#
#     more_than_value = convert_time_to_seconds(
#         more_than_seconds_value,
#         more_than_minutes_value,
#         more_than_hours_value
#     )
#
#     less_than_value = convert_time_to_seconds(
#         less_than_seconds_value,
#         less_than_minutes_value,
#         less_than_hours_value
#     )
#
#     filters = {}
#     if selected_activity_type != 'All':
#         filters['activity_type'] = selected_activity_type
#
#     if selected_activity_gear != 'All':
#         filters['activity_gear'] = selected_activity_gear
#
#     if commute == 'commute':
#         filters['commute'] = 1
#
#     query_string = (
#         Activity
#         .query
#         .filter_by(**filters)
#         .filter(ilike_op(Activity.activity_name, f'%{text_search}%'))
#         .filter(start_date <= Activity.start_time)
#         .filter(end_date >= Activity.start_time)
#         .filter(min_distance_value <= Activity.distance)
#         .filter(max_distance_value >= Activity.distance)
#         .filter(min_elevation_gain_value <= Activity.elevation_gain)
#         .filter(max_elevation_gain_value >= Activity.elevation_gain)
#         .filter(min_highest_elevation_value <= Activity.highest_elevation)
#         .filter(max_highest_elevation_value >= Activity.highest_elevation)
#         .filter(more_than_value <= Activity.moving_time_seconds)
#         .filter(less_than_value >= Activity.moving_time_seconds)
#         .filter(min_average_speed_value <= Activity.average_speed)
#         .filter(max_average_speed_value >= Activity.average_speed)
#         .filter(min_max_speed_value <= Activity.max_speed)
#         .filter(max_max_speed_value >= Activity.max_speed)
#
#         .order_by(Activity.start_time  # Order activities by date
#                   # .order_by(Activity.average_speed  # Order activities by average speed
#                   # .order_by(Activity.max_speed  # Order activities by max speed
#                   # .order_by(Activity.distance  # Order activities by distance
#                   # .order_by(Activity.elevation_gain  # Order activities by elevation gain
#                   # .order_by(Activity.highest_elevation  # Order activities by highest elevation
#                   # .order_by(Activity.moving_time_seconds  # Order activities by moving time
#                   .desc())  # Show newest activities first
#     )
#     activities = query_string.all()
#
#     df = pd.DataFrame([{
#         'start_time': activity.start_time,
#         'moving_time': activity.moving_time,
#         'distance': activity.distance,
#         'average_speed': activity.average_speed,
#         'max_speed': activity.max_speed,
#         'elevation_gain': activity.elevation_gain
#     } for activity in activities])
#
#     data = [
#         go.Line(
#             x=df['start_time'],
#             y=df['moving_time'],
#             mode='lines+markers',
#             name='Moving Time'
#         )
#     ]
#
#     layout = go.Layout(
#         title='Moving Time vs Activity Date',
#         xaxis=dict(title='Activity Date'),
#         yaxis=dict(title='Moving Time')
#     )
#
#     print(jsonify(graph_data=[trace.to_plotly_json() for trace in data], layout=layout.to_plotly_json()))
#
#     return jsonify(graph_data=[trace.to_plotly_json() for trace in data], layout=layout.to_plotly_json())

@app.route('/upload', methods=['POST', 'GET'])
def upload_activity():
    return render_template('upload_activities.html')

# Route to handle the file upload
@app.route('/upload-file', methods=['POST'])
def upload_file():

    uploaded_files = request.files.getlist('files')

    for file in uploaded_files:
        if os.path.basename(file.filename) == TARGET_FILENAME:
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename.split('/')[1])
            file.save(save_path)
            convert_activity_csv_to_db()
            transfer_data = {
                "relative_path": file.filename.split('/')[0]
            }
            json_file_data = json.dumps(transfer_data, indent=1)
            with open('transfer_data.json', 'w') as outfile:
                outfile.write(json_file_data)

            return jsonify({
                "message": f"File '{TARGET_FILENAME}' has been found!",
                "file_name": file.filename
            })

    return jsonify({
        "message": f"File '{TARGET_FILENAME}' not found in the selected directory."
    })

if __name__ == '__main__':
    app.run(
        # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
        debug=True,
        host='0.0.0.0',  # Use for local debugging
        port=5000  # Define the port to use when connecting.
    )
