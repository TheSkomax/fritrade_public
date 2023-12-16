import os
import time
import dotenv
import logging
import xAPIConnector
from sys import argv
import mysql.connector
from datetime import date
from datetime import datetime


dotenv.load_dotenv(".env")
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]


# ---------------- MYSQL ----------------
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)

# ---------------- LOGGING ----------------
log_xapi_comm = logging.getLogger("logger")
log_xapi_comm.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_post_xapi_comm.log")
file_handler.setFormatter(log_formatter)
log_xapi_comm.addHandler(file_handler)


def datetime_now(time_format: str) -> str:
    time_dict = {
        "hms": datetime.now().strftime("%H:%M:%S"),
        "ms": datetime.now().strftime("%M:%S"),
        "hm":  datetime.now().strftime("%H:%M"),
        "date": date.today().strftime("%d.%m.%Y")
    }
    return time_dict[time_format]


class XtbApi:
    def login(self):
        self.ssid = None
        self.status = None
        self.streamclient = None
        self.xtb_client = xAPIConnector.APIClient()

        self.initial_ping()  # initial command

        login_cmnd = {
            "command": "login",
            "arguments": {
                "userId": xtb_userId,
                "password": xtb_passw,
            },
            "customTag": "Login command"
        }
        logged_in = False

        while not logged_in:
            login_response = self.xtb_client.execute(login_cmnd)

            if login_response["status"]:
                out = "\nPost xAPI: Logged into XTB!"
                print(out)
                # mini_logger.info(out)

                logged_in = True
                self.ssid = login_response['streamSessionId']
                self.status = login_response["status"]
                self.streamclient = xAPIConnector.APIStreamClient(ssId=self.ssid)

            elif login_response['errorCode'] == "BE118":
                out = "Post xAPI: Already logged in!"
                print(out)
                logged_in = True

            else:
                logged_in = False
                out = f"Post xAPI: Login failed!   {login_response['errorCode']} - {login_response['errorDescr']}"
                print(out)
                # mini_logger.error(out)
                time.sleep(5)

    def logout(self):
        logout_cmnd = {
            "command": "logout",
            "customTag": "Logout command"
        }

        logged_out = False
        while not logged_out:
            logout_response = self.xtb_client.execute(logout_cmnd)

            if logout_response["status"]:
                out = "Post xAPI: Logged out of XTB!"
                print(f"\n{out}")
                # mini_logger.info(out)

                logged_out = True

            else:
                out = f"Post xAPI: Logout failed!   {logout_response['errorCode']} - {logout_response['errorDescr']}"
                print(out)
                # mini_logger.error(out)

                logged_out = False
                time.sleep(2)

    def initial_ping(self):
        ping_command = {
            "command": "ping"
        }
        execute_com = self.xtb_client.execute(ping_command)
        # mini_logger.info("%s %s", "Initial ping status:", execute_com["status"])

    def get_trade_margin(self, symbol, volume):
        time.sleep(.1)
        com = {
            "command": "getMarginTrade",
            "arguments": {
                "symbol": symbol,
                "volume": volume
            }
        }
        cmd = self.xtb_client.execute(com)
        return cmd["returnData"]["margin"]

    def get_symbol_specs(self, symbol):
        time.sleep(.1)
        com = {
            "command": "getSymbol",
            "arguments": {
                "symbol": symbol
            }
        }
        execute_com = self.xtb_client.execute(com)
        return execute_com["returnData"]

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
        cmd = self.xtb_client.execute(command)
        confirm = self.check_trade_status(cmd["returnData"]["order"])

        trade_accepted = 3
        if confirm[0] == trade_accepted:
            confirm_bool = True
        else:
            confirm_bool = False

        margin = xtb.get_trade_margin(symbol, volume)
        # mini_logger.warning(f"{cmdexe['returnData']['order']} TRYING TO OPEN --BUY-- ORDER: {symbol} {timeframe} {volume} {margin}€")

        return {"sent": cmd["status"],
                "order": cmd["returnData"]["order"],
                "opened": confirm_bool,
                "message": confirm[1],
                "margin": margin}

    def open_sell_position(self, symbol, volume, timeframe, sl, tp):
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
        cmdexe = self.xtb_client.execute(command)
        confirm = self.check_trade_status(cmdexe["returnData"]["order"])

        trade_accepted = 3
        if confirm[0] == trade_accepted:
            confirm_bool = True
        else:
            confirm_bool = False

        margin = xtb.get_trade_margin(symbol, volume)
        # mini_logger.warning(f"{cmdexe['returnData']['order']} TRYING TO OPEN --SELL-- ORDER: {symbol} {timeframe} {volume} {margin}€")

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
        cmd = self.xtb_client.execute(com)
        return [cmd["returnData"]["requestStatus"], cmd["returnData"]["message"]]

    def get_all_opened_only_positions(self):
        time.sleep(.05)
        com = {
            "command": "getTrades",
            "arguments": {
                "openedOnly": True
            }
        }
        cmd = self.xtb_client.execute(com)
        return cmd["returnData"]


