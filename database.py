from datetime import datetime, timedelta
import pytz
import pandas as pd
import sqlite3
from tkinter import filedialog as fd

class Database:

    DATABASE_NAME = 'instance/strava_data.db'
    TABLE_NAME = 'strava_activity'
    STRAVA_DATA_DIRECTORY = fd.askdirectory()
    # YEAR_FILTER1 = '2024'
    # YEAR_FILTER2 = '2024'
    CSV_FILE = '/activities.csv'

    # SQL Queries
    all_query = f'''SELECT * FROM {TABLE_NAME}'''

    column_name_query = f'''PRAGMA table_info({TABLE_NAME})'''

    drop_table = f'''DROP TABLE {TABLE_NAME}'''

    test_query = f'''SELECT
    "Activity Name",
     "Activity Date",
      "Moving Time",
       "Average Speed",
        "Distance",
         "Activity Type",
          "Start Hour"
     FROM {TABLE_NAME} 
     WHERE Commute = 0 AND "Activity Type" IS "Ride"'''

    commute_data = f'''SELECT 
    "Activity Name",
     "Activity Date",
      "Moving Time",
       "Average Speed",
        "Distance",
         "Activity Type",
          "Start Hour"
     FROM {TABLE_NAME} 
     WHERE Commute = 1 AND "Activity Type" IS "Ride"'''

    morning_commute = f'''SELECT
     "Activity Name",
      "Activity Date",
       "Moving Time",
        "Average Speed",
         "Distance",
          "Activity Type",
           "Start Hour" 
    FROM {TABLE_NAME} 
    WHERE (Commute = 1 OR
           "Activity Name" LIKE "%Commute%" OR
            "Activity Name" LIKE "%Morning%") AND
     "Activity Type" IS "Ride" AND "Start Hour" < 10'''

    afternoon_commute = f'''SELECT
     "Activity Name",
      "Activity Date",
       "Moving Time",
        "Average Speed",
         "Distance",
          "Activity Type",
           "Start Hour" 
    FROM {TABLE_NAME} 
    WHERE (Commute = 1  OR
           "Activity Name" LIKE "%Commute%" OR
            "Activity Name" LIKE "%Afternoon%") AND
     "Activity Type" IS "Ride" AND "Start Hour" >= 10'''

    activity_date = f'''SELECT "Activity Date"
    FROM {TABLE_NAME}
     WHERE Commute = 1'''

    def convert_csv_to_df(self):

        # Original Strava Activity CSV Location
        try:
            activity_csv_data = pd.read_csv(
                self.STRAVA_DATA_DIRECTORY + self.CSV_FILE
            )
        except FileNotFoundError:
            print(f'No file named {self.CSV_FILE[1:]} was found')
        else:
            # Pandas Data Frame with all the desired data
            desired_data = activity_csv_data[[
                'Activity ID',  # 0
                'Activity Date',  # 1
                'Activity Name',  # 2
                'Activity Type',  # 3
                'Distance',  # 4
                'Commute',  # 5
                'Activity Gear',  # 6
                'Athlete Weight',  # 7
                'Bike Weight',  # 8
                'Moving Time',  # 9
                'Max Speed',  # 10
                'Elevation Gain',  # 11
                'Elevation Loss',  # 12
                'Elevation Low',  # 13
                'Elevation High',  # 14
                'Max Grade',  # 15
                'Average Grade',  # 16
                'Average Cadence',  # 17
                'Average Heart Rate',  # 18
                'Average Watts',  # 19
                'Calories'  # 20
            ]]

            desired_data['Activity ID'] = desired_data.loc[:, 'Activity ID']
            desired_data['Activity Month'] = desired_data.loc[:, 'Activity Date'].apply(self.get_month_and_year)

            # Convert UTC datetime to PST in Desired Data DF
            # Chained Indexing Pandas Warning (Unsure how to resolve)
            # Tried the following without getting rid of the warning
            # desired_data['Activity Date'] = desired_data[
            # 'Activity Date'].apply(convert_utc_time_to_pst)
            # desired_data['Activity Date'] = desired_data.loc[
            # :, 'Activity Date'].apply(convert_utc_time_to_pst)

            desired_data['Activity Date'].update(desired_data.loc[:, 'Activity Date'].apply(self.convert_utc_time_to_pst))

            # Get activity date start hour and year and create a new column
            desired_data['Start Hour'] = desired_data.loc[:, 'Activity Date'].apply(self.get_start_hour)
            desired_data['Year'] = desired_data.loc[:, 'Activity Date'].apply(self.get_year)
            desired_data['Date'] = desired_data.loc[:, 'Activity Date'].apply(self.get_date)

            # Calculate avg speed and create a new column
            desired_data['Average Speed'] = desired_data.apply(self.average_speed, axis=1)

            # Optional fields that may not have data due to extra gear not used.
            desired_data['Average Cadence'].fillna(0, inplace=True)
            desired_data['Average Heart Rate'].fillna(0, inplace=True)

            # Calculated by Strava
            desired_data['Average Watts'].fillna(0, inplace=True)
            desired_data['Calories'].fillna(0, inplace=True)

            print(f'desired_data is: {desired_data}')

            return desired_data

    @staticmethod
    def convert_utc_time_to_pst(df):
        activity_start_time = datetime.strptime(df, '%b %d, %Y, %I:%M:%S %p')

        # Get daylight savings info(dst) for activity datetime
        tz = pytz.timezone('UTC')
        new_tz = pytz.timezone('PST8PDT')
        activity_start = tz.localize(activity_start_time)
        activity_start_time_dst_info = int(str(
            activity_start.astimezone(new_tz).dst()
        )[0])
        pst = 8  # PST offset
        # return str(activity_start_time - timedelta(
        #     hours=pst - activity_start_time_dst_info))

        adjusted_time = activity_start_time - timedelta(
            hours=pst - activity_start_time_dst_info)
        new_format = adjusted_time.strftime('%b %d, %Y, %I:%M:%S %p')

        return new_format

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
    def get_month_and_year(start_time):
        return datetime.strptime(
            start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%b')

    def df_to_csv(self, df, save_name):
        try:
            df.to_csv(f'{self.STRAVA_DATA_DIRECTORY}/{save_name}.csv', header=True, index_label='index')
        except PermissionError:
            print(f'\n!!!!!{save_name} Not Saved!!!!!\nPermission Denied. Make sure the file isn\'t open.\n')
        else:
            print(f'CSV File Saved: {save_name}')

    # Conversion Functions
    @staticmethod
    def kilometer_to_mile(km):
        if type(km) == float:
            return round(float(km) * 0.621371, 2)

    @staticmethod
    def meter_to_foot(meter):
        return meter * 3.28084

    # Takes seconds as an integer and converts it to a string in hh:mm:ss format
    @staticmethod
    def format_seconds(time_in_sec):
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

    @staticmethod
    def kg_to_lbs(weight):
        return weight * 2.20462

    def average_speed(self, row):
        if row['Distance'] is not None and row['Moving Time'] is not None and row['Activity Type'] == "Ride":
            distance_km = float(row['Distance'])
            distance_mile = self.kilometer_to_mile(distance_km)
            if int(row['Moving Time']) != 0:
                return round(distance_mile / float(row['Moving Time']) * 3600, 2)


    # SQL/Database Functions
    @staticmethod
    def connect_to_db(db_name):
        connection = sqlite3.connect(db_name)
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
            print(f'Start Hour: {result[i][6]} ({type(result[i][6])})')
            print(f'Moving Time: {result[i][2]} | {self.format_seconds(result[i][2])} ({type(result[i][2])} | {type(self.format_seconds(result[i][2]))})')
            print(f'Distance: {self.kilometer_to_mile(float(result[i][4]))} Miles ({type(self.kilometer_to_mile(float(result[i][4])))})')
            print(f'Average Speed: {result[i][3]} MPH ({type(result[i][3])})')
            print(f'Activity Type: {result[i][5]} ({type(result[i][5])})')


    @staticmethod
    def display_db_data(db_name, query_command):
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        print(c.execute(query_command).fetchall())
