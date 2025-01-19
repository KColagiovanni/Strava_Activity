from test.unit.webapp import client

from app import Activity

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

    # id = db.session.get(Activity, activity_id)
    id = Activity.activity_id

    print(f'activity_id(test) is: {id}')

    activity = client.get(f'/activity/{id}')

    # Check that the activity page is displayed successfully
    assert activity.status_code == 200
