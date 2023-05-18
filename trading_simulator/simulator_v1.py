import os
import dotenv
import mysql.connector
from datetime import date
from datetime import datetime

dotenv.load_dotenv("/home/fritrade/PycharmProjects/trade/.env")
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)

balance_eur = 10000
lots = 0.09
pip_eur = 0.1  # @0.01 lot
spread_pips = 0.00014  # @0.01 lot
margin_one_microlot = 33.3
base_onehundred_margin_eur = 2.32  # @price 100 and 0.01 lot
active_charts = [{"name": "US500_1h", "is_currency": False}, {"name": "EURCHF_1h", "is_currency": True}]


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


def get_all_candles(symbol, timeframe):
    all_candles_list = []
    q = f"""SELECT * FROM fri_trade.candle_data_{symbol}_{timeframe}_atr_sf order by id desc"""
    fri_trade_cursor.execute(q)
    all_candles = fri_trade_cursor.fetchall()

    for candle_data in all_candles:
        candle_dict = {
            'id': candle_data[0],
            'price_open': candle_data[1],
            'price_high': candle_data[2],
            'price_low': candle_data[3],
            'price_close': candle_data[4],

            'value_atr': candle_data[5],
            'ce_bool_buy': candle_data[6],
            'ce_bool_sell': candle_data[7],

            'sf_bool_buy': candle_data[8],
            'sf_bool_sell': candle_data[9],
            'sf_bool_buy_strong': candle_data[10],
            'sf_bool_sell_strong': candle_data[11],

            'processed': candle_data[12],
            'value_atrb_up': candle_data[13],
            'value_atrb_down': candle_data[14],
            "50sma": candle_data[15]
        }
        all_candles_list.append(candle_dict)
    return all_candles_list


def get_next_candle(symbol, timeframe):
    q = f"""SELECT * FROM fri_trade.candle_data_{symbol}_{timeframe}_atr_sf where processed = 0 order by id desc"""
    fri_trade_cursor.execute(q)
    candle_data = fri_trade_cursor.fetchone()

    candle = {
        'id': candle_data[0],
        'price_open': candle_data[1],
        'price_high': candle_data[2],
        'price_low': candle_data[3],
        'price_close': candle_data[4],

        'value_atr': candle_data[5],
        'ce_bool_buy': candle_data[6],
        'ce_bool_sell': candle_data[7],

        'sf_bool_buy': candle_data[8],
        'sf_bool_sell': candle_data[9],
        'sf_bool_buy_strong': candle_data[10],
        'sf_bool_sell_strong': candle_data[11],

        'value_atrb_up': candle_data[12],
        'value_atrb_down': candle_data[13],

        "50sma": candle_data[14]
    }
    return candle


def get_previous_candle(new_id, symbol, timeframe):
    q = f"""SELECT * FROM fri_trade.candle_data_{symbol}_{timeframe}_atr_sf where id = {new_id + 1}"""
    fri_trade_cursor.execute(q)
    candle_data = fri_trade_cursor.fetchone()
    if candle_data is not None:
        prev_candle = {
            'id': candle_data[0],
            'price_open': candle_data[1],
            'price_high': candle_data[2],
            'price_low': candle_data[3],
            'price_close': candle_data[4],

            'value_atr': candle_data[5],
            'ce_bool_buy': candle_data[6],
            'ce_bool_sell': candle_data[7],

            'sf_bool_buy': candle_data[8],
            'sf_bool_sell': candle_data[9],
            'sf_bool_buy_strong': candle_data[10],
            'sf_bool_sell_strong': candle_data[11],

            'value_atrb_up': candle_data[12],
            'value_atrb_down': candle_data[13],

            "50sma": candle_data[14]
        }
        return prev_candle
    else:
        return None


