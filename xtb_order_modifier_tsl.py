import time
import mysql.connector
import xAPIConnector
import logging
import traceback
import os
import dotenv

# ====== credentials ======
dotenv.load_dotenv(".env")

xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

# ====== basic config ======
block_bar = "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"

# ====== mysql - fri_trade schema ======
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)

# ====== Logging ======
modif_logger = logging.getLogger("xtb_modifier_logger")
modif_logger.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s", "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_modifier.log")
file_handler.setFormatter(log_formatter)
modif_logger.addHandler(file_handler)
modif_logger.info(f"\n{block_bar}")


# ====== XTB trading stuph ======
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
                modif_logger.info(out)

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
                modif_logger.error(out)
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
                modif_logger.info(out)

                logout_bool = True

            else:
                out = "Logout failed!   {code} - {desc}".format(code=logout_response['errorCode'],
                                                                desc=logout_response["errorDescr"])
                print(out)
                modif_logger.error(out)

                logout_bool = False
                time.sleep(2)

    def initial_ping(self):
        com = {
            "command": "ping"
        }
        cmd = self.client.execute(com)
        modif_logger.info(f"Initial ping status: {cmd['status']}")

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

# TODOne vyriesit offset pre VIX ako to zobrazuje trailing v xstation .. lebo to cislo nemoze byt float, preto je v get_ten_perc_from_margin_pips INT
# TODOone 1 vybrat marzu danej pozicie z databazy - get_margin_of_opened_order
# TODOne 2 zistit kolko je 10% z nej v eurach a pipoch - 20% a 30% atď bude 2nasobok a tak get_ten_perc_from_margin_eur+get_ten_perc_from_margin_eur_pips
# TODOne 3 loop, ktory bude pozerat profit na poziciach, ak bude 10% tak aktivovat trailing stoploss s offsetom z bodu 2, aby to bolo na breakeven - XTB TRADER
# TODOne 4 takto to vlastne bude vzdy o 10% nizsie, napr 15 pipov alebo tak, cize ked zisk bude 20% tak stoploss bude na 10% s danym offsetom a bude sa pripadne hybat hore

"""
trailing stoploss OFFSET = posun dole od aktuálnej ceny!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
offset level = current price - stoploss
offset sa meria od aktualnej ceny (oranzovej na xtb v pripade buy) k urovni stoplossu.
Cize offset v mojom pripade bude aktualna cena minus otvaracia, to bude offset k breakevenu 10%
"""


def check_db_for_empty_profits():
    position_list = []
    closed_positions_positionnum_list = []

    # symbol sa tu pridal lebo kvoli ciastocnemu uzatvaraniu pozicii vracia xAPI pozicie dvakrat alebo kolkokrat sa
    # ciastocne zavru, tak to skontroluje aj symbol a ak je rovnaky tak ich profity ta dalsia funkcia scita
    # pre este vacsiu istotu by sa dalo porovnavat aj 'open_timeString', ktory je tiez rovnaky tak ako position number
    # ale tak asi to nebude treba
    q = "SELECT symbol, positionnum from fri_trade.positions where profit IS NULL or profit = 0"
    # q = "SELECT symbol, positionnum from fri_trade.positions where profit IS NULL"
    fri_trade_cursor.execute(q)
    zero_profit_list = fri_trade_cursor.fetchall()

    closed_positions_list = xtb.get_all_closed_trades()

    if zero_profit_list is not None:
        for zero_profit_pos in zero_profit_list:
            symbol = zero_profit_pos[0]
            positionnum = zero_profit_pos[1]


            for closed_position in closed_positions_list:
                closed_positions_positionnum_list.append(str(closed_position["position"]))

            if str(positionnum) in closed_positions_positionnum_list:
                temp_tuple = (symbol, positionnum)
                position_list.append(temp_tuple)

    # print(position_list)
    if len(position_list) != 0:
        return position_list
    else:
        return None


