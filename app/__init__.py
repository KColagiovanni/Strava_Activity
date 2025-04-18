from flask import Flask
from config import config_options
from app.database import Database
import os
from config import Config
from app.models import db

def create_app():

    # Flask stuff
    app = Flask(__name__)

    # Configure and initialize the database
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
    app.config.from_object(config_options['testing'])
    app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # Set the max file/directory size.

    db.init_app(app)

    with app.app_context():
        from .routes import main  # import main from the routes file
        app.register_blueprint(main)  # register main in app

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload activities directory exists in the same directory of
    # this program and if not, create it.
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER  # Define the directory where flask will save the uploaded files.
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Define the directory size in bytes.

    return app
