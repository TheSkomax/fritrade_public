import time
import mysql.connector
import xAPIConnector
import logging
import traceback
import os
import dotenv

# ====== credentials ======
dotenv.load_dotenv(".env")

xtb_userId = os.environ["xtb_demo_temporary"]
xtb_passw = os.environ["xtb_pw"]

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]


# ====== mysql - fri_trade schema ======
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


# ---------------- LOGGING ----------------
log_protector = logging.getLogger("profit_prot_logger")
log_protector.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_protector.log")
file_handler.setFormatter(log_formatter)
log_protector.addHandler(file_handler)


class XtbApi:
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
                out = "Modifier logged IN"
                print(f"\n{out}")
                log_protector.info(out)

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
                log_protector.error(out)
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
                out = "Modifier logged OUT"
                print(f"{out}\n")
                log_protector.info(out)

                logout_bool = True

            else:
                out = "Logout failed!   {code} - {desc}".format(code=logout_response['errorCode'],
                                                                desc=logout_response["errorDescr"])
                print(out)
                log_protector.error(out)

                logout_bool = False
                time.sleep(2)

    def initial_ping(self):
        com = {
            "command": "ping"
        }
        cmd = self.client.execute(com)
        log_protector.info(f"Initial ping status: {cmd['status']}")

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

    def get_profit_calculation(self, symbol, volume, openprice, closeprice, operation):
        # cmd: 0 = Buy, 1 = Sell, 2 = Buy_limit, 3 = Sell_limit, 4 = Buy_stop, 5 = Sell_stop, 6 = Balance(read only),
        # 7 = Credit(read only)
        time.sleep(.1)
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
        # print(cmd)
        return cmd["returnData"]["profit"]

    def get_all_opened_only_orders(self):
        time.sleep(.1)
        com = {
            "command": "getTrades",
            "arguments": {
                "openedOnly": True
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

    def get_all_closed_trades(self):
        time.sleep(.1)
        com = {
            "command": "getTradesHistory",
            "arguments": {
                "start": 1659909600,
                "end": 0
            }
        }
        cmd = self.client.execute(com)
        return cmd["returnData"]

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

    def command_modify_order_add_trail_sl(self, symbol, volume, positionnum, offset_value, stoploss, takeprofit):
        type_modify = 3
        trade_trans_info = {
            "cmd": 0,
            "symbol": symbol,
            "volume": volume,
            "offset": offset_value,
            "sl": stoploss,
            "tp": takeprofit,
            "type": type_modify,
            "price": 0.1,  # placeholder hodnota pravdepodobne, minimalne je nepodstatna pri modify
            "order": positionnum
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
        return {"sent": cmd["status"],
                "order": cmd["returnData"]["order"],
                "modified": confirm_bool,
                "message": confirm[1]}

    def command_partially_close_order(self, symbol, volume_to_close, positionnum):
        type_close = 2
        trade_trans_info = {
            "cmd": 0,
            "symbol": symbol,
            "volume": volume_to_close,
            "type": type_close,
            "price": 0.1,
            "order": positionnum
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
        return {"sent": cmd["status"],
                "order": cmd["returnData"]["order"],
                "closed": confirm_bool,
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


xtb = XtbApi()
"""
trailing stoploss OFFSET = posun dole od aktuálnej ceny!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
offset level = current price - stoploss
offset sa meria od aktualnej ceny (oranzovej na xtb v pripade buy) k urovni stoplossu.
Cize offset v mojom pripade bude aktualna cena minus otvaracia, to bude offset k breakevenu 10%
"""






# TODO ATR Bands multiplier 3 -  su niekedy viac ako 10% z marze, niekedy menej. Zhruba tych 32 pipov je 10% zisk z marze
#     tak ked bude 10% menej ako je TP nastaveny, nech to ciastocne uzavrie a posunie na breakeven a bud to zoberie
#     ten TP alebo to pojde na breakeven
