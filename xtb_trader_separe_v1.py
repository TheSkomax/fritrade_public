import datetime
import math
import os
import dotenv
import threading
import time
from datetime import date
from datetime import datetime
from subprocess import Popen
import mysql.connector
import xAPIConnector
import logging


# ====== credentials ======
# userId je cislo uctu - demo alebo real
dotenv.load_dotenv(".env")

xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

# ====== basic config ======
max_lots_override = False
max_positions = 10
default_lots = 0.01  # ak je max_lots_override zapnute, bude otvarat len tieto loty


# ====== symbols ======
active_symbols = [
    {"US500": ["1h", "2h", "3h", "4h", "D", "W", "M"]
     },
    {"VIX": ["1h", "2h", "3h", "4h", "D", "W"]
     },
]


# ====== terminal config ======
PIPE_PATH = "/tmp/trader"
if not os.path.exists(PIPE_PATH):
    os.mkfifo(PIPE_PATH)
Popen(['xterm', '-fa', 'Monospace', '-fs', '12', '-e', 'tail -f %s' % PIPE_PATH])


# ====== mysql - fri_trade schema ======
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade", autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


# ====== Logging ======
xtb_logger = logging.getLogger("xtb_logger")
xtb_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("xtb_trader.log")
file_handler.setFormatter(log_formatter)
xtb_logger.addHandler(file_handler)


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
        append_file = open("trader_terminal_log.txt", "a")
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
        # self.login()

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
            # login_response = self.client.execute(xAPIConnector.loginCommand(userId=userId, password=password))
            login_response = self.client.execute(login_cmnd)

            if login_response["status"]:
                tradeterprint(date_now(), time_now(), "\n---- Logged into XTB! ----")
                xtb_logger.info("---- Logged into XTB! ----")
                login_bool = True
                self.ssid = login_response['streamSessionId']
                self.status = login_response["status"]
                self.streamclient = xAPIConnector.APIStreamClient(ssId=self.ssid)

                # print(self.status)
            elif login_response['errorCode'] == "BE118":
                login_bool = True
            else:
                print("Login failed!  ", login_response['errorCode'], login_response["errorDescr"])
                xtb_logger.warning("%s %s %s", "Login failed!  ", login_response['errorCode'],
                                   login_response["errorDescr"])
                login_bool = False
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
                print("Logged out!aaaaaaaaaaaaaaaaaaa")
                xtb_logger.info("Logged out!bbbbbbbbbbbbbb")
                logout_bool = True
            else:
                print("Logout failed!  ", logout_response['errorCode'], logout_response["errorDescr"])
                xtb_logger.warning("%s %s %s", "Logout failed!  ", logout_response['errorCode'],
                                   logout_response["errorDescr"])
                logout_bool = False
                time.sleep(2)

    def pinger(self):
        com = {
            "command": "ping"
        }
        while True:
            cmd = self.client.execute(com)
            tradeterprint("Ping:", cmd["status"])
            time.sleep(120)

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
            return False
        else:
            return True

        # symbol = cmd["returnData"][0]["symbol"]
        # timeframe = cmd["returnData"][0]["customComment"]
        # opentime = self.unix_mili_to_utc(cmd["returnData"][0]["open_time"])
        # return [symbol, timeframe, opentime]

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
        trade_trans_info = {
            "cmd": 0,
            "symbol": symbol,
            "customComment": timeframe,
            "volume": volume,
            "sl": sl,
            "tp": tp,
            "type": 0,
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
        tradeterprint("\nTRYING TO OPEN -BUY- POSITION:", "\nSymbol:    ", symbol, "\nTimeframe: ", timeframe,
                 "\nOrder:     ", cmd["returnData"]["order"],
                 "\nVolume:    ", volume, "lots", "\nMargin req:", margin, "€")
        return {"sent": cmd["status"], "order": cmd["returnData"]["order"], "opened": confirm_bool,
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
            "sl": 99.0,  # placeholder hodnota, podstatny je offset/trailstop, ten prepise sl takze sl je nepodstatny
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

    def stoploss_calc_buy(self, symbol, volume, timeframe):
        # verzia 1 alebo 3% z uctu (equity)
        account_indicators = self.getMarginLevel()
        balance = account_indicators["balance"]
        equity = account_indicators["equity"]

        if equity < balance:
            equity = equity
        else:
            equity = balance

        one_perc_from_equity = round(equity / 100, 2)
        two_perc_from_equity = round(one_perc_from_equity * 2, 2)
        three_perc_from_equity = round(one_perc_from_equity * 3, 2)

        if symbol == "US500":
            symbol_specs = self.getSymbol(symbol)
            ask = symbol_specs["ask"]
            one_pip_loss = self.getProfitCalculation(symbol, ask, ask - 1, volume, 0)
            # print(equity, one_perc_from_equity)

            # one_perc_loss = round(one_perc_from_equity / one_pip_loss, 2)
            # three_perc_loss = round(three_perc_from_equity / one_pip_loss, 2)
            one_perc_loss_pips = round(one_perc_from_equity / one_pip_loss, 1)
            three_perc_loss_pips = round(three_perc_from_equity / one_pip_loss, 1)

        elif symbol == "VIX":
            symbol_specs = self.getSymbol(symbol)
            ask = symbol_specs["ask"]
            one_pip_loss = self.getProfitCalculation(symbol, ask, ask - 0.01, volume, 0)
            # print(equity, one_perc_from_equity)

            # one_perc_loss = round(one_perc_from_equity / (one_pip_loss * 10), 2)
            # three_perc_loss = round(three_perc_from_equity / one_pip_loss, 2)
            one_perc_loss_pips = round(round(one_perc_from_equity / one_pip_loss, 2) / 100, 2)
            three_perc_loss_pips = round(round(three_perc_from_equity / one_pip_loss, 2) / 100, 2)

        elif symbol == "US100":
            symbol_specs = self.getSymbol(symbol)
            ask = symbol_specs["ask"]
            one_pip_loss = self.getProfitCalculation(symbol, ask, ask - 1, volume, 0)
            # print(equity, one_perc_from_equity)

            # one_perc_loss = round(one_perc_from_equity / one_pip_loss, 2)
            # three_perc_loss = round(three_perc_from_equity / one_pip_loss, 2)
            one_perc_loss_pips = round(one_perc_from_equity / one_pip_loss, 1)
            three_perc_loss_pips = round(three_perc_from_equity / one_pip_loss, 1)

        else:
            tradeterprint("!!!!!!! Stoploss pre tento symbol neni specificky naprogramovany !!!!!!!")
            tradeterprint(
                "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Možná chybná hodnota SL na tejto pozícii !!!!!!!!!!!!!!!!!!!!!!!!!!§")
            symbol_specs = self.getSymbol(symbol)
            ask = symbol_specs["ask"]
            one_pip_loss = self.getProfitCalculation(symbol, ask, ask - 1, volume, 0)
            # print(equity, one_perc_from_equity)

            # one_perc_loss = round(one_perc_from_equity / one_pip_loss, 2)
            # three_perc_loss = round(three_perc_from_equity / one_pip_loss, 2)
            one_perc_loss_pips = round(one_perc_from_equity / one_pip_loss, 1)
            three_perc_loss_pips = round(three_perc_from_equity / one_pip_loss, 1)


        tradeterprint("\nSTOPLOSS CALCULATION FOR SYMBOL:", symbol, "\nAsk price:          ", ask,
              "\nVolume:             ", volume, "lots",
              "\nOne pip loss:       ", one_pip_loss, "€", "\n1% loss from equity:", one_perc_from_equity, "€",
              "\n3% loss from equity:", three_perc_from_equity, "€", "\n1% loss in pips:    ", one_perc_loss_pips,
              "pips", "\n3% loss in pips:    ", three_perc_loss_pips, "pips")

        # plus je tam lebo to pricitava zapornu hodnotu, preto vyjde SL cena nizsia a tak to ma byt
        if volume > 0.01:
            result = round(ask + three_perc_loss_pips, 2)
        else:
            result = round(ask + one_perc_loss_pips, 2)

        if symbol == "VIX":  # TODO: ak je to vix, tak tam musi byt vacsi SL inak to nema zmysel ak je tam len 1%
            result = round(ask + one_perc_loss_pips, 2)


        # ukradnute z takeprofit_calc_buy - berie SL hodnoty z databazy
        symbol_specs = self.getSymbol(symbol)
        ask = symbol_specs["ask"]
        try:
            if symbol == "US500" or symbol == "VIX":
                qpart1 = 'select sl from tradeData where symbol = "'
                qpart2 = '" and timeframe = "'
                qpart3 = '"'
                q = qpart1 + symbol + qpart2 + timeframe + qpart3
                fri_trade_cursor.execute(q)
                pips = fri_trade_cursor.fetchone()[0]
                result = ask + pips  # pips je zaporna hodnota, preto +
                print(pips, ask)
                tradeterprint("\nStoploss pips in DB:", result)
                # return result

        except TypeError as e:
            tradeterprint("stoploss_calc_buy - CHYBA! {sym} Pravdepodobne bol zle "
                          "zadaný timeframe alebo daná hodnota nie je v DB".format(sym=symbol))
            tradeterprint(e)

        # print("SL:", result)
        return result

    def takeprofit_calc_buy(self, symbol, volume, timeframe):
        symbol_specs = self.getSymbol(symbol)
        ask = symbol_specs["ask"]
        try:
            if symbol == "US500" or symbol == "VIX":
                qpart1 = 'select sl from tradeData where symbol = "'
                qpart2 = '" and timeframe = "'
                qpart3 = '"'
                q = qpart1 + symbol + qpart2 + timeframe + qpart3
                fri_trade_cursor.execute(q)
                pips = fri_trade_cursor.fetchone()[0]
                tp = ask + pips
                # print(pips, ask)
                tradeterprint("\nTakeprofit pips in DB:", tp)
                return tp

        except TypeError as e:
            tradeterprint("takeprofit_calc - CHYBA! {sym} Pravdepodobne bol zle "
                          "zadaný timeframe alebo daná hodnota nie je v DB".format(sym=symbol))
            tradeterprint(e)

    # TODO: pridat tam takeprofit lebo ked tam je teraz len trSL tak po upraveni pozicie to zmaze TP, ktory na nej bol
    # TODO: nech si to nejako zisti aky tam je a nechat ho tam
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


    """
    def command(self):
        com = {
            "command": "getTrades",
            "arguments": {
                "openedOnly": True
            }
        }
        cmd = self.client.execute(com)
        # print(cmd["returnData"])
    """


xtb = XtbApi()


# ====== buy ======
def trader_buy(symbol, timeframe, condition):
    trade_bools = {"Non-duplicate symbol and tf": False, "Lots OK": False, "Margin OK": False, "Volume OK": False,
                   "Max num of trades NOT reached": False}
    lots = None

    """Zisti ci uz je na tomto symbole otvorena pozicia na rovnakom timeframe"""
    openedtrades = xtb.getWantedTradesTimeframe(wantedSymbol=symbol, wantedTimeframe=timeframe)
    trade_bools.update({"Non-duplicate symbol and tf": openedtrades})
    # if openedtrades:
    #     trade_bools.append(True)
    # else:
    #     trade_bools.append(False)

    """zisti vysku volnej marze, max marzu na novy trade atd"""
    account_indicators = xtb.getMarginLevel()
    max_percent_from_free_margin = 7
    # max x % from free margin for one trade
    max_margin_for_new_trade = round((account_indicators["margin_free"] / 100) * max_percent_from_free_margin, 2)
    def_lots_margin = xtb.getTradeMargin(symbol, default_lots)  # margin for default lots 0.01
    max_lots = math.trunc(max_margin_for_new_trade / def_lots_margin) / 100  # max volume in lots for one trade
    max_lots_margin = xtb.getTradeMargin(symbol, max_lots)  # max margin for one trade based on max_lots

    # terprint(max_margin_for_new_trade > max_lots_margin)
    tradeterprint("\n==============================", date_now(), time_now(),
                  "==============================\n",
                  "max_margin_for_new_trade", max_margin_for_new_trade, "\n", "def_lots_margin", def_lots_margin, "\n",
                  "max_lots", max_lots, "\n", "max_lots_margin", max_lots_margin)

    # TODO: ????????????
    if max_lots_override:
        lots = default_lots
        trade_bools.update({"Lots OK": True})
    elif max_lots > default_lots:
        lots = max_lots
        trade_bools.update({"Lots OK": True})
    elif def_lots_margin >= max_margin_for_new_trade:
        lots = default_lots
        trade_bools.update({"Lots OK": True})

    else:
        tradeterprint("funkcia trader - TU SA NIECO DOJEBALO, TU BY SME SA NEMALI DOSTAT ASI - NEDOSTATOK MARZE???????????????")
        trade_bools.update({"Lots OK": False})
    time.sleep(.1)

    """zisti ci je margin viac ako 50-60% z equity/balance - volnych prostriedkov"""
    equity = account_indicators["equity"]
    margin = account_indicators["margin"]
    balance = account_indicators["balance"]

    if equity < balance:
        fifty_percent_from_equity = round(equity * 0.5, 2)
        sixty_percent_from_equity = round(equity * 0.6, 2)
        tradeterprint("\nCURRENT ACCOUNT STATS: calculating from equity", "\nBalance:        ", balance, "€",
                      "\nEquity:         ", equity, "€", "\nMargin:         ", margin, "€", "\n50% from equity:",
                      fifty_percent_from_equity, "€", "\n60% from equity:", sixty_percent_from_equity, "€")
    else:
        fifty_percent_from_equity = round(balance * 0.5, 2)
        sixty_percent_from_equity = round(balance * 0.6, 2)
        tradeterprint("\nCURRENT ACCOUNT STATS: calculating with balance", "\nBalance:        ", balance, "€",
                      "\nEquity:         ", equity, "€", "\nMargin:         ", margin, "€", "\n50% from balance:",
                      fifty_percent_from_equity, "€", "\n60% from balance:", sixty_percent_from_equity, "€")

    # aktualny margin
    if (margin > fifty_percent_from_equity or
            margin > sixty_percent_from_equity):
        trade_bools.update({"Margin OK": False})
    else:
        trade_bools.update({"Margin OK": True})

    # predpokladany celkovy margin po novom trade
    # confirm_volume_bool = False
    expected_margin_for_new_trade = xtb.getTradeMargin(symbol, lots)

    if ((margin + expected_margin_for_new_trade) > fifty_percent_from_equity or
            (margin + expected_margin_for_new_trade) > sixty_percent_from_equity):
        while lots != 0.01:
            lots = round(lots - 0.01, 2)
            expected_margin_for_new_trade = xtb.getTradeMargin(symbol, lots)
            if ((margin + expected_margin_for_new_trade) > fifty_percent_from_equity or
                    (margin + expected_margin_for_new_trade) > sixty_percent_from_equity):
                confirm_volume_bool = False
                trade_bools.update({"Volume OK": confirm_volume_bool})
                time.sleep(.1)
            else:
                confirm_volume_bool = True
                trade_bools.update({"Volume OK": confirm_volume_bool})
    else:
        confirm_volume_bool = True
        trade_bools.update({"Volume OK": confirm_volume_bool})

    # kontrola max poctu otvorenych pozicii
    num_of_opened_trades = xtb.getAllTrades()
    if len(num_of_opened_trades) < max_positions:
        trade_bools.update({"Max num of trades NOT reached": True})
    else:
        trade_bools.update({"Max num of trades NOT reached": False})

    tradeterprint("\nTrade bools:", trade_bools)

    if False not in trade_bools.values():
        sl = xtb.stoploss_calc_buy(symbol, lots, timeframe)
        tp = xtb.takeprofit_calc_buy(symbol, lots, timeframe)
        print("sl", sl,"tp", tp)
        transaction = xtb.open_buy_position(symbol, volume=lots, timeframe=timeframe, sl=sl, tp=tp)

        tradeterprint("\nTRANSACTION STATS:", "\nOrder sent:  ", transaction["sent"],
                      "\nOrder opened:", transaction["opened"], "\nOrder number:", transaction["order"],
                      "\nReason:      ", transaction["message"])

        qpart1 = "insert into fri_trade.positions "
        qpart2 = "(date, time, ordernum, symbol, ordertype, lots, conditionTriggered, timeframe, sent, opened, reason) "
        qpart3 = "VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
        q = qpart1 + qpart2 + qpart3
        fri_trade_cursor.execute(q, (date_now(), time_now(), str(transaction["order"]), symbol, "buy", condition, timeframe,
                                     str(transaction["sent"]), str(transaction["opened"]), str(transaction["message"])))
    else:
        tradeterprint("Trade bools not satisfied - trade DENIED!")
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
    elif C > B and B < A and C > 0:
        buy = True
        condition = "greenRecover"

    # ostatné podmienky na print
    # if C > B and B < A and C < 0: nič - červená sa zlomila
    # elif 0 > C > B > A:
    #     self.red_wave_rising()
    # # nič - začína zelená vlna
    # elif C > B > A and C > 0:
    #     self.green_wave_starting()
    # # nič - zlomila sa zelená
    # elif B > C > 0 and A < B:
    #     self.green_wave_break()
    # # nič - začala sa červená
    # elif C < B < A and C < 0:
    #     self.red_wave_starting()
    # # nič - klesajúca červená
    # elif C < B < A and C < 0:
    #     self.red_wave_falling()

    if buy and condition is not None:
        # TODO: xtb trader buy s condition ako argument nech sa to zapise do db, ze ktora podmienka spustila buy
        # TODO: a na ktorom timeframe bol zlom - UZ HOTOVO????

        # print("Červená vlna sa zlomila! ------------- {symbol} {tf} BUY!".format(symbol=symbol, tf=timeframe))
        # soundfile = "/home/michal/PycharmProjects/trade/trade_beep.mp3"
        # os.system("mpg123 -q " + soundfile)

        # trader_buy(symbol=symbol, timeframe=timeframe)

        buy_thread = threading.Thread(target=trader_buy, name="trader_buy_thread", args=(symbol, timeframe, condition,))
        xtb.login()
        buy_thread.start()

    else:
        out = "(breakfinder) {symbol} {tf} - waiting for trade opportunity".format(symbol=symbol, tf=timeframe)
        print(out)
        xtb_logger.info(out)


def main():
    while True:
        print("===", time_now(), date_now(), "===")
        # print("active symbols:", active_symbols)
        for item in active_symbols:
            for symbol in item.keys():
                # print("-----", symbol, "-----")

                for timeframes_list in item.values():
                    for timeframe in timeframes_list:
                        # print(timeframe)
                        qpart1 = "select id, key_value, processed from fri_trade."
                        qpart2 = "_"
                        qpart3 = " order by id desc limit 3"
                        q = qpart1 + symbol + qpart2 + timeframe + qpart3
                        # q = "update fri_trade.US500_1m set processed = True where key_value = 1.2;"

                        fri_trade_cursor.execute(q)
                        result = fri_trade_cursor.fetchall()
                        # print(result, len(result))

                        try:
                            newest_id = result[0][0]
                            newest_id_status = result[0][2]
                            values = [float(result[0][1]), float(result[1][1]), float(result[2][1])]
                            # print(values)
                            if not newest_id_status:
                                print(symbol, timeframe, "- New value found!")
                                xtb_logger.info("%s %s %s", symbol, timeframe, "- New value found!")

                                breakfinder(values, symbol, timeframe)

                                qpart1 = "update fri_trade."
                                qpart2 = "_"
                                qpart3 = " set processed = True where id = "
                                q = qpart1 + symbol + qpart2 + timeframe + qpart3 + str(newest_id)
                                fri_trade_cursor.execute(q)

                        except IndexError:
                            # print(symbol, timeframe, "- Not enough values in database")
                            pass
        time.sleep(1)


""" --------- MAIN --------- """
# ping_thread = threading.Thread(target=xtb.pinger, name="ping_thread")
# ping_thread.start()
# main()


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
xtb.login()
trader_buy(symbol="VIX", timeframe="15m", condition="test")


# TODO: !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
# TODO: prerobit take profity a stop lossy na to nech si to vybera atrb hodnoty z databazy od key values!
# TODO: do loggera pridat info co trader prave robi - vybera stoploss z db, prepocitava nvm čo a tak podobne
