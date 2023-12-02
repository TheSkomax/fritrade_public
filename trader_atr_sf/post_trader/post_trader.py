# ===================================================================================
# POST TRADER WITH WEBHOOK SERVER
#
# VIX ATR - obchoduju sa ATR zlomy potvrdene 2(1?) stupajucimi hodnotami po zlome
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
main_cursor = db_connection.cursor(buffered=True)

# ---------------- LOGGING ----------------
log_sf_trader = logging.getLogger("logger")
log_sf_trader.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_post_trader.log")
file_handler.setFormatter(log_formatter)
log_sf_trader.addHandler(file_handler)


def datetime_now(time_format: str) -> str:
    time_dict = {
        "hms": datetime.now().strftime("%H:%M:%S"),
        "hm":  datetime.now().strftime("%H:%M"),
        "ms":  datetime.now().strftime("%M:%S"),
        "h":   datetime.now().hour,
        "m":   datetime.now().minute,
        "date": date.today().strftime("%d.%m.%Y")
    }
    return time_dict[time_format]


# accepts POST requests from tradingview_webhook_gateway.py
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.method == "POST":
        payload = request.json
        write_to_db(payload)

        return "OK", 200
    else:
        abort(400)


def write_to_db(message):
    print(f"\n------------------ Received new payload from gateway: ------------------\n{message}")

    if message["type"] == "value":
        time_received = message["time_received"]
        date_dmy = message["date_dmy"]
        sender = message["sender"]
        price_close = message["price_close"]
        atr_value = message["atr_value"]
        symbol = message["symbol"]
        timeframe = message["timeframe"]

        insert_query = f"""insert into fri_trade.post_values (timeReceived, dateReceived,
                            message_sender, symbol, timeframe, price_close,
                            value_atr, processed) VALUES ('{time_received}',
                            '{date_dmy}', '{sender}', '{symbol}', '{timeframe}',
                            {price_close}, {atr_value}, {False})"""

        main_cursor.execute(insert_query)

        mes = f"{symbol} {timeframe} - VALUE added!"
        print(f"{datetime_now('date')} {datetime_now('hms')} {mes}")
        log_sf_trader.warning(mes)

        check_last_alert_value()

    elif message["type"] == "alert":
        time_received = message["time_received"]
        date_dmy = message["date_dmy"]
        sender = message["sender"]
        symbol = message["symbol"]
        timeframe = message["timeframe"]
        operation = message["operation"]
        indicator = message["indicator"]

        insert_query = f"""insert into fri_trade.email_trader_alerts (timeReceived, dateReceived,
                        message_sender, symbol, timeframe, indicator, operation,
                        processed) VALUES('{time_received}', '{date_dmy}',
                        '{sender}', '{symbol}', '{timeframe}', '{indicator}', '{operation}', {False})"""
        main_cursor.execute(insert_query)

        mes = f"{symbol} {timeframe} - {operation} {indicator} ALERT added!"
        print(f"{datetime_now('date')} {datetime_now('hms')} {mes}")
        log_sf_trader.warning(mes)

        find_value_for_alert(time_received, date_dmy, operation, symbol, timeframe)


