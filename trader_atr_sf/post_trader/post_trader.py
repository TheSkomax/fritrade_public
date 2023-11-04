# ===================================================================================
# POST TRADER WITH WEBHOOK SERVER
#
# VIX ATR - obchoduju sa ATR zlomy potvrdene 2 stupajucimi hodnotami po zlome
# ===================================================================================


import os
import traceback

import dotenv
import mysql.connector
import time
from datetime import date
from datetime import datetime
import subprocess
import logging
from twilio.rest import Client
from flask import Flask, request, abort

app = Flask(__name__)
dotenv.load_dotenv(".env")

twilio_creds = {
    "twilio_sid":      os.environ["twilio_sid"],
    "twilio_token":    os.environ["twilio_token"],
    "twilio_number":   os.environ["twilio_number"],
    "my_phone_number": os.environ["my_phone_number"]
}
mysql_creds = {
    "mysql_user":  os.environ["mysql_user"],
    "mysql_passw": os.environ["mysql_passw"],
}

# ---------------- MYSQL ----------------
db_connection = mysql.connector.connect(host="localhost",
                                        user=mysql_creds["mysql_user"],
                                        passwd=mysql_creds["mysql_passw"],
                                        database="fri_trade",
                                        autocommit=True)
fri_trade_cursor = db_connection.cursor(buffered=True)

# ---------------- LOGGING ----------------
log_sf_trader = logging.getLogger("logger")
log_sf_trader.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_post_trader.log")
file_handler.setFormatter(log_formatter)
log_sf_trader.addHandler(file_handler)


def time_now_hms():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    return time_actual


def time_now_ms():
    time_object = datetime.now()
    time_actual = time_object.strftime("%M:%S")
    return time_actual


def hour_now():
    hour_actual = datetime.now().hour
    return int(hour_actual)


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    date_list = date_actual.split(".")
    list_int = [int(x) for x in date_list]
    list_str = [str(x) for x in list_int]
    date_actual = ".".join(list_str)
    return date_actual


# accepts POST requests from gateway.py
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        payload = request.json
        print(payload)
        db_write(payload)
        return "OK", 200
    else:
        abort(400)


