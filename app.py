from decimal import DivisionByZero
from idlelib.autocomplete import FILES

from flask import Flask, render_template, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.operators import ilike_op
# import datetime import timedelta
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from database import Database
import fitdecode
import gzip
import os
import gpxpy
import json
import tcxparser

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
db = SQLAlchemy(app)

# Set a path to save the uploaded files
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
TARGET_FILENAME = 'activities.csv'
METER_TO_MILE = 0.000621371
MPS_TO_MPH = 2.23694
METER_TO_FOOT = 3.28084

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


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
    print(f'elevation_list length is: {len(elevation_list)} and distance_list is: {len(distance_list)}')
    print(f'elevation_list is: \n{elevation_list}')
    print(f'distance_list is: \n{distance_list}')
    print(f'type(distance_list) is: {type(distance_list[10])}')
    print(f'type(elevation_list) is: {type(elevation_list[10])}')
    # for point in elevation_list:
    #     print(round(point, 1))

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
    print(f'heart_rate_list is: \n{heart_rate_list}')
    print(f'distance_list is: \n{distance_list}')
    print(f'type(distance_list) is: {type(distance_list[10])}')
    print(f'type(heart_rate_list) is: {type(heart_rate_list[10])}')

    heart_rate_data = {
        'Heart Rate(BPM)': heart_rate_list,
        'Distance(Miles)': distance_list
    }
    heart_rate_df = pd.DataFrame(heart_rate_data)
    heart_rate_fig = px.line(
        heart_rate_df,
        x='Distance(Miles)',
        y='Heart Rate(BPM)',
        title='Heart Rate vs Distance',
        # line_shape='spline'
    )
    heart_rate_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))
    return heart_rate_fig.to_html(full_html=False)


def decompress_gz_file(input_file, output_file):
    print(f'input_file from decompress_gz_file is: {input_file}')
    print(f'output_file from decompress_gz_file is: {output_file}')
    with gzip.open(input_file, 'rb') as f_in:
        with open(output_file, 'wb') as f_out:
            f_out.write(f_in.read())

def get_activity_tcx_file(activity_id, filepath):
    print('In get_activity_tcx_file()')

    data_dict = {}
    speed_list = []

    activity_data = db.session.get(Activity, activity_id)
    file = activity_data.filename.split("/")[0]
    input_file_path = f'{filepath}/{file}'
    output_file = activity_data.filename.split("/")[1]
    # output_file = f'{activity_data.filename.split("/")[1].split(".")[0]}.tcx'

    for file in os.listdir(input_file_path):
        if file == output_file:
            filepath = os.path.join(input_file_path, file)
            break  # Stop searching once the file is found.

    decompress_gz_file(filepath, output_file)

    print(f'output_file is: {output_file}')

    tcx = tcxparser.TCXParser(output_file)

    # Access the activity data totals
    print(tcx.activity_type)
    print(tcx.started_at)
    print(tcx.distance)
    print(tcx.duration)
    print(tcx.calories)
    print(tcx.hr_avg)
    print(tcx.hr_max)

    # Show activity data points
    # print(tcx.altitude_points())
    # print(tcx.distance_values())
    # print(tcx.time_values())
    # print(tcx.cadence_values())
    # print(tcx.hr_values())
    # print(tcx.position_values())
    # print(tcx.power_values())

    print(f'length of altitude list: {len(tcx.altitude_points())}')
    print(f'length of distance list: {len(tcx.distance_values())}')
    print(f'length of time list: {len(tcx.time_values())}')
    print(f'length of heart rate list: {len(tcx.hr_values())}')
    print(f'length of position list: {len(tcx.position_values())}')

    altitude_list = [int(convert_meters_to_feet(alt_point)) for alt_point in tcx.altitude_points()]
    print(f'altitude_list is: {altitude_list}')
    distance_list = [float(convert_meter_to_mile(value)) for value in tcx.distance_values()]
    time_list = [str(value) for value in tcx.time_values()]
    hr_list = [int(value) for value in tcx.hr_values()]
    position_list = [tuple(value) for value in tcx.position_values()]

    longest_list_length = max(len(altitude_list), len(distance_list), len(time_list), len(hr_list), len(position_list))
    list_of_data_lists = [altitude_list, distance_list, time_list, hr_list, position_list]

    print(f'max list length is {longest_list_length}')

    # Make all the lists the same length as the longest one.
    for data_list in list_of_data_lists:
        # if len(data_list) != longest_list_length:
        while len(data_list) < longest_list_length:
            data_list.append(data_list[-1])
            print(f'length is {len(data_list)}')

    for i in range(1, len(tcx.distance_values()) - 1):
        hour1 = time_list[i - 1].split(":")[-3][-2:]
        min1 = time_list[i - 1].split(":")[-2]
        sec1 = time_list[i - 1].split(":")[-1][0:2]
        hour2 = time_list[i].split(":")[-3][-2:]
        min2 = time_list[i].split(":")[-2]
        sec2 = time_list[i].split(":")[-1][0:2]

    # for i in range(1, len(tcx.time_values())):
        point1 = datetime.strptime(f'{hour1}:{min1}:{sec1}', '%H:%M:%S')
        point2 = datetime.strptime(f'{hour2}:{min2}:{sec2}', '%H:%M:%S')
    #
    #     print(f'point1 is: {point1}')
    #     print(f'point2 is: {point2}')
    #
        # Calculate the time, in hours, between data points (To later be converted to MPH)
        time_delta = (point2 - point1).total_seconds() / 3600
        # time_delta = int(time_delta)

        # print(f'time_delta.total_seconds() is: {time_delta.total_seconds()}')
        # if time_delta != 0:

        try:
            speed = (distance_list[i] - distance_list[i - 1])/time_delta
        except ZeroDivisionError:
            speed_list.append(speed_list[-1])
        else:
            # print(f'speed is: {speed} mph')
            # if speed == 0:
            #     speed_list.append(speed_list[-1])
            # else:
            speed_list.append(speed)


    while len(speed_list) < longest_list_length:
        speed_list.append(speed_list[-1])

    print(f'speed_list length is: {len(speed_list)}')
    # print(tcx.distance_units)



    # Plot Speed vs Distance
    data_dict['speed'] = plot_speed_vs_distance(speed_list, distance_list)

    # Plot Elevation vs Distance
    data_dict['elevation'] = plot_elevation_vs_distance(
        altitude_list,
        distance_list
    )

    # Plot Heart Rate vs Distance
    data_dict['heart rate'] = plot_heart_rate_vs_distance(hr_list, distance_list)
    return data_dict


