from flask import Flask, request, abort
import requests
import json

app = Flask(__name__)
webhook_url = "http://127.0.0.1:5001/webhook"


@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        print(request.json)
        payload = request.json
        send_to_trader(payload)
        return "OK", 200
    else:
        abort(400)


def send_to_trader(message):
    data = get_message_data(message)
    # print("\n===", data)
    r = requests.post(webhook_url, data=json.dumps(data), headers={"Content-Type": "application/json"}, timeout=5)


def get_message_data(message):
    if message["type"] == "alert":
        datetime_raw = (message['time'].replace("T", " ")).split(" ")
        date_raw = datetime_raw[0].split("-")
        date_dmy = f"{date_raw[2]}.{date_raw[1]}.{date_raw[0]}"

        time_hms = (datetime_raw[1].replace("Z", "")).split(":")
        time_hms[0] = int(time_hms[0])

        if time_hms[0] < 22:
            time_hms[0] = str(time_hms[0] + 2)
        elif time_hms[0] == 23:
            time_hms[0] = "1"
        elif time_hms[0] == 22:
            time_hms[0] = "0"
        time_received = ":".join(time_hms)

        symbol = message["symbol"]
        timeframe = message["timeframe"]
        operation = message["operation"]
        indicator = message["indicator"]
        # subject = f"{message["type"]} {symbol} {timeframe} {operation} {indicator}"

        return {"time_received": time_received, "date_dmy": date_dmy, "sender": "POST",
                "symbol": symbol, "timeframe": timeframe, "operation": operation, "indicator": indicator}

    if message["type"] == "value":
        datetime_raw = (message['time'].replace("T", " ")).split(" ")
        date_raw = datetime_raw[0].split("-")
        date_dmy = f"{date_raw[2]}.{date_raw[1]}.{date_raw[0]}"

        time_hms = (datetime_raw[1].replace("Z", "")).split(":")
        time_hms[0] = int(time_hms[0])

        if time_hms[0] < 22:
            time_hms[0] = str(time_hms[0] + 2)
        elif time_hms[0] == 23:
            time_hms[0] = "1"
        elif time_hms[0] == 22:
            time_hms[0] = "0"
        time_received = ":".join(time_hms)

        price_close = round(float(message["price"]), 5)
        atrup_value = round(float(message["ATR-upper"]), 5)
        atrlow_value = round(float(message["ATR-lower"]), 5)
        symbol = message["symbol"]
        timeframe = message["timeframe"]

        return {"time_received": time_received, "date_dmy": date_dmy, "sender": "POST",
                "price_close": price_close, "atrup_value": atrup_value,
                "atrlow_value": atrlow_value, "symbol": symbol, "timeframe": timeframe}
    else:
        pass


if __name__ == "__main__":
    print("=======================\nWebhook server started!\n=======================")
    app.run(host="0.0.0.0", port=80)
