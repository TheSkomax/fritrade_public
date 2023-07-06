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
active_charts = [{"chartname": "US500_1h",  "is_currency": False},
                 {"chartname": "VIX_1D",    "is_currency": False},
                 {"chartname": "EURCHF_1h", "is_currency": True},
                 {"chartname": "EURCHF_1D", "is_currency": True}]
twilio_credentials = {
    "twilio_sid": os.environ["twilio_sid"],
    "twilio_token": os.environ["twilio_token"],
    "twilio_number": os.environ["twilio_number"],
    "my_phone_number": os.environ["my_phone_number"]
}

# ---------------- EMAIL ----------------
azet_email_server = "imap.azet.sk"
azet_buy_alerts_login = os.environ["azet_buy_alerts_login"]
azet_buy_alerts_passw = os.environ["azet_buy_alerts_passw"]

values_report_login = os.environ["values_report_login"]
values_report_passw = os.environ["values_report_passw"]


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


def get_message_data(message, email_type):
    if email_type == "value":
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

        message = message.as_string()
        message = message.replace('\n', " ")
        message = message.split(" ")

        atrup_value = round(float(message[message.index("ATR-upper") + 1]), 5)
        atrlow_value = round(float(message[message.index("ATR-lower") + 1][:-4]), 5)
        price_close = round(float(message[message.index('2;">Price') + 1]), 5)

        return {"time_received": time_received, "date_dmy": date_dmy, "sender":sender, "subject":subject,
                "price_close": price_close, "atrup_value": atrup_value, "atrlow_value": atrlow_value}

    elif email_type == "alert":
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

        subject_parts = subject.split(" ")
        symbol = subject_parts[1]
        timeframe = subject_parts[2]
        operation = subject_parts[4].lower()

        return {"time_received": time_received, "date_dmy": date_dmy, "sender": sender, "subject": subject,
                "symbol": symbol, "timeframe": timeframe, "operation": operation}


def get_values(imap_gmail):
    success = False
    log_sf_trader.info("get_values_emails: Getting imap")
    # imap = imap_gmail

    while not success:
        try:
            time.sleep(0.3)
            imap = imaplib.IMAP4_SSL("imap.gmail.com")
            imap.login(values_report_login, values_report_passw)
            imap.select("Inbox")

            _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 1h Values report")')
            select_query = """select message_number from fri_trade.EURCHF_1h_values_sf_strong order by
                               message_number desc limit 1"""
            fri_trade_cursor.execute(select_query)
            last_msgnum = int(fri_trade_cursor.fetchone()[0])

            for msgnum in msgnums[0].split():
                time.sleep(0.3)
                msgnum = msgnum.decode("utf-8")

                try:
                    if int(msgnum) > last_msgnum:
                        message_ok = False
                        while not message_ok:
                            try:
                                time.sleep(0.3)
                                _, data = imap.fetch(msgnum, "(RFC822)")
                                message = email.message_from_bytes(data[0][1])
                                message_ok = True
                            except Exception as error:
                                log_sf_trader.critical(f"Gmail values err1: {type(error).__name__}, {error}")
                                time.sleep(10)

                        message_data = get_message_data(message, "value")
                        time_received = message_data["time_received"]
                        date_dmy = message_data["date_dmy"]
                        sender = message_data["sender"]
                        subject = message_data["subject"]
                        price_close = message_data["price_close"]
                        atrup_value = message_data["atrup_value"]
                        atrlow_value = message_data["atrlow_value"]

                        insert_query = f"""insert into fri_trade.EURCHF_1h_values_sf_strong (timeReceived, dateReceived,
                                            message_number, message_sender, message_subject, price_close, value_atr_up,
                                            value_atr_down, processed) VALUES ('{time_received}', '{date_dmy}',
                                            {msgnum}, '{sender}', '{subject}', {price_close}, {atrup_value},
                                            {atrlow_value}, {False})"""

                        fri_trade_cursor.execute(insert_query)
                        mes = "New value added!"
                        print(f"{date_now()} {time_now_hms()} {mes}")
                        log_sf_trader.warning(mes)
                    # else:
                    #     print(f"{msgnum} new msgnum not higher than last_msgnum")

                except TypeError:  # ak je prazdna databaza
                    print(f"{msgnum} Database empty - first email value!")

                    message_ok = False
                    while not message_ok:
                        try:
                            time.sleep(0.3)
                            _, data = imap.fetch(msgnum, "(RFC822)")
                            message = email.message_from_bytes(data[0][1])
                            message_ok = True
                        except Exception as error:
                            log_sf_trader.critical(f"Gmail values err1: {type(error).__name__}, {error}")
                            time.sleep(10)

                    message_data = get_message_data(message, "value")
                    time_received = message_data["time_received"]
                    date_dmy = message_data["date_dmy"]
                    sender = message_data["sender"]
                    subject = message_data["subject"]
                    price_close = message_data["price_close"]
                    atrup_value = message_data["atrup_value"]
                    atrlow_value = message_data["atrlow_value"]

                    insert_query = f"""insert into fri_trade.EURCHF_1h_values_sf_strong (timeReceived, dateReceived,
                                        message_number, message_sender, message_subject, price_close, value_atr_up,
                                        value_atr_down, processed) VALUES ('{time_received}', '{date_dmy}',
                                        {msgnum}, '{sender}', '{subject}', {price_close}, {atrup_value},
                                        {atrlow_value}, {False})"""

                    fri_trade_cursor.execute(insert_query)

                success = True

            # imap.close()
            # imap.logout()

        except Exception as error:
            log_sf_trader.critical(f"Gmail values err2: {type(error).__name__}: {error}")
            # imap.close()
            # imap.logout()
            time.sleep(30)


