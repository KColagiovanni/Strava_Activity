from datetime import timedelta
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Activity(db.Model):
    """ This class defines the database model. """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    strava_activity_id = db.Column(db.BigInteger, nullable=True)
    garmin_activity_id = db.Column(db.BigInteger, nullable=True)
    activity_name = db.Column(db.String(200))
    activity_description = db.Column(db.String(1000))
    # commute = db.Column(db.String(10), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    activity_duration = db.Column(db.String(200), nullable=False)
    moving_time_seconds = db.Column(db.Integer)
    distance = db.Column(db.Double, default=0)
    average_speed = db.Column(db.Double, default=0)
    max_speed = db.Column(db.Double, default=0)
    elevation_gain = db.Column(db.Double, default=0)
    highest_elevation = db.Column(db.Double, default=0)
    activity_type = db.Column(db.String(40), nullable=False)
    activity_gear = db.Column(db.String(50))
    strava_filename = db.Column(db.String(100))


    def __repr__(self):
        """
        Returns a string representation of the instance that can be used to recreate the object.
        :return: (str) the activity id.
        """
        return '<Activity %r' % self.strava_activity_id


    @property
    def convert_seconds_to_time_format(self):
        """
        Convert seconds as an integer (activity_duration) to elapsed time in HH:MM:SS format using the datatime.timedelta
        object.
        :return: (str) elapsed time in HH:MM:SS format.
        """
        return str(timedelta(seconds=self.activity_duration))


