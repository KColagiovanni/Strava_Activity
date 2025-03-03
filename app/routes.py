from flask import Blueprint, render_template, request, jsonify
from app.models import Activity, db
from sqlalchemy.sql.operators import ilike_op
from app.database import Database
import json
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
import fitdecode
import gzip
import os
import gpxpy
import xmltodict
import tcxparser
import xml.etree.ElementTree as ET
from geopy.distance import geodesic
from config import Config
import pytz


main = Blueprint('main', __name__)
TARGET_FILENAME = 'activities.csv'
DECOMPRESSED_ACTIVITY_FILES_FOLDER = 'decompressed_activity_files'  # Define the directory where decompressed files will
# be saved.


def convert_activity_csv_to_db():
    """
    This function creates an instance of the Database class (defined in database.py), drops(deletes) any existing
    database(Database.DATABASE_NAME), then creates a table(Database.TABLE_NAME) in the defined database
    (Database.DATABASE_NAME) with the defined columns(defined in the Database.convert_csv_to_df() method).
    :return: None
    """
    db = Database()
    db.drop_table(Config.DATABASE_NAME)
    db.create_db_table(Config.DATABASE_NAME, Config.TABLE_NAME, db.convert_csv_to_df())


# Define constants
METER_TO_MILE = 0.000621371
MPS_TO_MPH = 2.23694
METER_TO_FOOT = 3.28084

# Ensure the decompressed activities directory exists in the same directory of this program and if not, create it.
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

    if len(speed_list) == 0:
        print(f'speed_list is empty. Returning from plot_speed_vs_distance()')
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
    speed_fig.update_layout(
        xaxis=dict(dtick=round(distance_list[-1] / 12, 1)),  # Define x-axis tick marks.
        yaxis_range=[max(speed_list) * -0.05, max(speed_list) * 1.1]  # Define y-axis range.
    )
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
    elevation_fig.update_layout(
        # elevation_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1))),  # Define x-axis tick marks.
        yaxis_range=[min(elevation_list) * .7, max(elevation_list) * 1.2]  # Define y-axis range.
    )
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
    heart_rate_fig.update_layout(xaxis=dict(dtick=round(distance_list[-1] / 12, 1)))  # Define x-axis tick marks.
    return heart_rate_fig.to_html(full_html=False)


def plot_heart_rate_vs_time(heart_rate_list, time_list):
    """
    This function prepares the data to be plotted using Plotly. It takes two lists as parameters, converts them to
    Pandas dataframes, converts them to a figure, and finally converts the figure to an HTML div string. The heart rate
    list is plotted on the Y-Axis and the time is plotted on the X-Axis.
    :param heart_rate_list: (List of ints) The heart rate, in beats per minutes, at any given time in the activity.
    :param time_list: (List of strings) The time at each point during the activity.
    :return: The figure converted to an HTML div string.
    """

    if len(heart_rate_list) == 0:
        print(f'heart_rate_list is empty. Returning from plot_heart_rate_vs_time()')
        return

    if len(time_list) == 0:
        print(f'time_list is empty. Returning from plot_heart_rate_vs_time()')
        return

    heart_rate_data = {
        'Heart Rate(BPM)': heart_rate_list,
        'Time': time_list
    }
    # print(f'time_list is: {time_list}')
    heart_rate_df = pd.DataFrame(heart_rate_data)
    # print(f'heart_rate_df is: {heart_rate_df}')
    heart_rate_fig = px.line(
        heart_rate_df,
        x='Time',
        y='Heart Rate(BPM)',
        title='Heart Rate vs Time',
        # line_shape='spline' # This is supposed to smooth out the line.
    )
    heart_rate_fig.update_layout(xaxis=dict(dtick=len(time_list) / 8))  # Define x-axis tick marks.
    return heart_rate_fig.to_html(full_html=False)


