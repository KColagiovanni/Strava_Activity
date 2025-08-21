from test.unit.webapp import client, driver, db_session
from app.database import Database
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
import time
from bs4 import BeautifulSoup

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
    assert '<a class="nav-link" href="/create-db">Create DB</a>' in html

    # Check that the Calorie Calculator link is present in the HTML
    assert '<a class="nav-link" href="/calorie-calculator">Calorie Calculator</a>' in html

    # Check that the HR Zones link is present in the HTML
    assert '<a class="nav-link" href="/hr-zones">HR Zones</a>' in html

    # Check that the Settings link is present in the HTML
    assert '<a class="nav-link" href="/settings">Settings</a>' in html

    # Check that the landing/home page is displayed successfully
    assert landing.status_code == 200

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

    # TODO Add tests to test for min and max values, and possibly values somewhere in the middle of the min and max.

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

    # TODO Test values that are less and more than the min and max values respectivly

def test_settings(driver):
    """
    This function tests the settings page using positive and negative tests.
    :param driver: The WebDriver instance.
    :return: None
    """

    driver.get("http://localhost:5000/settings")

    # ========== Test the timezone dropdown field properties ==========
    timezone_select = driver.find_element(By.ID, 'dropdown-menu-timezone')
    settings_page_submit_button = driver.find_element(By.ID, 'settings-page-submit-button')

    # +++++ Positive Timezone Dropdown Tests ++++
    # Check for correct name attribute
    assert timezone_select.get_attribute('name') == 'timezone-options'

    # Check for correct submit button type
    assert settings_page_submit_button.get_attribute('type') == 'submit'