def get_activity_gpx_file(activity_id, filepath):
    print('In get_activity_gpx_file()')
    filename = f'{activity_id}.gpx'
    input_file_path = f'{filepath}/activities/{filename}'

    with open(input_file_path, 'r') as f:
        gpx = gpxpy.parse(f)

    for track in gpx.tracks:
        print(f'track is: {track}')
        for segment in track.segments:

            start_time = segment.points[0].time
            speed_list = []
            distance_list = []
            heart_rate_list = []
            total_distance = 0

            print(f'segment is: {segment}')

            for data_point in range(0, len(segment.points)):
                point1 = segment.points[data_point - 1]
                point2 = segment.points[data_point]
                # point3 = segment.points[i].extensions[0].find('{http://www.garmin.com/xmlschemas/TrackPointExtension/v1}hr')
                # heart_rate_list.append([el.text for el in segment.points[data_point].extensions[0] if 'hr' in el.tag][0])
                # print(f'point3 is: {point3}')
                # print(f'HR: {point3}')

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
            speed_graph = plot_speed_vs_distance(speed_list, distance_list)

            # Plot Elevation vs Distance
            elevation_graph = plot_elevation_vs_distance(
                [convert_meters_to_feet(point.elevation) for point in segment.points],
                distance_list
            )

            # Plot Heart Rate vs Distance
            # heart_rate_graph = plot_heart_rate_vs_distance(heart_rate_list, distance_list)

            return [elevation_graph, speed_graph]#, heart_rate_graph]

