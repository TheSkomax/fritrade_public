# =================================================================
# TRADER for ATR and Smart Forex (+ CE)
# =================================================================
import subprocess
from datetime import date
from datetime import datetime
import time
import mysql.connector
import os
import dotenv

table_name_part = "atr_smartfrx_"
active_charts = [{"name": "US500_1h", "is_currency": False}, {"name": "EURCHF_1h", "is_currency": True}]
dotenv.load_dotenv("../.env")
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

db_connection = mysql.connector.connect(host="localhost",
                                        user=mysql_user,
                                        passwd=mysql_passw,
                                        database="fri_trade",
                                        autocommit=True)
fri_trade_cursor = db_connection.cursor(buffered=True)


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


def check_atr_condition(chart_name):
    operation = None
    q = f"""SELECT value_atr, price_close, id FROM fri_trade.{table_name_part}{chart_name} where processed = False order by id desc"""
    new_data = execute_select_query(q)
    if new_data is not None:
        new_value_atr, new_price_close, new_id = new_data

        q = f"""SELECT value_atr, price_close FROM fri_trade.{table_name_part}{chart_name} where id = {new_id - 1}"""
        prev_data = execute_select_query(q)
        if prev_data is not None:
            prev_value_atr, prev_price_close = prev_data

            # buy condition
            if new_price_close > new_value_atr and prev_price_close < prev_value_atr:
                print(f"{chart_name} ATR - buy!")
                operation = "buy"

            # sell condition
            elif new_price_close < new_value_atr and prev_price_close > prev_value_atr:
                print(f"{chart_name} ATR - sell!")
                operation = "sell"
            else:
                print(f"{chart_name} ATR - no trade!")
        else:
            print(f"{chart_name} ATR prev_data - not enough values in database")
        q = f"""UPDATE fri_trade.{table_name_part}{chart_name} SET processed = true where id = {new_id}"""
        execute_non_return_query(q)
    else:
        print(f"{chart_name} ATR new_data - no new value in database")

    if operation is not None:
        get_sl_tp_for_atr_trade(chart_name, operation, new_value_atr, new_price_close, new_id)


def check_smartforex_condition(chart_name):
    operation = None
    q = f"""SELECT sf_bool_buy, sf_bool_sell, sf_bool_buy_strong, sf_bool_sell_strong, id FROM fri_trade.{table_name_part}{chart_name} where processed = False order by id desc"""
    new_data = execute_select_query(q)
    if new_data is not None:
        # new_sf_bool_buy, new_sf_bool_sell, new_sf_bool_buy_strong, new_sf_bool_sell_strong, new_id = new_data
        new_id = new_data[4]
        new_smartforex_trade_bools = {
            "buy": new_data[0],
            "sell": new_data[1],
            "buy_strong": new_data[2],
            "sell_strong": new_data[3]
        }
        # print(chart_name, "Smartforex new_data", new_smartforex_trade_bools)

        q = f"""SELECT sf_bool_buy, sf_bool_sell, sf_bool_buy_strong, sf_bool_sell_strong FROM fri_trade.{table_name_part}{chart_name} where id = {new_id - 1}"""
        prev_data = execute_select_query(q)
        if prev_data is not None:
            if True in new_smartforex_trade_bools.values():
                # prev_sf_bool_buy, prev_sf_bool_sell, prev_bool_buy_strong, prev_sf_bool_sell_strong = prev_data
                prev_smartforex_trade_bools = {
                    "buy": prev_data[0],
                    "sell": prev_data[1],
                    "buy_strong": prev_data[2],
                    "sell_strong": prev_data[3]
                }
                # print(chart_name, "Smartforex prev_data", prev_smartforex_trade_bools)

                for bool_name, bool_value in new_smartforex_trade_bools.items():
                    if bool_value and bool_value != prev_smartforex_trade_bools[bool_name]:
                        operation = bool_name
                        print(f"{chart_name} SF - no trade!")

            else:
                print(f"{chart_name} Smartforex new_data - no True value in dict")
        else:
            print(f"{chart_name} Smartforex prev_data - not enough values in database")
    else:
        print(f"{chart_name} Smartforex new_data - no new value in database")

    if operation is not None:
        q = f"""SELECT value_atr, price_close FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        new_value_atr, new_price_close = execute_select_query(q)
        get_sl_tp_for_smartforex_ce_trade(chart_name, operation, new_value_atr, new_price_close, new_id)


def check_ce_condition(chart_name):
    print("DEBUG CE")
    operation = None
    q = f"""SELECT ce_bool_buy, ce_bool_sell, id FROM fri_trade.{table_name_part}{chart_name} where processed = False order by id desc"""
    new_data = execute_select_query(q)
    if new_data is not None:
        new_id = new_data[2]
        new_ce_trade_bools = {
            "buy": new_data[0],
            "sell": new_data[1],
        }
        # print(chart_name, "CE new_data", new_ce_trade_bools)

        q = f"""SELECT ce_bool_buy, ce_bool_sell FROM fri_trade.{table_name_part}{chart_name} where id = {new_id - 1}"""
        prev_data = execute_select_query(q)
        if prev_data is not None:
            if True in new_ce_trade_bools.values():
                prev_ce_trade_bools = {
                    "buy": prev_data[0],
                    "sell": prev_data[1],
                }
                # print(chart_name, "CE prev_data", prev_ce_trade_bools)

                for bool_name, bool_value in new_ce_trade_bools.items():
                    if bool_value and bool_value != prev_ce_trade_bools[bool_name]:
                        operation = bool_name
                        print(f"{chart_name} CE - {operation}!")

            else:
                print(f"{chart_name} CE new_data - no True value in dict")
        else:
            print(f"{chart_name} CE prev_data - not enough values in database")
    else:
        print(f"{chart_name} CE new_data - no new value in database")

    if operation is not None:
        q = f"""SELECT value_atr, price_close FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        new_value_atr, new_price_close = execute_select_query(q)
        get_sl_tp_for_smartforex_ce_trade(chart_name, operation, new_value_atr, new_price_close, new_id)