def test_calorie_counter(driver, client):
    """
    This function tests the settings page using positive and negative tests.
    :param client: The Pytest test_client defined in webapp/__init__.py.
    :param driver: The WebDriver instance.
    :return: None
    """

    driver.get("http://localhost:5000/calorie-calculator")

    # ========== Define the input field properties ==========
    age_input = driver.find_element(By.ID, 'age')
    weight_input = driver.find_element(By.ID, 'weight')
    height_input = driver.find_element(By.ID, 'height')

    # +++++ Positive Input Tests +++++
    # Age - Check input type
    assert age_input.get_attribute('type') == 'number'

    # Age - Check min and max attributes
    assert age_input.get_attribute('min') == '1'
    assert age_input.get_attribute('max') == '120'

    # Age - Check step attribute
    assert age_input.get_attribute('step') == '1'

    # Age - Test valid input
    age_input.clear()
    age_input.send_keys('25')
    assert age_input.get_attribute('value') == '25'

    # Weight - Check input type
    assert weight_input.get_attribute('type') == 'number'

    # Weight - Check min and max attributes
    assert weight_input.get_attribute('min') == '1'
    assert weight_input.get_attribute('max') == '999'

    # Weight - Check step attribute
    assert weight_input.get_attribute('step') == '0.2'

    # Weight - Test valid input
    weight_input.clear()
    weight_input.send_keys('150')
    assert weight_input.get_attribute('value') == '150'

    # Height - Check input type
    assert height_input.get_attribute('type') == 'number'

    # Height - Check min and max attributes
    assert height_input.get_attribute('min') == '1'
    assert height_input.get_attribute('max') == '108'

    # Height - Check step attribute
    assert height_input.get_attribute('step') == '0.5'

    # Height - Test valid input
    height_input.clear()
    height_input.send_keys('69')
    assert height_input.get_attribute('value') == '69'

    # ----- Negative Input Tests -----
    # Age - More than the max
    age_input.clear()
    age_input.send_keys('121')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('value')) <= 120  # Should not allow 121

    # Age - Less than the min
    age_input.clear()
    age_input.send_keys('0')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('value')) >= 1  # Should not allow 0

    # Age - Negative value (less than min)
    age_input.clear()
    age_input.send_keys('-25')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('value')) >= 1  # Should not allow -25

    # Age - Invalid step size
    age_input.clear()
    age_input.send_keys('50.5')  # This should be restricted by the browser
    assert not int(age_input.get_attribute('step')) < 1  # Should not allow a step < 1

    # Age - Non-numeric
    age_input.clear()
    age_input.send_keys('ten')  # This should be restricted by the browser
    assert not age_input.get_attribute('type') != 'number'  # Should not allow non-numeric input

    # Weight - More than the max
    weight_input.clear()
    weight_input.send_keys('1000')  # This should be restricted by the browser
    assert not int(weight_input.get_attribute('value')) <= 999  # Should not allow 1000

    # Weight - Less than the min
    weight_input.clear()
    weight_input.send_keys('0')  # This should be restricted by the browser
    assert not int(weight_input.get_attribute('value')) >= 1  # Should not allow 0

    # Weight - Negative value (less than min)
    weight_input.clear()
    weight_input.send_keys('-120')  # This should be restricted by the browser
    assert not int(weight_input.get_attribute('value')) >= 1  # Should not allow -120

    # Weight - Invalid step size
    weight_input.clear()
    weight_input.send_keys('50.3')  # This should be restricted by the browser
    assert not float(weight_input.get_attribute('step')) < 0.2  # Should not allow a step < 0.2

    # Weight - Non-numeric
    weight_input.clear()
    weight_input.send_keys('ten')  # This should be restricted by the browser
    assert not weight_input.get_attribute('type') != 'number'  # Should not allow non-numeric input

    # Height - More than the max
    height_input.clear()
    height_input.send_keys('109')  # This should be restricted by the browser
    assert not int(height_input.get_attribute('value')) <= 108  # Should not allow 109

    # Height - Less than the min
    height_input.clear()
    height_input.send_keys('0')  # This should be restricted by the browser
    assert not int(height_input.get_attribute('value')) >= 1  # Should not allow 0

    # Height - Negative value (less than min)
    height_input.clear()
    height_input.send_keys('-65')  # This should be restricted by the browser
    assert not int(height_input.get_attribute('value')) >= 1  # Should not allow a value less than 1

    # Height - Invalid step size
    height_input.clear()
    height_input.send_keys('69.3')  # This should be restricted by the browser
    assert not float(height_input.get_attribute('step')) < 0.5  # Should not allow a step < 0.5

    # Height - Non-numeric
    height_input.clear()
    height_input.send_keys('ten')  # This should be restricted by the browser
    assert not height_input.get_attribute('type') != 'number'  # Should not allow non-numeric input

    # Check for correct submit button type
    calorie_counter_submit_button = driver.find_element(By.ID, 'calorie-counter-submit-button')
    assert calorie_counter_submit_button.get_attribute('type') == 'submit'

    # ========== Calculated table output values ==========
    # Test calculated values.

    # Test 1. Send POST data to the Calorie Calculator form to test each calculated calorie value.
    calorie_post_data = client.post('/calorie-calculator', data={
        'age':'25',
        'gender-options':'Female',
        'weight':'120',
        'height':'66',
        'activity-level-options':'1.2'
    })
    soup = BeautifulSoup(calorie_post_data.data, "html.parser")

    rmr = soup.find(id='rmr-value').text.strip()
    lose_fast = soup.find(id='lose-fast-value').text.strip()
    lose_moderate = soup.find(id='lose-moderate-value').text.strip()
    lose_slow = soup.find(id='lose-slow-value').text.strip()
    maintain = soup.find(id='maintain-value').text.strip()
    gain_slow = soup.find(id='gain-slow-value').text.strip()
    gain_moderate = soup.find(id='gain-moderate-value').text.strip()
    gain_fast = soup.find(id='gain-fast-value').text.strip()

    assert rmr == '1369.7'  # Resting (Basil) Metabolic Rate
    assert lose_fast == '643.64'  # Lose Fast Calories
    assert lose_moderate == '1143.64'  # Lose Moderate Calories
    assert lose_slow == '1393.64'  # Lose Slow Calories
    assert maintain == '1643.64'  # Maintain Calories
    assert gain_slow == '1893.64'  # Gain Slow Calories
    assert gain_moderate == '2143.64'  # Gain Moderate Calories
    assert gain_fast == '2643.64'  # Gain Fast Calories

    # Test 2. Send POST data to the Calorie Calculator form to test each calculated calorie value.
    calorie_post_data = client.post('/calorie-calculator', data={
        'age':'80',
        'gender-options':'Male',
        'weight':'140',
        'height':'68',
        'activity-level-options':'1.9'
    })
    soup = BeautifulSoup(calorie_post_data.data, "html.parser")

    rmr = soup.find(id='rmr-value').text.strip()
    lose_fast = soup.find(id='lose-fast-value').text.strip()
    lose_moderate = soup.find(id='lose-moderate-value').text.strip()
    lose_slow = soup.find(id='lose-slow-value').text.strip()
    maintain = soup.find(id='maintain-value').text.strip()
    gain_slow = soup.find(id='gain-slow-value').text.strip()
    gain_moderate = soup.find(id='gain-moderate-value').text.strip()
    gain_fast = soup.find(id='gain-fast-value').text.strip()

    assert rmr == '1257.8'  # Resting (Basil) Metabolic Rate
    assert lose_fast == '1389.82'  # Lose Fast Calories
    assert lose_moderate == '1889.82'  # Lose Moderate Calories
    assert lose_slow == '2139.82'  # Lose Slow Calories
    assert maintain == '2389.82'  # Maintain Calories
    assert gain_slow == '2639.82'  # Gain Slow Calories
    assert gain_moderate == '2889.82'  # Gain Moderate Calories
    assert gain_fast == '3389.82'  # Gain Fast Calories

    # Test 3. Send POST data to the Calorie Calculator form to test each calculated calorie value.
    calorie_post_data = client.post('/calorie-calculator', data={
        'age':'50',
        'gender-options':'Male',
        'weight':'180',
        'height':'72',
        'activity-level-options':'1.55'
    })
    soup = BeautifulSoup(calorie_post_data.data, "html.parser")

    rmr = soup.find(id='rmr-value').text.strip()
    lose_fast = soup.find(id='lose-fast-value').text.strip()
    lose_moderate = soup.find(id='lose-moderate-value').text.strip()
    lose_slow = soup.find(id='lose-slow-value').text.strip()
    maintain = soup.find(id='maintain-value').text.strip()
    gain_slow = soup.find(id='gain-slow-value').text.strip()
    gain_moderate = soup.find(id='gain-moderate-value').text.strip()
    gain_fast = soup.find(id='gain-fast-value').text.strip()

    assert rmr == '1761.8'  # Resting (Basil) Metabolic Rate
    assert lose_fast == '1730.79'  # Lose Fast Calories
    assert lose_moderate == '2230.79'  # Lose Moderate Calories
    assert lose_slow == '2480.79'  # Lose Slow Calories
    assert maintain == '2730.79'  # Maintain Calories
    assert gain_slow == '2980.79'  # Gain Slow Calories
    assert gain_moderate == '3230.79'  # Gain Moderate Calories
    assert gain_fast == '3730.79'  # Gain Fast Calories


    # Test 4. Send POST data to the Calorie Calculator form to test each calculated calorie value.
    calorie_post_data = client.post('/calorie-calculator', data={
        'age': '15',
        'gender-options': 'Female',
        'weight': '105',
        'height': '62.5',
        'activity-level-options': '1.75'
    })
    soup = BeautifulSoup(calorie_post_data.data, "html.parser")

    rmr = soup.find(id='rmr-value').text.strip()
    lose_fast = soup.find(id='lose-fast-value').text.strip()
    lose_moderate = soup.find(id='lose-moderate-value').text.strip()
    lose_slow = soup.find(id='lose-slow-value').text.strip()
    maintain = soup.find(id='maintain-value').text.strip()
    gain_slow = soup.find(id='gain-slow-value').text.strip()
    gain_moderate = soup.find(id='gain-moderate-value').text.strip()
    gain_fast = soup.find(id='gain-fast-value').text.strip()

    assert rmr == '1335.0'  # Resting (Basil) Metabolic Rate
    assert lose_fast == '1336.25'  # Lose Fast Calories
    assert lose_moderate == '1836.25'  # Lose Moderate Calories
    assert lose_slow == '2086.25'  # Lose Slow Calories
    assert maintain == '2336.25'  # Maintain Calories
    assert gain_slow == '2586.25'  # Gain Slow Calories
    assert gain_moderate == '2836.25'  # Gain Moderate Calories
    assert gain_fast == '3336.25'  # Gain Fast Calories

    # Test 5. Send POST data to the Calorie Calculator form to test each calculated calorie value.
    calorie_post_data = client.post('/calorie-calculator', data={
        'age': '37',
        'gender-options': 'Male',
        'weight': '185',
        'height': '70.5',
        'activity-level-options': '1.375'
    })
    soup = BeautifulSoup(calorie_post_data.data, "html.parser")

    rmr = soup.find(id='rmr-value').text.strip()
    lose_fast = soup.find(id='lose-fast-value').text.strip()
    lose_moderate = soup.find(id='lose-moderate-value').text.strip()
    lose_slow = soup.find(id='lose-slow-value').text.strip()
    maintain = soup.find(id='maintain-value').text.strip()
    gain_slow = soup.find(id='gain-slow-value').text.strip()
    gain_moderate = soup.find(id='gain-moderate-value').text.strip()
    gain_fast = soup.find(id='gain-fast-value').text.strip()

    assert rmr == '1862.3'  # Resting (Basil) Metabolic Rate
    assert lose_fast == '1560.66'  # Lose Fast Calories
    assert lose_moderate == '2060.66'  # Lose Moderate Calories
    assert lose_slow == '2310.66'  # Lose Slow Calories
    assert maintain == '2560.66'  # Maintain Calories
    assert gain_slow == '2810.66'  # Gain Slow Calories
    assert gain_moderate == '3060.66'  # Gain Moderate Calories
    assert gain_fast == '3560.66'  # Gain Fast Calories


