import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
import pytz
from tkinter import filedialog as fd

DATABASE_NAME = 'strava_data.db'
TABLE_NAME = 'strava_activity'
STRAVA_DATA_DIRECTORY = fd.askdirectory()

# SQL Queries
all_query = f'''SELECT * FROM {TABLE_NAME}'''
column_name_query = f'''PRAGMA table_info({TABLE_NAME})'''
drop_table = f'''DROP TABLE {TABLE_NAME}'''
commute_data = f'''SELECT "Activity Name", "Activity Date", "Moving Time", "Average Speed", "Distance", "Activity Type" FROM {TABLE_NAME} WHERE Commute = 1'''
morning_commute = f'''SELECT "Activity Name", "Activity Date", "Moving Time", "Average Speed", "Distance" FROM {TABLE_NAME} WHERE Commute = 1 AND Activity Date = '''
afternoon_commute = f'''SELECT "Activity Name", "Activity Date", "Moving Time", "Average Speed", "Distance" FROM {TABLE_NAME} WHERE Commute = 1 AND Activity Date = '''
activity_date = f'''SELECT "Activity Date" FROM {TABLE_NAME} WHERE Commute = 1'''


def convert_csv_to_df():
    # Original Strava Activity CSV Location
    activity_data_frame = pd.read_csv(STRAVA_DATA_DIRECTORY + '/activities.csv')
    # print(activity_data_frame)

    # Pandas Data Frames
    # activity_date = activity_data_frame[['Activity Date']]
    # commute = activity_data_frame[['Commute']]
    # gear = activity_data_frame[['Activity Gear']]
    # athlete_weight = activity_data_frame[['Athlete Weight']]
    # bike_weight = activity_data_frame[['Bike Weight']]
    # moving_time = activity_data_frame[['Moving Time']]
    # max_speed = activity_data_frame[['Max Speed']]
    # avg_speed = activity_data_frame[['Average Speed']]
    # elevation_gain = activity_data_frame[['Elevation Gain']]
    # elevation_loss = activity_data_frame[['Elevation Loss']]
    # elevation_min = activity_data_frame[['Elevation Low']]
    # elevation_max = activity_data_frame[['Elevation High']]
    # max_grade = activity_data_frame[['Max Grade']]
    # avg_grade = activity_data_frame[['Average Grade']]

    # Pandas Data Frame with all the desired data
    desired_data = activity_data_frame[[
        'Activity Date',  # 0
        'Activity Name',  # 1
        'Activity Type',  # 2
        'Distance',  # 3
        'Commute',  # 4
        'Activity Gear',  # 5
        'Athlete Weight',  # 6
        'Bike Weight',  # 7
        'Moving Time',  # 8
        'Max Speed',  # 9
        'Elevation Gain',  # 10
        'Elevation Loss',  # 11
        'Elevation Low',  # 12
        'Elevation High',  # 13
        'Max Grade',  # 14
        'Average Grade'  # 15
    ]]

    # Convert UTC datetime to PST
    ############### Chained Indexing Pandas Warning (Unsure how to resolve) ###############
    # desired_data['Activity Date'] = desired_data['Activity Date'].apply(convert_utc_time_to_pst)  # Original
    # desired_data['Activity Date'] = desired_data.loc[:, 'Activity Date'].apply(convert_utc_time_to_pst) # Second Attempt
    desired_data['Activity Date'].update(desired_data.loc[:, 'Activity Date'].apply(convert_utc_time_to_pst))  # Third Attempt

    # desired_data['Distance'].update(desired_data.loc[:, 'Distance'].apply(kilometer_to_mile))
    #
    # calculated_average_speed = []
    # avg_spd = desired_data.loc[:, ('Moving Time', 'Distance')].apply(average_speed)
    # print(f'Average Speed: {avg_spd}')
    # calculated_average_speed.append(avg_spd)

    return desired_data


def convert_utc_time_to_pst(df):
    activity_start_time = datetime.strptime(df, '%b %d, %Y, %I:%M:%S %p')

    # Get daylight savings info(dst) for activity datetime
    tz = pytz.timezone('UTC')
    new_tz = pytz.timezone('PST8PDT')
    activity_start = tz.localize(activity_start_time)
    activity_start_time_dst_info = int(str(activity_start.astimezone(new_tz).dst())[0])
    pst = 8  # PST offset
    return str(activity_start_time - timedelta(hours=pst - activity_start_time_dst_info))


