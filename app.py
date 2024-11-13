from flask import Flask, render_template, request, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql.operators import ilike_op
import datetime
from datetime import timedelta
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
import os
from database import Database

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
db = SQLAlchemy(app)

# Set a path to save the uploaded files
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}#, 'fit', 'gz', 'fit.gz', 'jpg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
TARGET_FILENAME = 'activities.csv'

# Ensure the upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class Activity(db.Model):

    activity_id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(200), nullable=False)
    activity_description = db.Column(db.String(1000), nullable=False)
    commute = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    moving_time = db.Column(db.String(200), nullable=False)
    moving_time_seconds = db.Column(db.Integer, nullable=False)
    distance = db.Column(db.Double, default=0)
    average_speed = db.Column(db.Double, default=0)
    max_speed = db.Column(db.Double, default=0)
    elevation_gain = db.Column(db.Double, default=0, nullable=False)
    highest_elevation = db.Column(db.Double, default=0)
    activity_type = db.Column(db.String(40), nullable=False)
    activity_gear = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return '<Activity %r' % self.activity_id

    @property
    def convert_seconds_to_time_format(self):
        return str(timedelta(seconds=self.moving_time))

def convert_time_to_seconds(seconds, minutes, hours):
    if hours == '' or hours is None:
        hours = '00'
    if minutes == '' or minutes is None:
        minutes = '00'
    if seconds == '' or seconds is None:
        seconds = '00'

    print(f'seconds is: {seconds}')
    print(f'minutes is: {minutes}')
    print(f'hours is: {hours}')

    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)

def split_time_string(time):
    """
    Returns the hour, minute, and second of a given time
    :param time:
    :return: hour, minute, second
    """
    if len(time) == 5:
        return_list = ['00']
        time_split = time.split(':')
        return_list.append(time_split[0])
        return_list.append(time_split[1])
        return return_list
    else:
        return time.split(':')

@app.route('/')  #, methods=['POST', 'GET'])
def index():
    """
    Function and route for the home page.

    :return: Renders the index.html page.
    """
    return render_template('index.html')