def test_hr_zones(driver, client):
    """
    This function tests the heart rate zones page using positive and negative tests.
    :param client: The Pytest test_client defined in webapp/__init__.py.
    :param driver: The WebDriver instance.
    :return: None
    """

    driver.get("http://localhost:5000/hr-zones")

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
    age_input.clear()
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

    # Check for correct submit button type
    heart_rate_zone_submit_button = driver.find_element(By.ID, 'heart-rate-zone-submit-button')
    assert heart_rate_zone_submit_button.get_attribute('type') == 'submit'

    # ========== Calculated table output values ==========
    # Test each HR Zone row labels.
    zone1_label = driver.find_element(By.ID, 'zone1').text
    zone2_label = driver.find_element(By.ID, 'zone2').text
    zone3_label = driver.find_element(By.ID, 'zone3').text
    zone4_label = driver.find_element(By.ID, 'zone4').text
    zone5_label = driver.find_element(By.ID, 'zone5').text

    assert 'Zone 1' in zone1_label
    assert 'Zone 2' in zone2_label
    assert 'Zone 3' in zone3_label
    assert 'Zone 4' in zone4_label
    assert 'Zone 5' in zone5_label

    # Test each HR Zone row percent range.
    zone1_percent_range = driver.find_element(By.ID, 'zone1-perc-range').text
    zone2_percent_range = driver.find_element(By.ID, 'zone2-perc-range').text
    zone3_percent_range = driver.find_element(By.ID, 'zone3-perc-range').text
    zone4_percent_range = driver.find_element(By.ID, 'zone4-perc-range').text
    zone5_percent_range = driver.find_element(By.ID, 'zone5-perc-range').text

    assert '50-60%' in zone1_percent_range
    assert '60-70%' in zone2_percent_range
    assert '70-80%' in zone3_percent_range
    assert '80-90%' in zone4_percent_range
    assert '90-100%' in zone5_percent_range

    # Test 1. Send POST data to the HR Zone form to test each HR Zone calculated bpm range.
    hr_zone_post_data = client.post('/hr-zones', data={'age':'25', 'activity-options':'general'})
    soup = BeautifulSoup(hr_zone_post_data.data, "html.parser")

    zone1_bpm = soup.find(id="zone1-bpm-range").text.strip()
    zone2_bpm = soup.find(id="zone2-bpm-range").text.strip()
    zone3_bpm = soup.find(id="zone3-bpm-range").text.strip()
    zone4_bpm = soup.find(id="zone4-bpm-range").text.strip()
    zone5_bpm = soup.find(id="zone5-bpm-range").text.strip()

    assert zone1_bpm == "95 - 114"  # Zone 1
    assert zone2_bpm == "114 - 133"  # Zone 2
    assert zone3_bpm == "133 - 152"  # Zone 3
    assert zone4_bpm == "152 - 171"  # Zone 4
    assert zone5_bpm == "171 - 190"  # Zone 5

    # Test 2. Send POST data to the HR Zone form to test each HR Zone calculated bpm range.
    hr_zone_post_data = client.post('/hr-zones', data={'age':'50', 'activity-options':'cycling'})
    soup = BeautifulSoup(hr_zone_post_data.data, "html.parser")

    zone1_bpm = soup.find(id="zone1-bpm-range").text.strip()
    zone2_bpm = soup.find(id="zone2-bpm-range").text.strip()
    zone3_bpm = soup.find(id="zone3-bpm-range").text.strip()
    zone4_bpm = soup.find(id="zone4-bpm-range").text.strip()
    zone5_bpm = soup.find(id="zone5-bpm-range").text.strip()

    assert zone1_bpm == "82 - 98"  # Zone 1
    assert zone2_bpm == "98 - 114"  # Zone 2
    assert zone3_bpm == "114 - 131"  # Zone 3
    assert zone4_bpm == "131 - 147"  # Zone 4
    assert zone5_bpm == "147 - 164"  # Zone 5

    # Test 3. Send POST data to the HR Zone form to test each HR Zone calculated bpm range.
    hr_zone_post_data = client.post('/hr-zones', data={'age':'100', 'activity-options':'rowing'})
    soup = BeautifulSoup(hr_zone_post_data.data, "html.parser")

    zone1_bpm = soup.find(id="zone1-bpm-range").text.strip()
    zone2_bpm = soup.find(id="zone2-bpm-range").text.strip()
    zone3_bpm = soup.find(id="zone3-bpm-range").text.strip()
    zone4_bpm = soup.find(id="zone4-bpm-range").text.strip()
    zone5_bpm = soup.find(id="zone5-bpm-range").text.strip()

    assert zone1_bpm == "66 - 79"  # Zone 1
    assert zone2_bpm == "79 - 93"  # Zone 2
    assert zone3_bpm == "93 - 106"  # Zone 3
    assert zone4_bpm == "106 - 119"  # Zone 4
    assert zone5_bpm == "119 - 133"  # Zone 5


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

