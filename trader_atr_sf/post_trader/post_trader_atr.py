# ===================================================================================
# POST TRADER WITH WEBHOOK SERVER
#
# VIX ATR - obchoduju sa ATR zlomy potvrdene 2(1?) stupajucimi hodnotami po zlome
# ===================================================================================

import os
import time
import queue
import dotenv
import logging
import threading
import subprocess
import mysql.connector
from datetime import date
from datetime import datetime
from twilio.rest import Client
from flask import Flask, request, abort


app = Flask(__name__)
dotenv.load_dotenv(".env")
mainqueue = queue.Queue()


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
log_post_trader = logging.getLogger("logger")
log_post_trader.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_post_trader.log")
file_handler.setFormatter(log_formatter)
log_post_trader.addHandler(file_handler)


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
        mainqueue.put(request.json)
        log_post_trader.info("Received post request was added to queue")

        return "OK", 200
    else:
        abort(400)


def writing():
    m = "=== Writing thread started! ==="
    print(m)
    log_post_trader.info(m)
    while True:
        if not mainqueue.empty():
            message = mainqueue.get()
            write_to_db(message)
        else:
            time.sleep(30)


def write_to_db(message):
    print(f"\n\n{datetime_now('date')} {datetime_now('hms')} ------ Received new payload from gateway"
          f" ------------------\n{message}")

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

        mes = f"{symbol} {timeframe} - VALUE added to db!"
        print(f"{datetime_now('date')} {datetime_now('hms')} {mes}")
        log_post_trader.warning(mes)

        check_last_alert_value(symbol, timeframe)

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

        mes = f"{symbol} {timeframe} - {operation} {indicator} ALERT added to db!"
        print(f"{datetime_now('date')} {datetime_now('hms')} {mes}")
        log_post_trader.warning(mes)

        find_value_for_alert(time_received, date_dmy, operation, symbol, timeframe)
        check_last_alert_value(symbol, timeframe)


def find_value_for_alert(alert_time_received, alert_date_received, operation, symbol, timeframe):
    alert_hour, alert_min, alert_sec = alert_time_received.split(":")

    log_post_trader.info("Trying to find value that corresponds with alert time/date")
    found = False
    while not found:
        q = f"""select id, timeReceived, dateReceived from fri_trade.post_values where 
                symbol = '{symbol}' and timeframe = '{timeframe}' order by id desc limit 1"""
        main_cursor.execute(q)
        value_id, value_time_received, value_date_received = main_cursor.fetchone()
        value_hour, value_min, value_sec = value_time_received.split(":")

        if (int(alert_hour) == int(value_hour) and int(alert_min) == int(value_min)
                and alert_date_received == value_date_received):
            q = f"""update fri_trade.post_values set alert_type = '{operation}' where id = {value_id}"""
            main_cursor.execute(q)
            log_post_trader.info("DONE")
            found = True
        else:
            print("alert_time_received:", alert_time_received, "value_time_received:", value_time_received)
            time.sleep(5)


def check_last_alert_value(symbol, timeframe):
    q = f"""select id, price_close, value_atr, alert_type, symbol, timeframe from fri_trade.post_values
            where alert_type is not Null and processed = False and symbol = '{symbol}' and
            timeframe = '{timeframe}' order by id desc limit 1"""
    main_cursor.execute(q)
    alert_value_data = main_cursor.fetchone()

    # if there is a new value that belongs to an alert and is not yet processed
    if alert_value_data is not None:
        (alert_value_id, alert_value_price_close, alert_value_atr,
         alert_value_operation, alert_value_symbol, alert_value_timeframe) = alert_value_data

        # selecting the latest VALUE that is in the db
        q = f"""select id, price_close, value_atr from fri_trade.post_values
                where symbol = '{alert_value_symbol}' and timeframe = '{alert_value_timeframe}' order by id desc limit 1"""
        main_cursor.execute(q)
        latest_data = main_cursor.fetchone()
        latest_value_id, latest_value_price_close, latest_value_atr = latest_data

        if alert_value_operation == "buy":
            if latest_value_atr > alert_value_atr:

                communicator(
                    alert_value_operation,
                    alert_value_price_close,
                    alert_value_atr,
                    alert_value_symbol,
                    alert_value_timeframe,
                )

                log_post_trader.critical("BUY !!!!")
                q = f"""update fri_trade.post_values set processed = True where id = {alert_value_id}"""
                main_cursor.execute(q)
        elif alert_value_operation == "sell":
            if latest_value_atr < alert_value_atr:

                communicator(
                    alert_value_operation,
                    alert_value_price_close,
                    alert_value_atr,
                    alert_value_symbol,
                    alert_value_timeframe,
                )

                log_post_trader.critical("SELL !!!!")
                q = f"""update fri_trade.post_values set processed = True where id = {alert_value_id}"""
                main_cursor.execute(q)
    else:
        log_post_trader.info(f"No new alert_value for {symbol} {timeframe} combination")


def communicator(alert_value_operation, alert_value_price_close, alert_value_atr, alert_value_symbol, alert_value_timeframe, ):
    proc = subprocess.call(["python3",
                            "./post_xapi_comm.py",
                            str(alert_value_operation),
                            str(alert_value_price_close),
                            str(alert_value_atr),
                            str(alert_value_symbol),
                            str(alert_value_timeframe)
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/trader_atr_sf/email_trader_forex/post_xapi_comm.py",
                         str(alert_value_operation),
                         str(alert_value_price_close),
                         str(alert_value_atr),
                         str(alert_value_symbol),
                         str(alert_value_timeframe)
                         ])


def send_sms(text_message):
    log_post_trader.warning(f"Sending SMS: {text_message}")
    client = Client(twilio_creds["twilio_sid"],
                    twilio_creds["twilio_token"])
    client.messages.create(body= text_message,
                           from_=twilio_creds["twilio_number"],
                           to=   twilio_creds["my_phone_number"])
    log_post_trader.warning(f"SMS has been sent: {text_message}")


if __name__ == "__main__":
    print("==========================================================================================\n"
          "Post trader ATR - obchoduju sa ATR zlomy potvrdene 2(1?) stupajucimi hodnotami po zlome\n"
          "==========================================================================================")
    log_post_trader.info("================== STARTED ==================")

    threading.Thread(target=writing, name="writing").start()
    app.run(port=5001)

# TODO: ked pride alert ale pocas trvania toho breaku sa ATR nepohne, teda nepotvrdi sa a tym padom alert_value zostane
#       nespracovane v db, ako bude program postupovat? Kedze to vybera podla najvyssieho (najnovsieho) ID
# TODO: Problem ked je hodnota pred polnocou (3m 23:57) tak si potom nevie najst nasledujucu hodnotu/alert - jednoducho problem s hodinou 23 a 00
