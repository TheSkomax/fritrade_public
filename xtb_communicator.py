import datetime
import math
import time
from datetime import date, datetime
import mysql.connector
import xAPIConnector
import logging
from sys import argv
import pytz
import os
import dotenv

# ====== credentials ======
# userId je cislo uctu - demo alebo real
dotenv.load_dotenv(".env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]

# ====== basic config ======
block_bar = "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"

friday_day = 4
max_orders_allowed = 6
max_percent_from_free_margin = 5
max_volume_per_trade = 0.05

max_lots_override = True
default_lots = 0.02  # ak je max_lots_override zapnute, bude otvarat len tieto loty
variable_lots = 0.03


# ====== mysql - fri_trade schema ======
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


# ====== Logging ======
comms_logger = logging.getLogger("xtb_communicator_logger")
comms_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_trades.log")
file_handler.setFormatter(log_formatter)
comms_logger.addHandler(file_handler)
comms_logger.info(f"\n{block_bar}")

if not max_lots_override:
    comms_logger.critical("POZOR! max_lots_override je VYPNUTÝ! Trader bude otvárať pozície v maximálnom možnom "
                          "vypočítanom objeme!!!")
else:
    comms_logger.warning(f"USING max_lots_override! Max volume per trade is {default_lots} lots!")



def time_now():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


def check_current_day():
    # 0 = monday...
    daynum = int(datetime.today().weekday())
    return int(daynum)


def check_current_hour():
    hour_actual = datetime.now().hour
    return int(hour_actual)


def check_current_minute():
    minute_actual = datetime.now().minute
    return int(minute_actual)


def check_current_second():
    second_actual = datetime.now().second
    return int(second_actual)


def dst_check(dt=None, timezone=None):
    if dt is None:
        dt = datetime.utcnow()
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(dt, is_dst=None)
    return timezone_aware_date.tzinfo._dst.seconds != 0


def order_time_check(symbol, timeframe):  # pouzivane pre trade bool "Right time for timeframe"
    dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day), timezone="US/Pacific")
    dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day), timezone="Europe/Bratislava")
    # comms_logger.info(f"DST - USA: {dst_usa}   SVK: {dst_svk}")

    if symbol == "US500":
        if dst_usa and not dst_svk:
            twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif (not dst_usa and not dst_svk) or (dst_usa and dst_svk):
            twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            fourhour_hour_list = [3, 7, 11, 15, 19, 22]

    elif symbol == "VIX":
        if dst_usa and not dst_svk:
            twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif (not dst_usa and not dst_svk) or (dst_usa and dst_svk):
            twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            fourhour_hour_list = [3, 7, 11, 15, 19, 22]

    elif symbol == "GOLD":
        if dst_usa and not dst_svk:
            twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif (not dst_usa and not dst_svk) or (dst_usa and dst_svk):
            twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            fourhour_hour_list = [3, 7, 11, 15, 19, 22]

    else:
        comms_logger.error("Unknown symbol - DENIED!")
        print("Unknown symbol - DENIED!")
        return False

    if timeframe == "2h":
        if (check_current_hour() in twohour_hour_list) or (check_current_hour() - 1) in twohour_hour_list:
            if (check_current_minute() == 59) or (check_current_minute() <= 2):
                return True
            else:
                return False
        else:
            return False

    elif timeframe == "3h":
        if (check_current_hour() in threehour_hour_list) or (check_current_hour() - 1) in threehour_hour_list:
            if (check_current_minute() == 59) or (check_current_minute() <= 2):
                return True
            else:
                return False
        else:
            return False

    elif timeframe == "4h":
        if (check_current_hour() in fourhour_hour_list) or (check_current_hour() - 1) in fourhour_hour_list:
            if (check_current_minute() == 59) or (check_current_minute() <= 2):
                return True
            else:
                return False
        else:
            return False

    elif timeframe == "1h" or timeframe == "D" or timeframe == "W":
        return True

    else:
        raise TypeError("!!!!!! Neznamy timeframe, tu by sme sa nemali dostat!!!")


