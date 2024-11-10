from datetime import datetime, timedelta
import pytz
import pandas as pd
import sqlite3
# from tkinter import filedialog as fd

class Database:

    # def __init__(self, upload_directory):
    #     self.STRAVA_DATA_DIRECTORY = upload_directory
    def __init__(self):
        self.DATABASE_NAME = 'instance/strava_data.db'
        self.TABLE_NAME = 'activity'
        # STRAVA_DATA_DIRECTORY = fd.askdirectory()
        self.ACTIVITIES_CSV_FILE = '/uploads/activities.csv'
        self.TIMEZONE_OFFSET = 8  # PST offset
        self.KM_TO_MILE = 0.621371
        self.METERS_PER_SECOND_TO_MPH = 2.23694
        self.METER_TO_FOOT = 3.28084
        self.METER_TO_MILE = 0.000621371
        self.KG_TO_LBS = 2.20462

    @staticmethod
    def get_start_hour(start_time):
        return int(datetime.strptime(
            start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%H'))

    @staticmethod
    def get_year(start_time):
        return datetime.strptime(
            start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y')

    @staticmethod
    def get_date(start_time):
        return datetime.strptime(
            start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y-%m-%d')

    @staticmethod
    def convert_time_format(start_time):
        return datetime.strptime(
            start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_month_and_year(start_time):
        return datetime.strptime(
            start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%b')

    @staticmethod
    def calculate_average_speed(row):
        if row['Distance'] is not None and row['Moving Time'] is not None:  # and row['Activity Type'] == "Ride":
            distance_mile = float(row['Distance'])
            if int(row['Moving Time']) != 0:
                return round(distance_mile / float(row['Moving Time']) * 3600, 2)

    # ============================== Conversion Functions ==============================
    def convert_csv_to_df(self):

        # Original Strava Activity CSV Location
        try:
            activity_csv_data = pd.read_csv(
                # self.STRAVA_DATA_DIRECTORY + self.ACTIVITIES_CSV_FILE,
                self.ACTIVITIES_CSV_FILE
                # dtype={
                #     'Activity ID': 'int32',
                #     'Activity Name': 'string',
                #     'Activity Type': 'string',
                #     'Distance': 'float',
                #     'Commute': 'string',
                #     'Moving Time': 'float',
                #     'Max Speed': 'float',
                #     'Elevation Gain': 'float',
                #     'Elevation High': 'float',
                # }
            )
        except FileNotFoundError:
            print(f'No file named {self.ACTIVITIES_CSV_FILE[1:]} was found')
        else:

            # Pandas Data Frame with all the desired data
            desired_data = activity_csv_data[[
                'Activity ID',  # 0
                'Activity Date',  # 1
                'Activity Name',  # 2
                'Activity Type',  # 3
                'Distance',  # 4
                'Commute',  # 5
                'Activity Description',
                'Activity Gear',  # 6
                # 'Athlete Weight',  # 7
                # 'Bike Weight',  # 8
                'Moving Time',  # 9
                'Max Speed',  # 10
                'Elevation Gain',  # 11
                # 'Elevation Loss',  # 12
                # 'Elevation Low',  # 13
                'Elevation High',  # 14
                # 'Max Grade',  # 15
                # 'Average Grade',  # 16
                # 'Average Cadence',  # 17
                # 'Average Heart Rate',  # 18
                # 'Average Watts',  # 19
                # 'Calories'  # 20
            ]]

            # desired_data.fillna({'Commute': False}, inplace=True)

            # activities_group = desired_data.groupby('Activity Type')
            # print(f'Activities Group is:\n {activities_group.first()}')
            # desired_data['activity_id'] = desired_data.loc[:, 'Activity ID']
            # desired_data['Distance'] = desired_data['Distance'].apply(lambda km : round(float(km) * 0.621371, 2))
            # desired_data['Distance'] = desired_data.loc[:, 'Distance']

            # distance = desired_data['Distance']
            # print(f"desired_data['Activity Type'] is: {type(desired_data['Activity Type'])}")
            # converted_distance = distance.apply(lambda dist: self.convert_meter_to_mile if desired_data['Activity Type'] == 'Swim' else self.convert_kilometer_to_mile)

            converted_distance = desired_data.apply(self.convert_distance, axis=1)
            desired_data['Distance'] = converted_distance

            max_speed = desired_data['Max Speed'].fillna(0)
            converted_max_speed = max_speed.apply(self.convert_max_speed)
            desired_data['Max Speed'] = converted_max_speed

            desired_data['Elevation Gain'] = desired_data['Elevation Gain'].fillna(0)
            elevation_gain = desired_data['Elevation Gain']
            converted_elevation_gain = elevation_gain.apply(self.convert_meter_to_foot)
            desired_data['Elevation Gain'] = converted_elevation_gain

            desired_data['Elevation High'] = desired_data['Elevation High'].fillna(0)
            highest_elevation = desired_data['Elevation High']
            converted_highest_elevation = highest_elevation.apply(self.convert_meter_to_foot)
            desired_data['Elevation High'] = converted_highest_elevation

            desired_data['Activity Date'] = desired_data['Activity Date'].apply(self.convert_utc_time_to_pst)
            desired_data['Activity Date'] = desired_data['Activity Date'].apply(self.convert_time_format)

            # Calculate avg speed and create a new column
            desired_data['average_speed'] = desired_data.apply(self.calculate_average_speed, axis=1)
            desired_data['average_speed'] = desired_data['average_speed'].fillna(0)

            desired_data['Moving Time Seconds'] = desired_data['Moving Time'].copy()
            desired_data['Moving Time'] = desired_data['Moving Time'].apply(self.convert_seconds_to_time_format)

            desired_data['Activity Gear'] = desired_data['Activity Gear'].fillna('No Gear Listed')

            # Optional fields that may not have data due to extra gear not used.
            # desired_data['Average Cadence'].fillna(0, inplace=True)
            # desired_data['Average Heart Rate'].fillna(0, inplace=True)

            # Calculated by Strava
            # desired_data['Average Watts'].fillna(0, inplace=True)
            # desired_data['Calories'].fillna(0, inplace=True)

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
                 'Activity Gear': 'activity_gear'
                 }
            )

            print(f'desired_data columns is:\n {renamed_column_titles.columns}')

            return renamed_column_titles

    def format_seconds(self, time):
        converted_time = timedelta(seconds=time)
        return converted_time

    def convert_utc_time_to_pst(self, df):
        activity_start_time = datetime.strptime(df, '%b %d, %Y, %I:%M:%S %p')

        # Get daylight savings info(dst) for activity datetime
        tz = pytz.timezone('UTC')
        new_tz = pytz.timezone('PST8PDT')
        activity_start = tz.localize(activity_start_time)
        activity_start_time_dst_info = int(str(
            activity_start.astimezone(new_tz).dst()
        )[0])

        adjusted_time = activity_start_time - timedelta(
            hours=self.TIMEZONE_OFFSET - activity_start_time_dst_info)
        new_format = adjusted_time.strftime('%b %d, %Y, %I:%M:%S %p')

        return new_format

    def convert_df_to_csv(self, df, save_name):
        try:
            # df.to_csv(f'{self.STRAVA_DATA_DIRECTORY}/{save_name}.csv', header=True, index_label='index')
            df.to_csv(f'{save_name}.csv', header=True, index_label='index')
        except PermissionError:
            print(f'\n!!!!!{save_name} Not Saved!!!!!\nPermission Denied. Make sure the file isn\'t open.\n')
        else:
            print(f'CSV File Saved: {save_name}')

    def convert_distance(self, row):
        # print(type(row['Distance']), type(row['Activity Type']))
        if row['Activity Type'] == 'Swim':
            # print('This is a swim activity')
            return self.convert_meter_to_mile(row['Distance'])
        else:
            # print('This is not a swim activity')
            # print(f'row is:\n {row}')
            return self.convert_kilometer_to_mile(row['Distance'])

    def convert_kilometer_to_mile(self, km):
        if type(km) == str:
            km = float(km.replace(',', ''))
        return round(km * self.KM_TO_MILE, 2)

    def convert_max_speed(self, max_speed):
        """
        Converting the max speed value from meters per second to MPH.
        :param max_speed:
        :return: max_speed * 2.23694 rounded to the nearest hundredth
        """
        return round(max_speed * self.METERS_PER_SECOND_TO_MPH, 2)

    def convert_meter_to_foot(self, meter):
        return round(meter * self.METER_TO_FOOT, 2)

    def convert_meter_to_mile(self, meter):
        if type(meter) == str:
            meter = meter.replace(',', '')  # Remove the comma from values so it can be converted to float.
            meter = float(meter)
        return round(meter * self.METER_TO_MILE, 2)

    # Takes seconds as an integer and converts it to a string in hh:mm:ss format
    @staticmethod
    def convert_seconds_to_time_format(time_in_sec):
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

    def convert_kg_to_lbs(self, kg):
        return kg * self.KG_TO_LBS

    # # ============================== SQL Queries ==============================
    # all_query = f'''SELECT * FROM {TABLE_NAME}'''
    #
    # column_name_query = f'''PRAGMA table_info({TABLE_NAME})'''
    #

    #
    # test_query = f'''SELECT
    # "Activity Name",
    #  "Activity Date",
    #   "Moving Time",
    #    "Average Speed",
    #     "Distance",
    #      "Activity Type",
    #       "Start Hour"
    #  FROM {TABLE_NAME}
    #  WHERE Commute = 0 AND "Activity Type" IS "Ride"'''
    #
    # commute_data = f'''SELECT
    # "Activity Name",
    #  "Activity Date",
    #   "Moving Time",
    #    "Average Speed",
    #     "Distance",
    #      "Activity Type",
    #       "Start Hour"
    #  FROM {TABLE_NAME}
    #  WHERE Commute = 1 AND "Activity Type" IS "Ride"'''
    #
    # morning_commute = f'''SELECT
    #  "Activity Name",
    #   "Activity Date",
    #    "Moving Time",
    #     "Average Speed",
    #      "Distance",
    #       "Activity Type",
    #        "Start Hour"
    # FROM {TABLE_NAME}
    # WHERE (Commute = 1 OR
    #        "Activity Name" LIKE "%Commute%" OR
    #         "Activity Name" LIKE "%Morning%") AND
    #  "Activity Type" IS "Ride" AND "Start Hour" < 10'''
    #
    # afternoon_commute = f'''SELECT
    #  "Activity Name",
    #   "Activity Date",
    #    "Moving Time",
    #     "Average Speed",
    #      "Distance",
    #       "Activity Type",
    #        "Start Hour"
    # FROM {TABLE_NAME}
    # WHERE (Commute = 1  OR
    #        "Activity Name" LIKE "%Commute%" OR
    #         "Activity Name" LIKE "%Afternoon%") AND
    #  "Activity Type" IS "Ride" AND "Start Hour" >= 10'''
    #
    # activity_date = f'''SELECT "Activity Date"
    # FROM {TABLE_NAME}
    #  WHERE Commute = 1'''
    #
    # ============================== SQL/Database Functions ==============================

    def drop_table(self, db_name):
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        c.execute(f'''DROP TABLE {self.TABLE_NAME}''')
        connection.close()

    @staticmethod
    def connect_to_db(db_name):
        connection = sqlite3.connect(db_name)
        print(f'Connected to db: {db_name}')
        return connection.cursor()

    @staticmethod
    def create_db_table(db_name, db_table_name, data_frame):
        print(f'data_frame is: {data_frame}')
        connection = sqlite3.connect(db_name)
        data_frame.to_sql(
            db_table_name, connection, if_exists='append', index=False
        )
        print(f'DB Table: {db_table_name} Created Successfully!!')

    def query(self, query_command):
        try:
            connection = sqlite3.connect(self.DATABASE_NAME)
            c = connection.cursor()
            result = c.execute(query_command).fetchall()
            connection.close()
        except Exception as e:
            # print(e)
            print(f'Query was NOT successful({e}).')
        else:
            print('Query executed successfully!!')
            return result

    def print_commute_specific_query_results(self, result):

        for i in range(len(result)):
            print()
            print(f'Activity Name: {result[i][0]} ({type(result[i][0])})')
            print(f'Start time: {result[i][1]} ({type(result[i][1])})')
            print(f'Commute: {result[i][6]} ({type(result[i][6])})')
            print(f'Moving Time: {result[i][2]} | {self.convert_seconds_to_time_format(result[i][2])} ({type(result[i][2])} | {type(self.convert_seconds_to_time_format(result[i][2]))})')
            print(f'Distance: {self.convert_kilometer_to_mile(float(result[i][4]))} Miles ({type(self.convert_kilometer_to_mile(float(result[i][4])))})')
            print(f'Average Speed: {result[i][3]} MPH ({type(result[i][3])})')
            print(f'Activity Type: {result[i][5]} ({type(result[i][5])})')


    @staticmethod
    def display_db_data(db_name, query_command):
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        print(c.execute(query_command).fetchall())
