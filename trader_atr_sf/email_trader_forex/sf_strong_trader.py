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
import logging
from twilio.rest import Client


dotenv.load_dotenv(".env")
table_name_part = ""
active_charts = [{"name": "US500_1h", "is_currency": False},
                 {"name": "EURCHF_1h", "is_currency": True}]
twilio_credentials = {
    "twilio_sid": os.environ["twilio_sid"],
    "twilio_token": os.environ["twilio_token"],
    "twilio_number": os.environ["twilio_number"],
    "my_phone_number": os.environ["my_phone_number"]
}

# ---------------- EMAIL ----------------
email_server = "imap.azet.sk"
azet_buy_alerts_login = os.environ["azet_buy_alerts_login"]
azet_buy_alerts_passw = os.environ["azet_buy_alerts_passw"]

azet_values_report_login = os.environ["azet_values_report_login"]
azet_values_report_passw = os.environ["azet_values_report_passw"]


# ---------------- MYSQL ----------------
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
db_connection = mysql.connector.connect(host="localhost",
                                        user=mysql_user,
                                        passwd=mysql_passw,
                                        database="fri_trade",
                                        autocommit=True)
fri_trade_cursor = db_connection.cursor(buffered=True)


# ---------------- LOGGING ----------------
log_sf_trader = logging.getLogger("sf_logger")
log_sf_trader.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_sf_trader.log")
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


def get_values_emails():
    imap = get_imap(azet_values_report_login, azet_values_report_passw)

    _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 1h Values report")')
    for msgnum in msgnums[0].split():
        msgnum = msgnum.decode("utf-8")
        _, data = imap.fetch(msgnum, "(RFC822)")
        message = email.message_from_bytes(data[0][1])

        sender = message.get('From')
        subject = message.get('subject')
        date_raw = message.get('date')
        timelist = date_raw.split(" ")
        date_dmy = f"{timelist[1]}.{time.strptime(timelist[2], '%b').tm_mon}.{timelist[3]}"
        time_hms = timelist[4]
        time_hms = time_hms.split(":")
        # time_hms[0] = str(int(time_hms[0]))
        time_hms[0] = int(time_hms[0])
        if time_hms[0] < 22:
            time_hms[0] = str(time_hms[0] + 2)
        elif time_hms[0] == 23:
            time_hms[0] = "1"
        elif time_hms[0] == 22:
            time_hms[0] = "0"
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
                mes = "New value added!"
                print(f"{date_now()} {time_now_hms()} {mes}")
                log_sf_trader.warning(mes)
            # else:
            #     print(f"{msgnum} Value already in database")

        except TypeError:
            print(f"{msgnum} Database empty - first email!")
            fri_trade_cursor.execute(insert_query)

    imap.close()
    imap.logout()


def get_alerts_strong_buy():
    imap = get_imap(azet_buy_alerts_login, azet_buy_alerts_passw)

    _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 1h STRONG BUY")')
    for msgnum in msgnums[0].split():
        msgnum = msgnum.decode("utf-8")
        # TODO if msgum > ako last_msgnum z databazy tak nech ten mail vytiahne, inak nie
        _, data = imap.fetch(msgnum, "(RFC822)")
        message = email.message_from_bytes(data[0][1])

        sender = message.get('From')
        subject = message.get('subject')
        date_raw = message.get('date')

        timelist = date_raw.split(" ")
        date_dmy = f"{timelist[1]}.{time.strptime(timelist[2], '%b').tm_mon}.{timelist[3]}"

        time_hms = timelist[4]
        time_hms = time_hms.split(":")
        time_hms[0] = int(time_hms[0])
        if time_hms[0] < 22:
            time_hms[0] = str(time_hms[0] + 2)
        elif time_hms[0] == 23:
            time_hms[0] = "1"
        elif time_hms[0] == 22:
            time_hms[0] = "0"
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
                mes = f"New {symbol} {timeframe} BUY email alert added!"
                print(f"{date_now()} {time_now_hms()} {mes}")
                log_sf_trader.warning(mes)

                get_sl_tp(operation, symbol, timeframe)

            # else:
            #     print(f"{msgnum} Alert already in database")

        except TypeError:
            print(f"{msgnum} Database empty - first email alert!")
            fri_trade_cursor.execute(insert_query)

    imap.close()
    imap.logout()


def get_imap(login, passw):
    logged_in = False
    log_sf_trader.info("Getting imap")
    while not logged_in:
        try:
            imap = imaplib.IMAP4_SSL(email_server)
            imap.login(login, passw)
            imap.select("Inbox")
            logged_in = True
            return imap
        except Exception as error:
            log_sf_trader.error(f"{type(error).__name__}, {error}")
            time.sleep(1)


