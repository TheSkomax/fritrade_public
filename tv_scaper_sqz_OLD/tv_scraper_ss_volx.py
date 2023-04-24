import calendar
import threading
import time
from csv import DictReader
import datetime
from datetime import date
from datetime import datetime
import traceback
import logging

import mysql.connector
import pytz
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from webdriver_manager.firefox import GeckoDriverManager
import os
import dotenv

dotenv.load_dotenv("../.env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]

block_bar = "▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"
friday_day = 4


chart_url = "https://www.tradingview.com/chart"
symbol_select_button_xpath = "/html/body/div[3]/div[6]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[5]/div/div/div[2]/span/span[2]"

key_value_xpath = "/html/body/div[3]/div[1]/div[2]/div[1]/div/table/tr[3]/td[2]/div/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div"
timeframe_number_xpath = "/html/body/div[3]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[3]"

atrb_up_xpath =  "/html/body/div[3]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[2]/div"
atrb_low_xpath = "/html/body/div[3]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[3]/div"
current_price_xpath = "/html/body/div[3]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[1]/div[1]/div[2]/div/div[5]/div[2]"

timeframe_button_xpaths = {
    "1h": "/html/body/div[3]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[1]",
    "2h": "/html/body/div[3]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[2]",
    "3h": "/html/body/div[3]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[3]",
    "4h": "/html/body/div[3]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[4]",
    "D":  "/html/body/div[3]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[5]",
    "W":  "/html/body/div[3]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[6]",
    "M":  "/html/body/div[3]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[7]",
    "check": "/html/body/div[3]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[1]/div[1]/div[1]/div[1]/div[3]",
}
timeframe_numbers = {
    "1h": "1h",
    "2h": "2h",
    "3h": "3h",
    "4h": "4h",
    "D": "1D",
    "W": "1W",
    "M": "1M"
}

handles_tabs = {
    "1h": "",
    "2h": "",
    "3h": "",
    "4h": "",
    "D": "",
    "W": "",
    "M": "",
    "def": ""
}


"""!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""

# pri uprave timeframeov treba upravit aj spustanie metod v right_time_finder-och!!!!!!!!!!!!!!!
timeframe_list = ["1h", "2h", "3h", "4h", "D", "W"]
symbol = "VIX"
threads_done = {symbol: False, }
symbol_atrb = {symbol: {}, }

active_vix = {}

"""!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""


# ====== browser logging ======
log_browser = logging.getLogger("VOLX_browser_logger")
log_browser.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_volx_browser.log")
file_handler.setFormatter(log_formatter)
log_browser.addHandler(file_handler)

# ====== writer Logging ======
log_writer = logging.getLogger("writer_logger")
log_writer.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_writer.log")
file_handler.setFormatter(log_formatter)
log_writer.addHandler(file_handler)


# ====== writing logging ======
log_writing = logging.getLogger("VOLX_writing_logger")
log_writing.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_volx_writing.log")
file_handler.setFormatter(log_formatter)
log_writing.addHandler(file_handler)


log_browser.info(f"\n{block_bar}")


def check_current_day():
    # 0 = monday...
    daynum = int(datetime.today().weekday())
    return int(daynum)


def check_current_hour():
    hour_actual = datetime.now().hour
    return int(hour_actual)


def check_current_minute():
    minute_actual = datetime.now().minute
    return int(minute_actual)


def check_current_second():
    second_actual = datetime.now().second
    return int(second_actual)


def time_now():
    time_object = datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    # print(time_actual)
    return time_actual


def date_now():
    date_object = date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


def dst_check(dt=None, timezone=None):
    if dt is None:
        dt = datetime.utcnow()
    timezone = pytz.timezone(timezone)
    timezone_aware_date = timezone.localize(dt, is_dst=None)
    return timezone_aware_date.tzinfo._dst.seconds != 0
# US indexy (a akcie?)
# dst_check(datetime(date.today().year, date.today().month, date.today().day), timezone="US/Pacific")


def mysql_keepalive():
    while True:
        q = "select id from fri_trade.VIX_1h order by id desc limit 1"
        fri_trade_cursor.execute(q)
        res = fri_trade_cursor.fetchall()
        log_writer.info("Keeping mysql connection alive")
        time.sleep(3600)


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
        self.driver = None
        self.title_to_assert = {"symbol": "VOLX",
                                "chart_name": "INDEXY Fritrade", }

        if check_current_day() == friday_day:
            self.its_friday = True
        else:
            self.its_friday = False

    def open_browser(self):
        def get_cookies_values(file):
            with open(file) as f:
                dict_reader = DictReader(f)
                list_of_dicts = list(dict_reader)
            return list_of_dicts

        print(f"\n{date_now()} {time_now()}")
        if self.options.headless:
            out = f"Deploying {symbol} browser in HEADLESS mode"
            log_browser.info(out)
            print(out)
        else:
            out = f"Deploying {symbol} browser in VISIBLE mode"
            log_browser.info(out)
            print(out)

        try:
            cookies = get_cookies_values("/home/remote/PycharmProjects/trade/tradingview_cookies_fritrade.csv")
        except FileNotFoundError:
            cookies = get_cookies_values("/home/fritrade/PycharmProjects/trade/tradingview_cookies_fritrade.csv")

        self.driver = webdriver.Firefox(service=Service(GeckoDriverManager().install()),
                                        options=self.options)
        self.driver.get("https://www.tradingview.com/chart")
        log_browser.info(f"Adding cookies to {symbol} driver")
        for cook in cookies:
            self.driver.add_cookie(cook)
        log_browser.info(f"Refreshing {symbol} driver\n-----------------------------------------")
        self.driver.refresh()

        self.handle_num = 0
        for timeframe in timeframe_list:
            # if timeframe not in long_timeframes:
            self.handle_num = self.handle_num + 1
            log_browser.info(f"Opening chart for timeframe {timeframe}")

            self.driver.execute_script(f'window.open("{chart_url}")')
            handles_tabs.update({timeframe: self.driver.window_handles[self.handle_num]})

            self.driver.switch_to.window(handles_tabs[timeframe])

            self.switch_chart_to_timeframe(timeframe)
            self.check_chart(timeframe)

        self.close_def_tab()

        print(f"\n{date_now()} {time_now()}")
        out = f"{symbol} driver succesfully deployed!"
        log_browser.info(out)
        print(out)

    def close_def_tab(self):
        self.driver.switch_to.window(handles_tabs["def"])
        log_browser.info(f"Closing def tab on {symbol}")
        self.driver.close()
        log_browser.info(f"{symbol} def tab closed")

    def switch_chart_to_timeframe(self, timeframe):
        if timeframe in timeframe_list:
            x = False
            while not x:
                try:
                    self.selected_timeframe = self.driver.find_element(By.XPATH,
                                                                       timeframe_button_xpaths[timeframe])
                    x = True
                except Exception as err:
                    # pass
                    time.sleep(5)
            while not self.selected_timeframe.is_displayed():
                self.driver.implicitly_wait(1)
                log_browser.warning(f"!!!!!!!!!!! Waiting for {timeframe} timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            log_browser.info(f"Selecting {timeframe} chart")
            self.selected_timeframe.click()

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)

        val_ok = False
        while not val_ok:
            value = self.driver.find_element(By.XPATH, key_value_xpath)
            while not value.is_displayed():
                log_browser.info(f"Waiting for key value to load on {timeframe} chart")
                time.sleep(2)
            log_browser.info(f"Checking chart {symbol} {timeframe} - key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    log_browser.info(f"Actual (not usable) key value on  {timeframe} is {key_value}")
                else:
                    key_value = float(value.text)
                    val_ok = True
                    log_browser.info(f"Actual (not usable) key value on {timeframe} is {key_value}")
                log_browser.info("-----------------------------------------")
            except ValueError:
                time.sleep(1)

    def try_to_assert(self):
        def select_symbol():
            y = False
            while not y:
                log_browser.info(f"Waiting for chart to load completely - trying to assert (selecting {symbol})")
                try:
                    button = self.driver.find_element(By.XPATH, symbol_select_button_xpath)
                    button.click()
                    y = True
                except Exception as e:
                    log_browser.warning(f"Can't find {symbol} button - 3s sleep!")
                    time.sleep(3)

        x = False
        while not x:
            try:
                assert self.title_to_assert["symbol"] in self.driver.title
                assert self.title_to_assert["chart_name"] in self.driver.title
                x = True
                val1 = self.title_to_assert["symbol"]
                val2 = self.title_to_assert["chart_name"]
                log_browser.info(f"{val1} {val2} in title confirmed!")
            except:
                select_symbol()

    def check_timeframe_number(self, timeframe):
        tf_ok = False
        while not tf_ok:
            try:
                number = self.driver.find_element(By.XPATH, timeframe_number_xpath)
                if number.text == timeframe_numbers[timeframe]:
                    log_browser.info(f"Timeframe {timeframe} confirmed!")
                    tf_ok = True
                # else:
                #     print("Timeframe of the chart is", number.text, "...should be", timeframe)
                #     self.switch_chart_to_timeframe(timeframe)
                #     time.sleep(1)
            except Exception as e:
                # print(e)
                raise TypeError("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Nesedi timeframe cislo! Tu by sme sa nemali dostat")

    def get_key_value(self, timeframe):
        val_ok = False
        log_browser.info(f"Selecting tab with chart {timeframe}")
        self.driver.switch_to.window(handles_tabs[timeframe])
        log_browser.warning(f"Switched to chart {timeframe}")

        while not val_ok:
            value = self.driver.find_element(By.XPATH, key_value_xpath)
            current_price = self.driver.find_element(By.XPATH, current_price_xpath)
            atrb_takeprofit = self.driver.find_element(By.XPATH, atrb_up_xpath)
            atrb_stoploss = self.driver.find_element(By.XPATH, atrb_low_xpath)

            if not value.is_displayed() or not current_price.is_displayed() or not atrb_takeprofit.is_displayed() or not atrb_stoploss.is_displayed():
                log_browser.info(f"Waiting for values to load on {timeframe} chart")
                time.sleep(0.5)
            else:
                current_price = float(current_price.text)
                atrb_takeprofit = float(atrb_takeprofit.text)
                atrb_stoploss = float(atrb_stoploss.text)

                # self.check_timeframe_number(timeframe)
                # self.try_to_assert()
                try:
                    if "−" in value.text:
                        key_value = float(value.text.replace("−", '-'))
                        val_ok = True
                    else:
                        key_value = float(value.text)
                        val_ok = True

                    log_browser.info(f"* Key value on selected chart and timeframe{timeframe}: {key_value}")
                    log_browser.info("\n************************************************************************")
                    return [key_value, current_price, atrb_takeprofit, atrb_stoploss]

                except Exception as err:
                    log_browser.critical("METHOD get_key_value - except triggered")
                    log_browser.critical(err)
                    time.sleep(1)


class Valuegrabber:
    def __init__(self):
        self.key_val = {}
        self.atrb_values = {
            "1h": [],
            "2h": [],
            "3h": [],
            "4h": [],
            "D": [],
            "W": [],
            "M": [],
        }
        self.dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="US/Pacific")
        self.dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="Europe/Bratislava")
        log_writer.info(f"DST - USA {self.dst_usa}     DST - SVK {self.dst_svk}")

        q = f"select target_second from fri_trade.tradeData where symbol = '{symbol}'"
        fri_trade_cursor.execute(q)
        self.target_secs = fri_trade_cursor.fetchone()[0]

        q = f"select target_minute from fri_trade.tradeData where symbol = '{symbol}'"
        fri_trade_cursor.execute(q)
        self.target_mins = fri_trade_cursor.fetchone()[0]

        self.friday_day = 4
        self.day_already_written = False
        self.week_already_written = False
        self.target_secs = None
        self.target_mins = None

        if check_current_day() == self.friday_day:
            self.its_friday = True
        else:
            self.its_friday = False

        # zoznamy su vzdy o 1 nizsie ako na tradingview, aby sa hodnota kontrolovala este v danej sviecke
        # aktualne som to daval podla VOLX - Mini VIX Future

            # TODO: if its friday - a pridat spešl rozsahy pre piatok, ak nebude piatok tak nechat tieto normalne
            #  co tu su <3
            # zoznamy su vzdy o 1 nizsie ako na tradingview, aby sa hodnota kontrolovala este v danej sviecke
            # TOTO PRVE JE AKTIVNE KED SA POSUVA CAS NA VSECH ZJETYCH NA SLOVENSKU!
            if self.dst_usa and not self.dst_svk:
                self.day_range = [0, 1, 2, 3, 4, 6]
                self.week_target_hour = 21
                self.week_target_minute = 57
                self.week_target_seconds_range = range(50, 60)

                # normal ----------------------------------
                self.day_target_hour = 23  # nvm ci je to dobry day end time lebo TV to rata, ze to co je potom este 23.00->0.00 ako jeden den furt

                self.hour_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23]
                self.twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
                self.threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
                self.fourhour_hour_list = [2, 6, 10, 14, 18, 22]

                # friday ----------------------------------
                self.friday_day_target_hour = 23  # nvm ci to tu ma byt

                self.hour_list_friday = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
                self.twohour_hour_list_friday = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 21]
                self.threehour_hour_list_friday = [1, 4, 7, 10, 13, 16, 19, 21]
                self.fourhour_hour_list_friday = [2, 6, 10, 14, 18, 21]

            elif (not self.dst_usa and not self.dst_svk) or (self.dst_usa and self.dst_svk):
                self.day_range = [0, 1, 2, 3, 4]
                self.week_target_hour = 21
                self.week_target_minute = 57
                self.week_target_seconds_range = range(50, 60)

                # normal ----------------------------------
                self.day_target_hour = 22

                self.hour_list = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
                self.twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
                self.threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
                self.fourhour_hour_list = [3, 7, 11, 15, 19, 22]

                # friday ----------------------------------
                self.friday_day_target_hour = 21

                self.hour_list_friday = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21]
                self.twohour_hour_list_friday = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21]
                self.threehour_hour_list_friday = [2, 5, 8, 11, 14, 17, 20, 21]
                self.fourhour_hour_list_friday = [3, 7, 11, 15, 19, 21]

    def right_time_finder(self):
        while True:
            threads_done.update({symbol: False})
            self.reinitialize_init_variables()

            self.key_val = {}
            self.atrb_values = {
                "1h": [],
                "2h": [],
                "3h": [],
                "4h": [],
                "D": [],
                "W": [],
            }
            self.hrs = check_current_hour()
            self.mins = check_current_minute()
            self.secs = check_current_second()
            self.day = check_current_day()

            self.onehour()
            self.twohour()
            self.threehour()
            self.fourhour()

            if not self.day_already_written:
                self.oneday()
            if not self.week_already_written:
                self.week()

            if len(self.key_val) != 0:
                out = f"*** {symbol} key vals: {self.key_val}"
                # print(out)
                log_browser.info(out)
                log_writing.info(out)

                active_vix.update(self.key_val)
                symbol_atrb["VIX"].update(self.atrb_values)
                threads_done.update({"VIX": True})

            else:
                # print(f"{time_now()} {symbol} - No key vals!")
                pass
            time.sleep(1)

    # -----------------------------------------------------------------------------------------------
    def onehour(self):
        if self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.hour_list_friday:
                            get_vals = webbrowser.get_key_value(timeframe="1h")
                            self.key_val.update({"1h": get_vals[0], })
                            self.atrb_values.update({"1h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})
        if not self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.hour_list:
                            get_vals = webbrowser.get_key_value(timeframe="1h")
                            self.key_val.update({"1h": get_vals[0], })
                            self.atrb_values.update({"1h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})

    def twohour(self):
        if self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.twohour_hour_list_friday:
                            get_vals = webbrowser.get_key_value(timeframe="2h")
                            self.key_val.update({"2h": get_vals[0], })
                            self.atrb_values.update({"2h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})
        if not self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.twohour_hour_list:
                            get_vals = webbrowser.get_key_value(timeframe="2h")
                            self.key_val.update({"2h": get_vals[0], })
                            self.atrb_values.update({"2h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})

    def threehour(self):
        if self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.threehour_hour_list_friday:
                            get_vals = webbrowser.get_key_value(timeframe="3h")
                            self.key_val.update({"3h": get_vals[0], })
                            self.atrb_values.update({"3h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})
        if not self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.threehour_hour_list:
                            get_vals = webbrowser.get_key_value(timeframe="3h")
                            self.key_val.update({"3h": get_vals[0], })
                            self.atrb_values.update({"3h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})

    def fourhour(self):
        if self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.fourhour_hour_list_friday:
                            get_vals = webbrowser.get_key_value(timeframe="4h")
                            self.key_val.update({"4h": get_vals[0], })
                            self.atrb_values.update({"4h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})
        if not self.its_friday:
            if self.secs == self.target_secs:
                if self.mins == self.target_mins:
                    if self.day in self.day_range:
                        if self.hrs in self.fourhour_hour_list:
                            get_vals = webbrowser.get_key_value(timeframe="4h")
                            self.key_val.update({"4h": get_vals[0], })
                            self.atrb_values.update({"4h": [get_vals[1],
                                                            get_vals[2],
                                                            get_vals[3]
                                                            ]})

    def oneday(self):
        day_target_minute = 58
        day_target_seconds_range = range(50, 60)

        # FRIDAY
        if self.its_friday:
            # print("F-its friday")
            if self.secs in day_target_seconds_range:
                if self.mins == day_target_minute:
                    if self.hrs == self.friday_day_target_hour:
                        get_vals = webbrowser.get_key_value(timeframe="D")
                        self.key_val.update({"D": get_vals[0], })
                        self.atrb_values.update({"D": [get_vals[1],
                                                       get_vals[2],
                                                       get_vals[3]
                                                       ]})
                        self.day_already_written = True

        # NORMAL DAY
        if not self.its_friday:
            if self.secs in day_target_seconds_range:
                if self.mins == day_target_minute:
                    if self.hrs == self.day_target_hour:
                        if self.day in self.day_range:
                            get_vals = webbrowser.get_key_value(timeframe="D")
                            self.key_val.update({"D": get_vals[0], })
                            self.atrb_values.update({"D": [get_vals[1],
                                                           get_vals[2],
                                                           get_vals[3]
                                                           ]})
                            self.day_already_written = True

    def week(self):
        if self.its_friday:
            if self.secs in self.week_target_seconds_range:
                if self.mins == self.week_target_minute:
                    if self.hrs == self.week_target_hour:
                        get_vals = webbrowser.get_key_value(timeframe="W")
                        self.key_val.update({"W": get_vals[0], })
                        self.atrb_values.update({"W": [get_vals[1],
                                                       get_vals[2],
                                                       get_vals[3]
                                                       ]})
                        self.week_already_written = True
                        out = f"\n{symbol} - HAVE A NICE WEEKEND!"
                        print(out)
                        log_writing.info(out)
                        log_browser.info(out)

    # month VOLX sa zatial nepouziva lebo nie je dostatok mesacnych dát pre indikator
    # obsolete!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    def month(self):
        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            target_time = "21:57:58"
        elif (not dst_usa and not dst_svk) or (dst_usa and dst_svk):
            target_time = "21:57:58"

        year = int(date_now()[6:])
        month = int(date_now()[3:5])
        last_day_of_month = calendar.monthrange(year=year, month=month)
        if (int(date_now()[3:5] == int(last_day_of_month[1])) and
                time_now() == target_time):
            log_browser.info(f"--- {time_now()}")
            func = webbrowser.get_key_value(timeframe="M")
            self.key_val.update({"M": func[0], })
            self.atrb_values.update({"M": [func[1],
                                           func[2],
                                           func[3]
                                           ]})

    def update_target_mins_secs(self):
        while True:
            q = f"select target_second from fri_trade.tradeData where symbol = '{symbol}'"
            fri_trade_cursor.execute(q)
            self.target_secs = fri_trade_cursor.fetchone()[0]

            q = f"select target_minute from fri_trade.tradeData where symbol = '{symbol}'"
            fri_trade_cursor.execute(q)
            self.target_mins = fri_trade_cursor.fetchone()[0]
            time.sleep(300)

    def reinitialize_init_variables(self):
        # toto je kvoli tomu americkemu posunu casu DST, kazdy den to kontroluje ci sa DST (de)aktivovalo
        if time_now() == "00:00:20":
            self.__init__()
            log_browser.info(f"{symbol} __init__ variables reinitialized!")


def writer_new():
    try:
        out = "\n!!! WRITER STARTED !!!\n"
        print(out)
        log_writer.info(out)

        """HLAVNY CYKLUS========================================================"""
        while True:
            vix_thread_done = threads_done["VIX"]


            # ========================  VIX  ========================
            if vix_thread_done:
                symbol_values = active_vix
                if len(symbol_values) != 0:
                    out = f"\n=========  VIX results {time_now()} {date_now()}  ========="
                    print(out)
                    # log_writing.info(out)
                    time_of_val = time_now()

                    for registered_timeframe in symbol_values:
                        value = symbol_values[registered_timeframe]
                        # symbol = "VIX"

                        qpart1 = "insert into fri_trade."
                        qpart2 = "_"
                        qpart3 = " (key_value, dateOfValue, timeOfValue, processed, price, atrb_tp, atrb_sl) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                        q = qpart1 + symbol + qpart2 + registered_timeframe + qpart3

                        try:
                            fri_trade_cursor.execute(q,
                                                     (value,
                                                      date_now(),
                                                      time_of_val,
                                                      False,
                                                      symbol_atrb[symbol][registered_timeframe][0],
                                                      symbol_atrb[symbol][registered_timeframe][1],
                                                      symbol_atrb[symbol][registered_timeframe][2]
                                                      )
                                                     )
                            print(f"{time_now()} {date_now()} {symbol} {registered_timeframe} - added to database!")
                            log_writing.info(f"{symbol} {registered_timeframe} - added to database!")


                        # DEBUG
                        except IndexError as error:
                            print(f"{symbol}    CHYBA!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            print("-symbol_atrb:-\n", symbol_atrb["VIX"])
                            print(f"{symbol} values", symbol_values)
                            print("tf", registered_timeframe,
                                  "\nsymbol", symbol,
                                  "\nlen of symbolatrb(symbol+tf)", len(symbol_atrb[symbol][registered_timeframe]))

                            log_writer.critical("{error} {registered_timeframe} {symbol}")
                            print("Error:", error)
                    symbol_values.clear()

            time.sleep(0.1)

    except RuntimeError:
        print("CRITICAL - Writer ERROR!!! {error}".format(error=traceback.print_exc()))
        log_writer.critical("Writer ERROR!!! {error}".format(error=traceback.print_exc()))

        print("Writer STOPPED! ************\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")
        log_writer.critical("Writer STOPPED! ************n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")


# ======================================================================================================================

# --- class definitons ---
webbrowser = Trading()
grabber = Valuegrabber()

# --- DAEMON thread definition ---
righttimefinder_thread = threading.Thread(target=grabber.right_time_finder,
                                          name="righttimefinder_volx_thread",
                                          daemon=True)

update_target_mins_secs_thread = threading.Thread(target=grabber.update_target_mins_secs,
                                                  name="update_target_mins_secs_thread",
                                                  daemon=True)

mysql_keepalive_thread = threading.Thread(target=mysql_keepalive,
                                          name="mysql_keepalive_thread",
                                          daemon=True)

writer_thread = threading.Thread(target=writer_new,
                                 name="MAIN_writer_thread")


# --------------------- open browsers ---------------------
webbrowser.open_browser()

# --------------------- threads launch ---------------------
righttimefinder_thread.start()
# mysql_keepalive_thread.start()
writer_thread.start()
update_target_mins_secs_thread.start()
# writer_new()
