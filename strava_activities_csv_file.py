import os

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import sqlite3
from datetime import datetime, timedelta
import pytz
from tkinter import filedialog as fd

DATABASE_NAME = 'strava_data.db'
TABLE_NAME = 'strava_activity'
STRAVA_DATA_DIRECTORY = fd.askdirectory()
YEAR_FILTER = '2023'

# SQL Queries
all_query = f'''SELECT * FROM {TABLE_NAME}'''

column_name_query = f'''PRAGMA table_info({TABLE_NAME})'''

drop_table = f'''DROP TABLE {TABLE_NAME}'''
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
WHERE Commute = 1 AND "Activity Type" IS "Ride" AND "Start Hour" < 10'''

afternoon_commute = f'''SELECT
 "Activity Name",
  "Activity Date",
   "Moving Time",
    "Average Speed",
     "Distance",
      "Activity Type",
       "Start Hour" 
FROM {TABLE_NAME} 
WHERE Commute = 1 AND "Activity Type" IS "Ride" AND "Start Hour" >= 10'''

activity_date = f'''SELECT "Activity Date"
FROM {TABLE_NAME}
 WHERE Commute = 1'''


def convert_csv_to_df():
    # Original Strava Activity CSV Location
    activity_data_frame = pd.read_csv(
        STRAVA_DATA_DIRECTORY + '/activities.csv'
    )
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
    # Chained Indexing Pandas Warning (Unsure how to resolve)
    # Tried the following without getting rid of the warning
    # desired_data['Activity Date'] = desired_data[
    # 'Activity Date'].apply(convert_utc_time_to_pst)
    # desired_data['Activity Date'] = desired_data.loc[
    # :, 'Activity Date'].apply(convert_utc_time_to_pst)
    desired_data['Activity Date'].update(
        desired_data.loc[:, 'Activity Date'].apply(
            convert_utc_time_to_pst
        )
    )

    # Get activity date start hour and year and create a new column
    desired_data['Start Hour'] = desired_data.loc[:, 'Activity Date'].apply(
        get_start_hour
    )
    desired_data['Year'] = desired_data.loc[:, 'Activity Date'].apply(get_year)
    desired_data['Date'] = desired_data.loc[:, 'Activity Date'].apply(get_date)

    # Calculate avg speed and create a new column
    desired_data['Average Speed'] = desired_data.apply(average_speed, axis=1)

    return desired_data


def filter_commute_to_work(df):
    return df.loc[(df['Start Hour'] < 10) &
                  (df['Activity Type'] == 'Ride') &
                  (df['Commute']) &
                  (df['Year'] == YEAR_FILTER)]


def filter_commute_home(df):
    return df.loc[(df['Start Hour'] >= 10) &
                  (df['Activity Type'] == 'Ride') &
                  (df['Commute']) &
                  (df['Year'] == YEAR_FILTER)]


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
    return str(activity_start_time - timedelta(
        hours=pst - activity_start_time_dst_info)
               )


def get_start_hour(start_time):
    return int(start_time[start_time.find(':') - 2:start_time.find(':')])


def get_year(start_time):
    return start_time[:4]


def get_date(start_time):
    return start_time[:11].replace(' ', '')


def df_to_csv(df, save_name):
    try:
        df.to_csv(
            f'{STRAVA_DATA_DIRECTORY}/{save_name}.csv',
            header=True,
            index_label='index'
        )
    except PermissionError:
        print(f'\n!!!!!{save_name} Not Saved!!!!!\nPermission Denied. Make '
              'sure the file isn\'t open.\n')
    else:
        print(f'CSV File Saved: {save_name}')


# Conversion Functions
def kilometer_to_mile(km):
    if type(km) == float:
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


def average_speed(row):
    if row['Distance'] is not None and\
            row['Moving Time'] is not None and\
            row['Activity Type'] == "Ride":
        # print()
        # print(f'Moving Time Type: {type(row["Moving Time"])}')
        # print(f'Moving Time: {row["Moving Time"]}')
        # print(f'Distance Type: {type(row["Distance"])}')
        # print(f'Distance: {row["Distance"]}')
        # print(f'Distance Type: {type(float(row["Distance"]))}')
        distance_km = float(row['Distance'])
        distance_mile = kilometer_to_mile(distance_km)
        # print(f'Activity Type: {row["Activity Type"]}')
        if int(row['Moving Time']) != 0:
            return round(distance_mile / float(row['Moving Time']) * 3600, 2)


# Use MatPlotLib to graph data
def plot_data(x, y, **kwargs):

    # Set the figure size
    fig, ax = plt.subplots(figsize=(10, 6))

    # Define the plot type of ride avg speed
    ax.scatter(x, y)

    # Plot the trend line of ride avg speeds
    try:
        z = np.polyfit(x, y, 1)
        p = np.poly1d(z)
    except TypeError as e:
        print(f'There are no rides to show. {e}')
        return
    else:
        ax.plot(x, p(x), color='green')

    trending_line_slope = (p(x)[-1] - p(x)[0])/(len(y))

    # Plot the overall avg speed of all rides
    ax.axhline(y.mean(), color='lightblue', linewidth=1, linestyle='--')

    # Display text info on the graph
    ax.annotate(f'Showing {len(y)} Activities',
                xy=(0.0, -0.1),
                xycoords='axes fraction',
                ha='left',
                va="center",
                fontsize=10)
    ax.annotate(f'Average Overall Speed: {round(y.mean(), 1)}MPH',
                xy=(0.0, -0.15),
                xycoords='axes fraction',
                ha='left',
                va="center",
                fontsize=10)
    ax.annotate('Average speed is trending '
                f'{"up" if trending_line_slope > 0 else "down"} by'
                f' {round(trending_line_slope * 100, 2)}%',
                xy=(0.0, -0.2),
                xycoords='axes fraction',
                ha='left',
                va="center",
                fontsize=10)
    ax.set_title(kwargs['title'])
    ax.set_xlabel(kwargs['x_label'])
    ax.set_ylabel(kwargs['y_label'])
    ax.legend(
        ['Ride Avg Speed',
         'Trend',
         f'Average Overall']
    )

    # Save the plot
    save_name = kwargs['title'].replace(' ', '_')
    save_name = save_name.replace(',', '')
    save_name = save_name.replace(':', '')
    if not os.path.exists(f'{STRAVA_DATA_DIRECTORY}/Saved_Plots'):
        os.mkdir(f'{STRAVA_DATA_DIRECTORY}/Saved_Plots')
    try:
        plt.savefig(f'{STRAVA_DATA_DIRECTORY}/Saved_Plots/{save_name}.jpg')
    except FileNotFoundError:
        print('That directory doesnt exist')
    else:
        print(f'Plot saved: Saved_Plots/{save_name}')

    fig.tight_layout()

    # Display the graph
    plt.show()


# SQL/Database Functions
def connect_to_db(db_name):
    connection = sqlite3.connect(db_name)
    return connection.cursor()


def create_db_table(db_name, db_table_name, data_frame):
    connection = sqlite3.connect(db_name)
    data_frame.to_sql(
        db_table_name, connection, if_exists='append', index=False
    )
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
        print(f'Start Hour: {result[i][6]}')
        print(f'Moving Time: {result[i][2]} | {format_seconds(result[i][2])}')
        print(f'Distance: {kilometer_to_mile(float(result[i][4]))} Miles')
        print(f'Average Speed: {result[i][3]} MPH')
        print(f'Activity Type: {result[i][5]}')


def display_db_data(db_name, query_command):
    connection = sqlite3.connect(db_name)
    c = connection.cursor()
    print(c.execute(query_command).fetchall())


# Create Database and add data
# create_db_table(DATABASE_NAME, TABLE_NAME, convert_csv_to_df())

# Delete the database
# query(DATABASE_NAME, drop_table)

# Print to the console the results of defined SQL queries
# print(query(DATABASE_NAME, column_name_query))
# print_commute_specific_results(query(DATABASE_NAME, commute_data))
# print_commute_specific_results(query(DATABASE_NAME, morning_commute))
# print_commute_specific_results(query(DATABASE_NAME, afternoon_commute))
# print_results(query(DATABASE_NAME, activity_date))


# Create a Pandas Dataframe with the desired/defined data
desired_columns = convert_csv_to_df()

# Graphing desired data
plot_data(
    np.arange(0, len(filter_commute_to_work(desired_columns)), 1),  # X Values
    filter_commute_to_work(desired_columns)['Average Speed'],  # Y Values
    title='Commute to Work('
          f'{filter_commute_to_work(desired_columns)["Date"].iloc[0]} - '
          f'{filter_commute_to_work(desired_columns)["Date"].iloc[-1]})',
    x_label='Activity Number',
    y_label='Speed(MPH)'
)

# Graphing desired data
plot_data(
    np.arange(1, len(filter_commute_home(desired_columns)) + 1, 1),  # X Values
    filter_commute_home(desired_columns)['Average Speed'],  # Y Values
    title='Commute Home('
          f'{filter_commute_home(desired_columns)["Date"].iloc[0]} - '
          f'{filter_commute_home(desired_columns)["Date"].iloc[-1]})',
    x_label='Activity Number',
    y_label='Speed(MPH)'
)

# Save dataframe data to a csv
df_to_csv(desired_columns, 'desired_data')
df_to_csv(filter_commute_to_work(desired_columns), 'commute_to_work')
df_to_csv(filter_commute_home(desired_columns), 'commute_home')