def check_condition_sf_strong(candle, prev_candle):
    operation = None
    print("SF strong - checking candle", candle["id"])

    buy_strong, sell_strong, new_id, price_close = candle["sf_bool_buy_strong"], candle["sf_bool_sell_strong"],\
        candle["id"], candle["price_close"]

    if prev_candle is not None:
        prev_buy_strong, prev_sell_strong = prev_candle["sf_bool_buy_strong"], prev_candle["sf_bool_sell_strong"]

        # buy condition
        if buy_strong and not prev_buy_strong:
            print(f"SF Strong - buy!")
            operation = "buy"

        # sell condition
        elif sell_strong and not prev_sell_strong:
            print(f"SF Strong - sell!")
            operation = "sell"

        if operation is not None:
            get_sl_tp_for_sf_trade("EURCHF", operation, price_close, new_id, candle["value_atrb_up"],
                                   candle["value_atrb_down"], candle["50sma"])


def check_condition_atr(candle, prev_candle, symbol):
    operation = None
    # print("ATR - checking candle", candle["id"])

    new_value_atr, new_price_close, new_id = candle["value_atr"], candle["price_close"], candle["id"]

    # prev_candle = get_previous_candle(new_id)
    if prev_candle is not None:
        prev_value_atr, prev_price_close = prev_candle["value_atr"], prev_candle["price_close"]

        # buy condition
        if new_price_close > new_value_atr and prev_price_close < prev_value_atr:
            # print(f"{chart_name} ATR - buy!")
            print(f"ATR - buy!")
            operation = "buy"

        # sell condition
        elif new_price_close < new_value_atr and prev_price_close > prev_value_atr:
            # print(f"{chart_name} ATR - sell!")
            print(f"ATR - sell!")
            operation = "sell"
        else:
            # print(f"{chart_name} ATR - no trade!")
            # print(f"ATR - no trade!")
            pass


    if operation is not None:
        get_sl_tp_for_atr_trade(symbol, operation, new_value_atr, new_price_close, new_id,
                                candle["value_atrb_up"], candle["value_atrb_down"], candle["50sma"])


def update_processed(candle,symbol, timeframe):
    new_id = candle["id"]
    q = f"""UPDATE fri_trade.candle_data_{symbol}_{timeframe}_atr_sf SET processed = true where id = {new_id}"""
    fri_trade_cursor.execute(q)


def get_sl_tp_for_atr_trade(symbol, operation, value_atr, candle_price_close, new_id, value_atrb_up,
                            value_atrb_down, sma50):
    indicator_name = "atr"
    if operation == "buy":
        # stoploss_pips = (candle_price_close - value_atr) + ((candle_price_close - value_atr) * 0.2)
        stoploss_pips = candle_price_close - value_atr
        stoploss_price = round(candle_price_close - stoploss_pips, 5)

        # q = f"""SELECT value_atrb_up FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        takeprofit_price = value_atrb_up
        takeprofit_pips = takeprofit_price - candle_price_close

    else:  # elif operation == "sell":
        # stoploss_pips = (value_atr - candle_price_close) + ((value_atr - candle_price_close) * 0.2)
        stoploss_pips = value_atr - candle_price_close
        stoploss_price = round(candle_price_close + stoploss_pips, 5)

        # q = f"""SELECT value_atrb_down FROM fri_trade.{table_name_part}{chart_name} where id = {new_id}"""
        takeprofit_price = value_atrb_down
        takeprofit_pips = candle_price_close - takeprofit_price

    open_position(symbol, operation, candle_price_close, indicator_name, takeprofit_price, stoploss_price, new_id,
                  sma50)


def get_sl_tp_for_sf_trade(symbol, operation, candle_price_close, new_id, value_atrb_up, value_atrb_down,
                           sma50):
    indicator_name = "smartforex"
    if operation == "buy":
        stoploss_pips = candle_price_close - value_atrb_down
        stoploss_price = round(candle_price_close - stoploss_pips, 5)

        takeprofit_price = value_atrb_up
        takeprofit_pips = takeprofit_price - candle_price_close
    else:  # elif operation == "sell":
        stoploss_pips = value_atrb_up - candle_price_close
        stoploss_price = round(candle_price_close + stoploss_pips, 5)

        takeprofit_price = value_atrb_down
        takeprofit_pips = candle_price_close - takeprofit_price

    open_position(symbol, operation, candle_price_close, indicator_name, takeprofit_price, stoploss_price, new_id, sma50)


