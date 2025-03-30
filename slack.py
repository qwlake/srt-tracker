import requests
import json

def send_slack_webhook(webhook_url, message):
    headers = {
        'Content-Type': 'application/json',
    }

    data = {
        'text': message,
    }

    response = requests.post(webhook_url, headers=headers, data=json.dumps(data), verify=False)

    if response.status_code != 200:
        return False

    return True