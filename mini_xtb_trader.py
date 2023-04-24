import threading
# import mini_xAPIConnector
import logging
import mysql.connector
import time
from datetime import date
from datetime import datetime
import os
import dotenv
import subprocess

# ====== basic config ======
filename = os.path.basename(__file__)[:-3]
block_bar = "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"

# max_positions_allowed = 6
# max_percent_from_free_margin = 7
# max_volume_per_trade = 0.05

dotenv.load_dotenv(".env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

# ====== mysql - fri_trade schema ======
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


# ====== Logging ======
mini_xtb_logger = logging.getLogger("mini_xtb_trader_logger")
mini_xtb_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_mini_xtb_trader.log")
file_handler.setFormatter(log_formatter)
mini_xtb_logger.addHandler(file_handler)
mini_xtb_logger.info(f"\n{block_bar}")


# ====== basic funkcie ======
def time_now():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    return date_actual


def main():
    print(f"{time_now()} {date_now()} Main started - working...")
    number_of_values_in_db = [0, ]

    # pri prvom spusteni to nahodi pocet hodnot v db, ktore tam uz su aby to neotvorilo obchody hned ako sa to spusti
    select_all_values = "select id, key_value, processed from fri_trade.US500_1h order by id desc"
    fri_trade_cursor.execute(select_all_values)
    db_out = fri_trade_cursor.fetchall()
    values_in_database_total_count = len(db_out)
    if values_in_database_total_count != 0:
        number_of_values_in_db.append(values_in_database_total_count)

    while True:
        # mysql_keep_alive
        q = "select id from fri_trade.US500_1h order by id desc limit 1"
        fri_trade_cursor.execute(q)
        res = fri_trade_cursor.fetchall()
        # mini_xtb_logger.info("Keeping mysql connection alive")

        select_all_values = "select id, key_value, processed from fri_trade.US500_1h order by id desc"
        fri_trade_cursor.execute(select_all_values)
        db_out = fri_trade_cursor.fetchall()

        values_in_database_total_count = len(db_out)

        # select_needed_values = "select id, key_value, processed from fri_trade.US500_1h order by id desc limit 4"
        select_needed_data = "select id, key_value from fri_trade.US500_1h order by id desc limit 4"
        fri_trade_cursor.execute(select_needed_data)

        try:
            data = fri_trade_cursor.fetchall()

            mini_xtb_logger.info(f"Total number of values in database: {values_in_database_total_count}")
            mini_xtb_logger.info(f"num of values in list: {len(number_of_values_in_db)}")
            mini_xtb_logger.info(f"newest val in list: {number_of_values_in_db[-1]}")
            mini_xtb_logger.info(f"newest needed values (from newest): {data[0][1]} {data[1][1]} {data[2][1]} {data[3][1]}")

            if int(values_in_database_total_count) > int(number_of_values_in_db[-1]):
                try:
                    number_of_values_in_db.append(values_in_database_total_count)

                    # newest_id = data[0][0]
                    # newest_id_status = data[0][2]
                    values = [float(data[0][1]),
                              float(data[1][1]),
                              float(data[2][1]),
                              float(data[3][1])]

                    # if newest_id_status == 0:
                    print(f"\n====== {time_now()} {date_now()} ======")
                    out = "US500 1h - New value found!"
                    print(out)
                    mini_xtb_logger.info(out)

                    # ======================================================================================
                    breakfinder(values)
                    # brk = threading.Thread(target=breakfinder, args=values)
                    # brk.start()
                    # ======================================================================================

                except IndexError:
                    out = "US500 1h - Not enough values in database"
                    print(out)
                    mini_xtb_logger.warning(out)
        except IndexError:
            out = "US500 1h - Not enough values in database"
            print(out)
            mini_xtb_logger.warning(out)
        time.sleep(180)


def breakfinder(values):
    symbol = "US500"
    timeframe = "1h"

    newest_val = values[0]  # C
    second_val = values[1]  # B
    third_val = values[2]  # A
    fourth_val = values[3]  # A2

    buy = False
    sell = False
    condition = None

    #  ------------------------- BUY
    # if second_val < newest_val < 0 and second_val < third_val:
    # if 0 > newest_val > second_val > third_val and third_val < fourth_val:
    if 0 > newest_val > second_val and second_val < third_val < fourth_val:
        buy = True
        sell = False
        condition = "mini_tr_buy"

    #  ------------------------- SELL
    # if third_val < second_val > newest_val > 0:
    # if 0 < newest_val < second_val < third_val and third_val > fourth_val:
    if 0 < newest_val < second_val and second_val > third_val > fourth_val:
        buy = False
        sell = True
        condition = "mini_tr_sell"

    #  ------------------------- BUY
    if buy and not sell:
        trade_type = "buy"
        out = "US500 1h - BUY break confirmed! Starting Mini XTB Communicator..."
        print(out)
        mini_xtb_logger.warning(out)

        buy_th = threading.Thread(target=communicator,
                                  args=(symbol, timeframe, condition, trade_type),
                                  name="mini_xtb_communicator_thread")
        buy_th.start()

    #  ------------------------- SELL
    elif sell and not buy:
        trade_type = "sell"
        out = "US500 1h - SELL break confirmed! Starting Mini XTB Communicator..."
        print(out)
        mini_xtb_logger.warning(out)

        sell_th = threading.Thread(target=communicator,
                                   args=(symbol, timeframe, condition, trade_type),
                                   name="mini_xtb_communicator_thread")
        sell_th.start()

    else:
        out = "US500 1h - waiting for trade opportunity"
        print(out)
        mini_xtb_logger.info(out)


def communicator(symbol, timeframe, condition, trade_type):
    proc = subprocess.call(["python3",
                            "./mini_xtb_communicator.py",
                            symbol,
                            timeframe,
                            condition,
                            trade_type
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/mini_xtb_communicator.py",
                         symbol,
                         timeframe,
                         condition,
                         trade_type
                         ])


main()
