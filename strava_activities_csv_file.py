from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import numpy as np
import os
import pandas as pd
import pytz
import sqlite3
from tkinter import filedialog as fd

DATABASE_NAME = 'strava_data.db'
TABLE_NAME = 'strava_activity'
STRAVA_DATA_DIRECTORY = fd.askdirectory()
YEAR_FILTER1 = '2020'
YEAR_FILTER2 = '2021'
CSV_FILE = '/activities.csv'

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
WHERE (Commute = 1 OR
       Activity Name LIKE "%Commute%" OR
        Activity Name LIKE "%Morning%") AND
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
       Activity Name LIKE "%Commute%" OR
        Activity Name LIKE "%Afternoon%") AND
 "Activity Type" IS "Ride" AND "Start Hour" >= 10'''

activity_date = f'''SELECT "Activity Date"
FROM {TABLE_NAME}
 WHERE Commute = 1'''


def convert_csv_to_df():
    # Original Strava Activity CSV Location
    try:
        activity_data_frame = pd.read_csv(
            STRAVA_DATA_DIRECTORY + CSV_FILE
        )
    except FileNotFoundError:
        print(f'No file named {CSV_FILE[1:]} was found')
    else:
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
            'Average Grade',  # 15
            'Average Cadence',  # 16
            'Average Heart Rate',  # 17
            'Average Watts',  # 18
            'Calories'  # 19
        ]]

        # Convert UTC datetime to PST in Desired Data DF
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
        desired_data['Start Hour'] =\
            desired_data.loc[:, 'Activity Date'].apply(
            get_start_hour
        )
        desired_data['Year'] =\
            desired_data.loc[:, 'Activity Date'].apply(get_year)
        desired_data['Date'] =\
            desired_data.loc[:, 'Activity Date'].apply(get_date)

        # Calculate avg speed and create a new column
        desired_data['Average Speed'] =\
            desired_data.apply(average_speed, axis=1)

        desired_data['Average Cadence'].fillna(0, inplace=True)
        desired_data['Average Heart Rate'].fillna(0, inplace=True)
        desired_data['Average Watts'].fillna(0, inplace=True)
        desired_data['Calories'].fillna(0, inplace=True)

        return desired_data


def filter_commute_to_work(df):
    # print(f'Activity Year: {df["Year"]}')
    # match = re.search(r'\s', df['Activity Name'])
    # print(f'Match is: {match}')
    # print(f'Morning in Activity Name: {match}')
    # print(df[df['Activity Name'].str.contains('Commute')])
    # print('Commute To Work:')
    # print(df.loc[(df['Start Hour'] < 10) &
    #              (df['Activity Type'] == 'Ride') &
    #              (
    #                      (df['Commute']) |
    #                      (df['Activity Name'].str.contains('Commute')) |
    #                      (df['Activity Name'].str.contains('Morning'))) &
    #              (
    #                      (df['Year'] == YEAR_FILTER1) |
    #                      (df['Year'] == YEAR_FILTER2))])
    #
    return df.loc[(df['Start Hour'] < 10) &
                  (df['Activity Type'] == 'Ride') &
                  (
                          (df['Commute']) |
                          (df['Activity Name'].str.contains('Commute')) |
                          (df['Activity Name'].str.contains('Morning'))) &
                  (
                          (df['Year'] == YEAR_FILTER1) |
                          (df['Year'] == YEAR_FILTER2))]


def filter_commute_home(df):
    # print('Commute Home:')
    # print(df.loc[(df['Start Hour'] >= 10) &
    #               (df['Activity Type'] == 'Ride') &
    #               (
    #                      (df['Commute']) |
    #                      (df['Activity Name'].str.contains('Commute')) |
    #                      (df['Activity Name'].str.contains('Afternoon'))) &
    #               (
    #                      (df['Year'] == YEAR_FILTER1) |
    #                      (df['Year'] == YEAR_FILTER2))])
    #
    return df.loc[(df['Start Hour'] >= 10) &
                  (df['Activity Type'] == 'Ride') &
                  (
                          (df['Commute']) |
                          (df['Activity Name'].str.contains('Commute')) |
                          (df['Activity Name'].str.contains('Afternoon'))) &
                  (
                          (df['Year'] == YEAR_FILTER1) |
                          (df['Year'] == YEAR_FILTER2))]


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
        distance_km = float(row['Distance'])
        distance_mile = kilometer_to_mile(distance_km)
        if int(row['Moving Time']) != 0:
            return round(distance_mile / float(row['Moving Time']) * 3600, 2)


# Use MatPlotLib to graph data
def plot_data(x, data_fields, num_col=1, **kwargs):

    # title = kwargs['title']
    # x_label = kwargs['x_label']
    # y_label = kwargs['y_label']

    plot_index = 1

    # Set the figure size
    # fig, ax = plt.subplots(
    #     1,
    #     sharex='all',
    #     figsize=(10, 6))

    fig = plt.figure(figsize=(10, num_col * 2))

    for i in range(num_col):
        ax = fig.add_subplot(num_col, 1, plot_index + i)
        ax.scatter(x, data_fields[i])

        # Plot the trend lines
        try:
            z1 = np.polyfit(x, data_fields[i], 1)
            p1 = np.poly1d(z1)
            z2 = np.polyfit(x, data_fields[i], 2)
            p2 = np.poly1d(z2)
            z3 = np.polyfit(x, data_fields[i], 5)
            p3 = np.poly1d(z3)
        except TypeError as e:
            print(f'There are no activities to show. {e}')
            return
        else:
            ax.plot(x, p1(x), color='cyan')
            ax.plot(x, p2(x), color='magenta')
            ax.plot(x, p3(x), color='orange')

        trending_line_slope = (p1(x)[-1] - p1(x)[0])/(len(data_fields[i]))

        # # Plot the average of all data points
        ax.axhline(
            data_fields[i].mean(),
            color='lightblue',
            linewidth=1,
            linestyle='--'
        )

    # ax.set_title(title)
    # ax.set_xlabel(x_label)
    # ax.set_ylabel(y_label)
    # ax.legend(
    #     ['Ride Avg Speed',
    #      'Trend',
    #      f'Average Overall']
    # )
    #
    # Display text info on the graph
    # ax.annotate(f'Showing {len(avg_speed)} Activities',
    #              xy=(0.0, -0.1),
    #              xycoords='axes fraction',
    #              ha='left',
    #              va="center",
    #              fontsize=10)
    # ax.annotate(f'Average Overall Speed: {round(avg_speed.mean(), 1)}MPH',
    #              xy=(0.0, -0.15),
    #              xycoords='axes fraction',
    #              ha='left',
    #              va="center",
    #              fontsize=10)
    # ax.annotate('Average speed is trending '
    #              f'{"up" if trending_line_slope > 0 else "down"} by'
    #              f' {round(trending_line_slope * 100, 2)}%',
    #              xy=(0.0, -0.2),
    #              xycoords='axes fraction',
    #              ha='left',
    #              va="center",
    #              fontsize=10)

    # Save the plot
    # save_name = kwargs['title'].replace(' ', '_')
    # save_name = save_name.replace(',', '')
    # save_name = save_name.replace(':', '')
    # if not os.path.exists(f'{STRAVA_DATA_DIRECTORY}/Saved_Plots'):
    #     os.mkdir(f'{STRAVA_DATA_DIRECTORY}/Saved_Plots')
    # try:
    #     plt.savefig(f'{STRAVA_DATA_DIRECTORY}/Saved_Plots/{save_name}.jpg')
    # except FileNotFoundError:
    #     print('That directory doesnt exist')
    # else:
    #     print(f'Plot saved: Saved_Plots/{save_name}')


    fig.tight_layout()

    # Display the graph
    plt.show()


def determine_number_of_subplots(**kwargs):

    num_of_subplots = 0
    data_fields_to_plot = []

    # Average Speed
    avg_spd = kwargs['avg_speed']
    avg_spd_masked_zero_values = np.ma.masked_where(avg_spd == 0, avg_spd)

    # print(f'Masked Avg Spd count: {np.ma.count_masked(avg_spd_masked_zero_values)}')
    # print(f'Number of Avg Spd elements: {len(avg_spd)}')

    if len(avg_spd) != np.ma.count_masked(avg_spd_masked_zero_values):
        print(f'{round(np.ma.count_masked(avg_spd_masked_zero_values) / len(avg_spd) * 100, 1)}% of Avg Spd data points are masked')
        num_of_subplots += 1
        data_fields_to_plot.append(avg_spd)
    else:
        print('All Avg Spd data points are masked')

    # Average Heart Rate
    hr = kwargs['hr']
    hr_masked_zero_values = np.ma.masked_where(hr == 0, hr)

    # print(f'\nMasked HR count: {np.ma.count_masked(hr_masked_zero_values)}')
    # print(f'Number of HR elements: {len(hr)}')

    if len(hr) != np.ma.count_masked(hr_masked_zero_values):
        print(f'{round(np.ma.count_masked(hr_masked_zero_values) / len(hr) * 100, 1)}% of HR data points are masked')
        num_of_subplots += 1
        data_fields_to_plot.append(hr)
    else:
        print('All HR data points are masked')

    # Watts/Power
    avg_pwr = kwargs['watts']
    avg_pwr_masked_zero_values = np.ma.masked_where(avg_pwr == 0, avg_pwr)

    # print(f'\nMasked Avg Pwr count: {np.ma.count_masked(avg_pwr_masked_zero_values)}')
    # print(f'Number of Avg Pwr elements: {len(avg_pwr)}')

    if len(avg_pwr) != np.ma.count_masked(avg_pwr_masked_zero_values):
        print(f'{round(np.ma.count_masked(avg_pwr_masked_zero_values) / len(avg_pwr) * 100, 1)}% of Avg Pwr data points are masked')
        num_of_subplots += 1
        data_fields_to_plot.append(avg_pwr)
    else:
        print('All Avg Pwr data points are masked')

    # Cadence
    cad = kwargs['cadence']
    cad_masked_zero_values = np.ma.masked_where(cad == 0, cad)

    # print(f'\nMasked Cad count: {np.ma.count_masked(cad_masked_zero_values)}')
    # print(f'Number of Cad elements: {len(cad)}')

    if len(cad) != np.ma.count_masked(cad_masked_zero_values):
        print(f'{round(np.ma.count_masked(cad_masked_zero_values) / len(cad) * 100, 1)}% of Cad data points are masked')
        num_of_subplots += 1
        data_fields_to_plot.append(cad)
    else:
        print('All Cad data points are masked')

    # Calories
    cal = kwargs['calories']
    cal_masked_zero_values = np.ma.masked_where(cal == 0, cal)

    # print(f'\nMasked Cal count: {np.ma.count_masked(cal_masked_zero_values)}')
    # print(f'Number of Cal elements: {len(cal)}')

    if len(cal) != np.ma.count_masked(cal_masked_zero_values):
        print(f'{round(np.ma.count_masked(cal_masked_zero_values) / len(cal) * 100, 1)}% of Cal data points are masked\n')
        num_of_subplots += 1
        data_fields_to_plot.append(cal)
    else:
        print('All Cal data points are masked')

    # print(f'data_fields_to_plot(line 492): {data_fields_to_plot}')

    return num_of_subplots, data_fields_to_plot


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


def print_commute_specific_query_results(result):

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

number_of_to_work_subplots = determine_number_of_subplots(
    watts=filter_commute_to_work(desired_columns)['Average Watts'],
    avg_speed=filter_commute_to_work(desired_columns)['Average Speed'],
    hr=filter_commute_to_work(desired_columns)['Average Heart Rate'],
    cadence=filter_commute_to_work(desired_columns)['Average Cadence'],
    calories=filter_commute_to_work(desired_columns)['Calories']
)

# print(f'Number of to work subplots: {number_of_to_work_subplots[0]}')
# print(f'To Work data fields to plot: {number_of_to_work_subplots[1]}')

number_of_home_subplots = determine_number_of_subplots(
    watts=filter_commute_home(desired_columns)['Average Watts'],
    avg_speed=filter_commute_home(desired_columns)['Average Speed'],
    hr=filter_commute_home(desired_columns)['Average Heart Rate'],
    cadence=filter_commute_home(desired_columns)['Average Cadence'],
    calories=filter_commute_home(desired_columns)['Calories']
)

# print(f'Number of home subplots: {number_of_home_subplots[0]}')
# print(f'Home data fields to plot: {number_of_home_subplots[1]}')

# Graphing desired data
plot_data(
    np.arange(0, len(filter_commute_to_work(desired_columns)), 1),  # X
    number_of_to_work_subplots[1],
    number_of_to_work_subplots[0],
    # avg_speed=filter_commute_to_work(desired_columns)['Average Speed'],
    # hr=filter_commute_to_work(desired_columns)['Average Heart Rate'],
    # title='Commute to Work('
    #       f'{filter_commute_to_work(desired_columns)["Date"].iloc[0]} - '
    #       f'{filter_commute_to_work(desired_columns)["Date"].iloc[-1]})',
    # x_label='Activity Number',
    # y_label='Speed(MPH)'
)

# Graphing desired data
plot_data(
    np.arange(1, len(filter_commute_home(desired_columns)) + 1, 1),  # X
    number_of_home_subplots[1],
    number_of_home_subplots[0],
    # avg_speed=filter_commute_home(desired_columns)['Average Speed'],
    # hr=filter_commute_home(desired_columns)['Average Heart Rate'],
    # title='Commute Home('
    #       f'{filter_commute_home(desired_columns)["Date"].iloc[0]} - '
    #       f'{filter_commute_home(desired_columns)["Date"].iloc[-1]})',
    # x_label='Activity Number',
    # y_label='Speed(MPH)'
)

# Save dataframe data to a csv
df_to_csv(desired_columns, 'desired_data')
df_to_csv(filter_commute_to_work(desired_columns), 'commute_to_work')
df_to_csv(filter_commute_home(desired_columns), 'commute_home')
