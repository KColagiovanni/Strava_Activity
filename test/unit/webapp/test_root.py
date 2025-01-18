from test.unit.webapp import client

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
    activity = client.get('/activity/13027315375')

    # Check that the activity page is displayed successfully
    assert activity.status_code == 200
