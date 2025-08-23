from datetime import datetime, timedelta
from pytz import timezone
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
    def get_hour(start_time):
        """
        Take a datetime as a parameter, and return the hour.
        :param start_time: (str) The date and time as a string, in the following format example:
        "Dec 21, 2001, 05:10:20 PM".
        :return: (str) The year (Ex. "17")
        """
        return int(datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%H'))

    @staticmethod
    def get_year(start_time):
        """
        Take a datetime as a parameter, and return the year.
        :param start_time: (str) The date and time as a string, in the following format example:
        "Dec 21, 2001, 05:10:20 PM".
        :return: (str) The year (Ex. "2001")
        """
        return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y')

    @staticmethod
    def get_date(start_time):
        """
        Take a datetime as a parameter, and return the short version of the month name.
        :param start_time: (str) The date and time as a string, in the following format example:
        "Dec 21, 2001, 05:10:20 PM".
        :return: (str) The date as a string, in the following format example: "2001-12-21"
        """
        return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%Y-%m-%d')

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

    @staticmethod
    def get_month(start_time):
        """
        Take a datetime as a parameter, and return the short version of the month name.
        :param start_time: (str) The date and time as a string, in the following format example:
        "Dec 21, 2001, 05:10:20 PM".
        :return: (str) The month name, short version (Ex. "Dec")
        """
        return datetime.strptime(start_time, '%b %d, %Y, %I:%M:%S %p').strftime('%b')

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


    # ============================== Conversion Functions ==============================
    def convert_csv_to_df(self):
        """
        This function converts the CSV file with the activity data into a Pandas data frame.
        :return: (Pandas dataframe) The dataframe with the desired activity data columns.
        """

        # Strava Activity CSV Location. If it doesn't exist, handle the FileNotFoundError.
        try:
            desired_data = pd.read_csv(
                self.activities_csv_file,
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
            print(f'No file named {self.activities_csv_file} was found')
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

    # @staticmethod
    # def format_seconds(time):
    #     """
    #     Takes the activity duration in HH:MM:SS and converts it to seconds.
    #     :param time: (int) Activity duration in HH:MM:SS format.
    #     :return: (datetime obj) Activity duration in seconds.
    #     """
    #     # TODO: Complete docstring comment
    #     return timedelta(seconds=time)

    @staticmethod
    def convert_utc_time_to_local_time(df_row_value):
        """
        # TODO: Complete docstring comment
        :param df_row_value:
        :return:
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

    @staticmethod
    def convert_df_to_csv(df, save_name):
        # TODO: Complete docstring comment
        try:
            df.to_csv(f'{save_name}.csv', header=True, index_label='index')
        except PermissionError:
            print(f'\n!!!!!{save_name} Not Saved!!!!!\nPermission Denied. Make sure the file isn\'t open.\n')
        else:
            print(f'CSV File Saved: {save_name}')

    def convert_distance(self, row):
        # TODO: Complete docstring comment
        if row['Activity Type'] == 'Swim':
            return self.convert_meter_to_mile(row['Distance'])
        else:
            return self.convert_kilometer_to_mile(row['Distance'])

    def convert_kilometer_to_mile(self, km):
        # TODO: Complete docstring comment
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
        # TODO: Complete docstring comment
        return round(meter * self.METER_TO_FOOT, 2)

    def convert_meter_to_mile(self, meter):
        # TODO: Complete docstring comment
        if type(meter) == str:
            meter = meter.replace(',', '')  # Remove the comma from values so it can be converted to float.
            meter = float(meter)
        return round(meter * self.METER_TO_MILE, 2)

    # Takes seconds as an integer and converts it to a string in hh:mm:ss format
    @staticmethod
    def convert_seconds_to_time_format(time_in_sec):
        # TODO: Complete docstring comment
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
        # TODO: Complete docstring comment
        return kg * self.KG_TO_LBS

    def drop_table(self, db_name):
        # TODO: Complete docstring comment
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        c.execute(f'''DROP TABLE IF EXISTS {self.table_name}''')
        print(f'The {self.table_name} table has been dropped.')
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
        # TODO: Complete docstring comment
        connection = sqlite3.connect(db_name)
        data_frame.to_sql(
            db_table_name, connection, if_exists='append', index=False
        )
        print(f'The db table "{db_table_name}" was created in the {db_table_name}.db database successfully!!')
