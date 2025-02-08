import os

class Config:
    # SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret')
    USER_TIMEZONE = 'PST8PDT'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///site.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///prod.db')

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'

# Dictionary to map environment names to configuration classes
config_options = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}