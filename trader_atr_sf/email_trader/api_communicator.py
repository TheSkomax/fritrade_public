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

    def get_symbol(self, symbol):
        time.sleep(.1)
        com = {
            "command": "getSymbol",
            "arguments": {
                "symbol": symbol
            }
        }
        cmd = self.xtb_client.execute(com)
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


def open_trade(chart_name, indicator, operation, takeprofit_pips, stoploss_pips):
    xtb.login()
    symbol, timeframe = chart_name.split("_")

    symbol_specs = xtb.get_symbol(symbol)
    ask = symbol_specs["ask"]
    bid = symbol_specs["bid"]
    # mini_logger.info("=== TRADE PREPARATIONS STARTED ===")

    q = f"""SELECT lots from fri_trade.tradeData where symbol = '{symbol}' and timeframe = '{timeframe}'"""
    fri_trade_cursor.execute(q)
    lots = fri_trade_cursor.fetchone()[0]
    print(f"Lots in database for {symbol} {timeframe}: {lots}")

    # account_properties = xtb.get_margin_level()
    # balance = account_properties["balance"]
    # margin_actual = account_properties["margin_needed_for_new_trade"]
    # currency = account_properties["currency"]
    # credit = account_properties["credit"]
    # equity = account_properties["equity"]
    # margin_free = account_properties["margin_free"]
    # margin_level = account_properties["margin_level"]
    # print("margin_actual", margin_actual, "Eur", "\nmargin_level", margin_level, "%")

    if operation == "buy":
        if symbol == "US500":
            takeprofit_price = round((ask + float(takeprofit_pips)), 1)
            stoploss_price = round((ask - float(stoploss_pips)), 1)
        elif symbol == "EURCHF":
            takeprofit_price = round((ask + float(takeprofit_pips)), 5)
            stoploss_price = round((ask - float(stoploss_pips)), 5)
        else:
            raise ValueError("Unknown symbol!")

        transaction_data = xtb.open_buy_order(symbol=symbol,
                                              volume=lots,
                                              timeframe=timeframe,
                                              sl=stoploss_price,
                                              tp=takeprofit_price)

    else:  # elif operation == "sell":
        if symbol == "US500":
            stoploss_price = round((bid + float(stoploss_pips)), 1)
            takeprofit_price = round((bid - float(takeprofit_pips)), 1)
        elif symbol == "EURCHF":
            stoploss_price = round((bid + float(stoploss_pips)), 5)
            takeprofit_price = round((bid - float(takeprofit_pips)), 5)
        else:
            raise ValueError("Unknown symbol!")

        transaction_data = xtb.open_sell_order(symbol=symbol,
                                               volume=lots,
                                               timeframe=timeframe,
                                               sl=stoploss_price,
                                               tp=takeprofit_price)

    ordernum = transaction_data["order"]
    sent = transaction_data["sent"]
    opened = transaction_data["opened"]
    message = transaction_data["message"]
    margin_needed_for_new_trade = transaction_data["margin"]

    out = f"TRANSACTION STATS - ORDER: \n\nOrder number: {ordernum}\nType: {operation}\nSymbol: {symbol} {timeframe}\nLots: {lots}    Margin: {margin_needed_for_new_trade}\nSent: {sent}\n\nOpened: {opened}\nMessage: {message}"
    print(out)

    if opened:
        out = f"{symbol} {timeframe} Order {ordernum} - TRADE OPENED!"
        # mini_logger.warning(out)
        print(out)
    else:
        out = f"{symbol} {timeframe} Order {ordernum} TRADE DENIED! - Reason: {message}"
        # mini_logger.error(out)
        print(out)

    allopenedtrades = xtb.get_all_opened_only_positions()
    for opened_trade in allopenedtrades:
        if opened_trade["order2"] == ordernum:
            positionnum = opened_trade["position"]
            timeframe = opened_trade["customComment"]
            symbol = opened_trade["symbol"]

            q = f"""insert into fri_trade.positions (date, time, positionnum, ordernum, symbol, ordertype, lots, margin,
                     conditionTriggered, timeframe, sent, opened, reason, protected) VALUES('{date_now()}',
                     '{time_now_hms()}', '{positionnum}', '{ordernum}', '{symbol}', '{operation}', '{lots}',
                     '{margin_needed_for_new_trade}', '{indicator}', '{timeframe}', '{sent}', '{opened}',
                     '{message}', False)"""
            fri_trade_cursor.execute(q)

    xtb.logout()


open_trade(chart_name=argv[1], indicator=argv[2], operation=argv[3],
           takeprofit_pips=argv[4], stoploss_pips=argv[5])
