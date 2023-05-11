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
        print(atrup_value, atrlow_value, price_close)

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
                print(f"{msgnum} New value added!")
            else:
                print(f"{msgnum} Value already in database")

        except TypeError:
            print(f"{msgnum} Database empty - first email!")
            fri_trade_cursor.execute(insert_query)


    imap.close()
    imap.logout()


def get_alert_emails():
    imap = imaplib.IMAP4_SSL(email_server)
    imap.login(azet_trade_alerts_login, azet_trade_alerts_passw)
    imap.select("Inbox")

    _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 5m STRONG BUY (fake)")')
    for msgnum in msgnums[0].split():
        msgnum = msgnum.decode("utf-8")
        # if msgum > ako last_msgnum z databazy tak nech ten mail vytiahne, inak nie
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
                print(f"{msgnum} New email alert added!")
                #     RUN COMMUNICATOR************************************************************************
            else:
                print(f"{msgnum} Email already in database")

        except TypeError:
            print(f"{msgnum} Database empty - first email!")
            fri_trade_cursor.execute(insert_query)

    imap.close()
    imap.logout()


def communicator(chart_name, indicator, operation, takeprofit_pips, stoploss_pips):
    proc = subprocess.call(["python3",
                            "./api_communicator.py", chart_name, indicator, operation, str(takeprofit_pips),
                            str(stoploss_pips)
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/trader_atr_sf/email_trader/api_communicator.py",
                         chart_name, indicator, operation, str(takeprofit_pips), str(stoploss_pips)
                         ])


def main():
    get_values_emails()
    # while True:
    #     get_alert_emails()
    #     time.sleep(30)


if __name__ == "__main__":
    main()

# TODO na zapisovanie udajov z atr indikatora pouzit dalsi samostatny ucet s alertom, ktory bude posielat udaje kazdu hodinu, dat tam nejaku podmienku co je stale splnena