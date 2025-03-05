import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from run import app
from selenium import webdriver

Base = declarative_base()

@pytest.fixture
def driver():
    """Set up and return the WebDriver instance."""
    driver = webdriver.Chrome()
    driver.get("http://localhost:5000/settings")
    yield driver
    driver.quit()

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