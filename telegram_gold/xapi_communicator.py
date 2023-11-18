import os
import dotenv
import mysql.connector
import time
import logging
from datetime import date
from datetime import datetime
import xAPIConnector
from sys import argv

dotenv.load_dotenv(".env")
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
xtb_userId = os.environ["xtb_demo_main"]
xtb_passw = os.environ["xtb_pw"]

log_communicator = logging.getLogger("logger")
log_communicator.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_communicator.log")
file_handler.setFormatter(log_formatter)
log_communicator.addHandler(file_handler)

# ---------------- MYSQL ----------------
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


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
                out = "Logged into XTB!"
                print("API:", out)
                # mini_logger.info(out)

                logged_in = True
                self.ssid = login_response['streamSessionId']
                self.status = login_response["status"]
                self.streamclient = xAPIConnector.APIStreamClient(ssId=self.ssid)

            elif login_response['errorCode'] == "BE118":
                out = "Already logged in!"
                print("API:", out)
                logged_in = True

            else:
                logged_in = False
                out = f"Login failed!   {login_response['errorCode']} - {login_response['errorDescr']}"
                print("API:", out)
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
                out = "Logged out of XTB!"
                print(f"\nAPI: {out}")
                # mini_logger.info(out)

                logged_out = True

            else:
                out = f"Logout failed!   {logout_response['errorCode']} - {logout_response['errorDescr']}"
                print("API:", out)

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

    def open_buy_position(self, symbol, volume, sl, tp):
        transaction_info = {
            "cmd": 0,
            "symbol": symbol,
            "customComment": "Telegram gold trader",
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


def calc_tp_sl(operation, price_message, TP1, TP2, TP3, SL, price_ask, price_bid):
    if operation == "buy":
        if TP2 is not None:
            takeprofit_pips = round(TP2 - price_message, 2)
            takeprofit_price = round(price_ask + takeprofit_pips, 2)
        else:
            takeprofit_pips = round(TP1 - price_message, 2)
            takeprofit_price = round(price_ask + takeprofit_pips, 2)

        stoploss_pips = round(price_message - SL, 2)
        stoploss_price = round(price_ask - stoploss_pips, 2)
        print("API:", "takeprofit_pips", takeprofit_pips, "stoploss_pips", stoploss_pips)

        return takeprofit_price, stoploss_price

    elif operation == "sell":
        if TP2 is not None:
            takeprofit_pips = round(price_message - TP2, 2)
            takeprofit_price = round(price_bid - takeprofit_pips, 2)
        else:
            takeprofit_pips = round(price_message - TP1, 2)
            takeprofit_price = round(price_bid - takeprofit_pips, 2)

        stoploss_pips = round(SL - price_message, 2)
        stoploss_price = round(price_bid + stoploss_pips, 2)
        print("API:", "takeprofit_pips", takeprofit_pips, "stoploss_pips", stoploss_pips)

        return takeprofit_price, stoploss_price


def open_trade(operation, price_message, range_start, range_end, TP1, TP2, TP3, SL):
    xtb.login()
    lots = 0.01
    symbol = "GOLD"
    gold_specs = xtb.get_symbol_specs(symbol)

    price_ask = float(gold_specs["ask"])
    price_bid = float(gold_specs["bid"])
    # print("API:", "price_message", price_message, "TP2", TP2, "SL", SL)
    takeprofit_price, stoploss_price = calc_tp_sl(operation, price_message, TP1, TP2, TP3, SL, price_ask, price_bid)
    # print("API:", "price_ask", price_ask, "price_bid", price_bid, "takeprofit_price",
    #       takeprofit_price, "stoploss_price", stoploss_price)

    mode = "instant-hulvat"
    # instant-hulvat - otvori okamzite ked pride signal, dava TP2 ak je urceny, ziadny trailing SL ani nic take
    transaction_data = xtb.open_buy_position(symbol=symbol, volume=lots,
                                             sl=stoploss_price, tp=takeprofit_price)

    ordernum = transaction_data["order"]
    sent = transaction_data["sent"]
    opened = transaction_data["opened"]
    message = transaction_data["message"]
    margin_required = transaction_data["margin"]

    if opened:
        opened_message_status = f"{symbol} Order number {ordernum} - TRADE OPENED!"
    else:
        opened_message_status = f"{symbol} Order number {ordernum} - TRADE DENIED! - Reason: {message}"
    log_communicator.warning(opened_message_status)
    # print("API:", opened_message_status)

    allopenedtrades = xtb.get_all_opened_only_positions()
    for opened_trade in allopenedtrades:
        if opened_trade["order2"] == ordernum:
            positionnum = opened_trade["position"]

            q = f"""insert into fri_trade.gold_positions (date, time, positionnum, ordernum, operation, lots,
                     margin, mode_used, sent, opened, reason) VALUES('{datetime_now("date")}',
                     '{datetime_now("hms")}', '{positionnum}', '{ordernum}', '{operation}', {lots},
                     {margin_required}, {mode}, {sent}, {opened}, '{message}')"""
            fri_trade_cursor.execute(q)
    xtb.logout()


open_trade(operation=argv[1],
           price_message=float(argv[2]),
           range_start=float(argv[3]),
           range_end=float(argv[4]),
           TP1=float(argv[5]),
           TP2=float(argv[6]),
           TP3=float(argv[7]),
           SL=float(argv[8]),
           )
