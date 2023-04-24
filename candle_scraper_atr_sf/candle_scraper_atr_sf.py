# ===================================================================================
# TRADINGVIEW DATASCRAPER FOR ATR, SMARTFOREX AND CHANDELIER EXIT INDICATORS
# ===================================================================================

import time
from datetime import date
from datetime import datetime
from csv import DictReader
import dotenv
import os
import pyautogui
import mysql.connector
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By

options = webdriver.FirefoxOptions()
options.binary_location = "/usr/bin/firefox"
driverService = Service("/usr/local/bin/geckodriver")

chart_url = "https://www.tradingview.com/chart"
cookies_file = "/trader_atr_sf/cookies-tradingview-com_mmajchl.csv"

xpaths = {
    "ce_bool_buy": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[3]/div",
    "ce_bool_sell": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[3]/div[2]/div/div[6]/div",

    "sf_bool_buy": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[1]/div",
    "sf_bool_sell": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[2]/div",
    "sf_bool_buy_strong": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[3]/div",
    "sf_bool_sell_strong": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[4]/div",

    "value_atr":     "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[4]/div[2]/div/div[1]/div",
    "value_atr_up":  "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[4]/div[2]/div/div[2]/div",
    "value_atr_down": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[4]/div[2]/div/div[3]/div",

    "price_open": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[2]/div[2]",
    "price_close": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[5]/div[2]",
    "price_high": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[3]/div[2]",
    "price_low": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[4]/div[2]",

    "50sma": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[4]/div[2]/div/div[6]/div"
}


# mysql - fri_trade schema
dotenv.load_dotenv("/home/fritrade/PycharmProjects/trade/.env")
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)

pyautogui.FAILSAFE = False

def time_now_hms():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    # print(time_actual)
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