def get_alerts():
    # Alert symbol timeframe indicator op
    # Alert EURCHF 1h SQZ-KC60 buy
    imap = get_imap(azet_buy_alerts_login, azet_buy_alerts_passw)

    _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 1h STRONGBUY")')
    # _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: Alert")')
    select_query = """select message_number from fri_trade.EURCHF_1h_alert_emails_sf_strong order by
                       message_number desc limit 1"""
    fri_trade_cursor.execute(select_query)
    last_msgnum = int(fri_trade_cursor.fetchone()[0])

    for msgnum in msgnums[0].split():
        time.sleep(0.3)
        msgnum = msgnum.decode("utf-8")

        try:
            if int(msgnum) > last_msgnum:
                message_ok = False
                while not message_ok:
                    try:
                        time.sleep(0.63)
                        _, data = imap.fetch(msgnum, "(RFC822)")
                        message = email.message_from_bytes(data[0][1])
                        message_ok = True
                    except Exception as error:
                        log_sf_trader.error(f"get_alerts: {type(error).__name__}, {error}")
                        time.sleep(10)

                message_data = get_message_data(message, "alert")
                time_received = message_data["time_received"]
                date_dmy = message_data["date_dmy"]
                sender = message_data["sender"]
                subject = message_data["subject"]
                symbol = message_data["symbol"]
                timeframe = message_data["timeframe"]
                operation = message_data["operation"]

                insert_query = f"""insert into fri_trade.EURCHF_1h_alert_emails_sf_strong (timeReceived, dateReceived,
                                    message_number, message_sender, message_subject, symbol, timeframe, operation, processed)
                                    VALUES('{time_received}', '{date_dmy}', {msgnum}, '{sender}', '{subject}', '{symbol}',
                                    '{timeframe}', '{operation}', {False})"""

                fri_trade_cursor.execute(insert_query)
                mes = f"New {symbol} {timeframe} STRONG BUY email alert added!"
                print(f"{date_now()} {time_now_hms()} {mes}")
                log_sf_trader.warning(mes)

                get_sl_tp(operation, symbol, timeframe)
            # else:
            #     print(f"{msgnum} new msgnum not higher than last_msgnum")

        except TypeError:  # ak je prazdna databaza
            print(f"{msgnum} Database empty - first email alert!")

            message_ok = False
            while not message_ok:
                try:
                    time.sleep(0.63)
                    _, data = imap.fetch(msgnum, "(RFC822)")
                    message = email.message_from_bytes(data[0][1])
                    message_ok = True
                except Exception as error:
                    log_sf_trader.error(f"get_alerts: {type(error).__name__}, {error}")
                    time.sleep(10)

            message_data = get_message_data(message, "alert")
            time_received = message_data["time_received"]
            date_dmy = message_data["date_dmy"]
            sender = message_data["sender"]
            subject = message_data["subject"]
            symbol = message_data["symbol"]
            timeframe = message_data["timeframe"]
            operation = message_data["operation"]

            insert_query = f"""insert into fri_trade.EURCHF_1h_alert_emails_sf_strong (timeReceived, dateReceived,
                                message_number, message_sender, message_subject, symbol, timeframe, operation, processed)
                                VALUES('{time_received}', '{date_dmy}', {msgnum}, '{sender}', '{subject}', '{symbol}',
                                '{timeframe}', '{operation}', {False})"""

            fri_trade_cursor.execute(insert_query)
            mes = f"New {symbol} {timeframe} STRONG BUY email alert added!"
            print(f"{date_now()} {time_now_hms()} {mes}")
            log_sf_trader.warning(mes)

            get_sl_tp(operation, symbol, timeframe)

    imap.close()
    imap.logout()


