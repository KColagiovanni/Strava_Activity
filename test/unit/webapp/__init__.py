import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from run import app
from selenium import webdriver

Base = declarative_base()

@pytest.fixture
def activities():
    """Set up and return the WebDriver instance for the settings page."""
    activities = webdriver.Chrome()
    activities.get("http://localhost:5000/activities")
    yield activities
    activities.quit()

@pytest.fixture
def setting():
    """Set up and return the WebDriver instance for the settings page."""
    setting = webdriver.Chrome()
    setting.get("http://localhost:5000/settings")
    yield setting
    setting.quit()

@pytest.fixture
def client():
    client = app.test_client()

    yield client

@pytest.fixture(scope='session')
def db_session():
    engine = create_engine('sqlite:///strava_data.db')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()