def df_to_csv(df):
    # save_strava_activity_csv = fd.asksaveasfilename()
    df.to_csv(STRAVA_DATA_DIRECTORY + '/desired_data.csv', header=True)


# Conversion Functions
def kilometer_to_mile(km):
    return round(float(km) * 0.621371, 2)


def meter_to_foot(meter):
    return meter * 3.28084


# Takes seconds as an integer and converts it to a string in hh:mm:ss format
def format_seconds(time_in_sec):
    time_in_sec = int(time_in_sec)
    if time_in_sec >= 3600:
        hour = time_in_sec // 3600
        minutes = (time_in_sec % 3600) // 60
        if minutes % 10 == 0:
            minutes = str(minutes) + '0'
        elif minutes < 10:
            minutes = '0' + str(minutes)
        else:
            minutes = str(minutes)
        seconds = time_in_sec % 60
        if seconds % 10 == 0:
            seconds = str(seconds) + '0'
        elif seconds < 10:
            seconds = '0' + str(seconds)
        else:
            seconds = str(seconds)
        return f'{hour}:{minutes}:{seconds}'
    else:
        minutes = time_in_sec // 60
        # if minutes % 10 == 0:
        #     minutes = str(minutes) + '0'
        # elif minutes < 10:
        if minutes < 10:
            minutes = '0' + str(minutes)
        else:
            minutes = str(minutes)
        seconds = int(time_in_sec % 60)
        if seconds % 10 == 0:
            seconds = str(seconds) + '0'
        elif seconds < 10:
            seconds = '0' + str(seconds)
        else:
            seconds = str(seconds)
        return f'{minutes}:{seconds}'


def kg_to_lbs(weight):
    return weight * 2.20462


def average_speed(moving_time_seconds, distance_miles):
    if moving_time_seconds is not None and distance_miles is not None:
        return round(distance_miles / moving_time_seconds * 3600, 2)


# Use MatPlotLib to plot data
def plot_data(df):
    df.plot()
    plt.show()


# SQL/Database Functions
def connect_to_db(db_name):
    connection = sqlite3.connect(db_name)
    return connection.cursor()


def create_db_table(db_name, db_table_name, data_frame):
    connection = sqlite3.connect(db_name)
    data_frame.to_sql(db_table_name, connection, if_exists='append', index=False)
    print(f'DB Table: {db_table_name} Created Successfully!!')


def query(db_name, query_command):
    try:
        connection = sqlite3.connect(db_name)
        c = connection.cursor()
        result = c.execute(query_command).fetchall()
        connection.close()
    except Exception as e:
        print(e)
        print('Query unsuccessful')
    else:
        print('Query executed successfully!!')
        # print(f'Query Result: {result}')
        return result


def print_commute_specific_results(result):

    # print(result)
    for i in range(len(result)):
        # print(result[i])
        print()
        print(f'Activity Name: {result[i][0]}')
        print(f'Start time: {result[i][1]}')
        print(f'Moving Time: {result[i][2]} | {format_seconds(result[i][2])}')
        print(f'Distance: {kilometer_to_mile(float(result[i][4]))} Miles')
        print(f'Activity Type: {result[i][5]}')

    # plot_data(average_speed(result[i][2], kilometer_to_mile(float(result[i][4]))))


def display_db_data(db_name, query_command):
    connection = sqlite3.connect(db_name)
    c = connection.cursor()
    print(c.execute(query_command).fetchall())


# Create Database and add data
create_db_table(DATABASE_NAME, TABLE_NAME, convert_csv_to_df())
# query(DATABASE_NAME, commute_data)

# print(query(DATABASE_NAME, column_name_query))
# query(DATABASE_NAME, drop_table)
print_commute_specific_results(query(DATABASE_NAME, commute_data))
# print_results(query(DATABASE_NAME, activity_date))

desired_columns = convert_csv_to_df()
df_to_csv(desired_columns)
