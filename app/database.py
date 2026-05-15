from datetime import datetime, timedelta
from json.decoder import NaN

from pytz import timezone
import pandas as pd
import sqlite3
from config import Config
from pandas import json_normalize
import json
import csv
import glob

class Database:

    def __init__(self):

        # Variables defined in config.py
        self.database_name = Config.DATABASE_NAME
        self.table_name = Config.ACTIVITY_TABLE_NAME
        self.strava_activities_csv_file = Config.STRAVA_ACTIVITIES_CSV_FILE
        self.garmin_activities_csv_file_dir_path = Config.GARMIN_ACTIVITY_CSV_FILE_DIR
        self.garmin_activities_json_file_path = Config.GARMIN_ACTIVITIES_JSON_FILE_DIR
        self.timezone_offset = Config.TIMEZONE_OFFSET
        self.strength_training_data_csv_file = 'strength_training_data.csv'
        self.activity_data_csv_file = 'activities.csv'


        # Local constants
        self.KM_TO_MILE = 0.621371
        self.METERS_PER_SECOND_TO_MPH = 2.23694
        self.METER_TO_FOOT = 3.28084
        self.METER_TO_MILE = 0.000621371
        self.KG_TO_LBS = 2.20462
        self.CM_TO_MILE = 160900
        self.CM_TO_FOOT = 30.48

        self.indoor_activity = [
            'indoor_cycling',
            'strength_training',
            'indoor_rowing',
            'indoor_cycling',
            'indoor_cardio',
            'yoga',

        ]


    @staticmethod
    def calculate_average_speed(dataframe_row):
        """
        This method does what is says in the name, it calculates the average speed of a data frame using the "Distance"
        and "Moving Time" data rows.
        :param dataframe_row: (pandas dataframe row) the dataframe row that will be calculated.
        :return: The calculated average speed of the dataframe row.
        """
        if dataframe_row['Distance'] is not None and dataframe_row['Moving Time'] is not None:
            distance_mile = float(dataframe_row['Distance'])
            if int(dataframe_row['Moving Time']) != 0:
                return round(distance_mile / float(dataframe_row['Moving Time']) * 3600, 2)

    # ============================== Conversion Methods ==============================
    # def flatten_dict(self, d, parent_key='', sep='_'):
    #     items = {}
    #     for k, v in d.items():
    #         new_key = f'{parent_key}{sep}{k}' if parent_key else k
    #         if isinstance(v, dict):
    #             items.update(self.flatten_dict(v, new_key, sep))
    #         elif isinstance(v, list):
    #             # Store list as JSON string (CSV-safe)
    #             items[new_key] = json.dumps(v)
    #         else:
    #             items[new_key] = v
    #     return items

    #TODO: Fully implement this. It is called in routes.py in the convert_activity_csv_to_db() function.

    def convert_json(self):
        json_activity_files_list = glob.glob(f'{self.garmin_activities_json_file_path}/*summarizedActivities.json')
        # print(f'json files are: {json_activity_files_list}')

        for activity_file in json_activity_files_list:

            with open(activity_file, 'r') as f:
                data = json.load(f)
            
            # JSON root is a list → take first element
            activities = data[0]['summarizedActivitiesExport']

            # Build clean rows
            rows = []

            for activity in activities:
                row = {
                    'activityId': activity.get('activityId'),
                    'startTimeLocal': activity.get('startTimeLocal'),
                    'name': activity.get('name'),

                    # activityType is usually nested
                    'activityType': (
                        activity.get('activityType', {}).get('typeKey')
                        if isinstance(activity.get('activityType'), dict)
                        else activity.get('activityType')
                    ),

                    'distance': activity.get('distance'),
                    'duration': activity.get('duration'),
                    'maxSpeed': activity.get('maxSpeed'),
                    'elevationGain': activity.get('elevationGain'),
                    'maxElevation': activity.get('maxElevation')
                }

                rows.append(row)

            # Create dataframe
            df = pd.DataFrame(rows)

            # Convert timestamps
            df['startTimeLocal'] = pd.to_datetime(df['startTimeLocal'], unit='ms').dt.strftime('%Y-%m-%d %H:%M:%S')

            # Convert distance
            # df['distance'] = df['distance'].fillna('N/A')
            df['distance'] = df['distance'].apply(self.convert_centimeter_to_mile)

            # Convert elapsed time
            # df['duration'] = df['duration'].fillna(0)
            df['duration'] = df['duration'].apply(self.convert_milliseconds_to_time_format)

            # Convert max speed
            df['maxSpeed'] = df['maxSpeed'].fillna(0)
            df['maxSpeed'] = df['maxSpeed'].apply(self.convert_garmin_max_speed_to_mph)

            # Convert elevation gain from meters to feet
            df['elevationGain'] = df['elevationGain'].fillna(0)
            df['elevationGain'] = df['elevationGain'].apply(self.convert_cm_to_foot)

            # Convert max elevation from meters to feet
            df['maxElevation'] = df['maxElevation'].fillna(0)
            df['maxElevation'] = df['maxElevation'].apply(self.convert_cm_to_foot)

            # Save CSV
            output_csv = f'{self.garmin_activities_csv_file_dir_path}/{self.activity_data_csv_file}'
            df.to_csv(output_csv, index=False)


            # ======================================= Strength Activities ==============================================
            # # Filter strength activities
            # strength_activities = [
            #     a for a in activities
            #     if a.get("summarizedExerciseSets")
            # ]
            #
            # # Flatten strength training JSON data
            # flattened_strength_training_df = pd.json_normalize(
            #     strength_activities,
            #     record_path='summarizedExerciseSets',
            #     meta=[
            #         'activityId',
            #         'activityType',
            #     ],
            #     errors='ignore'
            # )
            #
            # # Write CSV
            # strength_training_fieldnames = flattened_strength_training_df.columns.tolist()
            #
            # with open(
            #         f'{self.garmin_activities_csv_file_dir_path}/{self.strength_training_data_csv_file}',
            #         'w',
            #         newline='',
            #         encoding='utf-8'
            # ) as strength_training_data:
            #     writer = csv.DictWriter(strength_training_data, fieldnames=strength_training_fieldnames)
            #     writer.writeheader()
            #     writer.writerows(flattened_strength_training_df.to_dict(orient="records"))
            #
            # print(f'Strength Training data CSV saved as: {self.garmin_activities_csv_file_dir_path}')


    def convert_csv_to_df(self):
        """
        This function converts the CSV file with the activity data into a Pandas data frame.
        :return: (Pandas dataframe) The dataframe with the desired activity data columns.
        """

        # Strava Activity CSV Location. If it doesn't exist, handle the FileNotFoundError.
        try:
            desired_data = pd.read_csv(
                self.strava_activities_csv_file,
                usecols=[
                    'Activity ID',
                    'Activity Date',
                    'Activity Name',
                    'Activity Type',
                    'Distance',
                    'Commute',
                    'Activity Description',
                    'Activity Gear',
                    'Filename',
                    'Moving Time',
                    'Max Speed',
                    'Elevation Gain',
                    'Elevation High'
                ]
            )
        except FileNotFoundError:
            print(f'No file named {self.strava_activities_csv_file} was found')
        else:

            # Convert the distance from meters or kilometers to miles, depending on the activity.
            converted_distance = desired_data.apply(self.convert_distance, axis=1)
            desired_data['Distance'] = converted_distance

            # Convert max speed from meters per second to miles per hour.
            max_speed = desired_data['Max Speed'].fillna(0)
            converted_max_speed = max_speed.apply(self.convert_max_speed)
            desired_data['Max Speed'] = converted_max_speed

            # Convert elevation gain from meters to feet.
            desired_data['Elevation Gain'] = desired_data['Elevation Gain'].fillna(0)

            # Convert the elevation gain from meters to feet.
            elevation_gain = desired_data['Elevation Gain']
            converted_elevation_gain = elevation_gain.apply(self.convert_meter_to_foot)
            desired_data['Elevation Gain'] = converted_elevation_gain

            # Convert the highest altitude from meters to feet.
            desired_data['Elevation High'] = desired_data['Elevation High'].fillna(0)
            highest_elevation = desired_data['Elevation High']
            converted_highest_elevation = highest_elevation.apply(self.convert_meter_to_foot)
            desired_data['Elevation High'] = converted_highest_elevation

            # Convert the activity date from UTC to users local time, then convert the time format.
            desired_data['Activity Date'] = desired_data['Activity Date'].apply(self.convert_utc_time_to_local_time)
            desired_data['Activity Date'] = desired_data['Activity Date'].apply(self.convert_time_format)

            # Calculate avg speed and create a new average speed column.
            desired_data['average_speed'] = desired_data.apply(self.calculate_average_speed, axis=1)
            desired_data['average_speed'] = desired_data['average_speed'].fillna(0)

            # Convert the activity moving time to seconds.
            desired_data['Moving Time Seconds'] = desired_data['Moving Time'].copy()
            desired_data['Moving Time'] = desired_data['Moving Time'].apply(self.convert_seconds_to_time_format)

            # If there is no activity gear listed, then set activity gear to reflect that.
            desired_data['Activity Gear'] = desired_data['Activity Gear'].fillna('No Gear Listed')

            # Optional fields that may not have data due to extra gear not used.
            # desired_data['Average Cadence'].fillna(0, inplace=True)
            # desired_data['Average Heart Rate'].fillna(0, inplace=True)

            # Calculated by Strava
            # desired_data['Average Watts'].fillna(0, inplace=True)
            # desired_data['Calories'].fillna(0, inplace=True)

            # Rename the column names to be more pythonic.
            renamed_column_titles = desired_data.rename(
                columns=
                {'Activity ID': 'activity_id',
                 'Activity Date': 'start_time',
                 'Activity Name': 'activity_name',
                 'Activity Description': 'activity_description',
                 'Activity Type': 'activity_type',
                 'Distance': 'distance',
                 'Moving Time': 'moving_time',
                 'Moving Time Seconds': 'moving_time_seconds',
                 'Commute': 'commute',
                 'Max Speed': 'max_speed',
                 'Elevation Gain': 'elevation_gain',
                 'Elevation High': 'highest_elevation',
                 'Activity Gear': 'activity_gear',
                 'Filename': 'filename'
                 }
            )

            return renamed_column_titles

    @staticmethod
    def convert_time_format(start_time):
        """
        Take the datetime as a parameter and return it in a different format.
        :param start_time: (str) The date and time as a string, in the following format example:
        "Dec 21, 2001, 05:10:20 PM".
        :return: (str) The date and time as a string, in the following format example:
        "2001-12-21 15:10:20".
        """
        if type(start_time) == str:
            return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y-%m-%d %H:%M:%S')
        else:
            return 'Timestamp provided is not a string data type!!!'

    @staticmethod
    def convert_utc_time_to_local_time(df_row_value):
        """
        Convert the date and time string in UTC time to the users local timezone. The time will be in the following
        format: "Dec 21, 2001, 05:10:20 PM". If the df_row_value is not in string format, the value will not be
        converted and will be returned.
        :param df_row_value: (str) The UTC date and time in the following format: "Dec 21, 2001, 05:10:20 PM"
        :return: (str) The date and time in the users local time zone in the following format: "Dec 21, 2001, 05:10:20
        PM"
        """

        if type(df_row_value) == str:

            activity_start_time = datetime.strptime(df_row_value, '%b %d, %Y, %I:%M:%S %p')

            # Get daylight savings info(dst) for activity datetime
            utc_tz = timezone('UTC')
            local_tz = timezone(Config.USER_TIMEZONE) # Users local time zone.
            timezone_offset = int(datetime.now(timezone(Config.USER_TIMEZONE)).strftime("%z")[-3])
            activity_start = utc_tz.localize(activity_start_time)
            activity_start_time_dst_info = int(str(activity_start.astimezone(local_tz).dst())[0])
            adjusted_time = activity_start_time - timedelta(hours=timezone_offset - activity_start_time_dst_info)
            new_format = adjusted_time.strftime('%b %d, %Y, %I:%M:%S %p')

            return new_format

        return df_row_value

    def convert_distance(self, row):
        """
        Convert meter or kilometer, depending on the activity, to mile. If the activity is swimming, convert the
        distance in meters to mile(s) and return the value, otherwise convert the distance from kilometers to miles,
        and return the value.
        :param row: (pandas dataframe) A row from the activity.
        :return: (float) The distance converted to mile(s).
        """
        if row['Activity Type'] == 'Swim':
            return self.convert_meter_to_mile(row['Distance'])
        else:
            return self.convert_kilometer_to_mile(row['Distance'])

    def convert_kilometer_to_mile(self, km):
        """
        Convert the provided parameter in kilometers to miles.
        :param km: (str) Kilometers.
        :return: (float) Miles, rounded to the nearest hundredth.
        """
        if type(km) == str:
            km = float(km.replace(',', ''))
        return round(km * self.KM_TO_MILE, 2)

    def convert_max_speed(self, max_speed):
        """
        Converting the max speed value from meters per second to MPH.
        :param max_speed: (float) Speed in meters per second.
        :return: (float) Speed in miles per hour, rounded to the nearest hundredth.
        """
        return round(max_speed * self.METERS_PER_SECOND_TO_MPH, 2)

    def convert_meter_to_foot(self, meter):
        """
        Convert the provided parameter in meters to feet.
        :param meter: (str) Meters.
        :return: (float) Feet, rounded to the nearest hundredth.
        """
        return round(meter * self.METER_TO_FOOT, 2)

    def convert_meter_to_mile(self, meter):
        """
        Convert the provided parameter in meters to miles.
        :param meter: (str) Meters.
        :return: (float) Miles, rounded to the nearest hundredth.
        """
        if type(meter) == str:
            meter = meter.replace(',', '')  # Remove the comma from values so it can be converted to float.
            meter = float(meter)
        return round(meter * self.METER_TO_MILE, 2)

    @staticmethod
    def convert_seconds_to_time_format(time_in_sec):
        """
        Takes the time, in seconds, and converts it to HH:MM:SS format, or MM:SS if less than an hour.
        :param time_in_sec: (int or str) Seconds.
        :return: (str) Converted time in HH:MM:SS or MM:SS format.
        """
        time_in_sec = int(time_in_sec)
        if time_in_sec >= 3600:
            hour = time_in_sec // 3600
            minutes = (time_in_sec % 3600) // 60
            if minutes < 10:
                minutes = '0' + str(minutes)
            else:
                minutes = str(minutes)
            seconds = time_in_sec % 60
            if seconds < 10:
                seconds = '0' + str(seconds)
            else:
                seconds = str(seconds)
            return f'{hour}:{minutes}:{seconds}'
        else:
            minutes = time_in_sec // 60
            if minutes < 10:
                minutes = '0' + str(minutes)
            else:
                minutes = str(minutes)
            seconds = int(time_in_sec % 60)
            if seconds < 10:
                seconds = '0' + str(seconds)
            else:
                seconds = str(seconds)
            return f'{minutes}:{seconds}'

    def convert_milliseconds_to_time_format(self, time_in_ms):
        """
        Takes the time, in milliseconds, and converts it to seconds, then sends it to the
        convert_seconds_to_time_format() function.
        :param time_in_ms: (int or str) Milliseconds.
        :return: (str) Converted time in HH:MM:SS or MM:SS format.
        """
        return self.convert_seconds_to_time_format(str(int(time_in_ms/1000)))

    def convert_cm_to_foot(self, cm):
        return round(cm / self.CM_TO_FOOT, 2)

    def convert_centimeter_to_mile(self, cm):
        # Convert distance in cm to mile, rounded 2 places after the deciamal.
        return round(cm / self.CM_TO_MILE, 2)

    def convert_garmin_max_speed_to_mph(self, max_speed):
        # Convert max speed in m/s / 10 to MPH(max_speed * meters/second * 10)
        return round(max_speed * self.METERS_PER_SECOND_TO_MPH * 10, 2)

    #============================== Database Methods ==============================
    def drop_table(self, db_name):
        """
        Drop the table, which is defined in config.py, and is part of the database name passed into this function as a
        parameter. Used in the convert_activity_csv_to_db() function in routes.py.
        :param db_name: (str) The name of the database, defined in config.py.
        :return: None
        """
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        c.execute(f'''DROP TABLE IF EXISTS {self.table_name}''')
        print(f'The {self.table_name} table has been dropped.')
        connection.close()

    @staticmethod
    def create_db_tables(db_name, db_table_name, data_frame):
        """
        Create the database table, the name is defined in config.py.
        :param db_name:  (str) The name of the database, defined in config.py.
        :param db_table_name:  (str) The name of the table, defined in config.py.
        :param data_frame: (Pandas dataframe) A dataframe with the activity data.
        :return:
        """
        connection = sqlite3.connect(db_name)
        data_frame.to_sql(db_table_name, connection, if_exists='append', index=False)

        print(f'The db table "{db_table_name}" was created in the {db_table_name}.db database successfully!!')