def get_sl_tp(operation, symbol, timeframe):
    def get_hour_from_time(time_received):
        try:
            return int(time_received[:2])
        except ValueError:
            return int(time_received[:1])

    value_query = f"""select timeReceived, price_close, value_atr_up, value_atr_down, dateReceived, message_number from fri_trade.
                       EURCHF_1h_values_sf_strong order by id desc limit 1"""
    fri_trade_cursor.execute(value_query)
    value_sel_query_result = fri_trade_cursor.fetchone()
    value_data = {"time_received": value_sel_query_result[0],
                  "hour_received": get_hour_from_time(value_sel_query_result[0]),
                  "price_close": value_sel_query_result[1],
                  "value_atrb_up": value_sel_query_result[2],
                  "value_atrb_down": value_sel_query_result[3],
                  "date_received": value_sel_query_result[4],
                  "message_number": value_sel_query_result[5]}

    alert_query = f"""select timeReceived, dateReceived, message_number from fri_trade.EURCHF_1h_alert_emails_sf_strong
                        order by id desc limit 1"""
    fri_trade_cursor.execute(alert_query)
    alert_sel_query_result = fri_trade_cursor.fetchone()
    alert_data = {"time_received": alert_sel_query_result[0],
                  "hour_received": get_hour_from_time(alert_sel_query_result[0]),
                  "date_received": alert_sel_query_result[1],
                  "message_number": alert_sel_query_result[2]}

    time_date_condition = (value_data['hour_received'] == alert_data['hour_received'],
                           alert_data['hour_received'] == hour_now(),
                           value_data['date_received'] == alert_data['date_received'],
                           alert_data['date_received'] == date_now())

    if False not in time_date_condition:
        if operation == "buy":
            stoploss_pips = value_data['price_close'] - value_data['value_atrb_down']
            # stoploss_price = round(value_data['price_close'] - stoploss_pips, 5)

            takeprofit_price = value_data['value_atrb_up']
            takeprofit_pips = takeprofit_price - value_data['price_close']
        else:  # elif operation == "sell":
            stoploss_pips = value_data['value_atrb_up'] - value_data['price_close']
            # stoploss_price = round(value_data['price_close'] + stoploss_pips, 5)

            takeprofit_price = value_data['value_atrb_down']
            takeprofit_pips = value_data['price_close'] - takeprofit_price

        mes = f"OPENING BUY TRADE {symbol} {timeframe}"
        print(f"{date_now()} {time_now_hms()} {mes}")
        log_sf_trader.warning(mes)

        mes = f"""value hour_rec {value_data['hour_received']} -> alert hour_rec {alert_data['hour_received']} ->
                   hour_now {hour_now()},
                   value date rec {value_data['date_received']} -> alert date rec {alert_data['date_received']} ->
                   date_now {date_now()}, alert {alert_data['message_number']}"""
        log_sf_trader.warning(mes)

        send_sms(f"{symbol} {timeframe} strong {operation}")

        allow_comm = True
        if allow_comm:
            communicator(operation, value_data['price_close'], takeprofit_pips, stoploss_pips, symbol, timeframe)
        else:
            print("\n!!!!!!!!! Communicator is OFF !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")

    else:
        print("OLD value in database - see log for details!")
        mes = f"""value hour_rec {value_data['hour_received']} -> alert hour_rec {alert_data['hour_received']} ->
                   hour_now {hour_now()},
                   value date rec {value_data['date_received']} -> alert date rec {alert_data['date_received']} ->
                   date_now {date_now()}, alert {alert_data['message_number']}"""
        log_sf_trader.error(mes)


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


def send_sms(text_message):
    client = Client(twilio_credentials["twilio_sid"], twilio_credentials["twilio_token"])
    message = client.messages.create(
        body=text_message,
        from_=twilio_credentials["twilio_number"],
        to=twilio_credentials["my_phone_number"]
    )
    log_sf_trader.warning("SMS has been sent!")


def main():
    print(f"""\n--- SmartForex Strong signal email trader ---\n{date_now()} {time_now_hms()} Running...
           Check times are set to (min:sec) MAIN 00:20, BACKUP 01:00""")
    log_sf_trader.info("STARTED ---------------------------------------------------------------------")
    while True:
        check_time = time_now_ms()
        conditions = (check_time == "00:20", check_time == "0:20",
                      check_time == "01:00", check_time == "1:00",)

        if True in conditions:
            log_sf_trader.info("Getting values")
            get_values_emails()
            log_sf_trader.info("Done")

            log_sf_trader.info("Getting buy alerts")
            get_alerts_strong_buy()
            log_sf_trader.info("Done")

        time.sleep(1)


if __name__ == "__main__":
    main()

# TODO bud to urobit tak, ze to zisti strong signal a pocka 2-3 sviecky a cekne, ci tam ten signal stale je
#  to asi bude dost tazke, mozno zbytocne zlozite

# TODO druha moznost je kontrolovat aj klasicke BUY/SELL signaly z toho indikatora a otvorit obchod az ked budu dva
#  sell - strong sell alebo buy - buy a tak.
#     A bude to posielat sms upozornenia typu "EURCHF 1h buy" potom "EURCHF 1h strong buy" a potom manualne ceknem ci
#     je vhodne otvorit poziciu a manualne ju otvorim alebo prikazem FRIDAY, ktora si vezme SL/TP udaje a otvori,
#     alebo to nejak inak zautomatizujem - twilio by aj dostavalo sms odomna? Asi nie, to by bolo zlozite, tam skusit
#     skor nejaku inu appku na spravy na to, ak este nepouzijem FRIDAY
