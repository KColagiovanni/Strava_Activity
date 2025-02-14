from datetime import datetime, timedelta
import pytz
import pandas as pd
import sqlite3
from config import Config

class Database:

    def __init__(self):

        # Variables defined in config.py
        self.database_name = Config.DATABASE_NAME
        self.table_name = Config.TABLE_NAME
        self.activities_csv_file = Config.ACTIVITIES_CSV_FILE
        self.timezone_offset = Config.TIMEZONE_OFFSET

        # Local constants
        self.KM_TO_MILE = 0.621371
        self.METERS_PER_SECOND_TO_MPH = 2.23694
        self.METER_TO_FOOT = 3.28084
        self.METER_TO_MILE = 0.000621371
        self.KG_TO_LBS = 2.20462

    @staticmethod
    def get_start_hour(start_time):
        return int(datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%H'))

    @staticmethod
    def get_year(start_time):
        return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y')

    @staticmethod
    def get_date(start_time):
        return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y-%m-%d')

    @staticmethod
    def convert_time_format(start_time):
        return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y-%m-%d %H:%M:%S')

    @staticmethod
    def get_month_and_year(start_time):
        return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%b')

    @staticmethod
    def calculate_average_speed(dataframe):
        """
        This method does what is says in the name, it calculates the average speed of a data frame using the "Distance"
        and "Moving Time" data rows.
        # TODO Check how the dataframe.apply method works. Does it "apply" the method row by row, or as a dataframe.
        :param dataframe: (pandas dataframe) the dataframe that will be calculated.
        :return: The calculated average speed.
        """
        if dataframe['Distance'] is not None and dataframe['Moving Time'] is not None:
            distance_mile = float(dataframe['Distance'])
            if int(dataframe['Moving Time']) != 0:
                return round(distance_mile / float(dataframe['Moving Time']) * 3600, 2)

    # ============================== Conversion Functions ==============================
    def convert_csv_to_df(self):
        """
        This function converts the CSV file with the activity data into a Pandas data frame.
        :return: (Pandas dataframe) The dataframe with the desired activity data columns.
        """

        # Strava Activity CSV Location. If it doesn't exist, handle the error.
        try:
            # activity_csv_data = pd.read_csv(
            #     self.activities_csv_file,
            #     usecols=['Activity ID', 'Activity Date', 'Activity Name', 'Activity Type', 'Distance', 'Commute', 'Activity Description', 'Activity Gear', 'Filename', 'Moving Time', 'Max Speed', 'Elevation Gain', 'Elevation High']
            # )
            desired_data = pd.read_csv(
                self.activities_csv_file,
                nrows=10,
                skiprows=[-1],
                usecols=['Activity ID', 'Activity Date', 'Activity Name', 'Activity Type', 'Distance', 'Commute', 'Activity Description', 'Activity Gear', 'Filename', 'Moving Time', 'Max Speed', 'Elevation Gain', 'Elevation High']
            )
        except FileNotFoundError:
            print(f'No file named {self.activities_csv_file} was found')
        else:

            # Pandas Data Frame with all the desired data
            # desired_data = activity_csv_data[[
            #     'Activity ID',
            #     'Activity Date',
            #     'Activity Name',
            #     'Activity Type',
            #     'Distance',
            #     'Commute',
            #     'Activity Description',
            #     'Activity Gear',
            #     'Filename',
            #     'Moving Time',
            #     'Max Speed',
            #     'Elevation Gain',
            #     'Elevation High'
            #     # 'Athlete Weight',
            #     # 'Bike Weight',
            #     # 'Elevation Loss',
            #     # 'Elevation Low',
            #     # 'Max Grade',
            #     # 'Average Grade',
            #     # 'Average Cadence',
            #     # 'Average Heart Rate',
            #     # 'Average Watts',
            #     # 'Calories'
            # ]]

            print(f"desired_data is: {desired_data['Activity Date']}")

            # Convert the distance from meters or kilometers to miles, depending on the activity.
            converted_distance = desired_data.apply(self.convert_distance, axis=1)
            desired_data['Distance'] = converted_distance

            # Convert max speed from meters per second to miles per hour.
            max_speed = desired_data['Max Speed'].fillna(0)
            converted_max_speed = max_speed.apply(self.convert_max_speed)
            desired_data['Max Speed'] = converted_max_speed

            # Convert elevation gain from meters to feet.
            # desired_data['Elevation Gain'] = desired_data['Elevation Gain'].fillna(0)
            desired_data.loc['Elevation Gain'] = desired_data['Elevation Gain'].fillna(0)
            elevation_gain = desired_data['Elevation Gain']
            converted_elevation_gain = elevation_gain.apply(self.convert_meter_to_foot)
            desired_data['Elevation Gain'] = converted_elevation_gain

            # Convert the highest altitude from meters to feet.
            desired_data['Elevation High'] = desired_data['Elevation High'].fillna(0)
            highest_elevation = desired_data['Elevation High']
            converted_highest_elevation = highest_elevation.apply(self.convert_meter_to_foot)
            desired_data['Elevation High'] = converted_highest_elevation

            # Convert the activity date from UTC to users local time, then convert the time format.
            # TODO: Have the user pick their local timezone.

            print(f"df to string is:\n{desired_data.to_string()}")
            # print(f"df to string is:\n{desired_data['Activity Date'].to_string()}")
            print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
            desired_data['Activity Date'] = desired_data['Activity Date'].to_string(na_rep = 'Invalid')
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
    def format_seconds(time):
        return timedelta(seconds=time)

    def convert_utc_time_to_local_time(self, df_row_value):
        """

        :param df_row_value:
        :return:
        """
        # print(f'df from convert_utc_time_to_local_time is: {df_row_value}')
        # print(f'df type from convert_utc_time_to_local_time is: {type(df_row_value)}')

        if type(df_row_value) == str:

            activity_start_time = datetime.strptime(df_row_value, '%b %d, %Y, %I:%M:%S %p')

            # Get daylight savings info(dst) for activity datetime
            tz = pytz.timezone('UTC')
            # TODO change the timezone to be a dictionary with all the timezones.
            local_tz = pytz.timezone(Config.USER_TIMEZONE) # Users local time zone.
            activity_start = tz.localize(activity_start_time)
            activity_start_time_dst_info = int(str(
                activity_start.astimezone(local_tz).dst()
            )[0])
            utc_dt = datetime.utcnow()
            local_dt = local_tz.localize(utc_dt)
            # print(f'local_dt is: {local_dt}')
            timezone_offset = 8

            # adjusted_time = activity_start_time - timedelta(hours=self.TIMEZONE_OFFSET - activity_start_time_dst_info)
            adjusted_time = activity_start_time - timedelta(hours=timezone_offset - activity_start_time_dst_info)
            new_format = adjusted_time.strftime('%b %d, %Y, %I:%M:%S %p')

            return new_format

    def convert_df_to_csv(self, df, save_name):
        try:
            df.to_csv(f'{save_name}.csv', header=True, index_label='index')
        except PermissionError:
            print(f'\n!!!!!{save_name} Not Saved!!!!!\nPermission Denied. Make sure the file isn\'t open.\n')
        else:
            print(f'CSV File Saved: {save_name}')

    def convert_distance(self, row):
        if row['Activity Type'] == 'Swim':
            return self.convert_meter_to_mile(row['Distance'])
        else:
            return self.convert_kilometer_to_mile(row['Distance'])

    def convert_kilometer_to_mile(self, km):
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

    def drop_table(self, db_name):
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        c.execute(f'''DROP TABLE IF EXISTS {Config.TABLE_NAME}''')
        print(f'The {Config.TABLE_NAME} table has been dropped.')
        connection.close()

    @staticmethod
    def connect_to_db(db_name):
        """
        Connect to the database or create it if it doesn't exist.
        :param db_name:
        :return:
        """
        connection = sqlite3.connect(db_name)
        print(f'Connected to db: {db_name}')
        return connection.cursor()

    @staticmethod
    def create_db_table(db_name, db_table_name, data_frame):
        connection = sqlite3.connect(db_name)
        data_frame.to_sql(
            db_table_name, connection, if_exists='append', index=False
        )
        print(f'The db table "{db_table_name}" was created in the {db_table_name}.db database successfully!!')