def execute_select_query(q):
    fri_trade_cursor.execute(q)
    data = fri_trade_cursor.fetchone()
    return data


def execute_non_return_query(q):
    fri_trade_cursor.execute(q)


def get_sl_tp_for_atr_trade(chart_name, operation, value_atr, price_close, new_id):
    indicator_name = "atr"
    if operation == "buy":
        stoploss_pips = (price_close - value_atr) + ((price_close - value_atr) * 0.2)
        stoploss_price = price_close - stoploss_pips

        q = f"""SELECT value_atr_up FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        takeprofit_price = execute_select_query(q)[0]  # value_atr_up
        takeprofit_pips = takeprofit_price - price_close

    else:  # elif operation == "sell":
        stoploss_pips = (value_atr - price_close) + ((value_atr - price_close) * 0.2)
        stoploss_price = price_close + stoploss_pips

        q = f"""SELECT value_atr_down FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        takeprofit_price = execute_select_query(q)[0]  # value_atr_down
        takeprofit_pips = price_close - takeprofit_price

    # communicator(chart_name, indicator_name, operation, takeprofit_price, stoploss_price)
    communicator(chart_name, indicator_name, operation, takeprofit_pips, stoploss_pips)


def get_sl_tp_for_smartforex_ce_trade(chart_name, operation, value_atr, price_close, new_id):
    indicator_name = "smartforex"
    # DO BUDUCNOSTI PRIDAT ESTE PODMIENKY PRE STRONG BUY/SELL - nech to vezme vacsi takeprofit
    if "buy" in operation:
        operation = "buy"
        if value_atr < price_close:
            stoploss_pips = (price_close - value_atr) + ((price_close - value_atr) * 0.2)
            stoploss_price = price_close - stoploss_pips
        else:
            q = f"""SELECT value_atr_down FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
            stoploss_price = execute_select_query(q)[0]  # value_atr_down
            stoploss_pips = (price_close - stoploss_price) + ((price_close - stoploss_price) * 0.2)

        q = f"""SELECT value_atr_up FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        takeprofit_price = execute_select_query(q)[0]  # value_atr_up
        takeprofit_pips = takeprofit_price - price_close

    else:  # elif "sell" in operation:
        operation = "sell"
        if value_atr > price_close:
            stoploss_pips = (value_atr - price_close) + ((value_atr - price_close) * 0.2)
            stoploss_price = price_close + stoploss_pips
        else:
            q = f"""SELECT value_atr_up FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
            stoploss_price = execute_select_query(q)[0]  # value_atr_up
            stoploss_pips = (stoploss_price - price_close) + ((stoploss_price - price_close) * 0.2)

        q = f"""SELECT value_atr_down FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        takeprofit_price = execute_select_query(q)[0]  # value_atr_down
        takeprofit_pips = price_close - takeprofit_price

    # communicator(chart_name, indicator_name, operation, takeprofit_price, stoploss_price)
    communicator(chart_name, indicator_name, operation, takeprofit_pips, stoploss_pips)


def communicator(chart_name, indicator, operation, takeprofit_pips, stoploss_pips):
    proc = subprocess.call(["python3",
                            "./atr_sf_api_communicator.py",
                            chart_name,
                            indicator,
                            operation,
                            str(takeprofit_pips),
                            str(stoploss_pips)
                            ])
    if proc == 2:
        subprocess.call(["python3",
                         "/home/remote/PycharmProjects/trade/atr_sf_api_communicator.py",
                         chart_name,
                         indicator,
                         operation,
                         str(takeprofit_pips),
                         str(stoploss_pips)
                         ])


def main_loop():
    target_min_sec = "00:40"
    print(f"{date_now()} {time_now_hms()} Trader started...")

    while True:
        if time_now_ms() == target_min_sec:
            print(f"\n\n{date_now()} {time_now_hms()}")
            for chart in active_charts:
                if chart["is_currency"]:
                    check_smartforex_condition(chart["name"])
                else:
                    check_ce_condition(chart["name"])
                check_atr_condition(chart["name"])
        time.sleep(1)


# for chart in active_charts:
#     if chart["is_currency"]:
#         smartforex_trade = check_smartforex_condition(chart["name"])
#         print("smartforex_trade", smartforex_trade)
#     else:
#         ce_trade = check_ce_condition(chart["name"])
#         print("ce_trade",ce_trade)
#     atr_trade = check_atr_condition(chart["name"])
#     print("atr_trade", atr_trade)


if __name__ == "__main__":
    main_loop()