xtb = XtbApi()


def calc_tp_sl(operation, value_price_close, value_atr, symbol, timeframe, price_ask, price_bid):
    stoploss_pips = 15
    takeprofit_pips = 60

    if operation == "buy":
        stoploss_price = round(price_ask - ((value_price_close - value_atr) + stoploss_pips), 2)
        takeprofit_price = round(price_ask + takeprofit_pips, 2)

    else:
        stoploss_price = round(((value_atr - value_price_close) + stoploss_pips) + price_bid, 2)
        takeprofit_price = round(price_bid - takeprofit_pips, 2)

    mes = (f"Post xAPI: Currently set to - TP pips: {takeprofit_pips}, SL pips: {stoploss_pips},"
           f" TP price: {takeprofit_price}, SL price: {stoploss_price}")
    print(mes)
    log_xapi_comm.warning(mes)
    return takeprofit_price, stoploss_price


def open_trade(operation, value_price_close, value_atr, symbol, timeframe):
    lots = 0.05
    value_price_close = float(value_price_close)
    value_atr = float(value_atr)

    print("Post xAPI: operation", operation, "value_price_close", value_price_close,
          "value_atr", value_atr, "symbol", symbol, "timeframe", timeframe)

    if symbol == "BTCUSD":
        symbol = "BITCOIN"

    xtb.login()
    symbol_specs = xtb.get_symbol_specs(symbol)
    price_ask = float(symbol_specs["ask"])
    price_bid = float(symbol_specs["bid"])

    takeprofit_price, stoploss_price = calc_tp_sl(operation, value_price_close, value_atr, symbol, timeframe,
                                                  price_ask, price_bid)

    if operation == "buy":
        transaction_data = xtb.open_buy_position(symbol=symbol, volume=lots, timeframe=timeframe,
                                                 sl=stoploss_price, tp=takeprofit_price)
    else:
        transaction_data = xtb.open_sell_position(symbol=symbol, volume=lots, timeframe=timeframe,
                                                  sl=stoploss_price, tp=takeprofit_price)

    ordernum = transaction_data["order"]
    sent =     transaction_data["sent"]
    opened =   transaction_data["opened"]
    message =  transaction_data["message"]
    margin_required = transaction_data["margin"]

    if opened:
        opened_message_status = f"{symbol} {timeframe} Order number {ordernum} - TRADE OPENED!"
    else:
        opened_message_status = f"{symbol} {timeframe} Order number {ordernum} - TRADE DENIED! - Reason: {message}"
    # print(f"Post xAPI: {opened_message_status}")

    allopenedtrades = xtb.get_all_opened_only_positions()
    for opened_trade in allopenedtrades:
        if opened_trade["order2"] == ordernum:
            positionnum = opened_trade["position"]
            timeframe = opened_trade["customComment"]
            symbol = opened_trade["symbol"]

            q = f"""insert into fri_trade.positions_forex (date, time, positionnum, ordernum, symbol, ordertype, lots,
                     margin, conditionTriggered, timeframe, sent, opened, reason) VALUES('{datetime_now("date")}',
                     '{datetime_now("hms")}', '{positionnum}', '{ordernum}', '{symbol}', '{operation}', '{lots}',
                     '{margin_required}', 'ATR', '{timeframe}', '{sent}', '{opened}', '{message}')"""
            fri_trade_cursor.execute(q)

    print("Post xAPI: DONE")
    log_xapi_comm.info("Post xAPI: DONE")
    xtb.logout()


open_trade(
    operation=argv[1],
    value_price_close=argv[2],
    value_atr=argv[3],
    symbol=argv[5],
    timeframe=argv[6]
)
