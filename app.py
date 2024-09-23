from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from fontTools.misc.plistlib import end_date
from sqlalchemy.sql.operators import ilike_op
import datetime

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
db = SQLAlchemy(app)

class Activity(db.Model):

    activity_id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(200), nullable=False)
    # start_time = db.Column(db.String(200), nullable=False)
    commute = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    moving_time = db.Column(db.String(200), nullable=False)
    distance = db.Column(db.Double, default=0)
    average_speed = db.Column(db.Double, default=0)
    max_speed = db.Column(db.Double, default=0)
    elevation_gain = db.Column(db.Double, default=0)
    highest_elevation = db.Column(db.Double, default=0)
    activity_type = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return '<Activity %r' % self.activity_id

@app.route('/')  #, methods=['POST', 'GET'])
def index():
    """
    Function and route for the home page.

    :return: Renders the index.html page.
    """
    return render_template('index.html')

@app.route('/activity', methods=['POST', 'GET'])
def activity():
    """
    Function and route for the filter activities page.

    :return: Renders the filter_activities.html page.
    """
    # Order the SQL database by activity id
    # activities = Activity.query.order_by(Activity.activity_id).all()
    selected_activity = None
    activities = ''
    filters = None
    num_of_activities_string = 'Showing 0 Activities'
    start_date = None
    end_date = None

    print(f'request.method is: {request.method}')
    print(f"activity_name_search is: {request.form.get('activity_search')}")
    print(f"request.form.get('dropdown-menu') is: {request.form.get('options')}")
    print(f"request.form.get('start_date') is: {request.form.get('start_date')}")
    print(f"request.form.get('end_date') is: {request.form.get('end_date')}")
    print(f"request.form.get('commute') is: {request.form.get('commute')}")

    # When the form is submitted
    if request.method == 'POST':
        text_search = request.form.get('activity_search') or ''
        selected_activity_type = request.form.get('options')
        start_date = request.form.get('start_date') or Activity.query.order_by(Activity.start_time).first().start_time
        end_date = request.form.get('end_date') or datetime.datetime.now()
        commute = request.form.get('commute') or None

        print(f'Activity.start_time.first() is: {Activity.query.order_by(Activity.start_time).first().start_time}')
        print(f'type(start_date) is: {type(start_date)}')
        print(f'type(end_date) is: {type(end_date)}')

        filters = {}
        if selected_activity_type != 'All':
            filters['activity_type'] = selected_activity_type
        if commute == 'commute':
            filters['commute'] = 1

        # if start_date:
        #     filters['start_time'] = start_date
        #
        # if end_date:
        #     filters['start_time'] = end_date

        # print(f'filters is: {filters}')

        query_string = (
            Activity
            .query
            .filter_by(**filters)
            .filter(ilike_op(Activity.activity_name, f'%{text_search}%'))
            .filter(start_date <= Activity.start_time)
            .filter(end_date >= Activity.start_time)
            .order_by(Activity.start_time  # Order activities by date
            .desc())  # Show newest activities first
        )
        # query_string = Activity.query.filter(ilike_op(Activity.activity_name, f'%{text_search}%')).order_by(Activity.start_time.desc())
        # query_string = Activity.query.filter_by(**filters).order_by(Activity.start_time.desc())

        # activities = Activity.query.filter_by(**filters).filter(Activity.activity_name.ilike(f'{text_search}')).order_by(Activity.start_time.desc()).all()
        activities = query_string.all()
        num_of_activities = query_string.count()

        if num_of_activities == 1:
            num_of_activities_string = f'Showing {num_of_activities} Activity'
        else:
            num_of_activities_string = f'Showing {num_of_activities} Activities'

    # When the page loads
    if request.method == 'GET':

        query_string = Activity.query.order_by(Activity.start_time.desc())
        # query_string = Activity.query.filter(ilike_op(Activity.activity_name, f'%{text_search}%')).order_by(Activity.start_time.desc())
        # query_string = Activity.query.filter_by(**filters).order_by(Activity.start_time.desc())

        # activities = Activity.query.filter_by(**filters).filter(Activity.activity_name.ilike(f'{text_search}')).order_by(Activity.start_time.desc()).all()
        activities = query_string.all()
        num_of_activities = query_string.count()

        if num_of_activities == 1:
            num_of_activities_string = f'Showing {num_of_activities} Activity'
        else:
            num_of_activities_string = f'Showing {num_of_activities} Activities'


    # Group the activity types and create a list of each activity type to be used to populate the dropdown menu options.
    activity_type_categories = Activity.query.with_entities(Activity.activity_type).group_by(Activity.activity_type).all()
    activity_type_list = [type.activity_type for type in activity_type_categories]

    return render_template(
        'filter_activities.html',
        activities=activities,
        activity_type_list=activity_type_list,
        num_of_activities=num_of_activities_string
    )

if __name__ == '__main__':
    app.run(
        # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
        debug=True,
        host='0.0.0.0',  # Use for local debugging
        port=5000  # Define the port to use when connecting.
    )
