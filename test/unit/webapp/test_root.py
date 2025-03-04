from test.unit.webapp import client, driver
from test.unit.webapp import db_session
from app.database import Database
from selenium import webdriver
from selenium.webdriver.common.by import By

def test_age_input_field(driver):
    """Test the age input field properties."""
    age_input = driver.find_element(By.ID, "age")

    # Check input type
    assert age_input.get_attribute("type") == "number"

    # Check min and max attributes
    assert age_input.get_attribute("min") == "0"
    assert age_input.get_attribute("max") == "120"

    # Check step attribute
    assert age_input.get_attribute("step") == "1"

    # Test valid input
    age_input.send_keys("25")
    assert age_input.get_attribute("value") == "25"

    # Test out-of-range input
    age_input.clear()
    age_input.send_keys("150")  # This should be restricted by the browser
    assert int(age_input.get_attribute("value")) <= 120  # Should not allow 150

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

    # Check that the Settings link is present in the HTML
    assert '<a class="nav-link" href="/settings">Settings</a>' in html

    # Check that the landing/home page is displayed successfully
    assert landing.status_code == 200

# def test_activities(client):
#     """
#     This function checks that each activity loads correctly (status_code == 200).
#     :param client: The Pytest test_client defined in webapp/__init__.py.
#     :return: None.
#     """
#     db = Database()
#     df = db.convert_csv_to_df()
#
#     # Loop through all activities and check that they load correctly
#     for activity_id in df['activity_id']:
#
#         activity = client.get(f'/activity/{activity_id}')
#
#         # Check that the activity page is displayed successfully
#         assert activity.status_code == 200

# def test_settings(client):
#
#     settings_page = client.get('/settings')
#     html = settings_page.data.decode()
#
#     # Check that the age input label is present in the HTML
#     assert '<label  class="ms-2 my-2" for="age">Age</label>' in html
#
#     # # Check that the age input is present in the HTML
#     # assert ('<input class="my-2 number_input_three_char"'
#     #         'type="number"'
#     #         'id="age"'
#     #         'name="age"'
#     #         'min="0"'
#     #         'max="120"'
#     #         'step="1"/>') in html
#
#     # Check that the timezone dropdown menu label is present in the HTML
#     assert '<label for="dropdown-menu-timezone"' in html
#     assert '       class="ms-2 mt-2">Local Timezone</label>' in html
#
#     # Check that the timezone dropdown menu is present in the HTML
#     assert '<select name="timezone-options" id="dropdown-menu-timezone" class="form-select ms-2 mb-2" style="width:250px">' in html
#     assert '<option value="{{ current_timezone_selection }}">{{ current_timezone_selection }}</option>' in html
#     assert '{% for timezone in timezone_list %}' in html
#     assert '<option value="{{ timezone }}">{{ timezone }}</option>' in html
#     assert '{% endfor %}' in html
#     assert '</select>' in html
#
#     # Check that the settings page is displayed successfully
#     assert settings_page.status_code == 200
#