def get_margin_of_opened_order(positionnum):
    q = f'select margin from fri_trade.positions where positionnum = {positionnum}'
    fri_trade_cursor.execute(q)
    margin = fri_trade_cursor.fetchall()

    if len(margin) != 0:
        margin = float(margin[0][0])
        # print("*margin", margin)
        return margin
    else:
        return None


def get_ten_perc_from_margin_eur(margin):
    tenperc = round(float(margin * 0.1), 2)
    return tenperc


def get_ten_perc_from_margin_pips(symbol, volume, tenperc_target_eur, decimal_places):
    buy = 0
    openprice = 1.0
    closeprice = 2.0


    onepip_profit_eur = xtb.get_profit_calculation(symbol, volume, openprice, closeprice, buy)
    tenperc_target_pips = round(float(tenperc_target_eur / onepip_profit_eur), decimal_places)
    # if symbol != "VIX":
    #     tenperc_target_pips = round(int(tenperc_target_eur / onepip_profit_eur), 5)
    # else:
    #     tenperc_target_pips = round(float(tenperc_target_eur / onepip_profit_eur), 2)
    # print(tenperc_target_pips)
    return tenperc_target_pips


def get_order_profit_pips(symbol, volume, profit_eur):
    buy = 0
    openprice = 1.0
    closeprice = 2.0
    onepip_profit_eur = xtb.get_profit_calculation(symbol, volume, openprice, closeprice, buy)
    res = profit_eur / onepip_profit_eur
    # print(res)
    return res


def set_stoploss(symbol, volume, positionnum, offset_value, stoploss, takeprofit):
    modify = xtb.command_modify_order_add_trail_sl(symbol,
                                                   volume,
                                                   positionnum,
                                                   offset_value,
                                                   stoploss,
                                                   takeprofit)
    time.sleep(1)
    if modify["modified"]:
        print('set_stoploss - Success!')
        modif_logger.info('set_stoploss - Success!')
        return True
    else:
        print(f'FAILED!!!   Reason: {modify["message"]}')
        modif_logger.warning(f'FAILED!!!   Reason: {modify["message"]}')
        return False


def set_sl_to_tenperc(symbol, volume, positionnum, offset_value, stoploss, takeprofit):
    out = f"{symbol} {positionnum} has reached 20% profit, setting SL to 10%"
    print(out)
    modif_logger.info(out)
    modify = xtb.command_modify_order_add_trail_sl(symbol,
                                                   volume,
                                                   positionnum,
                                                   offset_value,
                                                   stoploss,
                                                   takeprofit)
    time.sleep(1)
    if modify["modified"]:
        print('Success!')
        modif_logger.info('Success!')
        return True
    else:
        print(f'FAILED!!!   Reason: {modify["message"]}')
        modif_logger.warning(f'FAILED!!!   Reason: {modify["message"]}')
        return False


def partially_close_order(symbol, volume_to_close, positionnum):
    out = f"{symbol} {positionnum} has reached 10% profit, partially closing {volume_to_close} lots"
    print(out)
    modif_logger.info(out)
    partially_close = xtb.command_partially_close_order(symbol,
                                                        volume_to_close,
                                                        positionnum)
    if partially_close["closed"]:
        print('Success!')
        modif_logger.info('Success!')
        return True
    else:
        print(f'FAILED!!!   Reason: {partially_close["message"]}')
        modif_logger.warning(f'FAILED!!!   Reason: {partially_close["message"]}')
        return False


def update_margin_and_volume_in_db_after_partial_close(positionnum):
    oldmargin = get_margin_of_opened_order(positionnum)
    newmargin = round(oldmargin * 0.5, 2)
    allopenedorders = xtb.get_all_opened_only_orders()

    wanted_order = None
    for listed_order in allopenedorders:
        if listed_order["position"] == positionnum:
            wanted_order = listed_order
            break
    newvolume = wanted_order["volume"]

    q = f'update fri_trade.positions set margin = {newmargin} where positionnum = {positionnum}'
    fri_trade_cursor.execute(q)
    q = f'update fri_trade.positions set lots = {newvolume} where positionnum = {positionnum}'
    fri_trade_cursor.execute(q)


