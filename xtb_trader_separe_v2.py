import datetime
import math
import threading
import time
from datetime import date
from datetime import datetime
from subprocess import Popen
import mysql.connector
import xAPIConnector
import logging
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
filename = os.path.basename(__file__)[:-3]
block_bar = "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"

max_positions_allowed = 6
max_percent_from_free_margin = 7
max_volume_per_trade = 0.05

max_lots_override = True
default_lots = 0.01  # ak je max_lots_override zapnute, bude otvarat len tieto loty
variable_lots = 0.02


# ====== symbols ======
active_symbols = [
    {"US500": ["1h", "2h", "3h", "4h", "D", "W", "M"]
     },
    {"VIX": ["1h", "2h", "3h", "4h", "D", "W"]
     },
]


# ====== terminal config ======
PIPE_PATH = "/tmp/trader_terminal"
if not os.path.exists(PIPE_PATH):
    os.mkfifo(PIPE_PATH)
Popen(['xterm', '-fa', 'Monospace', '-fs', '12', '-e', 'tail -f %s' % PIPE_PATH])


# ====== mysql - fri_trade schema ======
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


# ====== Logging ======
xtb_logger = logging.getLogger("xtb_logger")
xtb_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("xtb_trader.log")
file_handler.setFormatter(log_formatter)
xtb_logger.addHandler(file_handler)
xtb_logger.info("%s %s", "\n", block_bar)

if not max_lots_override:
    xtb_logger.critical("POZOR! max_lots_override je VYPNUTÝ! Trader bude otvárať pozície v maximálnom možnom vypočítanom objeme!!!")
else:
    xtb_logger.warning("USING max_lots_override! Max volume per trade is 0.01 lots!")


# ====== basic funkcie ======
def unix_mili_to_utc(unixtime):
    dt = datetime.datetime.fromtimestamp(unixtime / 1000).strftime("%H:%M:%S %d.%m.%Y")
    return dt


def time_now():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


def tradeterprint(*args):
    with open(PIPE_PATH, "w") as terminal1:
        append_file = open("trader_terminal_out.txt", "a")
        for arg in args:
            if args.index(arg) == len(args)-1:
                terminal1.write(str(arg) + "\n")
                append_file.write(str(arg) + "\n")
                # append_file.close()
            else:
                terminal1.write(str(arg) + " ")
                append_file.write(str(arg) + " ")
                # append_file.close()
            time.sleep(0.01)
        append_file.close()