def db_write(message):
    data = get_message_data(message)
    print("\n===", data)

    if message["type"] == "alert":
        time_received = data["time_received"]
        date_dmy =  data["date_dmy"]
        sender =    data["sender"]
        subject =   data["subject"]
        symbol =    data["symbol"]
        timeframe = data["timeframe"]
        operation = data["operation"]
        indicator = data["indicator"]
        insert_query = f"""insert into fri_trade.email_trader_alerts (timeReceived, dateReceived,
                        message_sender, symbol, timeframe, indicator, operation,
                        processed, message_subject) VALUES('{time_received}', '{date_dmy}',
                        '{sender}', '{symbol}', '{timeframe}', '{indicator}', '{operation}', {False},
                        '{subject}')"""
        fri_trade_cursor.execute(insert_query)

        mes = f"{symbol} {timeframe} - {operation} {indicator} alert added!"
        print(f"{date_now()} {time_now_hms()} {mes}")
        log_sf_trader.warning(mes)

    elif message["type"] == "values":
        time_received = data["time_received"]
        date_dmy = data["date_dmy"]
        sender = data["sender"]
        subject = data["subject"]
        price_close = data["price_close"]
        atrup_value = data["atrup_value"]
        atrlow_value = data["atrlow_value"]
        symbol = data["symbol"]
        timeframe = data["timeframe"]

        insert_query = f"""insert into fri_trade.email_trader_values (timeReceived, dateReceived,
                            message_sender, symbol, timeframe, price_close, value_atr_up,
                            value_atr_down, processed, message_subject) VALUES ('{time_received}',
                            '{date_dmy}', '{sender}', '{symbol}', '{timeframe}',
                            {price_close}, {atrup_value}, {atrlow_value}, {False}, '{subject}')"""

        fri_trade_cursor.execute(insert_query)

        mes = f"{symbol} {timeframe} - VALUE added!"
        print(f"{date_now()} {time_now_hms()} {mes}")
        log_sf_trader.warning(mes)


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

        return {"type": "alert", "time_received": time_received, "date_dmy": date_dmy, "sender": "POST",
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

        return {"type": "value", "time_received": time_received, "date_dmy": date_dmy, "sender": "POST",
                "price_close": price_close, "atrup_value": atrup_value,
                "atrlow_value": atrlow_value, "symbol": symbol, "timeframe": timeframe}
    else:
        pass


def get_sl_tp(operation, symbol, timeframe, indicator):
    def get_hour_from_time(time_received):
        try:
            return int(time_received[:2])
        except ValueError:
            return int(time_received[:1])

    value_query = f"""select timeReceived, price_close, value_atr_up, value_atr_down, dateReceived, message_number
                       from fri_trade.email_trader_values where symbol = '{symbol}' and timeframe = '{timeframe}'
                       order by id desc limit 1"""
    fri_trade_cursor.execute(value_query)
    value_sel_query_result = fri_trade_cursor.fetchone()

    value_data = {"time_received":   value_sel_query_result[0],
                  "hour_received":   get_hour_from_time(value_sel_query_result[0]),
                  "price_close":     value_sel_query_result[1],
                  "value_atrb_up":   value_sel_query_result[2],
                  "value_atrb_down": value_sel_query_result[3],
                  "date_received":   value_sel_query_result[4],
                  "message_number":  value_sel_query_result[5]}
    # print(value_data)

    # alert_query = f"""select timeReceived, dateReceived, message_number from fri_trade.EURCHF_1h_alert_emails_sf_strong
    #                    order by id desc limit 1"""
    alert_query = f"""select timeReceived, dateReceived, message_number from fri_trade.email_trader_alerts where
                       symbol = '{symbol}' and timeframe = '{timeframe}' order by id desc limit 1"""
    fri_trade_cursor.execute(alert_query)
    alert_sel_query_result = fri_trade_cursor.fetchone()
    alert_data = {"time_received":  alert_sel_query_result[0],
                  "hour_received":  get_hour_from_time(alert_sel_query_result[0]),
                  "date_received":  alert_sel_query_result[1],
                  "message_number": alert_sel_query_result[2]}
    # print(alert_data)

    time_date_condition = (value_data['hour_received'] == alert_data['hour_received'],
                           alert_data['hour_received'] == hour_now(),
                           value_data['date_received'] == alert_data['date_received'],
                           alert_data['date_received'] == date_now())
    # print(time_date_condition)

    if False not in time_date_condition:
        if "buy" in operation:
            stoploss_pips = round(value_data['price_close'] - value_data['value_atrb_down'], 5)
            # stoploss_price = round(value_data['price_close'] - stoploss_pips, 5)

            takeprofit_price = round(value_data['value_atrb_up'], 5)
            takeprofit_pips =  round(takeprofit_price - value_data['price_close'], 5)
        else:  # elif operation == "sell":
            stoploss_pips = round(value_data['value_atrb_up'] - value_data['price_close'], 5)
            # stoploss_price = round(value_data['price_close'] + stoploss_pips, 5)

            takeprofit_price = round(value_data['value_atrb_down'], 5)
            takeprofit_pips =  round(value_data['price_close'] - takeprofit_price, 5)

        mes = f" !!! OPENING TRADE:   {symbol} {timeframe} - {indicator} {operation}"
        print(f"{date_now()} {time_now_hms()} {mes}")
        log_sf_trader.warning(mes)

        mes = f"""VALUE hour_received {value_data['hour_received']} -> ALERT hour_received {alert_data['hour_received']} -> hour_now {hour_now()},
                   VALUE date_received {value_data['date_received']} -> ALERT date_received {alert_data['date_received']} -> date_now {date_now()}
                   EMAIL ALERT number: {alert_data['message_number']}"""
        log_sf_trader.warning(mes)

        manual_only = True
        if not manual_only:
            communicator(operation, value_data['price_close'], takeprofit_pips, stoploss_pips, symbol, timeframe)

        else:
            print("\nCommunicator is OFF!!!\n")
            log_sf_trader.warning("Communicator is OFF!!! - only manual trades")

        return takeprofit_pips, stoploss_pips

    else:
        print("OLD value in database - see log for details!")
        mes = f"""VALUE hour_received {value_data['hour_received']} -> ALERT hour_received {alert_data['hour_received']} -> hour_now {hour_now()},
                   VALUE date_received {value_data['date_received']} -> ALERT date_received {alert_data['date_received']} -> date_now {date_now()},
                   EMAIL ALERT number: {alert_data['message_number']}"""
        log_sf_trader.error(mes)

        return False, False


def communicator(operation, price_close, takeprofit_pips, stoploss_pips, symbol, timeframe):
    proc = subprocess.call(["python3",
                            "./xapi_communicator.py", operation, price_close, takeprofit_pips, stoploss_pips, symbol,
                            timeframe
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/trader_atr_sf/email_trader_forex/xapi_communicator.py",
                         operation, price_close, takeprofit_pips, stoploss_pips, symbol, timeframe
                         ])


def send_sms(text_message):
    log_sf_trader.warning(f"Sending SMS: {text_message}")
    client = Client(twilio_creds["twilio_sid"],
                    twilio_creds["twilio_token"])
    client.messages.create(body= text_message,
                           from_=twilio_creds["twilio_number"],
                           to=   twilio_creds["my_phone_number"])
    log_sf_trader.warning(f"SMS has been sent: {text_message}")


if __name__ == "__main__":
    print("==============\nVIX ATR - obchoduju sa ATR zlomy potvrdene 2 stupajucimi hodnotami po zlome\n==============")
    app.run(port=5001)