# def test_upload_no_file(driver):
#     """
#     This function tests the ability of the upload page to handle when no file has been chosen to be uploaded.
#     :param driver: The WebDriver instance.
#     :return: None
#     """
#
#     # Delete activities.csv in the upload folder
#     subprocess.run(['rm', '-r',  'uploads/activities.csv'])
#
#     # Get the upload page.
#     driver.get('http://localhost:5000/create-db')
#
#     # Get the create button element.
#     create_button = driver.find_element(By.ID, "file-create-button")
#
#     # Click create
#     create_button.click()
#
#     # Give the page time to process the file
#     time.sleep(2)
#
#     # Get the test result of the file upload.
#     result = driver.find_element(By.ID, "search-result").text
#
#     # Assert the tests
#     assert 'has not been found!!' in result
#     assert not 'sufficient' in result
#     assert not 'successfully' in result
#     assert not 'columns' in result
#
# def test_upload_empty_file(driver):
#     """
#     This function tests the ability of the upload page to handle when an empty csv file with no data is uploaded.
#     :param driver: The WebDriver instance.
#     :return: None
#     """
#
#     # Upload an empty activities.csv file to the upload directory
#     path = str(subprocess.run(['pwd'], capture_output=True, text=True).stdout.strip())
#     subprocess.run(['cp', '-r', 'test_dir/empty_file/activities.csv', f'{path}/uploads'])
#
#     # Get the upload page.
#     driver.get('http://localhost:5000/create-db')
#
#     # Get the create button element.
#     create_button = driver.find_element(By.ID, "file-create-button")
#
#     # Click create
#     create_button.click()
#
#     # Give the page time to process the file
#     time.sleep(2)
#
#     # Get the test result of the file upload.
#     result = driver.find_element(By.ID, "search-result").text
#
#     # Assert the tests
#     assert 'columns' in result
#     assert not 'sufficient' in result
#     assert not 'was not found!!' in result
#     assert not 'successfully' in result
#
# def test_upload_empty_file_with_headers(driver):
#     """
#     This function tests the ability of the upload page to handle an empty csv file that has headers only being uploaded.
#     :param driver: The WebDriver instance.
#     :return: None
#     """
#
#     # Delete activities.csv in the upload folder
#     subprocess.run(['rm', '-r',  'uploads/activities.csv'])
#
#     # Upload an empty activities.csv file, with headers, to the upload directory
#     path = str(subprocess.run(['pwd'], capture_output=True, text=True).stdout.strip())
#     subprocess.run(['cp', '-r', 'test_dir/empty_file_with_headers/activities.csv', f'{path}/uploads'])
#
#     # Get the upload page.
#     driver.get('http://localhost:5000/create-db')
#
#     # Get the file input element and the create button element.
#     upload_button = driver.find_element(By.ID, "file-create-button")
#
#     # Click upload
#     upload_button.click()
#
#     # Delay to allow the upload to happen.
#     time.sleep(2)
#
#     # Get the test result of the file upload.
#     result = driver.find_element(By.ID, "search-result").text
#
#     # Assert the tests
#     assert 'sufficient' in result
#     assert not 'successfully' in result
#     assert not 'was not found!!' in result
#     assert not 'columns' in result
#
# def test_upload_real_file(driver):
#     """
#     This function tests the ability of the upload page to handle a real csv file being uploaded.
#     :param driver: The WebDriver instance.
#     :return: None
#     """
#
#     # Delete activities.csv in the upload folder
#     subprocess.run(['rm', '-r',  'uploads/activities.csv'])
#
#     # Upload an empty activities.csv file, with headers, to the upload directory
#     path = str(subprocess.run(['pwd'], capture_output=True, text=True).stdout.strip())
#     subprocess.run(['cp', '-r', 'test_dir/real_test_file/activities.csv', f'{path}/uploads'])
#
#     # Get the upload page.
#     driver.get('http://localhost:5000/create-db')
#
#     # Get the file input element and the create button element.
#     upload_button = driver.find_element(By.ID, "file-create-button")
#
#     # Click upload
#     upload_button.click()
#
#     # Delay to allow the upload to happen.
#     time.sleep(2)
#
#     # Get the test result of the file upload.
#     result = driver.find_element(By.ID, "search-result").text
#
#     # Assert the tests
#     assert 'successfully!' in result
#     assert not 'sufficient' in result
#     assert not 'was not found!!' in result
#     assert not 'columns' in result
