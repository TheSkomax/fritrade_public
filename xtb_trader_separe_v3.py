import datetime
import os
import dotenv
import threading
import time
from datetime import date
from datetime import datetime
import subprocess
import mysql.connector
import logging


# ====== basic config ======
filename = os.path.basename(__file__)[:-3]
block_bar = "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"

max_positions_allowed = 10
max_percent_from_free_margin = 7
max_volume_per_trade = 0.05

max_lots_override = True
default_lots = 0.02  # ak je max_lots_override zapnute, bude otvarat len tieto loty
variable_lots = 0.02
allow_shorts = False

dotenv.load_dotenv(".env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

"""!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""

# ====== symboly a ich tf, ktoré má trader obchodovať - scraper ich musí zapisovať, čiže musia byť nastavené v ňom! ====
# pridat gold, us100, de30 atď
# PRESUNUTE DO MYSQL - funkcia make_active_sym_buy_list:

# active_symbols_buy = [
#     {"US500": ["1h", "2h", "3h", "4h", "D", "W", "M"]},
#     {  "VIX": ["1h", "2h", "3h", "4h", "D", "W"]},
# ]

# active_symbols_sell = [
#     {"aaa": ["1h", ]},
# ]

active_symbols_buy = []

"""!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""

# ====== terminal config ======
# PIPE_PATH = "/tmp/trader_terminal_v3"
# if not os.path.exists(PIPE_PATH):
#     os.mkfifo(PIPE_PATH)
# subprocess.Popen(['xterm', '-fa', 'Monospace', '-fs', '12', '-e', 'tail -f %s' % PIPE_PATH])


# ====== mysql - fri_trade schema ======
database = mysql.connector.connect(host="localhost",
                                   user=mysql_user,
                                   passwd=mysql_passw,
                                   database="fri_trade",
                                   autocommit=True)
fritrade_cursor = database.cursor(buffered=True)

db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
keepalive_cursor = db.cursor(buffered=True)


# ====== Logging ======
trader_logger = logging.getLogger("xtb_logger3")
trader_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_xtb_trader3.log")
file_handler.setFormatter(log_formatter)
trader_logger.addHandler(file_handler)
trader_logger.info(f"\n{block_bar}")

minute_list = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

if not max_lots_override:
    trader_logger.critical("POZOR! max_lots_override je VYPNUTÝ! Trader bude otvárať pozície v maximálnom možnom vypočítanom objeme!!!")
else:
    trader_logger.warning(f"USING max_lots_override! Max volume per trade is {default_lots} lots!")

def check_current_minute():
    minute_actual = datetime.now().minute
    return int(minute_actual)


def check_current_second():
    second_actual = datetime.now().second
    return int(second_actual)


def time_now():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


def mysql_keepalive():
    while True:
        q = "select id from fri_trade.US500_1h order by id desc limit 1"
        keepalive_cursor.execute(q)
        res = keepalive_cursor.fetchall()
        trader_logger.info("Keeping mysql connection alive")
        time.sleep(3600)


def make_active_sym_buy_list():
    q = "SELECT symbol FROM fri_trade.active_symbols"
    fritrade_cursor.execute(q)
    res = fritrade_cursor.fetchall()
    symbol_list = []

    for item in res:
        symbol = item[0]
        if symbol not in symbol_list:
            symbol_list.append(symbol)

    for symbol in symbol_list:
        temp_dict = {}
        temp_list = []
        q = f"SELECT timeframe, buyAllowed FROM fri_trade.active_symbols where symbol = '{symbol}'"
        fritrade_cursor.execute(q)
        res = fritrade_cursor.fetchall()

        for item in res:
            allowed = item[1]
            tf = item[0]
            if allowed:
                temp_list.append(tf)

        temp_dict[symbol] = temp_list
        active_symbols_buy.append(temp_dict)
    return active_symbols_buy


def check_if_allowed(symbol, timeframe, operation):
    if operation == "buy":
        q = f"SELECT buyAllowed FROM fri_trade.active_symbols where symbol = '{symbol}' and timeframe = '{timeframe}'"
    else:
        q = f"SELECT sellAllowed FROM fri_trade.active_symbols where symbol = '{symbol}' and timeframe = '{timeframe}'"
    fritrade_cursor.execute(q)
    result = fritrade_cursor.fetchone()
    return result[0]


# toto by malo pri cekovani symbolu+tf skontrolovat, ci posledne 3 hodnoty nemaju nahodou 0 spracovanie,
# ak hej tak by to nahodilo spracovanie 1 a preskocilo by ich to, aby to neotvorilo obchod pri spusteni
# ak by nahodou boli hodnoty v breaku
def check_db_at_start(symbol, timeframe):
    processed_list = []
    three_values = f"select id, key_value, processed from fri_trade.{symbol}_{timeframe} order by id desc limit 3"
    fritrade_cursor.execute(three_values)
    db_out = fritrade_cursor.fetchall()

    for item in db_out:
        processed = item[2]
        processed_list.append(processed)
    if 1 not in processed_list:
        pass


def communicator(symbol, timeframe, condition):
    proc = subprocess.call(["python3",
                            "./xtb_communicator.py",
                            symbol,
                            timeframe,
                            condition
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/xtb_communicator.py",
                         symbol,
                         timeframe,
                         condition
                         ])
    # new_buy(symbol, timeframe, condition)


def order_modifier():
    print(time_now())
    proc = subprocess.call(["python3",
                            "./xtb_order_modifier_tsl.py"])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/xtb_order_modifier_tsl.py"])


def breakfinder(values, symbol, timeframe):
    C = new_value = values[0]
    B = previous_value = values[1]
    A = prev_previous_value = values[2]
    # print(new_value, previous_value, prev_previous_value)

    buy = False
    sell = False
    condition = None

    """HLAVNÁ BUY PODMIENKA     if C > B and B < A and C < 0: -------- BUY!"""
    # klasicky zlom čer. vlny
    if previous_value < new_value < 0 and previous_value < prev_previous_value:
        buy = True
        condition = "main"


    # """zlom červenej s prierazom novej hodnoty do zelenej vlny"""
    elif C > B < A < 0 < C and B < 0:
        buy = True
        condition = "greenC"


    # zlom po dvoch rovnakých červených hodnotách - nebude tu problém?????????????????????
    # elif A == B and B < C < 0:
    #     buy = True
    #     condition = "doubleRed"


    # obnovenie zelenej vlny
    # TO-DO asi zmazat?
    # elif C > B and B < A and C > 0:
    #     buy = True
    #     condition = "greenRecover"

    if buy is True and condition is not None:
        if check_if_allowed(symbol, timeframe, "buy"):
            out = f"*BREAKFINDER* {symbol} {timeframe} - buy break found! Starting XTB Communicator...            !!!\n"
            print(out)
            trader_logger.info(out)

            # ========================================================================================================
            th = threading.Thread(target=communicator,
                                  args=(symbol, timeframe, condition),
                                  name="xtb communicator thread")
            th.start()
            # ========================================================================================================
        else:
            out = f"*BREAKFINDER* {symbol} {timeframe} - buy break found, trade on this symbol and timeframe not allowed\n"
            print(out)
            trader_logger.error(out)

    # obsolete
    elif sell is True and condition is not None and allow_shorts is True:
        out = f"*BREAKFINDER* {symbol} {timeframe} - sell break found! Starting XTB Communicator...\n"
        print(out)
        trader_logger.info(out)

        # ==============================================================================================================
        subprocess.call(["python3",
                         "./xtb_communicator.py",
                         symbol,
                         timeframe,
                         condition
                         ])
        # ==============================================================================================================

    else:
        out = f"*BREAKFINDER* {symbol} {timeframe} - waiting for trade opportunity\n"
        print(out)
        trader_logger.info(out)


def main():
    print(f"{date_now()} {time_now()}\nGetting active buy symbols...")
    make_active_sym_buy_list()

    print("\nActive symbols for BUY:")
    for item in active_symbols_buy:
        print(item)

    print(f"\n{date_now()} {time_now()}\nMain started - working...")
    trader_logger.info("Main started - working...")

    while True:
        # print("=== {time} {date} ===".format(time=time_now(), date=date_now()))

        for item in active_symbols_buy:
            for symbol in item.keys():

                for timeframes_list in item.values():
                    for timeframe in timeframes_list:
                        qpart1 = "select id, key_value, processed from fri_trade."
                        qpart2 = "_"
                        qpart3 = " order by id desc limit 3"
                        q = qpart1 + symbol + qpart2 + timeframe + qpart3

                        fritrade_cursor.execute(q)
                        db_output = fritrade_cursor.fetchall()

                        try:
                            newest_id = db_output[0][0]
                            newest_id_is_processed = db_output[0][2]
                            values = [float(db_output[0][1]),
                                      float(db_output[1][1]),
                                      float(db_output[2][1])]

                            if not newest_id_is_processed:
                                print(date_now(), time_now())
                                out = f"*MAIN* {symbol} {timeframe} - New value found!"
                                print(out)
                                trader_logger.info(out)

                                # ======================================================================================
                                breakfinder(values, symbol, timeframe)
                                # ======================================================================================

                                qpart1 = "update fri_trade."
                                qpart2 = "_"
                                qpart3 = " set processed = True where id = "
                                q = qpart1 + symbol + qpart2 + timeframe + qpart3 + str(newest_id)
                                fritrade_cursor.execute(q)

                        except IndexError:
                            # print(symbol, timeframe, "- Not enough values in database")
                            pass

        if check_current_minute() in minute_list and check_current_second() == 0:
            # print(time_now())
            th = threading.Thread(target=order_modifier,
                                  name="order_modifier_thread")
            th.start()

        time.sleep(1)


""" --------------------------- MAIN --------------------------- """
mysql_keepalive_thread = threading.Thread(target=mysql_keepalive,
                                          name="mysql_keepalive_thread",
                                          daemon=True)

mysql_keepalive_thread.start()


# main_loop = threading.Thread(target=main, name="main_loop_thread")
# main_loop.start()
main()


# TODO: do loggera pridat info co trader prave robi - vybera stoploss z db, prepocitava nvm čo a tak podobne

# TODO mozno pridat nejaku vec, ze na zaciatku to vyberie 3 posledne hodnoty a ak nie su spracovane, tak ich nespracuje
#  ale oznaci ako spracovane.. aby to neotvaralo pozicie hned po spusteni kvoli starym hodnotam v DB
#  -- funkcia check_db_at_start - asi to neni hotove este ne??????????????????????????????????????????????????????????????????????????

# TO-DO: ked to najde novy value tak akoby prestane bezat, prestane vypisovat cas. na us500 1h je tam vynechana
#  hodnota 10:59 a 9.59 sa zastavil xtb trader, neviem aku to ma spojitost.. mal by bezat furt ked je tam while true
#  Ono sa to akoby zacyklí v pass alebo tak nejak lebo nespadne to, bezi to ale nic to neprintuje ani nerobi, nic
#  pozriet vyznacene while, ci tam niekde neni pass, ktory by to mohol sposobovat, ze sa to tam kdesi strati
# TO-DO taka mala poznamka, mozno, ze to robi nejake problemy v spojitosti s threadingom.. lebo buy sa robi cez
#  samostatny thread tak mozno sa tomu nieco na tom nepaci
# TO-DO test funkcnosti 3 neuspesny! Vyzera to na nejaky problem s xtb loginom, tam je to blokovane akoby
