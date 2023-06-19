import logging
import os
import dotenv
import time
import imaplib
import email
import mysql.connector
from datetime import date
from datetime import datetime

dotenv.load_dotenv(".env")


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

# ---------------- LOGGING ----------------
log_sf_trader = logging.getLogger("sf_logger")
log_sf_trader.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_sf_trader.log")
file_handler.setFormatter(log_formatter)
log_sf_trader.addHandler(file_handler)

email_server = "imap.azet.sk"


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


def get_values_emails():
    # success = False
    log_sf_trader.info("SUBPROCESS get_values_emails: Getting imap")


    try:
        time.sleep(0.05)
        # imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap = imaplib.IMAP4_SSL(email_server)
        imap.login(values_report_login, values_report_passw)
        imap.select("Inbox")
        print(imap.state)
        _, msgnums = imap.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 1h Values report")')
        for msgnum in msgnums[0].split():
            time.sleep(0.05)
            msgnum = msgnum.decode("utf-8")

            message_ok = False
            while not message_ok:
                try:
                    time.sleep(1)
                    _, data = imap.fetch(msgnum, "(RFC822)")
                    message = email.message_from_bytes(data[0][1])
                    message_ok = True
                except Exception as error:
                    log_sf_trader.error(f"get_values_emails 1: {type(error).__name__}, {error}")
                    time.sleep(10)

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

            success = True

        imap.close()
        imap.logout()

    except Exception as error:
        log_sf_trader.error(f"get_values_emails 2: {type(error).__name__}: {error}")
        # imap.close()
        # imap.logout()
        time.sleep(30)

get_values_emails()