def calculate_offset_buy_pos(symbol, current_price, open_price, decimal_places):
    if decimal_places == 1 or decimal_places == 5:
        multiplier = 10
    elif decimal_places == 2:
        multiplier = 100

    # offset = current price - stoploss
    # offset nesmie byt zaporny!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! aspon pri buy nie, nvm ako pri sell!!
    offset_pips = float(round(current_price - open_price, decimal_places))

    if symbol == "VIX":
        offset_value = offset_pips * multiplier
    else:
        offset_value = int(offset_pips * multiplier)
    # print(f"{symbol} offset = {offset_pips} OFFSET VALUE = {offset_value}")

    return offset_pips, offset_value


def halving(symbol, volume, positionnum, offset_value, open_price, takeprofit, tenperc_target_eur, order_profit_eur,
            order_number):
    q = f"select halving from fri_trade.positions where positionnum = '{positionnum}'"
    fri_trade_cursor.execute(q)
    halved = fri_trade_cursor.fetchone()[0]

    if not halved:
        if tenperc_target_eur < order_profit_eur < (tenperc_target_eur * 2):
            operation_modify = set_stoploss(symbol=symbol, volume=volume,
                                            positionnum=positionnum,
                                            offset_value=offset_value,
                                            stoploss=open_price,
                                            takeprofit=takeprofit)
            out = f"{symbol} {positionnum} has reached 10% profit, setting SL to breakeven and adding trailing SL"
            print(out)
            modif_logger.info(out)

            if volume > 0.01:
                volume_to_close = round(volume * 0.5, 2)
                operation_partially_close = partially_close_order(symbol=symbol,
                                                                  volume_to_close=volume_to_close,
                                                                  positionnum=positionnum)
                q = f'update fri_trade.positions set halving = True where positionnum = {positionnum}'
                fri_trade_cursor.execute(q)
                out = f"Halving - {symbol} {positionnum} halved!"
                print(out)
                modif_logger.info(out)

                update_margin_and_volume_in_db_after_partial_close(positionnum)
                out = f"Halving - {symbol} {positionnum} margin and volume after partial close updated!"
                print(out)
                modif_logger.info(out)

            else:
                out = f"Halving - {symbol} {positionnum} has reached 10% profit but cannot be partially closed, volume = 0.01"
                print(out)
                modif_logger.info(out)

        else:
            out = f"Halving - {symbol} {positionnum} profit is not in needed % range"
            print(out)
            modif_logger.info(out)
    else:
        out = f"Halving - {symbol} {positionnum} already halved!"
        # print(out)
        modif_logger.info(out)


# half of halved
def quartering(symbol, volume, positionnum, offset_value, tenperc_target_pips, tp, tenperc_target_eur, curr_profit_eur):
    q = f"select halving, quartering from fri_trade.positions where positionnum = '{positionnum}'"
    fri_trade_cursor.execute(q)
    res_tuple = fri_trade_cursor.fetchone()

    if res_tuple is not None:
        halved = res_tuple[0]
        quartered = res_tuple[1]

        if halved and not quartered:
            # if (tenperc_target_eur * 2) < curr_profit_eur < (tenperc_target_eur * 3):
            if (tenperc_target_eur * 2) < curr_profit_eur:
                operation_modify = set_stoploss(symbol=symbol, volume=volume,
                                                positionnum=positionnum,
                                                offset_value=offset_value,
                                                stoploss=tenperc_target_pips,
                                                takeprofit=tp)

                if volume > 0.01:
                    volume_to_close = round(volume * 0.5, 2)
                    operation_partially_close = partially_close_order(symbol=symbol,
                                                                      volume_to_close=volume_to_close,
                                                                      positionnum=positionnum)
                    q = f'update fri_trade.positions set quartering = True where positionnum = {positionnum}'
                    fri_trade_cursor.execute(q)
                    out = f"Quartering - {symbol} {positionnum} halved!"
                    print(out)
                    modif_logger.info(out)

                    update_margin_and_volume_in_db_after_partial_close(positionnum)
                    out = f"Quartering - {symbol} {positionnum} margin and volume after partial close updated!"
                    print(out)
                    modif_logger.info(out)

                else:
                    out = f"Quartering - {symbol} {positionnum} has reached 20% profit but cannot be partially closed, volume = 0.01"
                    print(out)
                    modif_logger.info(out)

            else:
                out = f"Quartering - {symbol} {positionnum} profit is not in needed % range"
                print(out)
                modif_logger.info(out)
        else:
            out = f"Quartering - {symbol} {positionnum} already quartered!"
            # print(out)
            modif_logger.info(out)
    else:
        out = f"Quartering - No positions to quarter!"
        # print(out)
        modif_logger.info(out)


