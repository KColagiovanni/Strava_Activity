import os

class Config:
    # SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')

    # Variables used in database.py
    USER_TIMEZONE = 'PST8PDT'
    DATABASE_NAME = 'instance/strava_data.db'
    TABLE_NAME = 'activity'
    ACTIVITIES_CSV_FILE = 'uploads/activities.csv'
    TIMEZONE_OFFSET = 8  # PST offset

    # Variables in routes.py

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