def get_imap(login, passw):
    logged_in = False
    log_sf_trader.info("get_imap - Getting imap")
    while not logged_in:
        try:
            time.sleep(0.01)
            imap = imaplib.IMAP4_SSL(azet_email_server)
            imap.login(login, passw)
            imap.select("Inbox")
            logged_in = True
            return imap
        except Exception as error:
            log_sf_trader.error(f"get_imap: {type(error).__name__}: {error}")
            time.sleep(3)


def get_sl_tp(operation, symbol, timeframe):
    def get_hour_from_time(time_received):
        try:
            return int(time_received[:2])
        except ValueError:
            return int(time_received[:1])

    value_query = f"""select timeReceived, price_close, value_atr_up, value_atr_down, dateReceived, message_number
                       from fri_trade.EURCHF_1h_values_sf_strong order by id desc limit 1"""
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

        manual_only = True
        if not manual_only:
            communicator(operation, value_data['price_close'], takeprofit_pips, stoploss_pips, symbol, timeframe)
        else:
            print("\nCommunicator is OFF!!!!!\n")
            log_sf_trader.warning("Communicator is OFF!!! - only manual trades")

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
    client = Client(twilio_credentials["twilio_sid"],
                    twilio_credentials["twilio_token"])
    client.messages.create(body=text_message,
                           from_=twilio_credentials["twilio_number"],
                           to=twilio_credentials["my_phone_number"])
    log_sf_trader.warning(f"SMS has been sent: {text_message}")


def main():
    times = ("00:20", "0:20", "04:00", "4:00")

    print(f"\n--- SmartForex Strong signal email trader ---\n{date_now()} {time_now_hms()} Running...")
    print(f"Check times are set to (min:sec) MAIN {times[0]}, BACKUP {times[2]}")
    log_sf_trader.info(f"STARTED --- {times[0]} {times[2]} -------------------------------------------------")

    imap_gmail = ""
    # imap_gmail = imaplib.IMAP4_SSL("imap.gmail.com")
    # imap_gmail.login(values_report_login, values_report_passw)
    # imap_gmail.select("Inbox")

    while True:
        check_time = time_now_ms()

        if check_time in times:
            log_sf_trader.info("=== RUN STARTED")
            log_sf_trader.info("Getting values")
            get_values(imap_gmail)
            log_sf_trader.info("Done")

            log_sf_trader.info("Getting alerts")
            get_alerts()
            log_sf_trader.info("Done")
            log_sf_trader.info("=== RUN OVER")

        time.sleep(1)


if __name__ == "__main__":
    main()


# TODO druha moznost je kontrolovat aj klasicke BUY/SELL signaly z toho indikatora a otvorit obchod az ked budu dva
#  sell - strong sell alebo buy - buy a tak.
#     A bude to posielat sms upozornenia typu "EURCHF 1h buy" potom "EURCHF 1h strong buy" a potom manualne ceknem ci
#     je vhodne otvorit poziciu a manualne ju otvorim alebo prikazem FRIDAY, ktora si vezme SL/TP udaje a otvori,
#     alebo to nejak inak zautomatizujem - twilio by aj dostavalo sms odomna? Asi nie, to by bolo zlozite, tam skusit
#     skor nejaku inu appku na spravy na to, ak este nepouzijem FRIDAY

# TODO ■■■VIX 1D: Chandelier exit -> takeprofit 1 az 1.15pip, stoploss atrb
#      ■■■EURCHF 1h: 2xSF indikator -> nastaveny jeden na 2h a druhy na 4h, riadit sa podla oboch SF indikatorov,
#               skombinovat ich a pouzivat aj buy/sell aj strong signaly
#               10% takeprofit NIE!!! na 1h timeframe je to 32 pipov a to je moc!
#      ■■■EURCHF 1D: SF 1W -> pozerat len strong signaly

# TODO ■■■ ked bol critical na gmail imape tak bol len 1x a potom to pri dalsom rune zas slo normalne, tak mozno
#             ako je to zadefinovane na fest v main tak to je dobre tak EDIT: tak vtedy to bezalo po starom, ze
#               ten imap sa definoval az v get_values!!!!!!!