def position_profit_checker_closer_modifier():
    out = "- Starting position_profit_checker_closer_modifier"
    print(out)
    modif_logger.info(out)

    all_opened_orders = xtb.get_all_opened_only_orders()
    # print(all_opened_orders)

    for order in all_opened_orders:
        positionnum = order["position"]
        order_number = order["order2"]
        decimal_places = order["digits"]
        offset = order["offset"]  # in pips (?)
        open_price = order["open_price"]
        volume = order["volume"]
        symbol = order["symbol"]
        order_profit_eur = order["profit"]
        current_price = order["close_price"]
        position_type = order["cmd"]
        takeprofit = order["tp"]
        margin = get_margin_of_opened_order(positionnum)
        # print(positionnum)

        # print(offset, "offset")

        if decimal_places == 1 or decimal_places == 5:
            divider = 10
        elif decimal_places == 2:
            divider = 100

        # print(offset / divider, "offset / divider")
        # print(margin, "Eur margin")

        order_profit_pips = get_order_profit_pips(symbol, volume, order_profit_eur)
        tenperc_target_eur = get_ten_perc_from_margin_eur(margin)
        # print(tenperc_target_eur, "tenperc_target_eur")
        tenperc_target_pips = get_ten_perc_from_margin_pips(symbol, volume, tenperc_target_eur, decimal_places)
        oneperc_eur = tenperc_target_eur / 10

        try:
            # print(symbol, tenperc_target_pips, "tenperc_target_pips", "\ntenperc target eur", tenperc_target_eur)
            if position_type == 0:  # if buy order
                if offset == 0:
                    if order_profit_pips > 0:
                        offset_data = calculate_offset_buy_pos(symbol, current_price, open_price, decimal_places)
                        offset_pips = offset_data[0]
                        offset_value = offset_data[1]
                        # print("\nopenprice", open_price, "offset", offset_pips)
                        # print("order profit", order_profit_eur, "tenperc target", tenperc_target_eur)

                        # profit more than 10% (under 20%) -------------------------------------------------------------
                        halving(symbol, volume, positionnum, offset_value, open_price, takeprofit, tenperc_target_eur,
                                order_profit_eur, order_number)

                    else:
                        out = f"{symbol} {positionnum} no profit on this position"
                        print(out)
                        modif_logger.info(out)
                else:
                    out = f"{symbol} {positionnum} has offset on breakeven (is halved)"
                    print(out)
                    modif_logger.info(out)

                    offset_data = calculate_offset_buy_pos(symbol, current_price, open_price, decimal_places)
                    offset_pips = offset_data[0]
                    offset_value = offset_data[1]

                    # profit more than 20% (under 30%) -----------------------------------------------------------------
                    quartering(symbol, volume, positionnum, offset_value, tenperc_target_pips, takeprofit,
                               tenperc_target_eur, order_profit_eur)
            else:
                out = f"{symbol} {positionnum} is SELL!!! (not yet implemented)"
                print(out)
                modif_logger.error(out)

        except Exception as err:
            print("Modifier main:")
            traceback.print_exc()
            modif_logger.error(err)


