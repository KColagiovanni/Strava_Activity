from test.unit.webapp import client, driver
from test.unit.webapp import db_session
from app.database import Database
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

def test_activities(driver):

    driver.get("http://localhost:5000/activities")

    # ========== Test the filter field properties ==========
    search_activity = driver.find_element(By.ID, 'activity-name-search')

    # +++++ Positive Tests +++++
    # Check search activity field
    assert search_activity.get_attribute('type') == 'text'

    # search_activity.send_keys('test value')
    # assert search_activity.get_attribute('value') == 'test value'

    # Expand the filter section
    driver.find_element(By.ID, 'filter-results').click()

    # Test the activity type dropdown
    select_activity_type = driver.find_element(By.ID, 'dropdown-menu-type')
    select = Select(select_activity_type)
    select.select_by_index(0)
    assert select.first_selected_option.text == 'All'

def test_settings(driver):

    driver.get("http://localhost:5000/settings")

    # ========== Test the age input field properties ==========
    age_input = driver.find_element(By.ID, 'age')

    # +++++ Positive Age Input Tests +++++
    # Check input type
    assert age_input.get_attribute('type') == 'number'

    # Check min and max attributes
    assert age_input.get_attribute('min') == '1'
    assert age_input.get_attribute('max') == '120'

    # Check step attribute
    assert age_input.get_attribute('step') == '1'

    # Test valid input
    age_input.send_keys('25')
    assert age_input.get_attribute('value') == '25'

    # ----- Negative Age Input Tests -----
    # More than the max
    age_input.clear()
    age_input.send_keys('121')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('value')) <= 120  # Should not allow 121

    # Less than the min
    age_input.clear()
    age_input.send_keys('0')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('value')) >= 1  # Should not allow 0

    # Negative value (less than min)
    age_input.clear()
    age_input.send_keys('-25')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('value')) >= 1  # Should not allow -25

    # Invalid step size
    age_input.clear()
    age_input.send_keys('50.5')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('step')) < 1  # Should not allow a step < 1
    
    # Non-numeric
    age_input.clear()
    age_input.send_keys('ten')  # This should be restricted by the browser
    assert not age_input.get_attribute('type') != 'number'  # Should not allow 150

    # ========== Test the timezone dropdown field properties ==========
    timezone_select = driver.find_element(By.ID, 'dropdown-menu-timezone')
    settings_page_submit_button = driver.find_element(By.ID, 'settings-page-submit-button')

    # +++++ Positive Timezone Dropdown Tests ++++
    # Check for correct name attribute
    assert timezone_select.get_attribute('name') == 'timezone-options'

    # Check for correct submit button type
    assert settings_page_submit_button.get_attribute('type') == 'submit'

def test_landing(client):
    """
    This function tests that the landing page has the 'Show Activities' and 'Upload Activities' buttons, and also that
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