class Scraping:
    def open_browser(self):
        def get_cookies_values(file):
            with open(file) as f:
                dict_reader = DictReader(f)
                list_of_dicts = list(dict_reader)
            return list_of_dicts

        self.driver = webdriver.Firefox(service=driverService,
                                        options=options)
        self.driver.get(chart_url)

        cookies = get_cookies_values(cookies_file)
        for cook in cookies:
            self.driver.add_cookie(cook)
        self.driver.refresh()
        print("Driver successfuly deployed!")

    def start_scraping(self, symbol, timeframe, candle_count, pos_x, pos_y):
        candles_done = 0
        ce_values_names = ['ce_bool_buy', 'ce_bool_sell']
        bools_values_names = ['ce_bool_buy', 'ce_bool_sell', 'sf_bool_buy',
                              'sf_bool_sell', 'sf_bool_buy_strong', 'sf_bool_sell_strong']
        error = False

        while candles_done < candle_count:
            values_dict = {
                'ce_bool_buy': None,
                'ce_bool_sell': None,

                'sf_bool_buy': None,
                'sf_bool_sell': None,
                'sf_bool_buy_strong': None,
                'sf_bool_sell_strong': None,

                'value_atr': None,
                'value_atr_up': None,
                'value_atr_down': None,

                'price_open': None,
                'price_close': None,
                'price_high': None,
                'price_low': None,

                "50sma": None
            }
            pyautogui.moveTo(pos_x, pos_y)
            pyautogui.press("left")

            while None in values_dict.values():
                for needed_value in xpaths.keys():
                    val = self.driver.find_element(By.XPATH, xpaths[needed_value])

                    while not val.is_displayed() and val.text == '':
                        time.sleep(.2)

                    else:
                        if needed_value not in ce_values_names:
                            try:
                                values_dict[needed_value] = float(val.text)
                            except ValueError as err:
                                # values_dict[needed_value] = float(val.text)
                                # values_dict[needed_value] = 99999.9


                                # print(f"ERROR {needed_value} {val.text}\n{err}")
                                # soundfile = "/home/fritrade/PycharmProjects/trade/trade_beep.mp3"
                                # os.system("mpg123 -q " + soundfile)
                                # input("Press ENTER to continue and click inside the chart")
                                # time.sleep(2)ň

                                # tento while vymazat, nepomaha to ani ked to pocka 20 sekund na obnovenie hodnoty, stale to hadze Valueerror

                                x=0
                                while val.text == "" or x <= 5:
                                    try:
                                        # time.sleep(1)
                                        x += 1
                                        val = self.driver.find_element(By.XPATH, xpaths[needed_value])
                                        values_dict[needed_value] = float(val.text)
                                    except ValueError:
                                        pass

                                else:
                                    error = True
                                    error_val = needed_value
                                    if needed_value in bools_values_names:
                                        print(f"\n{needed_value} Valuerror - setting value to 0 (bool)")
                                        values_dict[needed_value] = 0
                                    else:
                                        # print(f"\n{needed_value} Valuerror - setting value to 99999.9 (float)")
                                        print(f"\n{needed_value} Valuerror - setting value to previous (float)")
                                        # values_dict[needed_value] = 99999.9

                                        q = f"""select {values_dict[needed_value]} from
                                            fri_trade.candle_data_{symbol}_{timeframe}_atr_sf order by id desc"""
                                        fri_trade_cursor.execute(q)
                                        replacement_val = fri_trade_cursor.fetchone()[0]
                                        values_dict[needed_value] = replacement_val
                        else:
                            try:
                                float(val.text)
                                values_dict[needed_value] = True
                            except ValueError:
                                values_dict[needed_value] = False

                            # q = f"""insert into fri_trade.candle_data_{symbol}_{timeframe}_atr_sf (price_open, price_high, price_low, price_close, value_atr, ce_bool_buy, ce_bool_sell, sf_bool_buy, sf_bool_sell, sf_bool_buy_strong, sf_bool_sell_strong, processed, value_atr_up, value_atr_down, 50sma) VALUES('{values_dict['price_open']}', '{values_dict['price_high']}', '{values_dict['price_low']}', '{values_dict['price_close']}', '{values_dict['value_atr']}', {values_dict['ce_bool_buy']}, {values_dict['ce_bool_sell']}, '{values_dict['sf_bool_buy']}', '{values_dict['sf_bool_sell']}', '{values_dict['sf_bool_buy_strong']}', '{values_dict['sf_bool_sell_strong']}', False, '{values_dict['value_atr_up']}', '{values_dict['value_atr_down']}', '{values_dict['50sma']}')"""
                            # fri_trade_cursor.execute(q)
                            # candles_done += 1
            if error:
                q = f"""insert into fri_trade.candle_data_{symbol}_{timeframe}_atr_sf (price_open, price_high, price_low, price_close, value_atr, ce_bool_buy, ce_bool_sell, sf_bool_buy, sf_bool_sell, sf_bool_buy_strong, sf_bool_sell_strong, processed, value_atr_up, value_atr_down, 50sma, error_vals) VALUES('{values_dict['price_open']}', '{values_dict['price_high']}', '{values_dict['price_low']}', '{values_dict['price_close']}', '{values_dict['value_atr']}', {values_dict['ce_bool_buy']}, {values_dict['ce_bool_sell']}, '{values_dict['sf_bool_buy']}', '{values_dict['sf_bool_sell']}', '{values_dict['sf_bool_buy_strong']}', '{values_dict['sf_bool_sell_strong']}', False, '{values_dict['value_atr_up']}', '{values_dict['value_atr_down']}', '{values_dict['50sma']}', '{error_val}')"""
                fri_trade_cursor.execute(q)
                candles_done += 1
            else:
                q = f"""insert into fri_trade.candle_data_{symbol}_{timeframe}_atr_sf (price_open, price_high, price_low, price_close, value_atr, ce_bool_buy, ce_bool_sell, sf_bool_buy, sf_bool_sell, sf_bool_buy_strong, sf_bool_sell_strong, processed, value_atr_up, value_atr_down, 50sma, error_vals) VALUES('{values_dict['price_open']}', '{values_dict['price_high']}', '{values_dict['price_low']}', '{values_dict['price_close']}', '{values_dict['value_atr']}', {values_dict['ce_bool_buy']}, {values_dict['ce_bool_sell']}, '{values_dict['sf_bool_buy']}', '{values_dict['sf_bool_sell']}', '{values_dict['sf_bool_buy_strong']}', '{values_dict['sf_bool_sell_strong']}', False, '{values_dict['value_atr_up']}', '{values_dict['value_atr_down']}', '{values_dict['50sma']}', False)"""
                fri_trade_cursor.execute(q)
                candles_done += 1

browser = Scraping()
browser.open_browser()


def main_loop():
    while True:
        symbol = input("Enter symbol that is going to be scraped: ")
        timeframe = input("Enter its timeframe: ")
        candle_count = int(input("Enter candle count (7200 should be for all): "))
        input(f"Select correct symbol and timeframe on the chart and press ENTER when fully loaded")

        print("Going to sleep for 5 seconds, move cursor to tradingview chart")
        time.sleep(5)
        pos_x, pos_y = pyautogui.position()
        print(pos_x, pos_y)

        print(f"{date_now()} {time_now_hms()} Scraping...")
        browser.start_scraping(symbol, timeframe, candle_count, pos_x, pos_y)
        print(f"{date_now()} {time_now_hms()} Scraping of {symbol} {timeframe} done!")


if __name__ == "__main__":
    main_loop()