def plot_cadence_vs_distance(cadence_list, distance_list):
    """
    This function prepares the data to be plotted using Plotly. It takes two lists as parameters, converts them to
    Pandas dataframes, converts them to a figure, and finally converts the figure to an HTML div string. The cadence
    list is plotted on the Y-Axis and the distance is plotted on the X-Axis.
    :param cadence_list: (List of floats) The cadence at any given time in the activity.
    :param distance_list: (List of floats) The distance at any given time of the activity.
    :return: The figure converted to an HTML div string.
    """

    if len(cadence_list) == 0:
        print(f'cadence_list is empty. Returning from plot_cadence_vs_distance()')
        return

    if len(distance_list) == 0:
        print(f'distance_list is empty. Returning from plot_cadence_vs_distance()')
        return

    cadence_data = {
        'Activity Cadence': cadence_list,
        'Distance(Miles)': distance_list
    }
    cadence_df = pd.DataFrame(cadence_data)
    cadence_fig = px.line(
        cadence_df,
        x='Distance(Miles)',
        y='Activity Cadence',
        title='Cadence vs Distance',
        # line_shape='spline' # This is supposed to smooth out the line.
    )
    cadence_fig.update_layout(
        xaxis=dict(dtick=round(distance_list[-1] / 12, 1)),  # Define x-axis tick marks.
        yaxis_range=[max(cadence_list) * -0.05, max(cadence_list) * 1.1]  # Define y-axis range.
    )
    return cadence_fig.to_html(full_html=False)


def plot_power_vs_distance(power_list, distance_list):
    """
    This function prepares the data to be plotted using Plotly. It takes two lists as parameters, converts them to
    Pandas dataframes, converts them to a figure, and finally converts the figure to an HTML div string. The power list
    is plotted on the Y-Axis and the distance is plotted on the X-Axis.
    :param power_list: (List of floats) The power at any given time in the activity.
    :param distance_list: (List of floats) The distance at any given time of the activity.
    :return: The figure converted to an HTML div string.
    """

    if len(power_list) == 0:
        print(f'power_list is empty. Returning from plot_power_vs_distance()')
        return

    if len(distance_list) == 0:
        print(f'distance_list is empty. Returning from plot_power_vs_distance()')
        return

    power_data = {
        'Activity Power': power_list,
        'Distance(Miles)': distance_list
    }
    power_df = pd.DataFrame(power_data)
    power_fig = px.line(
        power_df,
        x='Distance(Miles)',
        y='Activity Power',
        title='Power vs Distance',
        # line_shape='spline' # This is supposed to smooth out the line.
    )
    power_fig.update_layout(
        xaxis=dict(dtick=round(distance_list[-1] / 12, 1)),  # Define x-axis tick marks.
        yaxis_range=[max(power_list) * -0.05, max(power_list) * 1.1]  # Define y-axis range.
    )
    return power_fig.to_html(full_html=False)


def calculate_speed(trackpoints):
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
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Namespaces in TCX files
    ns = {'tcx': 'http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2'}

    trackpoints = []
    for tp in root.findall('.//tcx:Trackpoint', ns):
        time = tp.find('tcx:Time', ns)
        position = tp.find('tcx:Position', ns)

        if time is not None and position is not None:
            timestamp = datetime.fromisoformat(time.text.replace("Z", "+00:00"))
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
            with open(f'{DECOMPRESSED_ACTIVITY_FILES_FOLDER}/{output_file_name}', 'wb') as f_out:
            # with open(output_file, 'wb') as f_out:
                    f_out.write(f_in.read())
    else:
        print(f'There is no compressed file named {filename} in {filepath}')

