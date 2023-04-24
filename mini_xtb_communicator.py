import datetime
import os
import time
from datetime import date, datetime
import mysql.connector
import mini_xAPIConnector
import logging
from sys import argv
import os
import dotenv

# ====== credentials ======
dotenv.load_dotenv(".env")

xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]


# ====== basic config ======
filename = os.path.basename(__file__)[:-3]

# max_positions_allowed = 6
# max_percent_from_free_margin = 7
# max_volume_per_trade = 0.05


# ====== mysql - fri_trade schema ======
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


# ====== Logging ======
mini_logger = logging.getLogger("mini_xtb_trader_logger")
mini_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_mini_xtb_communicator.log")
file_handler.setFormatter(log_formatter)
mini_logger.addHandler(file_handler)


# ====== basic funkcie ======
def time_now():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


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
        self.client = mini_xAPIConnector.APIClient()

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
                out = "------------------------ Mini communicator logged into XTB! ------------------------"
                print(out)
                mini_logger.info(out)

                login_bool = True
                self.ssid = login_response['streamSessionId']
                self.status = login_response["status"]
                self.streamclient = mini_xAPIConnector.APIStreamClient(ssId=self.ssid)

            elif login_response['errorCode'] == "BE118":
                login_bool = True

            else:
                login_bool = False
                out = "Login failed!   {code} - {desc}".format(code=login_response['errorCode'],
                                                               desc=login_response["errorDescr"])
                print(out)
                mini_logger.error(out)
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
                out = "------------------------ Mini communicator logged out of XTB! ------------------------"
                print(f"\n{out}")
                mini_logger.info(out)

                logout_bool = True

            else:
                out = "Logout failed!   {code} - {desc}".format(code=logout_response['errorCode'],
                                                                desc=logout_response["errorDescr"])
                print(out)
                mini_logger.error(out)

                logout_bool = False
                time.sleep(2)

    def initial_ping(self):
        com = {
            "command": "ping"
        }
        cmd = self.client.execute(com)
        mini_logger.info("%s %s", "Initial ping status:", cmd["status"])

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
        mini_logger.warning(f"{cmdexe['returnData']['order']} TRYING TO OPEN --BUY-- ORDER: {symbol} {timeframe} {volume} {margin}€")

        return {"sent": cmdexe["status"],
                "order": cmdexe["returnData"]["order"],
                "opened": confirm_bool,
                "message": confirm[1],
                "margin": margin}

    def open_sell_order(self, symbol, volume, timeframe, sl, tp):
        transaction_info = {
            "cmd": 1,
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
        mini_logger.warning(f"{cmdexe['returnData']['order']} TRYING TO OPEN --SELL-- ORDER: {symbol} {timeframe} {volume} {margin}€")

        return {"sent": cmdexe["status"],
                "order": cmdexe["returnData"]["order"],
                "opened": confirm_bool,
                "message": confirm[1],
                "margin": margin}

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

    def sl_tp_override(self, symbol, timeframe, trade_type):
        symbol_specs = self.get_symbol(symbol)
        ask = symbol_specs["ask"]
        bid = symbol_specs["bid"]

        if trade_type == "buy":
            q = 'select sl from tradeData where symbol = "US500" and timeframe = "1h"'
            fri_trade_cursor.execute(q)
            sl_val = fri_trade_cursor.fetchone()[0]
            sl = round((ask + sl_val), 1)  # sl_val je zaporna hodnota, preto +
            # print(f"ask {ask} + sl_val {sl_val} = sl {sl}")

            q = 'select tp from tradeData where symbol = "US500" and timeframe = "1h"'
            fri_trade_cursor.execute(q)
            tp_val = fri_trade_cursor.fetchone()[0]
            tp = round((ask + tp_val), 1)
            # print(f"ask {ask} + tp_val {tp_val} = tp {tp}")

            return sl, tp

        elif trade_type == "sell":
            q = 'select sl from tradeData where symbol = "US500" and timeframe = "1h"'
            fri_trade_cursor.execute(q)
            sl_val = fri_trade_cursor.fetchone()[0]
            sl = round((bid - sl_val), 1)  # sl_val je zaporna hodnota

            q = 'select tp from tradeData where symbol = "US500" and timeframe = "1h"'
            fri_trade_cursor.execute(q)
            tp_val = fri_trade_cursor.fetchone()[0]
            tp = round((bid - tp_val), 1)

            return sl, tp



xtb = XtbApi()


def new_trade(symbol, timeframe, condition, trade_type):
    xtb.login()

    mini_logger.info("=== TRADE PREPARATIONS STARTED ===")

    q = f"SELECT lots from fri_trade.tradeData where symbol = '{symbol}' and timeframe = '{timeframe}'"
    fri_trade_cursor.execute(q)
    lots = fri_trade_cursor.fetchone()[0]
    print(f"Lots in database: {lots}")

    # account_properties = xtb.get_margin_level()
    # balance = account_properties["balance"]
    # margin_actual = account_properties["margin_needed_for_new_trade"]
    # currency = account_properties["currency"]
    # credit = account_properties["credit"]
    # equity = account_properties["equity"]
    # margin_free = account_properties["margin_free"]
    # margin_level = account_properties["margin_level"]
    # print("margin_actual", margin_actual, "Eur", "\nmargin_level", margin_level, "%")

    if trade_type == "buy":
        tradedata = xtb.sl_tp_override(symbol, timeframe, trade_type)
        sl = tradedata[0]
        tp = tradedata[1]

        transaction = xtb.open_buy_order(symbol=symbol,
                                         volume=lots,
                                         timeframe=timeframe,
                                         sl=sl,
                                         tp=tp)

        ordernum = transaction["order"]
        sent = transaction["sent"]
        opened = transaction["opened"]
        message = transaction["message"]
        margin_needed_for_new_trade = transaction["margin"]

        out = f"TRANSACTION STATS - ORDER: \n\nOrder number: {ordernum}\nType: {trade_type}\nSymbol: {symbol} {timeframe}\nLots: {lots}    Margin: {margin_needed_for_new_trade}\nSent: {sent}\n\nOpened: {opened}\nMessage: {message}"
        print(out)

        if opened:
            out = f"{symbol} {timeframe} Order {ordernum} - TRADE OPENED!"
            print(out)
            mini_logger.warning(out)
        else:
            out = f"{symbol} {timeframe} Order {ordernum} TRADE DENIED! - Reason: {message}"
            mini_logger.error(out)
            print(out)

        allopenedtrades = xtb.get_all_opened_only_positions()
        for opn_trade in allopenedtrades:
            if opn_trade["order2"] == ordernum:
                positionnum = opn_trade["position"]
                timeframe = opn_trade["customComment"]
                symbol = opn_trade["symbol"]

                q = f"insert into fri_trade.positions (date, time, positionnum, ordernum, symbol, ordertype, lots, margin, conditionTriggered, timeframe, sent, opened, reason, protected) VALUES('{date_now()}', '{time_now()}', '{positionnum}', '{ordernum}', '{symbol}', '{trade_type}', '{lots}', '{margin_needed_for_new_trade}', '{condition}', '{timeframe}', '{sent}', '{opened}', '{message}', False)"
                fri_trade_cursor.execute(q)

    elif trade_type == "sell":
        tradedata = xtb.sl_tp_override(symbol, timeframe, trade_type)
        sl = tradedata[0]
        tp = tradedata[1]

        transaction = xtb.open_sell_order(symbol=symbol,
                                          volume=lots,
                                          timeframe=timeframe,
                                          sl=sl,
                                          tp=tp)

        ordernum = transaction["order"]
        sent = transaction["sent"]
        opened = transaction["opened"]
        message = transaction["message"]
        margin_needed_for_new_trade = transaction["margin"]

        out = f"TRANSACTION STATS - ORDER: \n\nOrder number: {ordernum}\nType: {trade_type}\nSymbol: {symbol} {timeframe}\nLots: {lots}    Margin: {margin_needed_for_new_trade}\nSent: {sent}\n\nOpened: {opened}\nMessage: {message}"
        print(out)

        if opened:
            out = f"{symbol} {timeframe} Order {ordernum} - TRADE OPENED!"
            print(out)
            mini_logger.warning(out)
        else:
            out = f"{symbol} {timeframe} Order {ordernum} TRADE DENIED! - Reason: {message}"
            mini_logger.error(out)
            print(out)

        allopenedtrades = xtb.get_all_opened_only_positions()
        for opn_trade in allopenedtrades:
            if opn_trade["order2"] == ordernum:
                positionnum = opn_trade["position"]
                timeframe = opn_trade["customComment"]
                symbol = opn_trade["symbol"]

                q = f"insert into fri_trade.positions (date, time, positionnum, ordernum, symbol, ordertype, lots, margin, conditionTriggered, timeframe, sent, opened, reason, protected) VALUES('{date_now()}', '{time_now()}', '{positionnum}', '{ordernum}', '{symbol}', '{trade_type}', '{lots}', '{margin_needed_for_new_trade}', '{condition}', '{timeframe}', '{sent}', '{opened}', '{message}', False)"
                fri_trade_cursor.execute(q)

    xtb.logout()


new_trade(symbol=argv[1:2][0],
          timeframe=argv[2:3][0],
          condition=argv[3:4][0],
          trade_type=argv[4:5][0])