def open_position(symbol, operation, candle_price_close, indicator_name, takeprofit_price, stoploss_price, candle_id,
                  sma50):
    timeframe = "1h"
    opened = True

    # (cena, na ktorej sa pozicia otvara * marza_pri_cene_100) / 100
    margin_needed_for_new_trade = round((candle_price_close * base_onehundred_margin_eur) / 100, 2)
    margin_needed_for_new_trade = round((lots*100) * margin_one_microlot, 2) # pre EURCHF

    q = f"""select opened from fri_trade.simulator_positions_2 where opened = true and ordertype = '{operation}'"""
    fri_trade_cursor.execute(q)
    opened_orders = fri_trade_cursor.fetchone()

    sma_bool = False
    if (operation == "buy" and sma50 >= candle_price_close) or (operation == "sell" and sma50 <= candle_price_close):
        sma_bool = True

    if operation == "buy":
        opened_at_price = candle_price_close + (spread_pips * (lots * 100))
    elif operation == "sell":
        opened_at_price = candle_price_close - (spread_pips * (lots * 100))
    # if opened_orders is None and sma_bool:
    # if sma_bool:
    # if opened_orders is None:
    if True:
        q = f"""insert into fri_trade.simulator_positions_2 (symbol, ordertype, lots, margin,
        conditionTriggered, timeframe, opened, reason, profit, takeprofit_price, stoploss_price, price_open, open_candle_id)
        VALUES ('{symbol}', '{operation}', '{lots}', '{margin_needed_for_new_trade}', '{indicator_name}', '{timeframe}', 
        {opened}, '{None}', 0, {takeprofit_price}, {stoploss_price}, {opened_at_price}, {candle_id})"""  # {candle_price_close}
        fri_trade_cursor.execute(q)

        print(f"Order opened (added to database) - {symbol} {indicator_name} {operation} {candle_id}")
    else:
        print(f"There is another {operation} position on {symbol} {timeframe}! No new position opened!")