# ====== XTB trading stuph ======
class XtbApi:
    def __init__(self):
        self.ssid = None
        self.status = None
        self.streamclient = None
        self.client = xAPIConnector.APIClient()
        tradeterprint(block_bar)
        tradeterprint("TRADER VERSION:", filename)
        self.initial_ping()  # initial command

    def login(self):
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
            print("DEBUG:", login_response)

            if login_response["status"]:
                tradeterprint(date_now(), time_now(), "\n------------------ Logged into XTB! ------------------")

                xtb_logger.info("%s %s", "TRADER VERSION:", filename)
                out = "------------------ Logged into XTB! ------------------"
                print(out)
                xtb_logger.info(out)

                login_bool = True
                self.ssid = login_response['streamSessionId']
                self.status = login_response["status"]
                self.streamclient = xAPIConnector.APIStreamClient(ssId=self.ssid)

                # print(self.status)
            elif login_response['errorCode'] == "BE118":
                login_bool = True
            else:
                login_bool = False
                print("Login failed!  ", login_response['errorCode'], login_response["errorDescr"])
                xtb_logger.error("%s %s %s", "Login failed!  ",
                                 login_response['errorCode'],
                                 login_response["errorDescr"])
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
                out = "\n------------------ Logged out of XTB! ------------------"
                xtb_logger.info("------------------ Logged out of XTB! ------------------")
                print(out)
                tradeterprint(out)
                logout_bool = True

            else:
                print("Logout failed!  ", logout_response['errorCode'], logout_response["errorDescr"])
                xtb_logger.error("%s %s %s", "Logout failed!  ", logout_response['errorCode'],
                                   logout_response["errorDescr"])
                logout_bool = False
                time.sleep(2)

    # obsolete(?)
    def pinger(self):
        com = {
            "command": "ping"
        }
        while True:
            cmd = self.client.execute(com)
            tradeterprint(time_now(), "Ping:", cmd["status"])
            time.sleep(120)

    def initial_ping(self):
        com = {
            "command": "ping"
        }
        cmd = self.client.execute(com)
        tradeterprint(time_now(), "Initial ping status:", cmd["status"])
        xtb_logger.info("%s %s", "Initial ping status:", cmd["status"])

    def getTradeMargin(self, symbol, volume):
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

    def getProfitCalculation(self, symbol, openprice, closeprice, volume, operation):
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

    def getAllTrades(self):
        time.sleep(.1)
        com = {
            "command": "getTrades",
            "arguments": {
                "openedOnly": True
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

    def getWantedTradesTimeframe(self, wantedSymbol, wantedTimeframe):
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
            xtb_logger.warning("Existing position found - Trade will be denied!")
            return False
        else:
            xtb_logger.info("PASSED - No existing positions with given symbol and timeframe found")
            return True

    def getMarginLevel(self):
        time.sleep(.1)
        com = {
            "command": "getMarginLevel"
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

    def getSymbol(self, symbol):
        time.sleep(.1)
        com = {
            "command": "getSymbol",
            "arguments": {
                "symbol": symbol
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

    def open_buy_position(self, symbol, volume, timeframe, sl, tp):
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
        confirm = self.checkTradeStatus(cmdexe["returnData"]["order"])

        trade_accepted = 3
        if confirm[0] == trade_accepted:
            confirm_bool = True
        else:
            confirm_bool = False

        margin = xtb.getTradeMargin(symbol, volume)
        xtb_logger.warning("%s %s %s %s %s %s %s",
                           "TRYING TO OPEN --BUY-- POSITION:",
                           str(cmdexe["returnData"]["order"]),
                           str(symbol),
                           str(timeframe),
                           str(volume),
                           str(margin),
                           "€")
        tradeterprint("\nTRYING TO OPEN --BUY-- POSITION:",
                      "\nOrder:     ", cmdexe["returnData"]["order"],
                      "\nSymbol:    ", symbol,
                      "\nTimeframe: ", timeframe,
                      "\nVolume:    ", volume, "lots",
                      "\nMargin req:", margin, "€")

        return {"sent": cmdexe["status"],
                "order": cmdexe["returnData"]["order"],
                "opened": confirm_bool,
                "message": confirm[1]}

    def open_sell_position(self, symbol, volume, timeframe, sl, tp):
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
        confirm = self.checkTradeStatus(cmd["returnData"]["order"])
        if confirm[0] == 3:
            confirm_bool = True
        else:
            confirm_bool = False
        margin = xtb.getTradeMargin(symbol, volume)
        tradeterprint("\nTRYING TO OPEN -SELL- POSITION:", "\nSymbol:    ", symbol, "\nOrder: ", cmd["returnData"]["order"],
                      "\nVolume:    ", volume, "lots", "\nMargin req:", margin, "€", "\nTimeframe: ", timeframe)
        return {"sent": cmd["status"], "order": cmd["returnData"]["order"], "opened": confirm_bool,
                "message": confirm[1]}

    def modify_position_add_trail_sl(self, symbol, volume, ordernum, trailstop):
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
        confirm = self.checkTradeStatus(cmd["returnData"]["order"])
        if confirm[0] == 3:
            confirm_bool = True
        else:
            confirm_bool = False
        return {"sent": cmd["status"], "order": cmd["returnData"]["order"], "modified": confirm_bool,
                "message": confirm[1]}

    def checkTradeStatus(self, ordernumber):
        time.sleep(.1)
        com = {
            "command": "tradeTransactionStatus",
            "arguments": {
                "order": ordernumber
            }
        }
        cmd = self.client.execute(com)
        return [cmd["returnData"]["requestStatus"], cmd["returnData"]["message"]]

    def trailing_stoploss(self):
        alltrades = self.getAllTrades()

        for trade in alltrades:
            timeframe = trade["customComment"]
            open_price = trade["open_price"]

            # standard US500 1h wavebreak: 12 pips takeprofit(trailing stoploss)
            if trade["symbol"] == "US500" and timeframe == "1h":
                symbol_specs = self.getSymbol("US500")
                bidprice = symbol_specs["bid"]

                if open_price + 12 <= bidprice:
                    offset = 2  # TODO: asi to bude málo!!!!!!!!!!!!
                    modify = self.modify_position_add_trail_sl(ordernum=trade["order"], trailstop=offset * 10,
                                                               volume=trade["volume"], symbol=trade["symbol"])
                    tradeterprint("trailSL method:", modify["order"], trade["symbol"], "- MODIFIED:", modify["modified"],
                                  "   Message:", modify["message"])
                else:
                    tradeterprint("trailSL method:", trade["order"], trade["symbol"],
                                  "- profit not high enough for trailing stoploss!")

            # TODO:standard VIX ? pips takeprofit(trailing stoploss)
            elif trade["symbol"] == "VIX":
                pass
            else:
                pass

    def sl_tp_buy_atrb(self, symbol, timeframe):
        xtb_logger.info("Getting SL/TP data from database - ATRb")

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

        symbol_info = xtb.getSymbol(symbol)
        ask = symbol_info["ask"]
        # TODO prerobene zaokruhlovanie z 2 na 1, neviem ci to nerobilo problem
        #  pri us500, ze cisla boli s 2 desatinnymi misetami, ale to je pre VIX ok,
        #  tak nvm ale to by asi nerobilo ten problem
        tp = round((ask + tp_val), 1)
        sl = round((ask - sl_val), 1)
        return sl, tp

    def sl_tp_buy_override(self, symbol, timeframe):
        symbol_specs = self.getSymbol(symbol)
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


def novy_buy(symbol, timeframe, condition):
    lots = None
    trade_bools = {"Non-duplicate symbol and tf": False,
                   "Lots OK": False,
                   "Margin OK": False,
                   "Volume OK": False,
                   "Max num of trades NOT reached": False}

    xtb_logger.info("*TRADE PREPARATIONS STARTED*")

    account_properties = xtb.getMarginLevel()
    balance = account_properties["balance"]
    margin_actual = account_properties["margin"]
    currency = account_properties["currency"]
    credit = account_properties["credit"]
    equity = account_properties["equity"]
    margin_free = account_properties["margin_free"]
    margin_level = account_properties["margin_level"]
    print(margin_actual, "Eur", margin_level, "%")


    """Zisti ci uz je na tomto symbole otvorena pozicia na rovnakom timeframe ======================================="""
    # Non-duplicate symbol and tf
    xtb_logger.info("%s %s %s", "Checking for existing positions:", symbol, timeframe)
    openedtrades = xtb.getWantedTradesTimeframe(wantedSymbol=symbol, wantedTimeframe=timeframe)
    trade_bools.update({"Non-duplicate symbol and tf": openedtrades})

    # maximalna marza na jeden obchod podla zadaneho % v basic configu
    # zobere volnu marzu z uctu a vydeli ju 100, to je 1% z volnej marze a to vynasobi koeficientom v basic configu
    # Eur
    max_margin_for_new_trade = round((margin_free / 100) * max_percent_from_free_margin, 2)

    # marza potrebna pre defaultny objem v basic configu (0.01) - najnizsia mozna marza
    # Eur
    margin_for_def_volume = xtb.getTradeMargin(symbol, default_lots)  # margin for default lots 0.01
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
    xtb_logger.info("Calculating available volume size")

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
        tradeterprint(out)
        xtb_logger.error(out)
        trade_bools.update({"Lots OK": False})
    xtb_logger.info("%s %s", "Available volume:", lots)
    time.sleep(.1)


    """zisti ci je margin viac ako 50-60% z equity/balance - volnych prostriedkov ==================================="""
    # Margin OK
    if equity < balance:
        calculating_mode = equity
        fifty_percent = round(equity * 0.5, 2)
        sixty_percent = round(equity * 0.6, 2)
        xtb_logger.info("Checking margin - 50/60% rule - calculating from EQUITY")
        tradeterprint("\nCURRENT ACCOUNT STATS: calculating from EQUITY",
                      "\nBalance:        ", balance, "€",
                      "\nEquity:         ", equity, "€",
                      "\nActual margin:  ", margin_actual, "€",
                      "\n50% from equity:", fifty_percent, "€",
                      "\n60% from equity:", sixty_percent, "€")

    else:
        calculating_mode = balance
        fifty_percent = round(balance * 0.5, 2)
        sixty_percent = round(balance * 0.6, 2)
        xtb_logger.info("Checking margin - 50/60% rule - calculating from BALANCE")
        tradeterprint("\nCURRENT ACCOUNT STATS: calculating with BALANCE",
                      "\nBalance:         ", balance, "€",
                      "\nEquity:          ", equity, "€",
                      "\nActual margin:   ", margin_actual, "€",
                      "\n50% from balance:", fifty_percent, "€",
                      "\n60% from balance:", sixty_percent, "€")

    # ak je aktualna marza na otvorenych obchodoch viac ako 50% alebo 60%, tak zakaze trade
    if (margin_actual > fifty_percent or
            margin_actual > sixty_percent):
        trade_bools.update({"Margin OK": False})
        xtb_logger.warning("Margin is too high - Trade will be denied!")
    # ak je aktualna marza menej ako 50% z volnych prostriedkov, povoli trade
    else:
        trade_bools.update({"Margin OK": True})
        xtb_logger.info("PASSED")


    """Zisti aky bude celkovy margin na ucte po otvoreni tejto pozicie =============================================="""
    # Volume OK
    # Ak by bol vyratany objem moc vysoky a margin by potom presahovala 50/60% tak sa to bude snazit
    # znizit objem az na 0.01 lotu, otvori to najvyssi mozny, tak aby to nepresahovalo 50/60%.
    # Ak nemoze byt ani 0.01, tak to da false a trade je odmietnuty
    xtb_logger.info("Checking margin size after opened trade - 50/60% rule")
    margin_needed_for_new_trade = xtb.getTradeMargin(symbol, lots)
    if ((margin_actual + margin_needed_for_new_trade) > fifty_percent or
            (margin_actual + margin_needed_for_new_trade) > sixty_percent):

        while lots != 0.01:
            lots = round(lots - 0.01, 2)
            margin_needed_for_new_trade = xtb.getTradeMargin(symbol, lots)

            if ((margin_actual + margin_needed_for_new_trade) > fifty_percent or
                    (margin_actual + margin_needed_for_new_trade) > sixty_percent):
                confirm_volume = False
                trade_bools.update({"Volume OK": confirm_volume})
                xtb_logger.warning("Margin would be too high - Trade will be denied!")
            else:
                confirm_volume = True
                trade_bools.update({"Volume OK": confirm_volume})
                xtb_logger.info("PASSED")
            time.sleep(.1)

    else:
        confirm_volume = True
        trade_bools.update({"Volume OK": confirm_volume})
        xtb_logger.info("PASSED")


    """Skontroluje pocet aktualne otvorenych pozicii ================================================================"""
    # Max num of trades NOT reached"
    xtb_logger.info("Checking number of opened positions")
    num_of_opened_trades = xtb.getAllTrades()
    if len(num_of_opened_trades) < max_positions_allowed:
        trade_bools.update({"Max num of trades NOT reached": True})
        xtb_logger.info("PASSED")
    else:
        trade_bools.update({"Max num of trades NOT reached": False})
        xtb_logger.warning("Too many opened trades - Trade will be denied!")

    tradeterprint("\n\nTRADE BOOLS:")
    xtb_logger.info("TRADE BOOLS:")
    for i in trade_bools:
        tradeterprint(trade_bools[i], "-", i)
        if trade_bools[i]:
            xtb_logger.info("%s %s %s", trade_bools[i], "-", i)
        else:
            xtb_logger.warning("%s %s %s", trade_bools[i], "-", i)


    """Zhrnutie a otvorenie/zamietnutie pozicie ====================================================================="""
    if False not in trade_bools.values():
        if symbol == "US500" and timeframe == "1h":
            data = xtb.sl_tp_buy_override(symbol=symbol, timeframe=timeframe)
        else:
            data = xtb.sl_tp_buy_atrb(symbol=symbol, timeframe=timeframe)
        sl = data[0]
        tp = data[1]
        # print("sl", sl, "tp", tp)


        # ======================================================
        transaction = xtb.open_buy_position(symbol, volume=lots, timeframe=timeframe, sl=sl, tp=tp)
        # ======================================================

        tradeterprint("\nTRANSACTION STATS:",
                      "\nOrder number:", transaction["order"],
                      "\nOrder sent:  ", transaction["sent"],
                      "\nOrder opened:", transaction["opened"],
                      "\nReason:      ", transaction["message"])

        if transaction["opened"]:
            xtb_logger.warning("%s %s", "TRADE OPENED! -", transaction["order"])
            tradeterprint("\nTRADE OPENED! -", transaction["order"])
        else:
            xtb_logger.error("%s %s %s",
                               "TRADE REJECTED! -",
                               transaction["order"],
                               transaction["message"])
            tradeterprint("\nTRADE REJECTED! -",
                          transaction["order"],
                          transaction["message"])

        qpart1 = "insert into fri_trade.positions "
        qpart2 = "(date, time, ordernum, symbol, ordertype, lots, conditionTriggered, timeframe, sent, opened, reason) "
        qpart3 = "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        q = qpart1 + qpart2 + qpart3
        fri_trade_cursor.execute(q, (date_now(),
                                     time_now(),
                                     str(transaction["order"]),
                                     symbol,
                                     "buy",
                                     lots,
                                     condition,
                                     timeframe,
                                     str(transaction["sent"]),
                                     str(transaction["opened"]),
                                     str(transaction["message"])))
    else:
        out = "!!! Trade bools not satisfied - TRADE DENIED !!!"
        tradeterprint("\n", out)
        xtb_logger.error(out)

    xtb.logout()


def breakfinder(values, symbol, timeframe):
    C = new_value = values[0]
    B = previous_value = values[1]
    A = prev_previous_value = values[2]
    # print(new_value, previous_value, prev_previous_value)

    buy = False
    condition = None

    """HLAVNÁ BUY PODMIENKA        if C > B and B < A and C < 0: ------------------------- BUY!"""
    # klasicky zlom čer. vlny
    if previous_value < new_value < 0 and previous_value < prev_previous_value:
        buy = True
        condition = "main"

    # zlom červenej s prierazom novej hodnoty do zelenej vlny
    elif C > B < A < 0 < C and B < 0:
        buy = True
        condition = "greenC"

    # zlom po dvoch rovnakých červených hodnotách - nebude tu problém?????????????????????
    # elif A == B and B < C < 0:
    #     buy = True
    #     condition = "doubleRed"

    # obnovenie zelenej vlny
    # TODO asi zmazat?
    elif C > B and B < A and C > 0:
        buy = True
        condition = "greenRecover"

    if buy is True and condition is not None:
        print("TEST FUNKCNOSTI 1 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        # ==============================================================================================================
        buy_thread = threading.Thread(target=novy_buy,
                                      name="trade_buy_thread",
                                      args=(symbol, timeframe, condition,))
        # ==============================================================================================================
        print("TEST FUNKCNOSTI 2 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        xtb.login()
        print("TEST FUNKCNOSTI 3 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        buy_thread.start()
        print("TEST FUNKCNOSTI 4 $$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")

    else:
        out = "*BREAKFINDER* {symbol} {tf} - waiting for trade opportunity".format(symbol=symbol, tf=timeframe)
        print(out)
        xtb_logger.info(out)


def main():
    while True:
        print("\n===", time_now(), date_now(), "===")

        for item in active_symbols:
            for symbol in item.keys():

                for timeframes_list in item.values():
                    for timeframe in timeframes_list:
                        qpart1 = "select id, key_value, processed from fri_trade."
                        qpart2 = "_"
                        qpart3 = " order by id desc limit 3"
                        q = qpart1 + symbol + qpart2 + timeframe + qpart3

                        fri_trade_cursor.execute(q)
                        result = fri_trade_cursor.fetchall()

                        try:
                            newest_id = result[0][0]
                            newest_id_status = result[0][2]
                            values = [float(result[0][1]), float(result[1][1]), float(result[2][1])]

                            if not newest_id_status:
                                print("*MAIN*", symbol, timeframe, "- New value found!")
                                xtb_logger.info("%s %s %s %s", "*MAIN*", symbol, timeframe, "- New value found!")

                                # ======================================================================================
                                breakfinder(values, symbol, timeframe)
                                # ======================================================================================

                                qpart1 = "update fri_trade."
                                qpart2 = "_"
                                qpart3 = " set processed = True where id = "
                                q = qpart1 + symbol + qpart2 + timeframe + qpart3 + str(newest_id)
                                fri_trade_cursor.execute(q)

                        except IndexError:
                            # print(symbol, timeframe, "- Not enough values in database")
                            pass
        time.sleep(1)
        print("Testujem %%%%%%%%%%%%%%%%%%%%%")


""" --------- MAIN --------- """
ping_thread = threading.Thread(target=xtb.pinger, name="ping_thread")
ping_thread.start()

main_loop = threading.Thread(target=main, name="main_loop_thread")
# main()
main_loop.start()

""" --------- TEST COMMANDS --------- """
# xtb.command()
# print(xtb.getProfitCalculation("VIX", 29, 21.98, 0.01, 0))
# xtb.stoploss_calc_buy("VIX", 0.02, "1h")
# xtb.trailing_stoploss()
# xtb.modify_position(symbol="US500", ordernum=354154316, volume=0.03, trailstop=100*10)
# xtb.open_buy_position("US500", 0.01, "4h", 4000.0, None)
# xtb.getTradeMargin(symbol="US100", volume=1)
# xtb.getProfitCalculation(symbol="US500", openprice=4400.0, closeprice=4500.0, volume=0.1, operation=0)
# xtb.stoploss_calc_buy("US500", 0.01, "1h")


""" --------- BUY TRADE COMMAND --------- """
# xtb.login()
# novy_buy(symbol="VIX", timeframe="1h", condition="test")
# xtb.sl_tp_buy_atrb("VIX", 0.01, "1h")
# xtb.sl_tp_buy_override("US500", "1h")

# TODO: ----------------------------------------------------------------------------------------------------------------
# TODO: do loggera pridat info co trader prave robi - vybera stoploss z db, prepocitava nvm čo a tak podobne


# TODO: ked to najde novy value tak akoby prestane bezat, prestane vypisovat cas. na us500 1h je tam vynechana
#  hodnota 10:59 a 9.59 sa zastavil xtb trader, neviem aku to ma spojitost.. mal by bezat furt ked je tam while true
#  Ono sa to akoby zacyklí v pass alebo tak nejak lebo nespadne to, bezi to ale nic to neprintuje ani nerobi, nic
#  pozriet vyznacene while, ci tam niekde neni pass, ktory by to mohol sposobovat, ze sa to tam kdesi strati

# TODO taka mala poznamka, mozno, ze to robi nejake problemy v spojitosti s threadingom.. lebo buy sa robi cez
#  samostatny thread tak mozno sa tomu nieco na tom nepaci

# TODO mozno pridat nejaku vec, ze na zaciatku to vyberie 3 posledne hodnoty a ak nie su spracovane, tak ich nespracuje
#  ale oznaci ako spracovane.. aby to neotvaralo pozicie hned po spusteni kvoli starym hodnotam v DB

# TODO test funkcnosti 3 neuspesny! Vyzera to na nejaky problem s xtb loginom, tam je to blokovane akoby