def modify_tcx_file(file_name):
    """
    This function opens the .tcx file and removes the first line which was causing an issue. The first line was xml
    specific. TCX files are basically xml files, but for some reason the tcx parser would throw an error when trying to
    parse the tcx file. The original file is read into a list, all if it except for the first line. The list is then
    written back to the original file, overridding the original content.
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
    cadence_list = []
    power_list = []
    file_is_found = False

    # db = Database()

    # print(f'activity_id is: {activity_id}')
    activity_data = db.session.get(Activity, activity_id)
    # print(f'activity_data.filename is: {activity_data.filename}')
    filename = activity_data.filename.split("/")[-1]
    sub_dir = activity_data.filename.split("/")[0]
    print(f'filename from get_activity_tcx_file() is: {filename}')
    input_file_path = f'{filepath}/{sub_dir}'
    # print(f'input_file_path from get_activity_tcx_file() is: {input_file_path}')
    # output_file = f'{activity_data.filename.split("/")[1].split(".")[0]}.tcx'

    # Linear search for file
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
        xml_filename = DECOMPRESSED_ACTIVITY_FILES_FOLDER + '/' + filepath.split('/')[-1].split('.gz')[0]
        modify_tcx_file(xml_filename)
        with open(xml_filename, 'r') as f:
            tcx = tcxparser.TCXParser(f)

            print(f'TEST - Avg HR: {tcx.hr_avg}')

            # Get activity data points
            altitude_list = [int(convert_meters_to_feet(alt_point)) for alt_point in tcx.altitude_points()]
            distance_list = [float(convert_meter_to_mile(value)) for value in tcx.distance_values()]
            time_list = tcx.time_values()
            hr_list = tcx.hr_values()
            position_list = tcx.position_values()
            cadence_list = tcx.cadence_values()
            power_list = tcx.power_values()


            #     xml_string = f.read().strip()  # Strip leading/trailing whitespace
        #     xml_dict = xmltodict.parse(xml_string)
        #     # print(f'xml_string is: {xml_string}')
        #
        #     # Testing writing to a tcx file, modifying the file, and then closing it.
        #     txt_filename = 'xml_to_txt.txt'
        #     with open(txt_filename, 'w') as f:
        #         f.write(xml_string)
        #         f.close()

            # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ End Test ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

        #
        #     # print('filename head is:')
        #     # os.system(f'head {filepath}{filename}')
        #
            # tcx = tcxparser.TCXParser(xml_string)
            # #
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
            # for activity in xml_dict["TrainingCenterDatabase"]["Activities"]["Activity"]["Lap"]:
            #     print(f'activity is: {activity}')
            #     try:
            #         base = activity["Track"]["Trackpoint"]
            #         print(f'base is: {base}')
            #     except TypeError as e:
            #         print(e)
            #         print(f'activity is: {activity}')
            #     # print(base)
            #     else:
            #         for data_point in base:
            #
            #             # Time data point was taken
            #             # print(f'Time: {data_point["Time"]}')
            #             time_list.append(data_point["Time"])
            #
            #             # Position values of the data point
            #             try:
            #                 position_list.append(
            #                     (data_point["Position"]["LatitudeDegrees"], data_point["Position"]["LongitudeDegrees"])
            #                 )
            #                 # print(f'Longitude: {data_point["Position"]["LatitudeDegrees"]}')
            #                 # print(f'Longitude: {data_point["Position"]["LongitudeDegrees"]}')
            #             except KeyError:
            #                 # print(f'No Positional Data is available!')
            #                 # print(f'No Positional Data is available! Appending {position_list[-1]}')
            #                 if len(position_list) > 0:
            #                     position_list.append(position_list[-1])
            #                 else:
            #                     position_list.append((0, 0))
            #
            #             # Elevation value of the data point
            #             try:
            #                 altitude_list.append(float(data_point["AltitudeMeters"]))
            #                 # print(f'Elevation: {data_point["AltitudeMeters"]}')
            #             except KeyError:
            #                 # print(f'No Altitude Data is available!')
            #                 # print(f'No Altitude Data is available! Appending {altitude_list[-1]}')
            #                 if len(altitude_list) > 0:
            #                     altitude_list.append(altitude_list[-1])
            #                 else:
            #                     altitude_list.append(0)
            #
            #             # Distance value of the data point
            #             try:
            #                 # print(f'float(data_point["DistanceMeters"]) is: {float(data_point["DistanceMeters"])}')
            #                 # print(f'float(distance_list[-1]) is: {float(distance_list[-1])}')
            #                 if len(distance_list) > 0:
            #
            #                     # Handle GPS errors. **It was observed in one activity that distance jumped from 9656.46
            #                     # meters to 8051.73 meters (diff of 1604.73 meters) from one data point to the next.**
            #                     if float(distance_list[-1]) > float(data_point["DistanceMeters"]):
            #                         diff = abs(float(data_point["DistanceMeters"]) - float(distance_list[-1]))
            #                         # print(f'Distance: {data_point["DistanceMeters"]} ---> Diff {diff}')
            #                         distance_list.append(float(data_point["DistanceMeters"]) + diff)
            #                     else:
            #                         # print(f'Distance: {data_point["DistanceMeters"]}')
            #                         distance_list.append(float(data_point["DistanceMeters"]))
            #                 else:
            #                     distance_list.append(float(data_point["DistanceMeters"]))
            #
            #             except KeyError:
            #                 # print(f'No Distance Data is available!')
            #                 print(f'No Distance Data is available! Appending {distance_list[-1]}')
            #                 distance_list.append(distance_list[-1])
            #
            #             # Heart rate value of the data pont
            #             try:
            #                 hr_list.append(data_point["HeartRateBpm"]["Value"])
            #                 # print(f'HR: {data_point["HeartRateBpm"]["Value"]}')
            #             except KeyError:
            #                 # print('No Heart Rate Data is available!')
            #                 if len(hr_list) > 0:
            #                     # print(f'No Heart Rate Data is available! Appending {hr_list[-1]}')
            #                     hr_list.append(hr_list[-1])
            #                 else:
            #                     # print('No Heart Rate Data is available! Appending 0.')
            #                     hr_list.append(0)


                    # print(f'first distance point is: {distance_list[0]}')
                    # altitude_list = [int(convert_meters_to_feet(alt_point)) for alt_point in altitude_list]
                    # distance_list = [float(convert_meter_to_mile(value)) for value in distance_list]
                    # time_list = [str(value) for value in time_list]
                    # hr_list = [int(value) for value in hr_list]
                    # position_list = [tuple(value) for value in position_list]
                    #
                    # for i in range(1, len(distance_list) - 1):
                    #     hour1 = time_list[i - 1].split(":")[-3][-2:]
                    #     min1 = time_list[i - 1].split(":")[-2]
                    #     sec1 = time_list[i - 1].split(":")[-1][0:2]
                    #     hour2 = time_list[i].split(":")[-3][-2:]
                    #     min2 = time_list[i].split(":")[-2]
                    #     sec2 = time_list[i].split(":")[-1][0:2]
                    #
                    #     point1 = datetime.strptime(f'{hour1}:{min1}:{sec1}', '%H:%M:%S')
                    #     point2 = datetime.strptime(f'{hour2}:{min2}:{sec2}', '%H:%M:%S')
                    #
                    #     # Calculate the time, in hours, between data points (To later be converted to MPH)
                    #     time_delta = (point2 - point1).total_seconds() / 3600
                    #
                    #     try:
                    #         speed = (distance_list[i] - distance_list[i - 1])/time_delta
                    #     except ZeroDivisionError:
                    #         speed_list.append(speed_list[-1])
                    #     else:
                    #         speed_list.append(speed)
                    #

            # Make all the other lists the same length as the time_list by appending their last data point to the list
            # repeatedly until it is the same length as the time_list.
            if len(time_list) > 0:

                # Check if the altitude list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                if len(altitude_list) > 0:
                    while len(altitude_list) < len(time_list):
                        altitude_list.append(altitude_list[-1])

                # Check if the distance list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                if len(distance_list) > 0:
                    while len(distance_list) < len(time_list):
                        distance_list.append(distance_list[-1])

                # Create the speed list
                tcx_file = xml_filename
                trackpoints = parse_tcx(tcx_file)
                speed_list = calculate_speed(trackpoints)

                if len(speed_list) > 0:
                    while len(speed_list) < len(time_list):
                        speed_list.append(speed_list[-1])

                # Check if the heartrate list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                if len(hr_list) > 0:
                    while len(hr_list) < len(time_list):
                        hr_list.append(hr_list[-1])

                # Check if the position list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                if len(position_list) > 0:
                    while len(position_list) < len(time_list):
                        position_list.append(position_list[-1])

                # Check if the cadence list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                if len(cadence_list) > 0:
                    while len(cadence_list) < len(time_list):
                        cadence_list.append(cadence_list[-1])

                # Check if the power list is the same length as the time_list, if not, then make it the same length,
                # if it has any data in it.
                if len(power_list) > 0:
                    while len(power_list) < len(time_list):
                        power_list.append(power_list[-1])

            # Show activity data points
            # print(altitude_list)
            # print(f'distance_list is: {distance_list}')
            # print(f'time_list is: {time_list}')
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
                    message = f'No heart rate data was found.'

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

    # db = Database()

    activity_data = db.session.get(Activity, activity_id)
    activity_type = activity_data.activity_type
    print(f'Activity Type is: {activity_type}')
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
    count = 0

    with fitdecode.FitReader(output_file) as fit_file:
        try:
            for frame in fit_file:
                if isinstance(frame, fitdecode.FitDataMessage):
                    if frame.name == 'record':
                        count += 1
                        # Append activity time to the time_list
                        time = frame.get_value('timestamp')
                        if count == 1:
                            initial_time = time
                            print(f'[{count}] initial_time is: {initial_time.strftime("%H:%M:%S")}')
                        elapsed_time = (time - initial_time).total_seconds()
                        time_list.append(Database.convert_seconds_to_time_format(elapsed_time))

                        # Append activity distance to the distance_list
                        try:
                            distance = convert_meter_to_mile(frame.get_value('distance'))
                        except KeyError as e:
                            # print(f'ERROR: {e}. Skipping for now.')
                            if len(distance_list) > 0:
                                distance_list.append(distance_list[-1])
                            else:
                                distance_list.append(0)
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
                            if len(speed_list) > 0:
                                speed_list.append(speed_list[-1])
                            else:
                                speed_list.append(0)
                        else:
                            speed_list.append(speed)

                        # Append activity heart_rate to the heart_rate_list
                        try:
                            heart_rate = frame.get_value('heart_rate')
                        except KeyError as e:
                            # print(f'ERROR: {e}. Skipping for now.')
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
                            # print(f'ERROR: {e}. Skipping for now.')
                            if len(cadence_list) > 0:
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
                        try:
                            temperature = convert_celsius_to_fahrenheit(frame.get_value('temperature'))
                        except KeyError as e:
                            # print(f'ERROR: {e}. Skipping for now.')
                            temperature_list.append(temperature_list[-1])
                        else:
                            temperature_list.append(temperature)

                        # Append activity power to the power_list
                        try:
                            power = frame.get_value('power')
                        except KeyError as e:
                            # print(f'ERROR: {e}. Skipping for now.')
                            if len(power_list) > 0:
                                power_list.append(power_list[-1])
                        else:
                            power_list.append(power)

        except fitdecode.exceptions.FitEOFError as e:
            print(e)

        if activity_type == "Workout":
            print('workout')
            # Plot Heart Rate vs Distance
            # print(f'time_list is: {[Database.convert_seconds_to_time_format(Database.format_seconds(time=second)) for second in time_list]}')
            if len(heart_rate_list) > 0:
                data_dict['heart rate'] = plot_heart_rate_vs_time(heart_rate_list, time_list)


        else:
            # Plot Speed vs Distance
            data_dict['speed'] = plot_speed_vs_distance(speed_list, distance_list)

            # Plot Elevation vs Distance
            data_dict['elevation'] = plot_elevation_vs_distance(altitude_list, distance_list)

            # Plot Heart Rate vs Distance
            if len(heart_rate_list) > 0:
                data_dict['heart rate'] = plot_heart_rate_vs_distance(heart_rate_list, distance_list)

            # Plot Cadence Rate vs Distance
            if len(cadence_list) > 0:
                data_dict['cadence'] = plot_cadence_vs_distance(cadence_list, distance_list)

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
    Function and route for the activities page. If the request method is POST, then this function will get all of the
    data from the filter options and query the database based off the filter(s) that were chosen. If the request method
    is GET, then all the data wil be queried from the database. The filters that have max and min values will be
    populated with those values from the max and min values that are stored in the database. Graphs will be
    generated for moving time, distance, average speed, max speed, and elevation gain from the selected data.

    :return: Renders the activities.html page.
    """
    activities = ''
    num_of_activities = 0
    filetype = Activity.filename
    # print(f'filetype is: {filetype}')

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

    # Open and load the JSON file
    with open('transfer_data.json', 'r') as openfile:
        json_file_data = json.load(openfile)
        filepath = os.path.join(os.getcwd(), json_file_data['relative_path'])

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
@main.route('/upload-file', methods=['POST'])
def upload_file():
    """
    Get the full path to the directory that was chosen by the user and search for a file called 'activities.csv'. Write
    the relative path to the activities.csv file to the transfer_data.json file. Inform the user if the file has been
    found successfully or not.
    :return: (json) a json file with a message informing the user if the activities.csv file was found or not.
    """
    uploaded_files = request.files.getlist('files')
    ct = datetime.now()
    current_time = f'{ct.month}/{ct.day}/{ct.year} - {ct.hour}:{ct.minute}:{ct.second}'

    for file in uploaded_files:
        if os.path.basename(file.filename) == TARGET_FILENAME:
            save_path = os.path.join(Config.UPLOAD_FOLDER, file.filename.split('/')[1])
            file.save(save_path)
            convert_activity_csv_to_db()
            transfer_data = {
                "relative_path": file.filename.split('/')[0]
            }
            json_file_data = json.dumps(transfer_data, indent=1)
            with open('transfer_data.json', 'w') as outfile:
                outfile.write(json_file_data)

            return jsonify({
                "message": f'File "{TARGET_FILENAME}" has been found! [Uploaded at: {current_time}]',
                "file_name": file.filename
            })

    # print(f'Current Time: {current_time}')

    return jsonify({
        "message": f"File '{TARGET_FILENAME}' not found in the selected directoryyyy." # [{current_time}]"
    })


@main.route('/settings', methods=['POST', 'GET'])
def settings():
    """
    Function and route for the settings page, where the user will upload activity data.
    :return: Renders the settings.html page.
    """
    timezone_list = []
    for tz in pytz.all_timezones:
        # print(f'Timezone is: {type(tz)}')
        timezone_list.append(tz)

    if request.method == 'POST':
        print('settings is POST')
        timezone = request.form.get('timezone-options')

        print(f'Selected Time Zone is: {timezone}')
        Config.USER_TIMEZONE = timezone

        print(f'User Timezone is: {Config.USER_TIMEZONE}')

    return render_template(
        'settings.html',
        timezone_list=timezone_list,
        current_timezone_selection=Config.USER_TIMEZONE
    )


@main.route('/error', methods=['POST', 'GET'])
def error(error_message):
    """
    Function and route for the upload activity page, where the user will upload activity data.
    :return: Renders the upload_activities.html page.
    """

    return render_template('error.html', error_message=error_message)
