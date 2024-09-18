from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
db = SQLAlchemy(app)

class Activity(db.Model):

    activity_id = db.Column(db.Integer, primary_key=True)
    activity_name = db.Column(db.String(200), nullable=False)
    start_time = db.Column(db.String(200), nullable=False)
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
    activities = None

    if request.method == 'POST':
        selected_activity = request.form.get('dropdown-menu')

        print(f'selected_activity is: {selected_activity}')

        activities = Activity.query.filter_by(activity_type=selected_activity).order_by(Activity.activity_id).all()

        # filtered_activities = Activity.query.

    # Group the activity types and create a list of each activity type to be used to populate the dropdown menu options.
    activity_type_categories = Activity.query.with_entities(Activity.activity_type).group_by(Activity.activity_type).all()
    activity_type_list = [type.activity_type for type in activity_type_categories]

    return render_template(
        'filter_activities.html',
        activities=activities,
        activity_type_list=activity_type_list
    )

if __name__ == '__main__':
    app.run(
        # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
        debug=True,
        host='0.0.0.0',  # Use for local debugging
        port=8000  # Define the port to use when connecting.
    )
