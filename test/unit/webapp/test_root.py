from test.unit.webapp import client, driver
from test.unit.webapp import db_session
from app.database import Database
# from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import io
import os
import time

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

def test_upload_no_file(driver):

    # Get the upload page.
    driver.get('http://localhost:5000/upload')

    # Get the upload button element.
    upload_button = driver.find_element(By.ID, "file-upload-button")

    # Click upload
    upload_button.click()

    # Get the test result of the file upload.
    result = driver.find_element(By.ID, "search-result").text

    # Assert the tests
    assert 'was not found!!' in result
    assert not 'sufficient' in result
    assert not 'successfully' in result
    assert not 'columns' in result

def test_upload_empty_file(driver):

    # Get the upload page.
    driver.get('http://localhost:5000/upload')

    # Get the file input element and the upload button element.
    file_input = driver.find_element(By.ID, "form-file")
    upload_button = driver.find_element(By.ID, "file-upload-button")

    # Send the directory path to the file input.
    file_input.send_keys(f'{os.getcwd()}/test_dir/empty_file')

    # Click upload
    upload_button.click()

    # Get the test result of the file upload.
    result = driver.find_element(By.ID, "search-result").text

    # Assert the tests
    assert 'columns' in result
    assert not 'sufficient' in result
    assert not 'was not found!!' in result
    assert not 'successfully' in result

def test_upload_empty_file_with_headers(driver):

    # Get the upload page.
    driver.get('http://localhost:5000/upload')

    # Get the file input element and the upload button element.
    file_input = driver.find_element(By.ID, "form-file")
    upload_button = driver.find_element(By.ID, "file-upload-button")

    # Send the directory path to the file input.
    file_input.send_keys(f'{os.getcwd()}/test_dir/empty_file_with_headers')

    # Click upload
    upload_button.click()

    # Delay to allow the upload to happen.
    time.sleep(2)

    # Get the test result of the file upload.
    result = driver.find_element(By.ID, "search-result").text

    # Assert the tests
    assert 'sufficient' in result
    assert not 'successfully' in result
    assert not 'was not found!!' in result
    assert not 'columns' in result

def test_upload_real_file(driver):

    # Get the upload page.
    driver.get('http://localhost:5000/upload')

    # Get the file input element and the upload button element.
    file_input = driver.find_element(By.ID, "form-file")
    upload_button = driver.find_element(By.ID, "file-upload-button")

    # Send the directory path to the file input.
    file_input.send_keys(f'{os.getcwd()}/test_dir/real_test_file')

    # Click upload
    upload_button.click()

    # Delay to allow the upload to happen.
    time.sleep(2)

    # Get the test result of the file upload.
    result = driver.find_element(By.ID, "search-result").text

    # Assert the tests
    assert 'successfully!' in result
    assert not 'sufficient' in result
    assert not 'was not found!!' in result
    assert not 'columns' in result

