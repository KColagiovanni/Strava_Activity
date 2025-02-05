from datetime import datetime, timedelta
import pytz
import pandas as pd
import sqlite3

class Database:

    def __init__(self):
        self.DATABASE_NAME = 'instance/strava_data.db'
        self.TABLE_NAME = 'activity'
        self.ACTIVITIES_CSV_FILE = 'uploads/activities.csv'
        self.TIMEZONE_OFFSET = 8  # PST offset
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
        This function converts the activity CSV file, converts it to a Pandas data frame.
        :return:
        """

        # Strava Activity CSV Location
        try:
            activity_csv_data = pd.read_csv(
                self.ACTIVITIES_CSV_FILE
            )
        except FileNotFoundError:
            print(f'No file named {self.ACTIVITIES_CSV_FILE} was found')
        else:

            # Pandas Data Frame with all the desired data
            desired_data = activity_csv_data[[
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
                'Elevation High',
                # 'Athlete Weight',
                # 'Bike Weight',
                # 'Elevation Loss',
                # 'Elevation Low',
                # 'Max Grade',
                # 'Average Grade',
                # 'Average Cadence',
                # 'Average Heart Rate',
                # 'Average Watts',
                # 'Calories'
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
                 'Activity Gear': 'activity_gear',
                 'Filename': 'filename'
                 }
            )
            return renamed_column_titles

    @staticmethod
    def format_seconds(time):
        return timedelta(seconds=time)

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

    def drop_table(self, db_name):
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        c.execute(f'''DROP TABLE {self.TABLE_NAME}''')
        print(f'The {self.TABLE_NAME} table has been dropped.')
        connection.close()

    @staticmethod
    def connect_to_db(db_name):
        '''
        Connect to the database or create it if it doesn't exist.

        :param db_name:
        :return:
        '''
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
