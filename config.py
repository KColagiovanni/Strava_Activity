import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')

    # Variables used in database.py
    USER_TIMEZONE = 'PST8PDT'
    USER_AGE = '1'
    USER_GENDER = 'Female'
    USER_WEIGHT = '1'
    USER_HEIGHT = '1'
    USER_ACTIVITY_LEVEL = 'sedentary'
    DATABASE_NAME = 'instance/strava_data.db'
    ACTIVITY_TABLE_NAME = 'activity'
    WORKOUTS_TABLE_NAME = 'workouts'
    EXERCISES_TABLE_NAME = 'exercises'
    SETS_TABLE_NAME = 'sets'
    STRAVA_ACTIVITIES_CSV_FILE = 'uploads/strava_activities.csv'
    GARMIN_CSV_FILE = 'uploads/garmin_activities.csv'
    GARMIN_ACTIVITIES_JSON_FILE = 'uploads/kevster025_1001_summarizedActivities.json'
    TIMEZONE_OFFSET = 8  # PST offset

    # Variables in routes.py
    TARGET_FILENAME = 'strava_activities.csv'
    DECOMPRESSED_ACTIVITY_FILES_FOLDER = 'decompressed_activity_files'  # Define the directory where decompressed files
    # will be saved.
    ALLOWED_EXTENSIONS = {'gpx', 'fit', 'tcx', 'gz'}
    INDOOR_ACTIVITIES = ['Workout', 'Weight Training', 'Rowing']  # Define indoor activities
    PER_PAGE = 10
    TEXT_SEARCH = ''
    SELECTED_ACTIVITY_TYPE = ''
    SELECTED_ACTIVITY_GEAR = ''
    START_DATE = ''
    END_DATE = ''
    COMMUTE = ''
    MIN_DISTANCE_VALUE = ''
    MAX_DISTANCE_VALUE = ''
    MIN_ELEVATION_GAIN_VALUE = ''
    MAX_ELEVATION_GAIN_VALUE = ''
    MIN_HIGHEST_ELEVATION_VALUE = ''
    MAX_HIGHEST_ELEVATION_VALUE = ''
    MORE_THAN_SECONDS_VALUE = ''
    MORE_THAN_MINUTES_VALUE = ''
    MORE_THAN_HOURS_VALUE = ''
    LESS_THAN_SECONDS_VALUE = ''
    LESS_THAN_MINUTES_VALUE = ''
    LESS_THAN_HOURS_VALUE = ''
    MIN_AVERAGE_SPEED_VALUE = ''
    MAX_AVERAGE_SPEED_VALUE = ''
    MIN_MAX_SPEED_VALUE = ''
    MAX_MAX_SPEED_VALUE = ''

    # Variables in __init__.py
    UPLOAD_FOLDER = 'uploads'  # Define the directory where the activity files will be saved.

    # SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///prod.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///strava_data.db'

# Dictionary to map environment names to configuration classes
config_options = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}