from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import pandas as pd
import plotly.express as px
from config import config_options
from database import Database
import fitdecode
import gzip
import os
import gpxpy
import xmltodict
from config import Config

db = SQLAlchemy()

def create_app():

    # Flask stuff
    app = Flask(__name__)

    # Configure and initialize the database
    # app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///strava_data.db'
    app.config.from_object(config_options['testing'])

    db.init_app(app)

    with app.app_context():
        from .routes import main  # import main from the routes file
        app.register_blueprint(main)  # register main in app

    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)  # Ensure the upload activities directory exists in the same directory of
    # this program and if not, create it.
    app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER  # Define the directory where flask will save the uploaded files.
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # Define the directory size in bytes.

    return app


# if __name__ == '__main__':
#     app.run(
#         # Enabling debug mode will show an interactive traceback and console in the browser when there is an error.
#         debug=True,
#         host='0.0.0.0',  # Use for local debugging
#         port=5000  # Define the port to use when connecting.
#     )
