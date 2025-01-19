import pytest
from app import db, app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

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