import requests
import json

vps_url = "http://38.242.253.153:80/webhook"
webhook_url = "http://127.0.0.1:5000/post-signal"

data = {"symbol": "GOLD",
        "price": 1980.5,
        "type": "buy",
        }

p = requests.post(url=webhook_url,
                  data=json.dumps(data),
                  headers={"Content-Type": "application/json"},
                  timeout=5)

g = requests.get("http://127.0.0.1:5000/get-signal", timeout=5)
res = json.loads(g.content)
print("Result of GET:\n", res, type(res))
