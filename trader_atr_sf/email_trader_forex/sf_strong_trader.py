# ===================================================================================
# EMAIL TRADER - checks email client for email alerts from tradingview.com
# ===================================================================================

import imaplib
import email
import os
import dotenv
import mysql.connector
import time
from datetime import date
from datetime import datetime
import subprocess

from urllib.request import urlopen
from bs4 import BeautifulSoup


dotenv.load_dotenv(".env")
azet_trade_alerts_login = os.environ["azet_trade_alerts_login"]
azet_trade_alerts_passw = os.environ["azet_trade_alerts_passw"]

azet_values_report_login = os.environ["azet_values_report_login"]
azet_values_report_passw = os.environ["azet_values_report_passw"]

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

table_name_part = ""
active_charts = [{"name": "US500_1h", "is_currency": False},
                 {"name": "EURCHF_1h", "is_currency": True}]


# ---------------- EMAIL ----------------
email_server = "imap.azet.sk"


# ---------------- MYSQL ----------------
db_connection = mysql.connector.connect(host="localhost",
                                        user=mysql_user,
                                        passwd=mysql_passw,
                                        database="fri_trade",
                                        autocommit=True)
fri_trade_cursor = db_connection.cursor(buffered=True)


def time_now_hms():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    # print(time_actual)
    return time_actual


def time_now_ms():
    time_object = datetime.now()
    time_actual = time_object.strftime("%M:%S")
    # print(time_actual)
    return time_actual

def hour_now():
    hour_actual = datetime.now().hour
    return int(hour_actual)


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


def get_values_emails():
    imap = imaplib.IMAP4_SSL(email_server)
    imap.login(azet_values_report_login, azet_values_report_passw)
    imap.select("Inbox")

    _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 1h Values report")')
    for msgnum in msgnums[0].split():
        msgnum = msgnum.decode("utf-8")
        _, data = imap.fetch(msgnum, "(RFC822)")
        message = email.message_from_bytes(data[0][1])

        sender = message.get('From')
        subject = message.get('subject')
        date_raw = message.get('date')
        timelist = date_raw.split(" ")
        date_dmy = f"{timelist[1]}.{time.strptime(timelist[2], '%B').tm_mon}.{timelist[3]}"
        time_hms = timelist[4]
        time_hms = time_hms.split(":")
        time_hms[0] = str(int(time_hms[0]) + 2)
        time_received = ":".join(time_hms)

        message = message.as_string()
        message = message.replace('\n', " ")
        message = message.split(" ")

        atrup_value = round(float(message[message.index("ATR-upper") + 1]), 5)
        atrlow_value = round(float(message[message.index("ATR-lower") + 1][:-4]), 5)
        price_close = round(float(message[message.index('2;">Price') + 1]), 5)

        insert_query = f"""insert into fri_trade.EURCHF_1h_values_sf_strong (timeReceived, dateReceived, message_number,
                            message_sender, message_subject, price_close, value_atr_up, value_atr_down, processed) VALUES('{time_received}',
                            '{date_dmy}', {msgnum}, '{sender}', '{subject}', {price_close}, {atrup_value},
                            {atrlow_value}, {False})"""
        select_query = """select message_number from fri_trade.EURCHF_1h_values_sf_strong order by
                           message_number desc limit 1"""
        try:
            fri_trade_cursor.execute(select_query)
            last_msgnum = int(fri_trade_cursor.fetchone()[0])
            if int(msgnum) > last_msgnum:
                fri_trade_cursor.execute(insert_query)
                print(f"{date_now()} {time_now_hms()} New value added!")
            # else:
            #     print(f"{msgnum} Value already in database")

        except TypeError:
            print(f"{msgnum} Database empty - first email!")
            fri_trade_cursor.execute(insert_query)

    imap.close()
    imap.logout()


