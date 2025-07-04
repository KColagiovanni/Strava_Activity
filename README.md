## This project is under construction and is currently being worked on.

## Description
This project was designed to analyze downloaded data from Strava activities(or any other fitness tracker that uses the 
same file types) and allow users to easily filter and search for activities and see their filtered or unfiltered 
activity data graphed. The user can also view the details of the individual activities, when they are selected.

## User Guide

### To Download Strava Activity
Sign into your [Strava](www.strava.com) account using a web browser(can't be done via Moble app):
* From the upper right, click on your profile picture to expand profile menu
* Click on "My Account".
* Scroll down to "Download or Delete Your Account" and select "Get Started".
* Under "Download Request (optional)", select "Request You Archive".
* The archive will be emailed to the email account associated with the account, it could take several hours, but 
typically takes about 10 minutes.
* Once the email arrives, select "Download Archive". The archive will be downloaded to your default download directory.

### How to Run (On Linux) from command line
* `sudo apt install python3.12-venv -y`
* Navigate to the directory where the program will be setup using the cli (Ex. `cd ~ && mkdir Strava && cd Strava`)
* `git clone https://github.com/kcolagiovanni/Strava_Activity`
* `python3 -m venv strava`
* `source strava/bin/activate`
* `pip install -r requirements.txt`
* To start the program: `python3 run.py`

* Troubleshooting:
* If `ModuleNotFoundError: No module named 'idlelib'` is seen when trying to run the program, it may be resolved using 
* the following command: `sudo apt-get install python3-tk -y && sudo apt-get install idle3 -y` (Found while trying to 
* run the program on an Ubuntu 22.04 PC using Python 3.10.12).

### How to Use
* Download activity data from Strava.
* Copy the "Activity" folder from the Strava download, to the "uploads" folder in this project.
* If the program is not running, start it (See the "How to Run" section above).
* Open a web browser and enter the following URL: http://localhost:5000/
* Click on "Create DB" from the top menu (or click the hamburger icon in the upper right corner to show the menu).
* Click on the "Create" button.
* View all activities or filter for specific activities, by selecting "Show Activities" from the menu.
* Click on an activity to view its specific details.