def add_profits_of_closed_positions_to_db():
    out = "- Starting add_profits_of_closed_positions_to_db"
    print(out)
    modif_logger.error(out)

    empty_profit_positions_list = check_db_for_empty_profits()
    # print("positions with null profit:", empty_profit_positions_list)

    if empty_profit_positions_list is not None:

        closed_positions_list = xtb.get_all_closed_trades()
        # print(closed_positions_list)

        for pair_tuple in empty_profit_positions_list:
            symbol = pair_tuple[0]
            positionnum = pair_tuple[1]
            profit_list = []

            # print("\n\n***************************************************** checking pos num", positionnum, symbol)
            for clos_position in closed_positions_list:
                # print(clos_position["position"])
                if str(clos_position["position"]) == positionnum and str(clos_position["symbol"] == symbol):
                    # print(f"Found:\n{clos_position}")
                    profit_list.append(clos_position["profit"])

            total_profit = sum(profit_list)
            # print(total_profit)
            q = f"update fri_trade.positions set profit = '{total_profit}' where positionnum = '{positionnum}'"
            fri_trade_cursor.execute(q)

            out = f"{symbol} {positionnum} added profit {total_profit}"
            print(out)
            modif_logger.info(out)

    else:
        pass


def profit_protector():
    out = "- Starting profit_protector"
    print(out)
    modif_logger.error(out)

    all_opened_orders = xtb.get_all_opened_only_orders()
    # print(all_opened_orders)

    for order in all_opened_orders:
        positionnum = order["position"]
        open_price = order["open_price"]
        volume = order["volume"]
        symbol = order["symbol"]
        order_profit_eur = order["profit"]
        takeprofit = order["tp"]
        decimal_places = order["digits"]
        margin = get_margin_of_opened_order(positionnum)

        threeperc_target_eur = get_ten_perc_from_margin_eur(margin) * 0.3
        oneperc_target_eur = get_ten_perc_from_margin_eur(margin) * 0.1

        oneperc_target_pips = get_ten_perc_from_margin_pips(symbol, volume, oneperc_target_eur, decimal_places)


        q = f"select protected from fri_trade.positions where positionnum = '{positionnum}'"
        fri_trade_cursor.execute(q)
        protected = fri_trade_cursor.fetchone()[0]

        if not protected:
            if order_profit_eur > threeperc_target_eur:
                operation_modify = set_stoploss(symbol=symbol, volume=volume,
                                                positionnum=positionnum,
                                                offset_value=0,
                                                stoploss=round(open_price + oneperc_target_pips, decimal_places),
                                                takeprofit=takeprofit)

                q = f"update fri_trade.positions set protected = True where positionnum = '{positionnum}'"
                fri_trade_cursor.execute(q)
                out = f"Protector - {symbol} {positionnum} protected!"
                print(out)
                modif_logger.info(out)

            else:
                out = f"Protector - {symbol} {positionnum} profit hasnt reached 3%, cannot protect!"
                # print(out)
                modif_logger.info(out)


def main():
    out = "*****   Order modifier started!   *****"
    modif_logger.info(out)
    # print(out)

    xtb.login()

    position_profit_checker_closer_modifier()
    add_profits_of_closed_positions_to_db()
    profit_protector()

    xtb.logout()


main()







# xtb.login()
# update_margin_and_volume_in_db_after_partial_close(430262333)

# aaa = xtb.get_profit_calculation("VIX", 0.01, 1.00, 2.00, 0)
# print(aaa)

# www = xtb.get_all_opened_only_positions()
# print(www)

# bbb = get_order_profit_pips("DE30", 0.01, 70)
# print(bbb)

# xtb.command_modify_order_add_trail_sl("DE30", 0.01, 425831710, 1810, 200.6)  # cislo objednavky musi byt position, nie order, offset nesmie byt float!!!

# symbol, volume, ordernum, trailstop

# a=xtb.get_symbol("DE30")
# print(a)

# ord = xtb.get_all_closed_trades()
# a = 0
# for i in ord:
#     print(i["order"], i["symbol"], i["profit"], i["close_timeString"])

#     a = a + 1
# print(a)
# xtb.logout()