def get_sl_tp(operation, symbol, timeframe, indicator):
    def get_hour_from_time(time_received):
        try:
            return int(time_received[:2])
        except ValueError:
            return int(time_received[:1])

    value_query = f"""select timeReceived, price_close, value_atr_up, value_atr_down, dateReceived, message_number
                       from fri_trade.post_values where symbol = '{symbol}' and timeframe = '{timeframe}'
                       order by id desc limit 1"""
    main_cursor.execute(value_query)
    value_sel_query_result = main_cursor.fetchone()

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
    main_cursor.execute(alert_query)
    alert_sel_query_result = main_cursor.fetchone()
    alert_data = {"time_received":  alert_sel_query_result[0],
                  "hour_received":  get_hour_from_time(alert_sel_query_result[0]),
                  "date_received":  alert_sel_query_result[1],
                  "message_number": alert_sel_query_result[2]}
    # print(alert_data)

    time_date_condition = (value_data['hour_received'] == alert_data['hour_received'],
                           alert_data['hour_received'] == datetime_now("h"),
                           value_data['date_received'] == alert_data['date_received'],
                           alert_data['date_received'] == datetime_now("date"))
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
        print(f"{datetime_now('date')} {datetime_now('hms')} {mes}")
        log_sf_trader.warning(mes)

        mes = f"""VALUE hour_received {value_data['hour_received']} -> ALERT hour_received {alert_data['hour_received']} -> hour_now {datetime_now("h")},
                   VALUE date_received {value_data['date_received']} -> ALERT date_received {alert_data['date_received']} -> date_now {datetime_now("date")}
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
        mes = f"""VALUE hour_received {value_data['hour_received']} -> ALERT hour_received {alert_data['hour_received']} -> hour_now {datetime_now("h")},
                   VALUE date_received {value_data['date_received']} -> ALERT date_received {alert_data['date_received']} -> date_now {datetime_now("date")},
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


def find_value_for_alert(alert_time_received, alert_date_received, operation, symbol, timeframe):
    alert_hour, alert_min, alert_sec = alert_time_received.split(":")

    log_sf_trader.info("Trying to find value that corresponds with alert time/date")
    ok = False
    while not ok:
        q = f"""select id, timeReceived, dateReceived from fri_trade.post_values where 
                symbol = '{symbol}' and timeframe = '{timeframe}' order by id desc limit 1"""
        main_cursor.execute(q)
        value_id, value_time_received, value_date_received = main_cursor.fetchone()
        value_hour, value_min, value_sec = value_time_received.split(":")

        if alert_hour == value_hour and int(alert_min) == int(value_min) and alert_date_received == value_date_received:
            q = f"""update fri_trade.post_values set alert_type = '{operation}' where id = {value_id}"""
            main_cursor.execute(q)
            log_sf_trader.info("DONE")
            ok = True
        else:
            time.sleep(5)


def check_last_alert_value():
    q = f"""select id, price_close, value_atr, alert_type, symbol, timeframe from fri_trade.post_values
            where alert_type is not Null and processed = False order by id desc limit 1"""
    main_cursor.execute(q)
    value_data = main_cursor.fetchone()

    if value_data is not None:
        alert_value_id, alert_price_close, alert_value_atr, alert_operation, alert_symbol, alert_timeframe = value_data

        q = f"""select id, price_close, value_atr from fri_trade.post_values
                where symbol = '{alert_symbol}' and timeframe = '{alert_timeframe}' order by id desc limit 1"""
        main_cursor.execute(q)
        latest_data = main_cursor.fetchone()
        latest_value_id, latest_price_close, latest_value_atr = latest_data

        if alert_operation == "buy":
            if alert_value_atr > latest_value_atr:
                print("open trade1")
                q = f"""update table fri_trade.post_values set processed = True where id = {alert_value_id}"""

        elif alert_operation == "sell":
            if alert_value_atr < latest_value_atr:
                print("open trade2")
                q = f"""update table fri_trade.post_values set processed = True where id = {alert_value_id}"""
    else:
        pass


if __name__ == "__main__":
    # check_last_alert_value()
    print("============================\nATR - obchoduju sa ATR zlomy potvrdene 2(1?) stupajucimi hodnotami po zlome\n============================")
    app.run(port=5001)

    # symbol = "META"
    # timeframe = "1h"
    # q = f"""select id, timeReceived from fri_trade.post_values where symbol = '{symbol}' and timeframe = '{timeframe}'
    #             order by message_number desc limit 1"""
    # main_cursor.execute(q)
    # value_id, value_time_received = main_cursor.fetchone()
    # value_hour, value_min, value_sec = value_time_received.split(":")