# def tradeterprint(*args):
#     with open(PIPE_PATH, "w") as terminal1:
#         append_file = open("trader_terminal_out.txt", "a")
#         for arg in args:
#             if args.index(arg) == len(args)-1:
#                 terminal1.write(str(arg) + "\n")
#                 append_file.write(str(arg) + "\n")
#                 # append_file.close()
#             else:
#                 terminal1.write(str(arg) + " ")
#                 append_file.write(str(arg) + " ")
#                 # append_file.close()
#             time.sleep(0.01)
#         append_file.close()


# ====== XTB trading stuph ======
class XtbApi:
    def __init__(self):
        pass
        # self.ssid = None
        # self.status = None
        # self.streamclient = None
        # self.client = xAPIConnector.APIClient()
        #
        # self.initial_ping()  # initial command

    def login(self):
        self.ssid = None
        self.status = None
        self.streamclient = None
        self.client = xAPIConnector.APIClient()

        self.initial_ping()  # initial command

        login_cmnd = {
            "command": "login",
            "arguments": {
                "userId": xtb_userId,
                "password": xtb_passw,
            },
            "customTag": "Login command"
        }
        login_bool = False

        while not login_bool:
            login_response = self.client.execute(login_cmnd)

            if login_response["status"]:
                out = "------------------------ Communicator logged into XTB! ------------------------"
                print(out)
                comms_logger.info(out)

                login_bool = True
                self.ssid = login_response['streamSessionId']
                self.status = login_response["status"]
                self.streamclient = xAPIConnector.APIStreamClient(ssId=self.ssid)

            elif login_response['errorCode'] == "BE118":
                login_bool = True

            else:
                login_bool = False
                out = "Login failed!   {code} - {desc}".format(code=login_response['errorCode'],
                                                               desc=login_response["errorDescr"])
                print(out)
                comms_logger.error(out)
                time.sleep(5)

    def logout(self):
        logout_cmnd = {
            "command": "logout",
            "customTag": "Logout command"
        }
        logout_bool = False
        while not logout_bool:
            logout_response = self.client.execute(logout_cmnd)

            if logout_response["status"]:
                out = "------------------------ Communicator logged out of XTB! ------------------------"
                print("\n", out)
                comms_logger.info(out)

                logout_bool = True

            else:
                out = "Logout failed!   {code} - {desc}".format(code=logout_response['errorCode'],
                                                                desc=logout_response["errorDescr"])
                print(out)
                comms_logger.error(out)

                logout_bool = False
                time.sleep(2)

    # obsolete(?)
    def pinger(self):
        com = {
            "command": "ping"
        }
        while True:
            cmd = self.client.execute(com)
            comms_logger.info("Ping: {status}".format(status=cmd["status"]))
            time.sleep(120)

    def initial_ping(self):
        com = {
            "command": "ping"
        }
        cmd = self.client.execute(com)
        comms_logger.info("%s %s", "Initial ping status:", cmd["status"])

    def get_trade_margin(self, symbol, volume):
        time.sleep(.1)
        com = {
            "command": "getMarginTrade",
            "arguments": {
                "symbol": symbol,
                "volume": volume
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]["margin"]

    def get_profit_calculation(self, symbol, openprice, closeprice, volume, operation):
        # cmd: 0 = Buy, 1 = Sell, 2 = Buy_limit, 3 = Sell_limit, 4 = Buy_stop, 5 = Sell_stop, 6 = Balance(read only),
        # 7 = Credit(read only)
        com = {
            "command": "getProfitCalculation",
            "arguments": {
                "closePrice": closeprice,
                "cmd": operation,
                "openPrice": openprice,
                "symbol": symbol,
                "volume": volume
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]["profit"]

    def get_all_opened_only_positions(self):
        time.sleep(.05)
        com = {
            "command": "getTrades",
            "arguments": {
                "openedOnly": True
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

    def get_wanted_trades_timeframe(self, wantedSymbol, wantedTimeframe):
        time.sleep(.1)
        com = {
            "command": "getTrades",
            "arguments": {
                "openedOnly": True
            }
        }
        cmd = self.client.execute(com)
        bool_list = []
        for trade in cmd["returnData"]:
            # print(trade["symbol"], trade["customComment"])
            if trade["symbol"] == wantedSymbol and trade["customComment"] == wantedTimeframe:
                bool_list.append(False)
            else:
                bool_list.append(True)
        if False in bool_list:
            comms_logger.warning("FAILED - Existing position found - Trade will be denied!")
            return False
        else:
            comms_logger.info("PASSED - No existing positions with given symbol and timeframe found")
            return True

    def get_margin_level(self):
        time.sleep(.1)
        com = {
            "command": "getMarginLevel"
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

    def get_symbol(self, symbol):
        time.sleep(.1)
        com = {
            "command": "getSymbol",
            "arguments": {
                "symbol": symbol
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

    def open_buy_order(self, symbol, volume, timeframe, sl, tp):
        transaction_info = {
            "cmd": 0,
            "symbol": symbol,
            "customComment": timeframe,
            "volume": volume,
            "sl": sl,
            "tp": tp,
            "type": 0,
            "price": 0.1
        }
        command = {
            "command": "tradeTransaction",
            "arguments": {
                "tradeTransInfo": transaction_info
            }
        }
        cmdexe = self.client.execute(command)
        confirm = self.check_trade_status(cmdexe["returnData"]["order"])

        trade_accepted = 3
        if confirm[0] == trade_accepted:
            confirm_bool = True
        else:
            confirm_bool = False

        margin = xtb.get_trade_margin(symbol, volume)
        comms_logger.warning(f"{cmdexe['returnData']['order']} TRYING TO OPEN --BUY-- ORDER: {symbol} {timeframe} {volume} {margin}€")

        return {"sent": cmdexe["status"],
                "order": cmdexe["returnData"]["order"],
                "opened": confirm_bool,
                "message": confirm[1]}

    # -------------------------------------------------------------------------------------------------------------------------- unused
    def open_sell_order(self, symbol, volume, timeframe, sl, tp):
        trade_trans_info = {
            "cmd": 0,
            "symbol": symbol,
            "customComment": timeframe,
            "volume": volume,
            "sl": sl,
            "tp": tp,
            "type": 1,
            "price": 0.1
        }
        com = {
            "command": "tradeTransaction",
            "arguments": {
                "tradeTransInfo": trade_trans_info
            }
        }
        cmd = self.client.execute(com)
        confirm = self.check_trade_status(cmd["returnData"]["order"])
        if confirm[0] == 3:
            confirm_bool = True
        else:
            confirm_bool = False

        margin = xtb.get_trade_margin(symbol, volume)

        return {"sent": cmd["status"], "order": cmd["returnData"]["order"], "opened": confirm_bool,
                "message": confirm[1]}


    # -------------------------------------------------------------------------------------------------------------------------- unused/obsolete?
    def add_trailing_stoploss(self):
        alltrades = self.get_all_opened_only_positions()

        for trade in alltrades:
            timeframe = trade["customComment"]
            open_price = trade["open_price"]

            # standard US500 1h wavebreak: 12 pips takeprofit(trailing stoploss)
            if trade["symbol"] == "US500" and timeframe == "1h":
                symbol_specs = self.get_symbol("US500")
                bidprice = symbol_specs["bid"]

                if open_price + 12 <= bidprice:
                    offset = 2  # TODO: asi to bude málo!!!!!!!!!!!!
                    modify = self.modify_order_add_trail_sl(ordernum=trade["order"], trailstop=offset * 10,
                                                               volume=trade["volume"], symbol=trade["symbol"])
                #     tradeterprint("trailSL method:", modify["order"],trade["symbol"], "- MODIFIED:", modify["modified"],
                #                   "   Message:", modify["message"])
                # else:
                #     tradeterprint("trailSL method:", trade["order"], trade["symbol"],
                #                   "- profit not high enough for trailing stoploss!")

            # TODO:standard VIX ? pips takeprofit(trailing stoploss)
            elif trade["symbol"] == "VIX":
                pass
            else:
                pass

    # -------------------------------------------------------------------------------------------------------------------------- unused/obsolete?
    # order musi byt CISLO POZICIE!!! nie cislo objednavky!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def modify_order_add_trail_sl(self, symbol, volume, ordernum, trailstop):
        # "cmd": 0,
        # "symbol": "US500",
        # "volume": 0.03,
        # "offset": 990,
        # "sl": 4000.0,
        # "tp": 5000.0,
        # "type": 3,
        # "price": 0.1,
        # "order": 354154316
        trade_trans_info = {
            "cmd": 0,
            "symbol": symbol,
            "volume": volume,
            "offset": trailstop,
            "sl": 99.0,  # placeholder hodnota, podstatny je offset/trailstop, ten prepise sl takze sl je nepodstatny <- the fuck?
            "tp": 0.0,
            "type": 3,
            "price": 0.1,
            "order": ordernum
        }
        com = {
            "command": "tradeTransaction",
            "arguments": {
                "tradeTransInfo": trade_trans_info
            }
        }

        cmd = self.client.execute(com)
        # print(cmd)
        confirm = self.check_trade_status(cmd["returnData"]["order"])
        if confirm[0] == 3:
            confirm_bool = True
        else:
            confirm_bool = False
        return {"sent": cmd["status"], "order": cmd["returnData"]["order"], "modified": confirm_bool,
                "message": confirm[1]}

    def check_trade_status(self, ordernumber):
        time.sleep(.1)
        com = {
            "command": "tradeTransactionStatus",
            "arguments": {
                "order": ordernumber
            }
        }
        cmd = self.client.execute(com)
        return [cmd["returnData"]["requestStatus"], cmd["returnData"]["message"]]

    def sl_tp_buy_atrb(self, symbol, timeframe):
        comms_logger.info("Getting SL/TP data from database - ATRb")

        qpart1 = "select price, atrb_tp, atrb_sl from "
        qpart2 = symbol
        qpart3 = "_"
        qpart4 = timeframe
        qpart5 = " order by id desc limit 1"
        q = qpart1 + qpart2 + qpart3 + qpart4 + qpart5
        fri_trade_cursor.execute(q)

        data = fri_trade_cursor.fetchone()
        price = data[0]
        atrb_tp = data[1]
        atrb_sl = data[2]

        tp_val = round((atrb_tp - price), 2)
        sl_val = round((price - atrb_sl), 2)

        symbol_info = xtb.get_symbol(symbol)
        ask = symbol_info["ask"]
        bid = symbol_info["bid"]
        # TODO prerobene zaokruhlovanie z 2 na 1, neviem ci to nerobilo problem
        #  pri us500, ze cisla boli s 2 desatinnymi miestami, ale to je pre VIX ok,
        #  tak nvm ale to by asi nerobilo ten problem
        tp = round((ask + tp_val), 1)
        sl = round((ask - sl_val), 1)

        return sl, tp

    def sl_tp_buy_override(self, symbol, timeframe):
        symbol_specs = self.get_symbol(symbol)
        ask = symbol_specs["ask"]
        if symbol == "US500" and timeframe == "1h":
            qpart1 = 'select sl from tradeData where symbol = "'
            qpart2 = '" and timeframe = "'
            qpart3 = '"'
            q = qpart1 + symbol + qpart2 + timeframe + qpart3
            fri_trade_cursor.execute(q)
            sl_val = fri_trade_cursor.fetchone()[0]
            sl = round((ask + sl_val), 1)  # pips je zaporna hodnota, preto +

            qpart1 = 'select tp from tradeData where symbol = "'
            qpart2 = '" and timeframe = "'
            qpart3 = '"'
            q = qpart1 + symbol + qpart2 + timeframe + qpart3
            fri_trade_cursor.execute(q)
            tp_val = fri_trade_cursor.fetchone()[0]
            tp = round((ask + tp_val), 1)

            # print(ask, sl, tp)
            return sl, tp


xtb = XtbApi()


def new_buy(symbol, timeframe, condition):
    xtb.login()

    lots = None
    trade_bools = {"Non-duplicate symbol and tf": False,
                   "Lots OK": False,
                   "Margin OK": False,
                   "Volume OK": False,
                   "Right time for timeframe": False,
                   "Max num of trades not reached": False}

    comms_logger.info("=== TRADE PREPARATIONS STARTED ===")

    account_properties = xtb.get_margin_level()
    balance = account_properties["balance"]
    margin_actual = account_properties["margin"]
    currency = account_properties["currency"]
    credit = account_properties["credit"]
    equity = account_properties["equity"]
    margin_free = account_properties["margin_free"]
    margin_level = account_properties["margin_level"]
    # print(margin_actual, "Eur", margin_level, "%")


    """Zisti ci uz je na tomto symbole otvorena pozicia na rovnakom timeframe ======================================="""
    # Non-duplicate symbol and tf
    comms_logger.info(f"Checking for existing positions:             {symbol} {timeframe}")
    openedtrades = xtb.get_wanted_trades_timeframe(wantedSymbol=symbol, wantedTimeframe=timeframe)
    trade_bools.update({"Non-duplicate symbol and tf": openedtrades})

    # maximalna marza na jeden obchod podla zadaneho % v basic configu
    # zobere volnu marzu z uctu a vydeli ju 100, to je 1% z volnej marze a to vynasobi koeficientom v basic configu
    # Eur
    max_margin_for_new_trade = round((margin_free / 100) * max_percent_from_free_margin, 2)

    # marza potrebna pre defaultny objem v basic configu (0.01) - najnizsia mozna marza
    # Eur
    margin_for_def_volume = xtb.get_trade_margin(symbol, default_lots)  # margin for default lots 0.01
    lowest_possible_margin = margin_for_def_volume

    # maximalny povoleny objem na obchod, vyratane vydelenim max marze na obchod (podla % v basic configu)
    # marzou na def loty (0.01) a to cele deleno 100 pre mikroloty
    # math.trunc vyberie z desatinneho cisla cele cislo, integer, vyhodi desatinne cisla 3.54 -> 3
    # vyrata kolkokrat sa marza na def lots vojde do maximalnej marze... 2x -> 0.02 lot
    # Lot
    max_lots_allowed_for_one_trade = math.trunc(max_margin_for_new_trade/margin_for_def_volume) / 100


    """Zisti, ake loty má otvorit/moze otvorit ======================================================================"""
    # Lots OK
    # otvara len 0.01
    # ak je config override na def loty 0.01 ALEBO ak je marza pre 0.01 vyssia/rovnaka ako najvyssia
    # vypocitana marza na trade
    # TODO: to margin_for_def_volume >= max_margin_for_new_trade sa mi zda ako blbost ale nvm preco
    comms_logger.info("Calculating available volume size")

    if max_lots_override or margin_for_def_volume >= max_margin_for_new_trade:
        lots = default_lots
        trade_bools.update({"Lots OK": True})

    # otvori maximalny mozny VYRATANY objem
    elif max_lots_allowed_for_one_trade > default_lots:
        lots = max_lots_allowed_for_one_trade
        if lots > max_volume_per_trade:
            lots = max_volume_per_trade
        trade_bools.update({"Lots OK": True})

    else:
        out = "funkcia traderbuy - TU SA NIECO DOJEBALO, TU BY SME SA NEMALI DOSTAT ASI - NEDOSTATOK MARZE???"
        comms_logger.error(out)

        trade_bools.update({"Lots OK": False})
    comms_logger.info(f"Available volume: {lots}")
    time.sleep(.1)


    """zisti ci je margin viac ako 50-60% z equity/balance - volnych prostriedkov ==================================="""
    # Margin OK
    if equity < balance:
        calculating_mode = equity
        fifty_percent = round(equity * 0.5, 2)
        sixty_percent = round(equity * 0.6, 2)
        comms_logger.info("Checking margin - 50/60% rule - calculating from EQUITY")

        # print("\nCURRENT ACCOUNT STATS: calculating from EQUITY",
        #       "\nBalance:        ", balance, "€",
        #       "\nEquity:         ", equity, "€",
        #       "\nActual margin:  ", margin_actual, "€",
        #       "\n50% from equity:", fifty_percent, "€",
        #       "\n60% from equity:", sixty_percent, "€")

    else:
        calculating_mode = balance
        fifty_percent = round(balance * 0.5, 2)
        sixty_percent = round(balance * 0.6, 2)
        comms_logger.info("Checking margin - 50/60% rule - calculating from BALANCE")

        # print("\nCURRENT ACCOUNT STATS: calculating with BALANCE",
        #       "\nBalance:         ", balance, "€",
        #       "\nEquity:          ", equity, "€",
        #       "\nActual margin:   ", margin_actual, "€",
        #       "\n50% from balance:", fifty_percent, "€",
        #       "\n60% from balance:", sixty_percent, "€")

    # ak je aktualna marza na otvorenych obchodoch viac ako 50% alebo 60%, tak zakaze trade
    if (margin_actual > fifty_percent or
            margin_actual > sixty_percent):
        trade_bools.update({"Margin OK": False})
        comms_logger.warning("FAILED - Margin is too high - Trade will be denied!")
    # ak je aktualna marza menej ako 50% z volnych prostriedkov, povoli trade
    else:
        trade_bools.update({"Margin OK": True})
        comms_logger.info("PASSED")


    """Zisti aky bude celkovy margin na ucte po otvoreni tejto pozicie =============================================="""
    # Volume OK
    # Ak by bol vyratany objem moc vysoky a margin by potom presahovala 50/60% tak sa to bude snazit
    # znizit objem az na 0.01 lotu, otvori to najvyssi mozny, tak aby to nepresahovalo 50/60%.
    # Ak nemoze byt ani 0.01, tak to da false a trade je odmietnuty
    comms_logger.info("Checking margin size after opened trade - 50/60% rule")
    margin_needed_for_new_trade = xtb.get_trade_margin(symbol, lots)
    if ((margin_actual + margin_needed_for_new_trade) > fifty_percent or
            (margin_actual + margin_needed_for_new_trade) > sixty_percent):

        while lots != 0.01:
            lots = round(lots - 0.01, 2)
            margin_needed_for_new_trade = xtb.get_trade_margin(symbol, lots)

            if ((margin_actual + margin_needed_for_new_trade) > fifty_percent or
                    (margin_actual + margin_needed_for_new_trade) > sixty_percent):
                confirm_volume = False
                trade_bools.update({"Volume OK": confirm_volume})
                comms_logger.warning("FAILED - Margin would be too high - Trade will be denied!")
            else:
                confirm_volume = True
                trade_bools.update({"Volume OK": confirm_volume})
                comms_logger.info("PASSED")
            time.sleep(.1)

    else:
        confirm_volume = True
        trade_bools.update({"Volume OK": confirm_volume})
        comms_logger.info("PASSED")


    """Skontroluje ci je spravny cas na otvorenie pozicie vzhladom na timeframe - 4h nemoze otvorit o 17.00 ========="""
    comms_logger.info("Checking if it is right time for order with specified timeframe")

    time_ok = order_time_check(symbol, timeframe)
    trade_bools.update({"Right time for timeframe": time_ok})
    if time_ok:
        comms_logger.info("PASSED")
    else:
        comms_logger.warning("FAILED - Not the right time for this timeframe - Trade will be denied!")


    """Skontroluje pocet aktualne otvorenych pozicii ================================================================"""
    # Max num of trades not reached
    comms_logger.info("Checking number of opened positions")
    num_of_opened_trades = xtb.get_all_opened_only_positions()
    if len(num_of_opened_trades) < max_orders_allowed:
        trade_bools.update({"Max num of trades not reached": True})
        comms_logger.info("PASSED")
    else:
        trade_bools.update({"Max num of trades not reached": False})
        comms_logger.warning("FAILED - Too many opened trades - Trade will be denied!")

    comms_logger.info("=== TRADE BOOLS ===")
    for i in trade_bools:
        if trade_bools[i]:
            comms_logger.info(f"{trade_bools[i]} - {i}")
        else:
            comms_logger.warning(f"{trade_bools[i]} - {i}")


    """Zhrnutie a otvorenie/zamietnutie pozicie ====================================================================="""
    if False not in trade_bools.values():
        if symbol == "US500" and timeframe == "1h":
            data = xtb.sl_tp_buy_override(symbol=symbol, timeframe=timeframe)
        else:
            data = xtb.sl_tp_buy_atrb(symbol=symbol, timeframe=timeframe)
        sl = data[0]
        tp = data[1]

        # ============================================================================================================
        transaction = xtb.open_buy_order(symbol=symbol,
                                         volume=lots,
                                         timeframe=timeframe,
                                         sl=sl,
                                         tp=tp)
        # ============================================================================================================

        ordernum = transaction["order"]
        sent = transaction["sent"]
        opened = transaction["opened"]
        message = transaction["message"]
        ordertype = "buy"

        print("\nTRANSACTION STATS - ORDER:",
              "\n\nSymbol:", symbol, timeframe,
              "\nLots:", lots, "   Margin:", margin_needed_for_new_trade,
              "\n\nNumber:", ordernum,
              "\nSent:  ", sent,
              "\n\nOpened:", opened, "     Reason:", message)

        if opened:
            out = f"Order {ordernum} {symbol} {timeframe} - TRADE OPENED!"
            print(out)
            comms_logger.warning(out)
        else:
            out = f"Order {ordernum} {symbol} {timeframe} TRADE DENIED! - {message}"
            comms_logger.error(out)
            print(out)

        allopenedtrades = xtb.get_all_opened_only_positions()
        for opn_trade in allopenedtrades:
            if opn_trade["order2"] == ordernum:
                positionnum = opn_trade["position"]
                timeframe = opn_trade["customComment"]
                symbol = opn_trade["symbol"]

                q = f"insert into fri_trade.positions (date, time, positionnum, ordernum, symbol, ordertype, lots, margin, conditionTriggered, timeframe, sent, opened, reason, protected) VALUES('{date_now()}', '{time_now()}', '{positionnum}', '{ordernum}', '{symbol}', '{ordertype}', '{lots}', '{margin_needed_for_new_trade}', '{condition}', '{timeframe}', '{sent}', '{opened}', '{message}', False)"
                fri_trade_cursor.execute(q)

        # qpart1 = "insert into fri_trade.positions "
        # qpart2 = "(date, time, ordernum, symbol, ordertype, lots, margin, conditionTriggered, timeframe, sent, opened, reason) "
        # qpart3 = "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        # q = qpart1 + qpart2 + qpart3
        # fri_trade_cursor.execute(q, (date_now(),
        #                              time_now(),
        #                              str(positionnum),
        #                              str(symbol),
        #                              "buy",
        #                              str(lots),
        #                              margin_needed_for_new_trade,
        #                              str(condition),
        #                              str(timeframe),
        #                              str(sent),
        #                              str(opened),
        #                              str(message)
        #                              )
        #                          )
    else:
        out = f"{symbol} {timeframe}  !!! Trade bools not satisfied - TRADE DENIED !!!"
        comms_logger.error(out)
        print(out)

        for item in trade_bools:
            if not trade_bools[item]:
                print(f"{item} : {trade_bools[item]}")
                comms_logger.error(f"{item} : {trade_bools[item]}")

    xtb.logout()


new_buy(symbol=argv[1:2][0],
        timeframe=argv[2:3][0],
        condition=argv[3:4][0])