def get_alert_emails_buy():
    imap = imaplib.IMAP4_SSL(email_server)
    imap.login(azet_trade_alerts_login, azet_trade_alerts_passw)
    imap.select("Inbox")

    _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 5m STRONG BUY (fake)")')
    for msgnum in msgnums[0].split():
        msgnum = msgnum.decode("utf-8")
        # TODO if msgum > ako last_msgnum z databazy tak nech ten mail vytiahne, inak nie
        _, data = imap.fetch(msgnum, "(RFC822)")
        message = email.message_from_bytes(data[0][1])

        sender = message.get('From')
        subject = message.get('subject')
        date_raw = message.get('date')

        timelist = date_raw.split(" ")
        date_dmy = f"{timelist[1]}.{time.strptime(timelist[2], '%B').tm_mon}.{timelist[3]}"

        time_hms = timelist[4]
        time_hms = time_hms.split(":")
        time_hms[0] = str(int(time_hms[0]) + 2)
        time_received = ":".join(time_hms)

        # print("\n", msgnum, time_now_hms())
        # print("SENDER:", sender)
        # print("SUBJECT", subject)
        # print("DATE:", time_received, date_dmy)

        subject_parts = subject.split(" ")
        symbol = subject_parts[1]
        timeframe = subject_parts[2]
        operation = subject_parts[4].lower()

        insert_query = f"""insert into fri_trade.EURCHF_1h_alert_emails_sf_strong (timeReceived, dateReceived, message_number,
                            message_sender, message_subject, symbol, timeframe, operation, processed) VALUES('{time_received}',
                            '{date_dmy}', {msgnum}, '{sender}', '{subject}', '{symbol}', '{timeframe}', '{operation}',
                            {False})"""
        select_query = """select message_number from fri_trade.EURCHF_1h_alert_emails_sf_strong order by
                           message_number desc limit 1"""

        try:
            fri_trade_cursor.execute(select_query)
            last_msgnum = int(fri_trade_cursor.fetchone()[0])
            if int(msgnum) > last_msgnum:
                fri_trade_cursor.execute(insert_query)
                print(f"{date_now()} {time_now_hms()} New email alert added!")
                get_sl_tp(operation, symbol, timeframe)
            # else:
            #     print(f"{msgnum} Alert already in database")

        except TypeError:
            print(f"{msgnum} Database empty - first email alert!")
            fri_trade_cursor.execute(insert_query)

    imap.close()
    imap.logout()


def get_sl_tp(operation, symbol, timeframe):
    select_query = f"""select timeReceived, price_close, value_atr_up, value_atr_down, dateReceived from fri_trade.
                       EURCHF_1h_values_sf_strong order by id desc limit 1"""
    fri_trade_cursor.execute(select_query)
    res = fri_trade_cursor.fetchone()

    time_received = res[0]
    hour = int(time_received[:2])
    price_close = res[1]
    value_atrb_up = res[2]
    value_atrb_down = res[3]
    date_received = res[4]

    if hour == hour_now() and date_received == date_now():
        if operation == "buy":
            stoploss_pips = price_close - value_atrb_down
            stoploss_price = round(price_close - stoploss_pips, 5)

            takeprofit_price = value_atrb_up
            takeprofit_pips = takeprofit_price - price_close
        else:  # elif operation == "sell":
            stoploss_pips = value_atrb_up - price_close
            stoploss_price = round(price_close + stoploss_pips, 5)

            takeprofit_price = value_atrb_down
            takeprofit_pips = price_close - takeprofit_price

        print("OPENING TRADE!!!")
        # communicator(operation, price_close, takeprofit_pips, stoploss_pips, symbol, timeframe)
    else:
        print("Wrong value in database - old one, hour/date condition is not satisfied")
        print(f"Hour {hour}, hour_now {hour_now()}, date rec {date_received}, date_now {date_now()}")


def communicator(operation, price_close, takeprofit_pips, stoploss_pips, symbol, timeframe):
    proc = subprocess.call(["python3",
                            "./api_communicator.py", operation, price_close, takeprofit_pips, stoploss_pips, symbol,
                            timeframe
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/trader_atr_sf/email_trader_forex/api_communicator.py",
                         operation, price_close, takeprofit_pips, stoploss_pips, symbol, timeframe
                         ])


def main():
    print(f"{date_now()} {time_now_hms()} Started")
    while True:
        print(f"{date_now()} {time_now_hms()} Checking...\n")
        get_values_emails()
        get_alert_emails_buy()

        print(f"\n{date_now()} {time_now_hms()} Sleeping...\n")
        time.sleep(60)
    # pass


if __name__ == "__main__":
    main()
