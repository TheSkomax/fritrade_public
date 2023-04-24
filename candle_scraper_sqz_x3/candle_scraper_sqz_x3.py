# ===================================================================================
# TRADINGVIEW DATASCRAPER FOR THREE SQZ INDICATORS
# ===================================================================================

import calendar
import threading
import time
from csv import DictReader
import datetime
from datetime import date
from datetime import datetime
import traceback
import logging
import dotenv
import os
import pyautogui
import mysql.connector
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary

chart_url = "https://www.tradingview.com/chart"
symbol_select_button_xpath = "/html/body/div[3]/div[6]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div/div/div[2]/span"

open_price_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[2]/div[2]"
close_price_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[5]/div[2]"
high_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[3]/div[2]"
low_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[2]/div/div[4]/div[2]"

sqz_kc_20_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[3]/td[2]/div/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div"
sqz_kc_40_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[5]/td[2]/div/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div"
sqz_kc_60_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[7]/td[2]/div/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div"

dotenv.load_dotenv(".env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]

# mysql - fri_trade schema
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


class Trading:
    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.driver_us500 = None
        self.title_to_assert_us500 = {"symbol": "US500",
                                      "chart_name": "INDEXY Fritrade",
                                      }

    def open_browser(self):
        def get_cookies_values(file):
            with open(file) as f:
                dict_reader = DictReader(f)
                list_of_dicts = list(dict_reader)
            return list_of_dicts

        cookies = get_cookies_values("/home/fritrade/PycharmProjects/trade/tradingview_cookies_mmajchl901.csv")
        binary = FirefoxBinary('/usr/bin/firefox')

        self.driver_us500 = webdriver.Firefox(service=Service(GeckoDriverManager().install()),
                                              options=self.options,
                                              firefox_binary=binary)
        self.driver_us500.get("https://www.tradingview.com/chart")
        for cook in cookies:
            self.driver_us500.add_cookie(cook)
        self.driver_us500.refresh()
        self.handle_num = 0

        out = "US500 driver successfuly deployed!"
        print(out)

    def get_key_value(self):
        x = 0
        while x < 5030:
            ok_20 = False
            ok_40 = False
            ok_60 = False
            pyautogui.press("left")

            while not ok_20 and not ok_40 and not ok_60:

                # value = self.driver_us500.find_element(By.XPATH, key_value_xpath)
                # current_price = self.driver_us500.find_element(By.XPATH, current_price_xpath)
                sqz_kc_20 = self.driver_us500.find_element(By.XPATH, sqz_kc_20_xpath)
                sqz_kc_40 = self.driver_us500.find_element(By.XPATH, sqz_kc_40_xpath)
                sqz_kc_60 = self.driver_us500.find_element(By.XPATH, sqz_kc_60_xpath)
                low = self.driver_us500.find_element(By.XPATH, low_xpath)
                high = self.driver_us500.find_element(By.XPATH, high_xpath)
                open_price = self.driver_us500.find_element(By.XPATH, open_price_xpath)
                close_price = self.driver_us500.find_element(By.XPATH, close_price_xpath)

                if not sqz_kc_20.is_displayed() or not sqz_kc_40.is_displayed() or not sqz_kc_60.is_displayed() or not low.is_displayed() or not high.is_displayed() or not open_price.is_displayed() or not close_price.is_displayed():
                    time.sleep(0.5)
                else:
                    # current_price = float(current_price.text)
                    # atrb_takeprofit = float(atrb_takeprofit.text)
                    # atrb_stoploss = float(atrb_stoploss.text)
                    # sqz_kc_20_float = float(sqz_kc_20.text)
                    # sqz_kc_40_float = float(sqz_kc_40.text)
                    # sqz_kc_60_float = float(sqz_kc_60.text)
                    low_float = float(low.text)
                    high_float = float(high.text)
                    open_price_float = float(open_price.text)
                    close_price_float = float(close_price.text)

                    if "−" in sqz_kc_20.text:
                        sqz_kc_20_float = float(sqz_kc_20.text.replace("−", '-'))
                        ok_20 = True
                    else:
                        sqz_kc_20_float = float(sqz_kc_20.text)
                        ok_20 = True

                    if "−" in sqz_kc_40.text:
                        sqz_kc_40_float = float(sqz_kc_40.text.replace("−", '-'))
                        ok_40 = True
                    else:
                        sqz_kc_40_float = float(sqz_kc_40.text)
                        ok_40 = True

                    if "−" in sqz_kc_60.text:
                        sqz_kc_60_float = float(sqz_kc_60.text.replace("−", '-'))
                        ok_60 = True
                    else:
                        sqz_kc_60_float = float(sqz_kc_60.text)
                        ok_60 = True

                    # return [high_float, low_float, open_price_float, close_price_float,
                    #         sqz_kc_20_float, sqz_kc_40_float, sqz_kc_60_float]
                    q = f"insert into fri_trade.US500_1h_data (high, low, open_price, close_price, sqz_kc20, sqz_kc40, sqz_kc60) values ('{high_float}', '{low_float}', '{open_price_float}', '{close_price_float}', '{sqz_kc_20_float}', '{sqz_kc_40_float}', '{sqz_kc_60_float}')"
                    fri_trade_cursor.execute(q)
                    x += 1

browser = Trading()
browser.open_browser()




should_start = input("Should I start gathering data?\n")
if should_start == "y":
    browser.get_key_value()

should_start_again = input("Should I start again?\n")
if should_start_again == "y":
    browser.get_key_value()
