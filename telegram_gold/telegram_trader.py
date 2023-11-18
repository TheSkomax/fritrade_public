import subprocess
import time
import logging
import os
import dotenv
import mysql.connector
from datetime import date
from datetime import datetime

import xAPIConnector

dotenv.load_dotenv(".env")
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
xtb_demo_main = os.environ["xtb_demo_main"]
xtb_pw = os.environ["xtb_pw"]

db_connection = mysql.connector.connect(host="localhost",
                                        user=mysql_user,
                                        passwd=mysql_passw,
                                        database="fri_trade",
                                        autocommit=True)
cursor = db_connection.cursor(buffered=True)

log_trader = logging.getLogger("logger")
log_trader.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_trader.log")
file_handler.setFormatter(log_formatter)
log_trader.addHandler(file_handler)


def datetime_now(time_format: str) -> str:
    time_dict = {
        "hms": datetime.now().strftime("%H:%M:%S"),
        "hm":  datetime.now().strftime("%H:%M"),
        "date": date.today().strftime("%d.%m.%Y")
    }
    return time_dict[time_format]


def check_time(message_time: str) -> bool:
    hour_actual, minute_actual = datetime_now("hm").split(":")
    hour_message, minute_message = message_time.split(":")
    hour_actual, minute_actual = int(hour_actual), int(minute_actual)
    hour_message, minute_message = int(hour_message), int(minute_message)

    if hour_actual == hour_message or hour_actual == hour_message + 1:
        if (minute_actual == minute_message or (minute_actual <= 4 and minute_message >= 56) or
                minute_actual <= minute_message + 5):
            return True
        else:
            return False
    else:
        return False


def main():
    print(f"{datetime_now('date')} {datetime_now('hms')} Starting trader")
    log_trader.info("*****   Starting trader   **********************")

    q = """select message_number from fri_trade.gold_messages where processed = 1 order by message_number desc limit 1"""
    cursor.execute(q)

    # print("last_msg_num",last_msg_num)
    q = """select * from fri_trade.gold_messages where processed = 0 order by message_number desc limit 1"""

    count = 0
    while True:
        try:
            last_msg_num = cursor.fetchone()[0]
            if count == 90:
                log_trader.info("Still alive!")
                count = 0

            cursor.execute(q)
            new_msg = cursor.fetchone()
            new_msg_num = new_msg[1]
            # print("new_msg_num", new_msg_num)

            if new_msg_num > last_msg_num:
                log_trader.info("New value in database!")
                values = {
                    "id": int(new_msg[0]),
                    "message_number": int(new_msg[1]),
                    "message_time": new_msg[2],
                    "message_date": new_msg[3],

                    "price_actual": new_msg[4],
                    "operation": new_msg[5],

                    "range_start": new_msg[6],
                    "range_end": new_msg[7],
                    "TP1": new_msg[8],
                    "TP2": new_msg[9],
                    "TP3": new_msg[10],
                    "SL": new_msg[11],

                    "processed": new_msg[12],
                }
                if values["message_date"] == datetime_now("date") and check_time(values["message_time"]):
                    log_trader.info("Date and time OK")
                    log_trader.warning("Starting communicator!")

                    communicator(values["operation"],
                                 values["price_actual"],
                                 values["range_start"],
                                 values["range_end"],
                                 values["TP1"],
                                 values["TP2"],
                                 values["TP3"],
                                 values["SL"],
                                 )
                else:
                    warn = f"Value number {values['message_number']} is old, NO TRADE!!!"
                    print(warn)
                    log_trader.warning(warn)

                q_set_processed = f"""UPDATE fri_trade.gold_messages SET processed = True where id = {values['id']}"""
                cursor.execute(q_set_processed)
            else:
                count = count + 1
                time.sleep(20)
        except TypeError:
            count = count + 1
            time.sleep(20)


def communicator(operation, price_actual, range_start, range_end, TP1, TP2, TP3, SL):
    proc = subprocess.call(["python3",
                            "./xapi_communicator.py",
                            operation,
                            str(price_actual),
                            str(range_start),
                            str(range_end),
                            str(TP1),
                            str(TP2),
                            str(TP3),
                            str(SL),
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/fritrade_public/telegram_gold/xapi_communicator.py",
                         operation,
                         str(price_actual),
                         str(range_start),
                         str(range_end),
                         str(TP1),
                         str(TP2),
                         str(TP3),
                         str(SL),
                         ])


if __name__ == '__main__':
    main()
