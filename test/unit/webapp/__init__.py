import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from run import app
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

Base = declarative_base()

@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()

    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)

    # Normal Selenium operations should not take minutes.
    driver.set_page_load_timeout(60)

    # Long-running JavaScript operations such as /create-db
    # are handled explicitly with execute_async_script().
    driver.set_script_timeout(900)

    yield driver

    driver.quit()

# @pytest.fixture
# def driver():
#     """Set up and return the WebDriver instance for the tests."""
#     chrome_options = Options()
#     chrome_options.add_argument("--headless")  # Run in headless mode (no UI)
#     # service = Service("chromedriver")
#     # driver = webdriver.Chrome(service=service, options=chrome_options)
#     driver = webdriver.Chrome(options=chrome_options)
#     # driver = webdriver.Chrome()
#     yield driver
#     driver.quit()

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