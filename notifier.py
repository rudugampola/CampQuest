# pushover_client.py
import os
import http.client
import urllib.parse
import requests
from dotenv import load_dotenv
import logging


# Load environment variables from .env file
load_dotenv()

# Read user_key and api_token from environment variables
USER_KEY = os.getenv("PUSHOVER_USER_KEY")
API_TOKEN = os.getenv("PUSHOVER_API_TOKEN")

LOG = logging.getLogger(__name__)
log_formatter = logging.Formatter(
    "%(asctime)s - %(process)s - %(levelname)s - %(message)s"
)

# FileHandler for file output
fh = logging.FileHandler('campquest.log')  # specify your log file name
fh.setFormatter(log_formatter)
LOG.addHandler(fh)


def send_notification(message, title="CampQuest Notification"):
    if not API_TOKEN or not USER_KEY:
        LOG.error(
            "PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN environment variables must be set.")
        raise ValueError(
            "PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN environment variables must be set.")

    """Send a notification using the Pushover API."""
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request(
        "POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": API_TOKEN,
            "user": USER_KEY,
            "message": message,
            "title": title,
        }),
        {"Content-type": "application/x-www-form-urlencoded"}
    )
    response = conn.getresponse()
    return response.status, response.reason


def check_limit():
    if not API_TOKEN or not USER_KEY:
        LOG.error(
            "PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN environment variables must be set.")
        raise ValueError(
            "PUSHOVER_USER_KEY and PUSHOVER_API_TOKEN environment variables must be set.")
    url = f"https://api.pushover.net/1/apps/limits.json?token={API_TOKEN}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return {
            "limit": data.get("limit"),
            "remaining": data.get("remaining"),
            "reset": data.get("reset")
        }

    return None
