from test.unit.webapp import client
from test.unit.webapp import db_session
from app import Database


def test_landing(client):
    landing = client.get('/')
    html = landing.data.decode()

    # Check that the Show Activities page is present in the HTML
    assert '<a class="nav-link" href="/activities">Show Activities</a>' in html

    # Check that the Upload Activities page is present in the HTML
    assert '<a class="nav-link" href="/upload">Upload Activities</a>' in html

    # Check that the landing/home page is displayed successfully
    assert landing.status_code == 200

def test_activities(client):

    db = Database()
    df = db.convert_csv_to_df()
    count = 0

    for id in df['activity_id']:
        count += 1
        print(f'[{count}]activity_id(test) is: {id}')

        activity = client.get(f'/activity/{id}')

        # Check that the activity page is displayed successfully
        assert activity.status_code == 200