def position_checker(candle):
    all_positions_list = []
    q = """SELECT * FROM fri_trade.simulator_positions_2 where opened like true"""
    fri_trade_cursor.execute(q)
    data = fri_trade_cursor.fetchall()

    for position_data in data:
        position_dict = {
            'id': position_data[0],
            'symbol': position_data[1],
            'ordertype': position_data[2],
            'lots': position_data[3],
            'margin': position_data[4],

            'condition': position_data[5],
            'timeframe': position_data[6],
            'opened': position_data[7],

            'reason': position_data[8],
            'profit': position_data[9],
            'takeprofit_price': position_data[10],
            'stoploss_price': position_data[11],
            'price_open': position_data[12],

        }
        all_positions_list.append(position_dict)

    for position in all_positions_list:
        tp, sl = position["takeprofit_price"], position["stoploss_price"]

        if position["ordertype"] == "buy":
            if candle["price_high"] >= tp or candle["price_close"] >= tp:
                reason = "TP"

                profit_pips = (position["takeprofit_price"] - position["price_open"])
                profit_eur = round(profit_pips * (pip_eur * (lots * 100)), 2)

                # EURCHF CURRENCY OVERRIDE
                profit_eur = round((profit_pips * 10000) * pip_eur * (lots * 100), 2)


                q = f"""UPDATE simulator_positions_2 set opened = false, reason = '{reason}', profit = {profit_eur}, 
                price_close = {tp}, close_candle_id = {candle['id']} where id = {position['id']}"""
                fri_trade_cursor.execute(q)

            elif candle["price_low"] <= sl or candle["price_close"] <= sl:
                reason = "SL"

                profit_pips = (position["stoploss_price"] - position["price_open"])
                profit_eur = round(profit_pips * (pip_eur * (lots * 100)), 2)

                # EURCHF CURRENCY OVERRIDE
                profit_eur = round((profit_pips * 10000) * pip_eur * (lots * 100), 2)

                q = f"""UPDATE simulator_positions_2 set opened = false, reason = '{reason}', profit = {profit_eur},
                price_close = {sl}, close_candle_id = {candle['id']} where id = {position['id']}"""
                fri_trade_cursor.execute(q)

            elif (candle["price_high"] >= tp or candle["price_close"] >= tp) and \
                    (candle["price_low"] <= sl or candle["price_close"] <= sl):
                reason = "undecided"
                profit_eur = 0

                q = f"""UPDATE simulator_positions_2 set opened = false, reason = '{reason}', profit = {profit_eur}
                                where id = {position['id']}"""
                fri_trade_cursor.execute(q)

        else:  # elif position["ordertype"] == "sell":
            if candle["price_low"] <= tp or candle["price_close"] <= tp:
                reason = "TP"

                profit_pips = (position["price_open"] - position["takeprofit_price"])
                profit_eur = round(profit_pips * (pip_eur * (lots * 100)), 2)

                # EURCHF CURRENCY OVERRIDE
                profit_eur = round((profit_pips * 10000) * pip_eur * (lots * 100), 2)

                q = f"""UPDATE simulator_positions_2 set opened = false, reason = '{reason}', profit = {profit_eur},
                price_close = {tp}, close_candle_id = {candle['id']} where id = {position['id']}"""
                fri_trade_cursor.execute(q)

            elif candle["price_high"] >= sl or candle["price_close"] >= sl:
                reason = "SL"

                profit_pips = (position["price_open"] - position["stoploss_price"])
                profit_eur = round(profit_pips * (pip_eur * (lots * 100)), 2)

                # EURCHF CURRENCY OVERRIDE
                profit_eur = round((profit_pips * 10000) * pip_eur * (lots * 100), 2)

                q = f"""UPDATE simulator_positions_2 set opened = false, reason = '{reason}', profit = {profit_eur},
                price_close = {sl}, close_candle_id = {candle['id']} where id = {position['id']}"""
                fri_trade_cursor.execute(q)

            elif (candle["price_low"] <= tp or candle["price_close"] <= tp) and \
                    (candle["price_high"] <= sl or candle["price_close"] <= sl):
                reason = "undecided"
                profit_eur = 0

                q = f"""UPDATE simulator_positions_2 set opened = false, reason = '{reason}', profit = {profit_eur}
                    where id = {position['id']}"""
                fri_trade_cursor.execute(q)


def main():
    symbol = input("Insert symbol: ")
    timeframe = input("Insert timeframe: ")
    all_candles_list = get_all_candles(symbol, timeframe)
    q = f"""UPDATE fri_trade.candle_data_{symbol}_{timeframe}_atr_sf SET processed = false"""
    fri_trade_cursor.execute(q)

    for candle in all_candles_list:
        prev_candle = None
        candle_index = all_candles_list.index(candle)
        if candle_index != 0:
            prev_candle = all_candles_list[candle_index - 1]

        position_checker(candle)
        check_condition_sf_strong(candle, prev_candle)
        # check_condition_atr(candle, prev_candle, symbol)

        update_processed(candle, symbol, timeframe)

    print("\n---   DONE!")


if __name__ == "__main__":
    main()


# TODO free margin kontrolor, ktory ju bude pocitat z balacne a z margin na otvorenych poziciach, margin z pozicii, ktore sa zavru, prirata k free margin
# TODOne nastavit to, nech to ignoruje error values ako 99999.9 >>> prerobene hodnoty v table a scraper nastaveny, nech tam dava hodnoty z predoslej sviecky
# TODO urobit funkciu na SF a CE
# TODOne skusit s 50sma, ze neotvarat ked je cena pod nim ci tak nejak
# TODOne nech to neotvara buy ked uz je jeden buy otvoreny - tym padom max otvorenych pozicii naraz su 2???
# TODO profit protector - ukradnut z prveho tradera, nech to berie dajme tomu len ten 10% zisk na pozitivny stoploss ked je to zatial len s 0.01 lotmi

# otvaracia cena pozicie bude vzdy price_close tej sviecky, ktora potvrdi podmienku atr alebo SF / CE