# ===================================================================================
# POST TRADER WITH WEBHOOK SERVER - GATEWAY: Tradingview -> VPS
#
# ATR - obchoduju sa ATR zlomy potvrdene 2 stupajucimi hodnotami po zlome
# ===================================================================================

import threading
from flask import Flask, request, abort
import requests
import json
from datetime import datetime
import queue
import time

app = Flask(__name__)
localhost_url = "http://127.0.0.1:5001/webhook"
mainqueue = queue.Queue()


@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        payload = request.json
        print(f"\n\n------------------ New TV payload received ------------------"
              f"\n{payload}")
        # send_request_to_posttrader(payload)
        mainqueue.put(payload)

        return "OK", 200
    else:
        abort(400)


def send_request_to_posttrader():
    print("send_request_to_posttrader thread started!")
    while True:
        if not mainqueue.empty():
            payload = mainqueue.get()
            data = extract_message_data(payload)
            # print("\n======= DATA", data)
            requests.post(localhost_url, data=json.dumps(data), headers={"Content-Type": "application/json"}, timeout=5)
        else:
            time.sleep(30)


def extract_message_data(message):
    if message["type"] == "alert":
        datetime_raw = (message['time'].replace("T", " ")).split(" ")
        date_raw = datetime_raw[0].split("-")
        date_dmy = f"{date_raw[2]}.{date_raw[1]}.{date_raw[0]}"

        time_hms = (datetime_raw[1].replace("Z", "")).split(":")
        time_hms[0] = int(time_hms[0])

        if (datetime.now().hour - time_hms[0]) == 2:
            if time_hms[0] < 22:
                time_hms[0] = str(time_hms[0] + 2)
            elif time_hms[0] == 23:
                time_hms[0] = "1"
            elif time_hms[0] == 22:
                time_hms[0] = "0"
            time_received = ":".join(time_hms)
        elif (datetime.now().hour - time_hms[0]) == 1:
            if time_hms[0] < 22:
                time_hms[0] = str(time_hms[0] + 1)
            elif time_hms[0] == 23:
                time_hms[0] = "0"
            elif time_hms[0] == 22:
                time_hms[0] = "23"
            time_received = ":".join(time_hms)
        else:
            print("Test spracovani casu 1 nepresiel!!!\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")

        symbol = message["symbol"]
        timeframe = message["timeframe"]
        operation = message["operation"]
        indicator = message["indicator"]
        # subject = f"{message["type"]} {symbol} {timeframe} {operation} {indicator}"

        return {"type": "alert", "time_received": time_received, "date_dmy": date_dmy, "sender": "POST",
                "symbol": symbol, "timeframe": timeframe, "operation": operation, "indicator": indicator}

    elif message["type"] == "value":
        datetime_raw = (message['time'].replace("T", " ")).split(" ")
        date_raw = datetime_raw[0].split("-")
        date_dmy = f"{date_raw[2]}.{date_raw[1]}.{date_raw[0]}"

        time_hms = (datetime_raw[1].replace("Z", "")).split(":")
        time_hms[0] = int(time_hms[0])

        if (datetime.now().hour - time_hms[0]) == 2:
            if time_hms[0] < 22:
                time_hms[0] = str(time_hms[0] + 2)
            elif time_hms[0] == 23:
                time_hms[0] = "1"
            elif time_hms[0] == 22:
                time_hms[0] = "0"
            time_received = ":".join(time_hms)
        elif (datetime.now().hour - time_hms[0]) == 1:
            if time_hms[0] < 22:
                time_hms[0] = str(time_hms[0] + 1)
            elif time_hms[0] == 23:
                time_hms[0] = "0"
            elif time_hms[0] == 22:
                time_hms[0] = "23"
            time_received = ":".join(time_hms)
        else:
            print("Test spracovani casu 2 nepresiel!!!\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")

        price_close = round(float(message["price"]), 5)
        # atrup_value = round(float(message["ATR-upper"]), 5)
        # atrlow_value = round(float(message["ATR-lower"]), 5)
        atr_value = round(float(message["ATR"]), 5)
        symbol = message["symbol"]
        timeframe = message["timeframe"]

        return {"type": "value", "time_received": time_received, "date_dmy": date_dmy, "sender": "POST",
                "price_close": price_close, "atr_value": atr_value, "symbol": symbol, "timeframe": timeframe}


if __name__ == "__main__":
    print("=======================\nGateway server started!\n=======================")
    threading.Thread(target=send_request_to_posttrader, name="send_request_to_posttrader").start()
    app.run(host="0.0.0.0", port=80)