@app.route('/activities', methods=['POST', 'GET'])
def activity():
    """
    Function and route for the activities page.

    :return: Renders the filter_activities.html page.
    """
    activities = ''
    num_of_activities = 0

    # print(f'request.method is: {request.method}')
    # print(f"activity_name_search is: {request.form.get('activity_search')}")
    # print(f"request.form.get('dropdown-menu') is: {request.form.get('options')}")
    # print(f"request.form.get('start_date') is: {request.form.get('start_date')}")
    # print(f"request.form.get('end_date') is: {request.form.get('end_date')}")
    # print(f"request.form.get('commute') is: {request.form.get('commute')}")
    # print(f"request.form.get('more_than_distance') is: {request.form.get('more_than_distance')}")
    # print(f"request.form.get('less_than_distance') is: {request.form.get('less_than_distance')}")
    # print(f"request.form.get('more_than_elevation_gain') is: {request.form.get('more_than_elevation_gain')}")
    # print(f"request.form.get('less_than_elevation_gain') is: {request.form.get('less_than_elevation_gain')}")
    # print(f"request.form.get('elevation_gain_none') is: {request.form.get('elevation_gain_none')}")
    # print(f"request.form.get('more_than_seconds') is: {request.form.get('more_than_seconds')}")
    # print(f"request.form.get('more_than_minutes') is: {request.form.get('more_than_minutes')}")
    # print(f"request.form.get('more_than_hours') is: {request.form.get('more_than_hours')}")
    # print(f"request.form.get('less_than_seconds') is: {request.form.get('less_than_seconds')}")
    # print(f"request.form.get('less_than_minutes') is: {request.form.get('less_than_minutes')}")
    # print(f"request.form.get('less_than_hours') is: {request.form.get('less_than_hours')}")
    # print(f"request.form.get('more_than_average_speed') is: {request.form.get('more_than_average_speed')}")
    # print(f"request.form.get('less_than_average_speed') is: {request.form.get('less_than_average_speed')}")
    # print(f"request.form.get('more_than_max_speed') is: {request.form.get('more_than_max_speed')}")
    # print(f"request.form.get('less_than_max_speed') is: {request.form.get('less_than_max_speed')}")

    # When the filter form is submitted
    if request.method == 'POST':
        text_search = request.form.get('activity_search') or ''
        selected_activity_type = request.form.get('type-options')
        selected_activity_gear = request.form.get('gear-options')
        start_date = request.form.get('start_date')
        end_date = request.form.get('end_date') or datetime.datetime.now()
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
    activity_type_list = [type.activity_type for type in activity_type_categories]

    # Group the activity gear and create a list of each activity gear to be used to populate the dropdown menu options.
    activity_gear_categories = (Activity.query.with_entities(Activity.activity_gear).
                                group_by(Activity.activity_gear).all())
    activity_gear_list = [gear.activity_gear for gear in activity_gear_categories]

    # Create a DataFrame using the desired data, create a simple Plotly line chart, then convert the figure to an HTML
    # div for activity Date vs Moving Time.
    moving_time_data = {
        'Activity Moving Time': [activity.moving_time_seconds for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Distance': [activity.distance for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Average Speed': [activity.average_speed for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Max Speed': [activity.max_speed for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'Activity Elevation Gain': [activity.elevation_gain for activity in activities],
        'Activity Date': [activity.start_time for activity in activities]
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
        'filter_activities.html',
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

@app.route('/activity/<activity_id>', methods=['GET'])
def activity_info(activity_id):
    # print(Activity.query.get(activity_id).activity_name)
    activity_data = Activity.query.get(activity_id)
    return render_template('activity_info.html', activity_data=activity_data)

@app.route('/graph', methods=['POST'])
def plot_data():
    text_search = request.form.get('activity_search') or ''
    selected_activity_type = request.form.get('type-options')
    selected_activity_gear = request.form.get('gear-options')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date') or datetime.datetime.now()
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

    df = pd.DataFrame([{
        'start_time': activity.start_time,
        'moving_time': activity.moving_time,
        'distance': activity.distance,
        'average_speed': activity.average_speed,
        'max_speed': activity.max_speed,
        'elevation_gain': activity.elevation_gain
    } for activity in activities])

    data = [
        go.Line(
            x=df['start_time'],
            y=df['moving_time'],
            mode='lines+markers',
            name='Moving Time'
        )
    ]

    layout = go.Layout(
        title='Moving Time vs Activity Date',
        xaxis=dict(title='Activity Date'),
        yaxis=dict(title='Moving Time')
    )

    print(jsonify(graph_data=[trace.to_plotly_json() for trace in data], layout=layout.to_plotly_json()))

    return jsonify(graph_data=[trace.to_plotly_json() for trace in data], layout=layout.to_plotly_json())

@app.route('/upload', methods=['POST'])
def upload_activity():
    print('In upload_activity()')
    return render_template('upload_activities.html')

# # Route to list files in the selected directory
# @app.route('/list_files', methods=['POST'])
# def list_files():
#     directory = request.json.get('directory')
#     dir_path = os.path.join(BASE_DIR, directory)
#
#     if os.path.isdir(dir_path):
#         files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
#         return jsonify(files=files)
#     return jsonify(error="Directory not found"), 400
#
# # Route to process the selected file
# @app.route('/process_file', methods=['POST'])
# def process_file():
#     directory = request.json.get('directory')
#     file_name = request.json.get('file')
#     if file_name == 'activities.csv':
#         file_path = os.path.join(BASE_DIR, directory, file_name)
#
#         if os.path.isfile(file_path):
#             # Example file processing
#             with open(file_path, 'r') as file:
#                 content = file.read()
#             return jsonify(content=content)  # Just returning file content as an example
#         return jsonify(error="File not found"), 400
#
# def allowed_file(filename):
#     return '.' in filename and \
#            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to handle the file upload
@app.route('/upload-file', methods=['POST'])
def upload_file():

    uploaded_files = request.files.getlist('files')

    for file in uploaded_files:
        if os.path.basename(file.filename) == TARGET_FILENAME:
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename.split('/')[1])
            file.save(save_path)
            convert_activity_csv_to_db()
            return jsonify({
                "message": f"File '{TARGET_FILENAME}' has been found!",
                "file_name": file.filename
            })

    return jsonify({
        "message": f"File '{TARGET_FILENAME}' not found in the selected directory."
    })

def convert_activity_csv_to_db():

    db = Database()
    db.drop_table(db.DATABASE_NAME)
    db.create_db_table(db.DATABASE_NAME, db.TABLE_NAME, db.convert_csv_to_df())

if __name__ == '__main__':
    app.run(
        # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
        debug=True,
        host='0.0.0.0',  # Use for local debugging
        port=5000  # Define the port to use when connecting.
    )