def get_activity_fit_file(activity_id, filepath):
    """
    This function takes an activity_id and filepath as parameters. It searches for the .fit file associated with the
    activity_id in the specified filepath. It extracts the time, elevation, distance, speed, heart rate, cadence, and
    temperature from the file. Finally, it plots the speed, elevation, and heart rate vs distance.

    :param activity_id: The activity_id of the activity associated with the .fit file.
    :param filepath: The filepath to the .fit file.
    :return: data_dict: A dictionary with the data to be plotted.
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
    print(f'filepath is: {filepath}')
    print(f'activity_dir is: {activity_dir}')
    input_file_path = f'{filepath}/{activity_dir}'
    output_file = activity_data.filename.split('/')[1]
    print(f'input_file_path is: {input_file_path}')
    print(f'output_file is: {output_file}')

    # print(f'.fit file path is: {input_file_path}')

    for file in os.listdir(input_file_path):
        # print(f'file is: {file}')
        if file == output_file:
            filepath = os.path.join(input_file_path, file)
            print(f'{output_file} has been found(from get_activity_fit_file()')
            break  # Stop searching once the file is found.
        # else:
        #     print(f'{output_file} has not been found(from get_ativity_fit_file()')
        #     # return
        #     return FileNotFoundError

    decompress_gz_file(filepath, output_file)

    with fitdecode.FitReader(output_file) as fit_file:
        for_count = 0
        if_count = 0
        count = 0
        for frame in fit_file:
            for_count += 1
            # print(f'[{for_count}]frame is: {frame}')
            # print(f'fitdecode.FitDefinitionMessage is: {fitdecode.FitDefinitionMessage}\n')
            if isinstance(frame, fitdecode.FitDataMessage):
                # if for_count == 1:
                #     print(f'[{if_count}]frame.name: {frame.get_value("distance")}\n')
                if frame.name == 'record':
                    if_count += 1
                    # print(f'frame.name is: {frame.name}')
                    # if frame.get_value('distance')
                    # print(f'frame.get_value: {frame.get_value("distance")}\n')

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
                        else:
                            heart_rate_list.append(0)
                    else:
                        heart_rate_list.append(heart_rate)

                    # Append activity cadence to the cadence_list
                    try:
                        cadence = frame.get_value('cadence')
                    except KeyError as e:
                        print(f'ERROR: {e}. Skipping for now.')
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

        # if heart_rate and speed and distance and time:
        #             count += 1
        #             print(f'\n({count})Time: {time} - Distance: {distance} mi - Altitude: {altitude} ft - Heart Rate: {heart_rate} bpm - Speed: {speed} mph - Cadence: {cadence} RPM - Temperature: {temperature} F')
        #             print(f'distance: {len(distance_list)}')
        #             print(f'Time: {len(time_list)}')
        #             print(f'Altitude: {len(altitude_list)}')
        #             print(f'Heart Rate: {len(heart_rate_list)}')
        #             print(f'Speed: {len(speed_list)}')
        #             print(f'Cadence: {len(cadence_list)}')
        #             print(f'Temperature: {len(temperature_list)}')

        # Plot Speed vs Distance
        data_dict['speed'] = plot_speed_vs_distance(speed_list, distance_list)
        # speed_data = {
        #     'Activity Speed(MPH)': speed_list,
        #     'Distance(Miles)': distance_list
        # }
        # speed_df = pd.DataFrame(speed_data)
        # speed_fig = px.line(
        #     speed_df,
        #     x='Distance(Miles)',
        #     y='Activity Speed(MPH)',
        #     title='Speed vs Distance',
        #     # line_shape='spline'
        # )
        # speed_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1]/12, 1)))
        # # plot_speed_data = speed_fig.to_html(full_html=False)
        # data_dict['speed'] = speed_fig.to_html(full_html=False)

        # Plot Elevation vs Distance
        data_dict['elevation'] = plot_elevation_vs_distance(altitude_list, distance_list)

        # elevation_data = {
        #     'Activity Elevation(Feet)': altitude_list,
        #     'Distance(Miles)': distance_list
        # }
        # elevation_df = pd.DataFrame(elevation_data)
        # elevation_fig = px.line(
        #     elevation_df,
        #     x='Distance(Miles)',
        #     y='Activity Elevation(Feet)',
        #     title='Elevation vs Distance',
        #     # line_shape='spline'
        # )
        # elevation_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1]/12, 1)))
        # # plot_elevation_data = elevation_fig.to_html(full_html=False)
        # data_dict['elevation'] = elevation_fig.to_html(full_html=False)

        # Plot Heart Rate vs Distance
        data_dict['heart rate'] = plot_heart_rate_vs_distance(heart_rate_list, distance_list)

        # print(f'heart_rate_list is: {len(heart_rate_list)}')
        # # print(f'distance_list is: {len(distance_list)}')
        # if len(heart_rate_list) > 0:
        #     heart_rate_data = {
        #         'Heart Rate(BPM)': heart_rate_list,
        #         'Distance(Miles)': distance_list
        #     }
        #     # for i in range(0, len(distance_list)):
        #     #     print(f'hr: {heart_rate_list[i]} | distance {distance_list[i]}')
        #     heart_rate_df = pd.DataFrame(heart_rate_data)
        #     heart_rate_fig = px.line(
        #         heart_rate_df,
        #         x='Distance(Miles)',
        #         y='Heart Rate(BPM)',
        #         title='Heart Rate vs Distance',
        #         # line_shape='spline'
        #     )
        #     heart_rate_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1]/12, 1)))
        #     # heart_rate_fig.update_layout(yaxis=dict(dtick=5))
        #     # plot_heart_rate_data = heart_rate_fig.to_html(full_html=False)
        #     data_dict['heart rate'] = heart_rate_fig.to_html(full_html=False)

        print('Returning a .fit file from get_activity_fit_file()')
        # print(f'data_dict: {data_dict}')
        # for hr in data_dict['heart rate']:
        #     print(hr)
        # return [plot_elevation_data, plot_speed_data, plot_heart_rate_data]
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
    activity_type_list = [type.activity_type for type in activity_type_categories]

    # Group the activity gear and create a list of each activity gear to be used to populate the dropdown menu options.
    activity_gear_categories = (Activity.query.with_entities(Activity.activity_gear).
                                group_by(Activity.activity_gear).all())
    activity_gear_list = [gear.activity_gear for gear in activity_gear_categories]

    # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # div for activity Date vs Moving Time.
    moving_time_data = {
        'Activity Moving Time': [activity.moving_time_seconds for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Distance': [activity.distance for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Average Speed': [activity.average_speed for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Max Speed': [activity.max_speed for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Elevation Gain': [activity.elevation_gain for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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

    activity_data = db.session.get(Activity, activity_id)
    print(f'activity_id is: {activity_id}')
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
    activity_graph_data = ''

    # Open and load the JSON file
    with open('transfer_data.json', 'r') as openfile:
        json_file_data = json.load(openfile)

    # Search for .gpx file associated with the provided activity ID.
    if filetype == 'gpx':
        print('Looking for a .gpx file!!')
        activity_graph_data = get_activity_gpx_file(
            activity_id,
            os.path.join(os.getcwd(), json_file_data['relative_path'])
        )
        # print(f'activity_graph_data is: {activity_graph_data}')
        # converted_activity_grap_data = activity_graph_data.to_html(full_html=False)

    # If a .gpx file was not found.
    # except FileNotFoundError:
    #     print(f'Activity ID: {activity_id} does not have an associated .gpx file')

        # Search for .fit file associated with the provided activity ID.
    elif filetype == 'fit':
        print('Looking for a .fit file!!')
        activity_graph_data = get_activity_fit_file(
            activity_id,
            os.path.join(os.getcwd(), json_file_data['relative_path'])
        )
        # converted_activity_grap_data = activity_graph_data.to_html(full_html=False)

        # If a .gpx file was not found.
        # except FileNotFoundError:
        #     print(f'Activity ID: {activity_id} does not have an associated .fit file')

            # Search for .tcx file associated with the provided activity ID.
    elif filetype == 'tcx':
        print('Looking for a .tcx file!!')
        activity_graph_data = get_activity_tcx_file(
            activity_id,
            os.path.join(os.getcwd(), json_file_data['relative_path'])
        )
    else:
        raise FileNotFoundError(f'The activity file({activity_data.filename.split("/")[-1]}) was not found.')
            # If a .tcx file was not found.
        #     except FileNotFoundError:
        #         print(f'Activity ID: {activity_id} does not have an associated .tcx file')
        #     else:
        #         print(f'Activity ID: {activity_id} does have an associated .tcx file')
        #         # return render_template(
        #         #     'individual_activity.html',
        #         #     activity_data=activity_data,
        #         #     elevation=activity_graph_data[0],
        #         #     speed=activity_graph_data[1],
        #         #     heart_rate=activity_graph_data[2]
        #         # )
        #
        # else:
        #     print(f'Activity ID: {activity_id} does have an associated .fit file')
    print(f'activity_graph_data length: {len(activity_graph_data)}')
    # print(activity_graph_data['heart rate'])

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
