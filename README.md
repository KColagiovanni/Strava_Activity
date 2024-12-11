## This project is under construction and is currently being worked on.

## Description
This project was designed to analyze downloaded data from Strava activities and allow users to easily filter and search 
for activities and see their filtered or unfiltered activity data graphed. The user can also view the details of the 
individual activities, when they are selected.

## User Guide

### To Download Strava Activity
Sign into your [Strava](www.strava.com) account using a web browser(can't be done via Moble app):
* From the upper right, click on your profile picture to expand profile menu
* Click on "My Profile".
* Scroll down to "Download or Delete Your Account" and select "Get Started".
* Under "Download Request (optional)", select "Request You Archive".
* The archive will be emailed to the email account associated with the account, it could take several hours.
* Once the email arrives, select "Download Archive". The archive will be downloaded to your default download directory.

### How to Run (On Linux)
* `sudo apt install python3.12-venv -y`
* `sudo apt-get install python3-tk -y`
* Navigate to the directory where the program will be setup using the cli (Ex. `cd ~ && mkdir Strava && cd Strava`)
* `git clone https://github.com/kcolagiovanni/Strava_Activity`
* `python3 -m venv strava`
* `source strava/bin/activate`
* `pip install matplotlib pandas flask Flask-SQLAlchemy plotly fitdecode gpxpy python-tcxparser `

### How to Use
* Upload Files
* View Activities
* View Songle Activity
