import requests
import json

webhook_url = "http://38.242.253.153:80/webhook"

data = {"name": "---TEST---   ",
        "Channel URL": "testovacia url",
        "aa": "Feri",
        "bb URL": "testovacia url",
        }

r = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"}, timeout=5)
