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
    activity_type = db.Column(db.String(40), nullable=False)

    def __repr__(self):
        return '<Activity %r' % self.activity_id

@app.route('/', methods=['POST', 'GET'])
def index():
    '''
    Function and route for the home page.

    Parameters: None

    Returns: Renders the index.html page.
    '''

    return render_template('index.html')

@app.route('/activity')  #, methods=['POST', 'GET'])
def activity():
    '''
    Function and route for the filter activities page.

    Parameters: None

    Returns: Renders the filter_activities.html page.
    '''
    # if request.method == 'POST':
    #     activity_content = request.form['content']
    #     new_activity = Activity(content=activity_content)
    #
    #     try:
    #         db.session.add(new_activity)
    #         db.session.commit()
    #         return redirect('/activity')
    #     except:
    #         return "There was an showing the activity"
    # else:
    activities = Activity.query.order_by(Activity.activity_id).all()
    return render_template('filter_activities.html', activities=activities)

if __name__ == '__main__':
    app.run(
        # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
        debug=True,
        host='0.0.0.0',  # Use for local debugging
        port=8000  # Define the port to use when connecting.
    )
