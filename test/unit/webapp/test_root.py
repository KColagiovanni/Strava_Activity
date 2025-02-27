from test.unit.webapp import client
from test.unit.webapp import db_session
from app.database import Database


def test_landing(client):
    """
    This function tests that the landing page has the "Show Activities" and "Upload Activities" buttons, and also that
    it loads correctly (status_code == 200).
    :param client: The Pytest test_client defined in webapp/__init__.py.
    :return: None.
    """
    landing = client.get('/')
    html = landing.data.decode()

    # Check that the Show Activities link is present in the HTML
    assert '<a class="nav-link" href="/activities">Show Activities</a>' in html

    # Check that the Upload Activities link is present in the HTML
    assert '<a class="nav-link" href="/upload">Upload Activities</a>' in html

    # Check that the landing/home page is displayed successfully
    assert landing.status_code == 200

def test_activities(client):
    """
    This function tests if each activity loads correctly (status_code == 200).
    :param client: The Pytest test_client defined in webapp/__init__.py.
    :return: None.
    """
    db = Database()
    df = db.convert_csv_to_df()

    # Loop through all activities and check that they load correctly
    for activity_id in df['activity_id']:

        activity = client.get(f'/activity/{activity_id}')

        # Check that the activity page is displayed successfully
        assert activity.status_code == 200