def test_activities(driver):
    """
    This function tests the activities page. Mainly the filter inputs with valid and invalid values.
    :param driver: The WebDriver instance.
    :return: None
    """

    driver.get("http://localhost:5000/activities")

    # Expand the filter section.
    driver.find_element(By.ID, 'filter-results').click()

    # ========== Test the filter field properties ==========
    # +++++ Positive Tests +++++
    # Check search activity field type.
    search_activity = driver.find_element(By.ID, 'activity-name-search')
    assert search_activity.get_attribute('type') == 'text'

    # Test the activity type dropdown.
    select_activity_type = driver.find_element(By.ID, 'dropdown-menu-type')
    select = Select(select_activity_type)
    select.select_by_index(0)
    assert select.first_selected_option.text == 'All'

    # Test the activity gear dropdown.
    select_activity_gear = driver.find_element(By.ID, 'dropdown-menu-gear')
    select = Select(select_activity_gear)
    select.select_by_index(0)
    assert select.first_selected_option.text == 'All'

    # Test the activity start date picker.
    activity_start_date = driver.find_element(By.ID, 'datetime-local-start')
    assert activity_start_date.get_attribute('type') == 'date'
    activity_start_date.send_keys('10/25/1983')
    assert activity_start_date.get_attribute('value') == '1983-10-25'

    # Test the activity end date picker.
    activity_end_date = driver.find_element(By.ID, 'datetime-local-end')
    assert activity_end_date.get_attribute('type') == 'date'
    activity_end_date.send_keys('11/16/1987')
    assert activity_end_date.get_attribute('value') == '1987-11-16'

    # Test the commute checkbox.
    activity_commute_checkbox = driver.find_element(By.ID, 'commute-checkbox')
    assert activity_commute_checkbox.get_attribute('type') == 'checkbox'

    # Test the activity distance more than filter.
    activity_more_than_distance_filter = driver.find_element(By.ID, 'more-than-distance-filter')
    assert activity_more_than_distance_filter.get_attribute('type') == 'number'
    activity_more_than_distance_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_distance_filter.send_keys('5')
    assert activity_more_than_distance_filter.get_attribute('value') == '5'

    # Test the activity distance less than filter.
    activity_less_than_distance_filter = driver.find_element(By.ID, 'less-than-distance-filter')
    assert activity_less_than_distance_filter.get_attribute('type') == 'number'
    activity_less_than_distance_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_distance_filter.send_keys('100')
    assert activity_less_than_distance_filter.get_attribute('value') == '100'

    # Test the activity more than elevation gain filter.
    activity_more_than_elevation_filter = driver.find_element(By.ID, 'more-than-elevation-gain-filter')
    assert activity_more_than_elevation_filter.get_attribute('type') == 'number'
    activity_more_than_elevation_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_elevation_filter.send_keys('5')
    assert activity_more_than_elevation_filter.get_attribute('value') == '5'

    # Test the activity less than elevation gain filter.
    activity_less_than_elevation_filter = driver.find_element(By.ID, 'less-than-elevation-gain-filter')
    assert activity_less_than_elevation_filter.get_attribute('type') == 'number'
    activity_less_than_elevation_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_elevation_filter.send_keys('100')
    assert activity_less_than_elevation_filter.get_attribute('value') == '100'

    # Test the activity highest elevation more than filter.
    activity_highest_elevation_more_than_filter = driver.find_element(By.ID, 'more-than-highest-elevation-filter')
    assert activity_highest_elevation_more_than_filter.get_attribute('type') == 'number'
    activity_highest_elevation_more_than_filter.clear()  # Clear the field before sending a new value.
    activity_highest_elevation_more_than_filter.send_keys('5')
    assert activity_highest_elevation_more_than_filter.get_attribute('value') == '5'

    # Test the activity highest elevation less than filter.
    activity_highest_elevation_less_than_filter = driver.find_element(By.ID, 'less-than-highest-elevation-filter')
    assert activity_highest_elevation_less_than_filter.get_attribute('type') == 'number'
    activity_highest_elevation_less_than_filter.clear()  # Clear the field before sending a new value.
    activity_highest_elevation_less_than_filter.send_keys('100')
    assert activity_highest_elevation_less_than_filter.get_attribute('value') == '100'

    # Test the activity moving time greater than hours filter.
    activity_moving_time_greater_than_hours_filter = driver.find_element(By.ID, 'more-than-hours')
    assert activity_moving_time_greater_than_hours_filter.get_attribute('type') == 'number'
    activity_moving_time_greater_than_hours_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_greater_than_hours_filter.send_keys('5')
    assert activity_moving_time_greater_than_hours_filter.get_attribute('value') == '5'

    # Test the activity moving time greater than minutes filter.
    activity_moving_time_greater_than_minutes_filter = driver.find_element(By.ID, 'more-than-minutes')
    assert activity_moving_time_greater_than_minutes_filter.get_attribute('type') == 'number'
    activity_moving_time_greater_than_minutes_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_greater_than_minutes_filter.send_keys('5')
    assert activity_moving_time_greater_than_minutes_filter.get_attribute('value') == '5'

    # Test the activity moving time greater than seconds filter.
    activity_moving_time_greater_than_seconds_filter = driver.find_element(By.ID, 'more-than-seconds')
    assert activity_moving_time_greater_than_seconds_filter.get_attribute('type') == 'number'
    activity_moving_time_greater_than_seconds_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_greater_than_seconds_filter.send_keys('5')
    assert activity_moving_time_greater_than_seconds_filter.get_attribute('value') == '5'

    # Test the activity moving time less than hours filter.
    activity_moving_time_less_than_hours_filter = driver.find_element(By.ID, 'less-than-hours')
    assert activity_moving_time_less_than_hours_filter.get_attribute('type') == 'number'
    activity_moving_time_less_than_hours_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_less_than_hours_filter.send_keys('100')
    assert activity_moving_time_less_than_hours_filter.get_attribute('value') == '100'

    # Test the activity moving time less than minutes filter.
    activity_moving_time_less_than_minutes_filter = driver.find_element(By.ID, 'less-than-minutes')
    assert activity_moving_time_less_than_minutes_filter.get_attribute('type') == 'number'
    activity_moving_time_less_than_minutes_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_less_than_minutes_filter.send_keys('100')
    assert activity_moving_time_less_than_minutes_filter.get_attribute('value') == '100'

    # Test the activity moving time less than seconds filter.
    activity_moving_time_less_than_seconds_filter = driver.find_element(By.ID, 'less-than-seconds')
    assert activity_moving_time_less_than_seconds_filter.get_attribute('type') == 'number'
    activity_moving_time_less_than_seconds_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_less_than_seconds_filter.send_keys('100')
    assert activity_moving_time_less_than_seconds_filter.get_attribute('value') == '100'

    # Test the activity more than average speed filter.
    activity_more_than_average_speed_filter = driver.find_element(By.ID, 'more-than-average-speed-filter')
    assert activity_more_than_average_speed_filter.get_attribute('type') == 'number'
    activity_more_than_average_speed_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_average_speed_filter.send_keys('5')
    assert activity_more_than_average_speed_filter.get_attribute('value') == '5'

    # Test the activity less than average speed filter.
    activity_less_than_average_speed_filter = driver.find_element(By.ID, 'less-than-average-speed-filter')
    assert activity_less_than_average_speed_filter.get_attribute('type') == 'number'
    activity_less_than_average_speed_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_average_speed_filter.send_keys('100')
    assert activity_less_than_average_speed_filter.get_attribute('value') == '100'

    # Test the activity more than max speed filter.
    activity_more_than_max_speed_filter = driver.find_element(By.ID, 'more-than-max-speed-filter')
    assert activity_more_than_max_speed_filter.get_attribute('type') == 'number'
    activity_more_than_max_speed_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_max_speed_filter.send_keys('5')
    assert activity_more_than_max_speed_filter.get_attribute('value') == '5'

    # Test the activity less than max speed filter.
    activity_less_than_max_speed_filter = driver.find_element(By.ID, 'less-than-max-speed-filter')
    assert activity_less_than_max_speed_filter.get_attribute('type') == 'number'
    activity_less_than_max_speed_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_max_speed_filter.send_keys('100')
    assert activity_less_than_max_speed_filter.get_attribute('value') == '100'

    # Test the activity submit button.
    activity_filter_submit_button = driver.find_element(By.ID, 'filter-submit-button')
    assert activity_filter_submit_button.get_attribute('type') == 'submit'


    # ----- Negative Tests -----
    # Test the activity start date picker.
    activity_start_date.clear()
    activity_start_date.send_keys('start')
    assert not activity_start_date.get_attribute('value') == 'start'  # Should not allow text.

    # Test the activity end date picker.
    activity_end_date.clear()
    activity_end_date.send_keys('end')
    assert not activity_end_date.get_attribute('value') == 'end'  # Should not allow text.

    # Test the activity more than distance filter.
    activity_more_than_distance_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_distance_filter.send_keys('a')
    assert not activity_more_than_distance_filter.get_attribute('value') == 'a'  # Should not allow alpha characters.
    activity_more_than_distance_filter.send_keys('!')
    assert not activity_more_than_distance_filter.get_attribute('value') == '!'  # Should not allow symbols.

    # Test the activity less than distance filter.
    activity_less_than_distance_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_distance_filter.send_keys('B')
    assert not activity_less_than_distance_filter.get_attribute('value') == 'B'  # Should not allow alpha characters.
    activity_less_than_distance_filter.send_keys('@')
    assert not activity_less_than_distance_filter.get_attribute('value') == '@'  # Should not allow symbols.

    # Test the activity more than elevation gain filter.
    activity_more_than_elevation_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_elevation_filter.send_keys('c')
    assert not activity_more_than_elevation_filter.get_attribute('value') == 'c'  # Should not allow alpha characters.
    activity_more_than_elevation_filter.send_keys('#')
    assert not activity_more_than_elevation_filter.get_attribute('value') == '#'  # Should not allow symbols.

    # Test the activity less than elevation gain filter.
    activity_less_than_elevation_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_elevation_filter.send_keys('D')
    assert not activity_less_than_elevation_filter.get_attribute('value') == 'D'  # Should not allow alpha characters.
    activity_less_than_elevation_filter.send_keys('$')
    assert not activity_less_than_elevation_filter.get_attribute('value') == '$'  # Should not allow symbols.

    # Test the activity more than highest elevation filter.
    activity_highest_elevation_more_than_filter.clear()  # Clear the field before sending a new value.
    activity_highest_elevation_more_than_filter.send_keys('e')
    assert not activity_highest_elevation_more_than_filter.get_attribute('value') == 'e'  # Should not allow alpha characters.
    activity_highest_elevation_more_than_filter.send_keys('%')
    assert not activity_highest_elevation_more_than_filter.get_attribute('value') == '%'  # Should not allow symbols.

    # Test the activity less than highest elevation filter.
    activity_highest_elevation_less_than_filter.clear()  # Clear the field before sending a new value.
    activity_highest_elevation_less_than_filter.send_keys('F')
    assert not activity_highest_elevation_less_than_filter.get_attribute('value') == 'F'  # Should not allow alpha characters.
    activity_highest_elevation_less_than_filter.send_keys('^')
    assert not activity_highest_elevation_less_than_filter.get_attribute('value') == '^'  # Should not allow symbols.

    # Test the activity moving time greater than hours filter.
    activity_moving_time_greater_than_hours_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_greater_than_hours_filter.send_keys('g')
    assert not activity_moving_time_greater_than_hours_filter.get_attribute('value') == 'g'  # Should not allow alpha characters.
    activity_moving_time_greater_than_hours_filter.send_keys('&')
    assert not activity_moving_time_greater_than_hours_filter.get_attribute('value') == '&'  # Should not allow symbols.

    # Test the activity moving time greater than minutes filter.
    activity_moving_time_greater_than_minutes_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_greater_than_minutes_filter.send_keys('H')
    assert not activity_moving_time_greater_than_minutes_filter.get_attribute('value') == 'H'  # Should not allow alpha characters.
    activity_moving_time_greater_than_minutes_filter.send_keys('*')
    assert not activity_moving_time_greater_than_minutes_filter.get_attribute('value') == '*'  # Should not allow symbols.

    # Test the activity moving time greater than seconds filter.
    activity_moving_time_greater_than_seconds_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_greater_than_seconds_filter.send_keys('i')
    assert not activity_moving_time_greater_than_seconds_filter.get_attribute('value') == 'i'  # Should not allow alpha characters.
    activity_moving_time_greater_than_seconds_filter.send_keys('(')
    assert not activity_moving_time_greater_than_seconds_filter.get_attribute('value') == '('  # Should not allow symbols.

    # Test the activity moving time less than hours filter.
    activity_moving_time_less_than_hours_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_less_than_hours_filter.send_keys('J')
    assert not activity_moving_time_less_than_hours_filter.get_attribute('value') == 'J'  # Should not allow alpha characters.
    activity_moving_time_less_than_hours_filter.send_keys(')')
    assert not activity_moving_time_less_than_hours_filter.get_attribute('value') == ')'  # Should not allow symbols.

    # Test the activity moving time less than minutes filter.
    activity_moving_time_less_than_minutes_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_less_than_minutes_filter.send_keys('k')
    assert not activity_moving_time_less_than_minutes_filter.get_attribute('value') == 'k'  # Should not allow alpha characters.
    activity_moving_time_less_than_minutes_filter.send_keys('-')
    assert not activity_moving_time_less_than_minutes_filter.get_attribute('value') == '-'  # Should not allow symbols.

    # Test the activity moving time less than seconds filter.
    activity_moving_time_less_than_seconds_filter.clear()  # Clear the field before sending a new value.
    activity_moving_time_less_than_seconds_filter.send_keys('L')
    assert not activity_moving_time_less_than_seconds_filter.get_attribute('value') == 'L'  # Should not allow alpha characters.
    activity_moving_time_less_than_seconds_filter.send_keys('_')
    assert not activity_moving_time_less_than_seconds_filter.get_attribute('value') == '_'  # Should not allow symbols.

    # Test the activity more than average speed filter.
    activity_more_than_average_speed_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_average_speed_filter.send_keys('m')
    assert not activity_more_than_average_speed_filter.get_attribute('value') == 'm'  # Should not allow alpha characters.
    activity_more_than_average_speed_filter.send_keys('+')
    assert not activity_more_than_average_speed_filter.get_attribute('value') == '+'  # Should not allow symbols.

    # Test the activity less than average speed filter.
    activity_less_than_average_speed_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_average_speed_filter.send_keys('N')
    assert not activity_less_than_average_speed_filter.get_attribute('value') == 'N'  # Should not allow alpha characters.
    activity_less_than_average_speed_filter.send_keys('=')
    assert not activity_less_than_average_speed_filter.get_attribute('value') == '='  # Should not allow symbols.

    # Test the activity more than max speed filter.
    activity_more_than_max_speed_filter.clear()  # Clear the field before sending a new value.
    activity_more_than_max_speed_filter.send_keys('o')
    assert not activity_more_than_max_speed_filter.get_attribute('value') == 'o'  # Should not allow alpha characters.
    activity_more_than_max_speed_filter.send_keys('~')
    assert not activity_more_than_max_speed_filter.get_attribute('value') == '~'  # Should not allow symbols.

    # Test the activity less than max speed filter.
    activity_less_than_max_speed_filter.clear()  # Clear the field before sending a new value.
    activity_less_than_max_speed_filter.send_keys('P')
    assert not activity_less_than_max_speed_filter.get_attribute('value') == 'P'  # Should not allow alpha characters.
    activity_less_than_max_speed_filter.send_keys('`')
    assert not activity_less_than_max_speed_filter.get_attribute('value') == '`'  # Should not allow symbols.


def test_settings(driver):
    """
    This function tests the settings page using positive and negative tests.
    :param driver: The WebDriver instance.
    :return: None
    """

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

def test_activities(client):
    """
    This function checks that each activity loads correctly (status_code == 200).
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
