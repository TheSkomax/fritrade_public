# =================================================================
# TRADINGVIEW SCRAPER for ATR and Smart Forex (+ CE) values
# =================================================================

from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from csv import DictReader
import mysql.connector
from datetime import date
from datetime import datetime
import time
import os
import dotenv

dotenv.load_dotenv("../.env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]


options = webdriver.FirefoxOptions()
options.binary_location = "/usr/bin/firefox"
driverService = Service("/usr/local/bin/geckodriver")

target_min_sec = "59:51"
# target_min_sec = "42:40"
chart_url = "https://www.tradingview.com/chart"
cookies_file = "cookies-tradingview-com_fritrade.csv"
table_name_part = "atr_smartfrx_"
handles_of_windows = {
    "US500_1h": None,
    "EURCHF_1h": None,
}

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
}

db_connection = mysql.connector.connect(host="localhost",
                                        user=mysql_user,
                                        passwd=mysql_passw,
                                        database="fri_trade",
                                        autocommit=True)
fri_trade_cursor = db_connection.cursor(buffered=True)


driver = webdriver.Firefox(service=driverService,
                           options=options)
driver.get(chart_url)


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


def open_browser():
    def get_cookies_values(file):
        with open(file, encoding="utf-8-sig") as f:
            dict_reader = DictReader(f)
            list_of_dicts = list(dict_reader)
        return list_of_dicts

    cookies = get_cookies_values(cookies_file)

    for cookie in cookies:
        driver.add_cookie(cookie)
    print("Cookies added, refreshing")
    driver.refresh()

    handle_num = 0
    for needed_item in handles_of_windows.keys():
        handle_num += 1
        driver.execute_script(f'window.open("{chart_url}")')
        handles_of_windows.update({needed_item: driver.window_handles[handle_num]})
        driver.switch_to.window(handles_of_windows[needed_item])
        input(f"- {needed_item}  Please select correct symbol and timeframe and press ENTER when fully loaded")
    input("Please close the default first tab and press ENTER\n")
    print(f"{date_now()} {time_now_hms()} Driver deployed!")


def check_if_loaded():
    for chart in handles_of_windows.keys():
        driver.switch_to.window(handles_of_windows[chart])

        for item in xpaths.keys():
            val = driver.find_element(By.XPATH, xpaths[item])
            if val.is_displayed():
                print(f"{chart} {item}    {val.text}")
            else:
                print(f"!!! ERROR {chart} {item}    {val.text}")


def get_values():
    for chart in handles_of_windows.keys():
        driver.switch_to.window(handles_of_windows[chart])
        ce_values_names = ['ce_bool_buy', 'ce_bool_sell']
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
            'price_low': None
        }

        for needed_value in xpaths.keys():
            val = driver.find_element(By.XPATH, xpaths[needed_value])
            if needed_value not in ce_values_names:
                values_dict[needed_value] = float(val.text)
            else:
                try:
                    float(val.text)
                    values_dict[needed_value] = True
                except ValueError:
                    values_dict[needed_value] = False

        # print(values_dict)
        write_to_db(values_dict, chart)


def write_to_db(values_dict, chart_name):
    q = f"""insert into fri_trade.{table_name_part}{chart_name} (timeOfValue, dateOfValue, price_open, price_high, 
    price_low, price_close, value_atr, ce_bool_buy, ce_bool_sell, sf_bool_buy, sf_bool_sell, sf_bool_buy_strong, 
    sf_bool_sell_strong, processed, value_atr_up, value_atr_down) VALUES('{time_now_hms()}', '{date_now()}', 
    '{values_dict['price_open']}', '{values_dict['price_high']}', '{values_dict['price_low']}', 
    '{values_dict['price_close']}', '{values_dict['value_atr']}', {values_dict['ce_bool_buy']}, 
    {values_dict['ce_bool_sell']}, '{values_dict['sf_bool_buy']}', '{values_dict['sf_bool_sell']}', 
    '{values_dict['sf_bool_buy_strong']}', '{values_dict['sf_bool_sell_strong']}', False, 
    '{values_dict['value_atr_up']}', '{values_dict['value_atr_down']}')"""

    fri_trade_cursor.execute(q)
    print(f"{date_now()} {time_now_hms()} {chart_name} Added to database")


def main_loop():
    open_browser()

    print(f"{date_now()} {time_now_hms()} Scraper started... (Target time: *{target_min_sec})\n")
    while True:
        if time_now_ms() == target_min_sec:
            print("\n")
            get_values()
        time.sleep(1)


if __name__ == "__main__":
    main_loop()
