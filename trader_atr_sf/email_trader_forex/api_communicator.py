import os
import dotenv
import mysql.connector
import time
from datetime import date
from datetime import datetime
import xAPIConnector
from sys import argv

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


def time_now_hms():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    # print(time_actual)
    return time_actual


def time_now_ms():
    time_object = datetime.now()
    time_actual = time_object.strftime("%M:%S")
    # print(time_actual)
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


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
                print(out)
                # mini_logger.info(out)

                logged_in = True
                self.ssid = login_response['streamSessionId']
                self.status = login_response["status"]
                self.streamclient = xAPIConnector.APIStreamClient(ssId=self.ssid)

            elif login_response['errorCode'] == "BE118":
                out = "Already logged in!"
                print(out)
                logged_in = True

            else:
                logged_in = False
                out = f"Login failed!   {login_response['errorCode']} - {login_response['errorDescr']}"
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
                out = "Logged out of XTB!"
                print(f"\n{out}")
                # mini_logger.info(out)

                logged_out = True

            else:
                out = f"Logout failed!   {logout_response['errorCode']} - {logout_response['errorDescr']}"
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


def open_trade(operation, price_close, takeprofit_pips, stoploss_pips, symbol, timeframe):
    xtb.login()
    lots = 0.09
    indicator = "SF Strong"
    symbol_specs = xtb.get_symbol_specs(symbol)
    ask = symbol_specs["ask"]
    bid = symbol_specs["bid"]

    if operation == "buy":
        takeprofit_price = round((ask + float(takeprofit_pips)), 5)
        stoploss_price =   round((ask - float(stoploss_pips)), 5)

        transaction_data = xtb.open_buy_position(symbol=symbol, volume=lots, timeframe=timeframe,
                                                 sl=stoploss_price, tp=takeprofit_price)
    elif operation == "sell":
        takeprofit_price = round((bid - float(takeprofit_pips)), 5)
        stoploss_price =   round((bid + float(stoploss_pips)), 5)

        transaction_data = xtb.open_sell_position(symbol=symbol, volume=lots, timeframe=timeframe,
                                                  sl=stoploss_price, tp=takeprofit_price)

    ordernum = transaction_data["order"]
    sent = transaction_data["sent"]
    opened = transaction_data["opened"]
    message = transaction_data["message"]
    margin_required = transaction_data["margin"]

    if opened:
        opened_message_status = f"{symbol} {timeframe} Order number {ordernum} - TRADE OPENED!"
    else:
        opened_message_status = f"{symbol} {timeframe} Order number {ordernum} - TRADE DENIED! - Reason: {message}"
    print(opened_message_status)

    allopenedtrades = xtb.get_all_opened_only_positions()
    for opened_trade in allopenedtrades:
        if opened_trade["order2"] == ordernum:
            positionnum = opened_trade["position"]
            timeframe = opened_trade["customComment"]
            symbol = opened_trade["symbol"]

            q = f"""insert into fri_trade.positions_forex (date, time, positionnum, ordernum, symbol, ordertype, lots,
                     margin, conditionTriggered, timeframe, sent, opened, reason, protected) VALUES('{date_now()}',
                     '{time_now_hms()}', '{positionnum}', '{ordernum}', '{symbol}', '{operation}', '{lots}',
                     '{margin_required}', '{indicator}', '{timeframe}', '{sent}', '{opened}', '{message}', False)"""
            fri_trade_cursor.execute(q)
    xtb.logout()


# open_trade(operation=argv[1], price_close=argv[2], takeprofit_pips=argv[3], stoploss_pips=argv[4], symbol=argv[5],
#            timeframe=argv[6])
