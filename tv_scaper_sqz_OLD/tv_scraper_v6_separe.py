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

email_button_xpath = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div[1]/div[4]/div/span"
login_button = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/form/div[5]/div[2]/button/span[2]"
us500_button_xpath = "/html/body/div[2]/div[6]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div/div/div[2]/span"
volx_button_xpath =  "/html/body/div[2]/div[6]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[5]/div/div/div[2]/span"
gold_button_xpath =  "/html/body/div[2]/div[6]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[6]/div/div/div[2]/span"

value_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[3]/td[2]/div/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div"
chart_url = "https://www.tradingview.com/chart"
time_on_chart_xpath = "/html/body/div[2]/div[1]/div[1]/div/div[3]/div[1]/div/span/button/span"
timeframe_number_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[1]/div[1]/div[3]"

atrb_up_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[2]/div"
atrb_low_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[2]/div[2]/div[2]/div[2]/div/div[3]/div"
current_price_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div[1]/div[1]/div[2]/div/div[5]/div[2]"

timeframe_button_xpaths = {
    "1h": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[7]",
    "2h": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[8]",
    "3h": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[9]",
    "4h": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[10]",
    "D": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[11]",
    "W": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[12]",
    "M": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[13]",
    "check": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[1]/div[1]/div[3]",
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
handles_us500 = {
    "1h": "",
    "2h": "",
    "3h": "",
    "4h": "",
    "D": "",
    "W": "",
    "M": "",
    "def": ""
}
handles_volx = {
    "1h": "",
    "2h": "",
    "3h": "",
    "4h": "",
    "D": "",
    "W": "",
    "M": "",
    "def": ""
}

handles_gold = {
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
timeframe_list_us500 = ["1h", "2h", "3h", "4h", "D", "W"]
timeframe_list_volx = ["1h", "2h", "3h", "4h", "D", "W"]
timeframe_list_gold = ["1h", "2h", "3h", "4h", "D", "W"]
long_timeframes = ["D", "W", "M"]

threads_done = {"US500": False,
                "VIX": False,
                "GOLD": False}
symbol_atrb = {
    "US500": {},
    "VIX": {},
    "GOLD": {},
    }

active_us500 = {}
active_vix = {}
active_gold = {}

"""!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"""


# ====== US500 browser logging ======      ------------------------------------------------------
log_us500_browser = logging.getLogger("US500_browser_logger")
log_us500_browser.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_us500_browser.log")
file_handler.setFormatter(log_formatter)
log_us500_browser.addHandler(file_handler)

# ====== VOLX browser logging ======
log_volx_browser = logging.getLogger("VOLX_browser_logger")
log_volx_browser.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_volx_browser.log")
file_handler.setFormatter(log_formatter)
log_volx_browser.addHandler(file_handler)

# ====== GOLD browser logging ======
log_gold_browser = logging.getLogger("GOLD_browser_logger")
log_gold_browser.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_gold_browser.log")
file_handler.setFormatter(log_formatter)
log_gold_browser.addHandler(file_handler)

# ====== writer Logging ======
log_writer = logging.getLogger("writer_logger")
log_writer.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_writer.log")
file_handler.setFormatter(log_formatter)
log_writer.addHandler(file_handler)


# ====== US500 writing logging ======      ------------------------------------------------------
log_us500_writing = logging.getLogger("US500_writing_logger")
log_us500_writing.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_us500_writing.log")
file_handler.setFormatter(log_formatter)
log_us500_writing.addHandler(file_handler)

# ====== VOLX writing logging ======
log_volx_writing = logging.getLogger("VOLX_writing_logger")
log_volx_writing.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_volx_writing.log")
file_handler.setFormatter(log_formatter)
log_volx_writing.addHandler(file_handler)

# ====== GOLD writing logging ======
log_gold_writing = logging.getLogger("GOLD_writing_logger")
log_gold_writing.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_gold_writing.log")
file_handler.setFormatter(log_formatter)
log_gold_writing.addHandler(file_handler)


log_us500_browser.info(f"\n{block_bar}")


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
        q = "select id from fri_trade.US500_1h order by id desc limit 1"
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


class US500:
    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.driver_us500 = None
        self.executable = "/home/michal/geckodriver-v0.30.0-linux32/geckodriver"
        self.title_to_assert_us500 = {"symbol": "US500",
                                      "chart_name": "INDEXY Fritrade",
                                      }
        self.us500_oneday_isopened = None
        self.us500_oneweek_isopened = None

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
            out = "Deploying US500 browser in HEADLESS mode"
            log_us500_browser.info(out)
            print(out)
        else:
            out = "Deploying US500 browser in VISIBLE mode"
            log_us500_browser.info(out)
            print(out)

        try:
            cookies = get_cookies_values("/home/remote/PycharmProjects/trade/tradingview_cookies_fritrade.csv")
        except FileNotFoundError:
            cookies = get_cookies_values("/home/fritrade/PycharmProjects/trade/tradingview_cookies_fritrade.csv")

        self.driver_us500 = webdriver.Firefox(service=Service(GeckoDriverManager().install()),
                                              options=self.options)
        self.driver_us500.get("https://www.tradingview.com/chart")
        log_us500_browser.info("Adding cookies to US500 driver")
        for cook in cookies:
            self.driver_us500.add_cookie(cook)
        log_us500_browser.info("Refreshing US500 driver\n-----------------------------------------")
        self.driver_us500.refresh()

        self.handle_num = 0
        for timeframe in timeframe_list_us500:
            if timeframe not in long_timeframes:
                self.handle_num = self.handle_num + 1
                log_us500_browser.info(f"Opening chart for timeframe {timeframe}")

                self.driver_us500.execute_script(f'window.open("{chart_url}")')
                handles_us500.update({timeframe: self.driver_us500.window_handles[self.handle_num]})

                self.driver_us500.switch_to.window(handles_us500[timeframe])
                self.switch_chart_to_timeframe(timeframe)

                self.check_chart(timeframe)

            else:
                log_us500_browser.warning(f"Timeframe {timeframe} will be opened only at specified time")

        self.close_def_tab()

        print(f"\n{date_now()} {time_now()}")
        out = "US500 driver successfuly deployed!"
        log_us500_browser.info(out)
        print(out)

    def oneday_opener(self):
        day_opentime_list = ["22:40:30",
                             "22:40:31",
                             "22:40:32",
                             "22:40:33",
                             "22:40:34",
                             "22:40:35",
                             "22:45:30",
                             "22:45:31",
                             "22:45:32",
                             "22:45:33",
                             "22:45:34",
                             "22:45:35",
                             ]
        friday_opentime_list = ["21:40:30",
                                "21:40:31",
                                "21:40:32",
                                "21:40:33",
                                "21:40:34",
                                "21:40:35",
                                "21:45:30",
                                "21:45:31",
                                "21:45:32",
                                "21:45:33",
                                "21:45:34",
                                "21:45:35",
                                ]
        day_closetime_list = ["23:04:00",
                              "23:04:01",
                              "23:04:02",
                              "23:04:03",
                              "23:04:04",
                              "23:04:05",
                              "23:07:00",
                              "23:07:01",
                              "23:07:02",
                              "23:07:03",
                              "23:07:04",
                              "23:07:05",
                              ]
        friday_closetime_list = ["22:04:00",
                                 "22:04:01",
                                 "22:04:02",
                                 "22:04:03",
                                 "22:04:04",
                                 "22:04:05",
                                 "22:07:00",
                                 "22:07:01",
                                 "22:07:02",
                                 "22:07:03",
                                 "22:07:04",
                                 "22:07:05",
                                 ]

        log_us500_browser.info("US500 oneday opener thread started")
        while True:
            if (time_now() in day_opentime_list and not self.its_friday and not self.us500_oneday_isopened) or \
                    (time_now() in friday_opentime_list and self.its_friday and not self.us500_oneday_isopened):
                self.open_oneday()
                self.us500_oneday_isopened = True

            if (time_now() in day_closetime_list and not self.its_friday and self.us500_oneday_isopened) or \
                    (time_now() in friday_closetime_list and self.its_friday and self.us500_oneday_isopened):
                self.close_oneday_tab()
            time.sleep(1)

    def open_oneday(self):
        timeframe = "D"
        log_us500_browser.info(f"Opening chart for timeframe {timeframe}")

        self.driver_us500.execute_script(f'window.open("{chart_url}")')
        self.handle_num = self.handle_num + 1
        handles_us500.update({timeframe: self.driver_us500.window_handles[self.handle_num]})

        self.driver_us500.switch_to.window(handles_us500[timeframe])
        self.switch_chart_to_timeframe(timeframe)

        self.check_chart(timeframe)

    def close_oneday_tab(self):
        self.driver_us500.switch_to.window(handles_us500["D"])
        log_us500_browser.info("Closing D tab on US500")
        self.driver_us500.close()
        self.us500_oneday_isopened = False
        log_us500_browser.info("US500 D tab closed")

    def oneweek_opener(self):
        friday_opentime_list = ["21:40:30",
                                "21:40:31",
                                "21:40:32",
                                "21:40:33",
                                "21:40:34",
                                "21:40:35",
                                "21:45:30",
                                "21:45:31",
                                "21:45:32",
                                "21:45:33",
                                "21:45:34",
                                "21:45:35",
                                ]
        friday_closetime_list = ["22:04:00",
                                 "22:04:01",
                                 "22:04:02",
                                 "22:04:03",
                                 "22:04:04",
                                 "22:04:05",
                                 "22:07:00",
                                 "22:07:01",
                                 "22:07:02",
                                 "22:07:03",
                                 "22:07:04",
                                 "22:07:05",
                                 ]

        log_us500_browser.info("US500 oneweek opener thread started")
        while True:
            if time_now() in friday_opentime_list and self.its_friday and not self.us500_oneweek_isopened:
                self.open_oneweek()
                self.us500_oneweek_isopened = True

            if time_now() in friday_closetime_list and self.its_friday and self.us500_oneday_isopened:
                self.close_oneweek_tab()
            time.sleep(1)

    def open_oneweek(self):
        timeframe = "W"
        log_us500_browser.info(f"Opening chart for timeframe {timeframe}")

        self.driver_us500.execute_script(f'window.open("{chart_url}")')
        self.handle_num = self.handle_num + 1
        handles_us500.update({timeframe: self.driver_us500.window_handles[self.handle_num]})

        self.driver_us500.switch_to.window(handles_us500[timeframe])
        self.switch_chart_to_timeframe(timeframe)

        self.check_chart(timeframe)

    def close_oneweek_tab(self):
        self.driver_us500.switch_to.window(handles_us500["W"])
        log_us500_browser.info("Closing W tab on US500")
        self.driver_us500.close()
        self.us500_oneweek_isopened = False
        log_us500_browser.info("US500 W tab closed")

    def close_def_tab(self):
        self.driver_us500.switch_to.window(handles_us500["def"])
        log_us500_browser.info("Closing def tab on US500")
        self.driver_us500.close()
        log_us500_browser.info("US500 def tab closed")

    def switch_chart_to_timeframe(self, timeframe):
        if timeframe in timeframe_list_us500:
            x = False
            while not x:
                try:
                    self.selected_timeframe = self.driver_us500.find_element(By.XPATH,
                                                                             timeframe_button_xpaths[timeframe])
                    x = True
                except:
                    pass
            while not self.selected_timeframe.is_displayed():
                self.driver_us500.implicitly_wait(1)
                log_us500_browser.error("%s %s %s", "!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe,
                                        "timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            log_us500_browser.info("Selecting {tf} chart".format(tf=timeframe))
            self.selected_timeframe.click()

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)

        val_ok = False
        while not val_ok:
            x = 0
            log_us500_browser.info("Selecting element value_xpath - if stuck in loop ctrlF E48613")
            while x == 0:
                try:
                    value = self.driver_us500.find_element(By.XPATH, value_xpath)
                    x = 1
                except Exception as err:
                    print("E48613")
                    log_us500_browser.error(f"E48613 {err}")
                    time.sleep(1)

            while not value.is_displayed():
                log_us500_browser.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
                time.sleep(2)
            log_us500_browser.info("%s %s %s", "Checking chart US500", timeframe, "- key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    log_us500_browser.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                else:
                    key_value = float(value.text)
                    val_ok = True
                    log_us500_browser.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                log_us500_browser.info("-----------------------------------------")
            except ValueError:
                time.sleep(1)

    def try_to_assert(self):
        x = 0
        y = 0
        while x == 0:
            try:
                assert self.title_to_assert_us500["symbol"] in self.driver_us500.title
                assert self.title_to_assert_us500["chart_name"] in self.driver_us500.title
                x = 1
                log_us500_browser.info("%s %s %s", self.title_to_assert_us500["symbol"], self.title_to_assert_us500["chart_name"],
                             "in title confirmed!")
            except Exception as e:
                # print(e)
                while y == 0:
                    try:
                        log_us500_browser.info("Waiting for chart to load completely - trying to assert (selecting US500)")
                        select_us500 = self.driver_us500.find_element(By.XPATH, us500_button_xpath)
                        select_us500.click()
                        y = 1
                    except:
                        log_us500_browser.warning("Failed asserting/selecting US500")
                        time.sleep(3)

    def check_timeframe_number(self, timeframe):
        tf_ok = False
        while not tf_ok:
            try:
                number = self.driver_us500.find_element(By.XPATH, timeframe_number_xpath)

                if number.text == timeframe_numbers[timeframe]:
                    log_us500_browser.info("%s %s %s", "Timeframe", timeframe, "confirmed!")
                    tf_ok = True
                else:
                    log_us500_browser.warning("%s %s %s %s %s", "Timeframe of the chart is", number.text, "...should be",
                                              timeframe, "- trying to switch")
                    self.switch_chart_to_timeframe(timeframe)
                    time.sleep(1)
                    if number.text == timeframe_numbers[timeframe]:
                        log_us500_browser.info("%s %s %s", "Timeframe", timeframe, "confirmed!")
                        tf_ok = True
            except Exception as e:
                # print(e)
                raise TypeError("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Nesedi timeframe cislo! Tu by sme sa nemali dostat")

    def get_key_value(self, timeframe):
        val_ok = False
        log_us500_browser.info(f"Selecting tab with chart {timeframe}")
        self.driver_us500.switch_to.window(handles_us500[timeframe])

        while not val_ok:
            value = self.driver_us500.find_element(By.XPATH, value_xpath)
            current_price = float(self.driver_us500.find_element(By.XPATH, current_price_xpath).text)
            atrb_takeprofit = float(self.driver_us500.find_element(By.XPATH, atrb_up_xpath).text)
            atrb_stoploss = float(self.driver_us500.find_element(By.XPATH, atrb_low_xpath).text)

            if not value.is_displayed():
                log_us500_browser.info(f"Waiting for key value to load on {timeframe} chart")
                time.sleep(0.5)
            else:
                self.check_timeframe_number(timeframe)
                self.try_to_assert()
                try:
                    if "−" in value.text:
                        key_value = float(value.text.replace("−", '-'))
                        val_ok = True
                    else:
                        key_value = float(value.text)
                        val_ok = True
                    log_us500_browser.info("%s %s %s %s", "* Key value on selected chart and timeframe", timeframe + ":", key_value,
                                           "\n***************************************")
                    return [key_value, current_price, atrb_takeprofit, atrb_stoploss]

                except ValueError:
                    time.sleep(1)


class VOLX:
    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.driver_volx = None
        self.executable = "/home/michal/geckodriver-v0.30.0-linux32/geckodriver"
        self.title_to_assert_volx = {"symbol": "VOLX",
                                     "chart_name": "INDEXY Fritrade", }
        self.volx_oneday_isopened = None
        self.volx_oneweek_isopened = None

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
            out = "Deploying VOLX browser in HEADLESS mode"
            log_volx_browser.info(out)
            print(out)
        else:
            out = "Deploying VOLX browser in VISIBLE mode"
            log_volx_browser.info(out)
            print(out)

        try:
            cookies = get_cookies_values("/home/remote/PycharmProjects/trade/tradingview_cookies_fritrade.csv")
        except FileNotFoundError:
            cookies = get_cookies_values("/home/fritrade/PycharmProjects/trade/tradingview_cookies_fritrade.csv")

        self.driver_volx = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=self.options)
        self.driver_volx.get("https://www.tradingview.com/chart")
        log_volx_browser.info("Adding cookies to VOLX driver")
        for cook in cookies:
            self.driver_volx.add_cookie(cook)
        log_volx_browser.info("Refreshing VOLX driver\n-----------------------------------------")
        self.driver_volx.refresh()

        self.handle_num = 0
        for timeframe in timeframe_list_volx:
            if timeframe not in long_timeframes:
                self.handle_num = self.handle_num + 1
                log_volx_browser.info("Opening chart for timeframe {tf}".format(tf=timeframe))
                self.driver_volx.execute_script('window.open("{charturl}")'.format(charturl=chart_url))
                handles_volx.update({timeframe: self.driver_volx.window_handles[self.handle_num]})
                # print(handles)
                self.driver_volx.switch_to.window(handles_volx[timeframe])

                self.switch_chart_to_timeframe(timeframe)
                self.check_chart(timeframe)
            else:
                log_volx_browser.warning(f"Timeframe {timeframe} will be opened only at specified time")

        self.close_def_tab()

        print(f"\n{date_now()} {time_now()}")
        out = "VOLX driver succesfully deployed!"
        log_volx_browser.info(out)
        print(out)

    def oneday_opener(self):
        day_opentime_list = ["22:40:30",
                             "22:40:31",
                             "22:40:32",
                             "22:40:33",
                             "22:40:34",
                             "22:40:35",
                             "22:45:30",
                             "22:45:31",
                             "22:45:32",
                             "22:45:33",
                             "22:45:34",
                             "22:45:35",
                             ]
        friday_opentime_list = ["21:40:30",
                                "21:40:31",
                                "21:40:32",
                                "21:40:33",
                                "21:40:34",
                                "21:40:35",
                                "21:45:30",
                                "21:45:31",
                                "21:45:32",
                                "21:45:33",
                                "21:45:34",
                                "21:45:35",
                                ]
        day_closetime_list = ["23:04:00",
                              "23:04:01",
                              "23:04:02",
                              "23:04:03",
                              "23:04:04",
                              "23:04:05",
                              "23:07:00",
                              "23:07:01",
                              "23:07:02",
                              "23:07:03",
                              "23:07:04",
                              "23:07:05",
                              ]
        friday_closetime_list = ["22:04:00",
                                 "22:04:01",
                                 "22:04:02",
                                 "22:04:03",
                                 "22:04:04",
                                 "22:04:05",
                                 "22:07:00",
                                 "22:07:01",
                                 "22:07:02",
                                 "22:07:03",
                                 "22:07:04",
                                 "22:07:05",
                                 ]

        log_volx_browser.info("VOLX oneday opener thread started")
        while True:
            if (time_now() in day_opentime_list and not self.its_friday and not self.volx_oneday_isopened) or \
                    (time_now() in friday_opentime_list and self.its_friday and not self.volx_oneday_isopened):
                self.open_oneday()
                self.volx_oneday_isopened = True

            if (time_now() in day_closetime_list and not self.its_friday and self.volx_oneday_isopened) or \
                    (time_now() in friday_closetime_list and self.its_friday and self.volx_oneday_isopened):
                self.close_oneday_tab()
            time.sleep(1)

    def open_oneday(self):
        timeframe = "D"
        log_volx_browser.info(f"Opening chart for timeframe {timeframe}")

        self.driver_volx.execute_script(f'window.open("{chart_url}")')
        self.handle_num = self.handle_num + 1
        handles_volx.update({timeframe: self.driver_volx.window_handles[self.handle_num]})

        self.driver_volx.switch_to.window(handles_volx[timeframe])
        self.switch_chart_to_timeframe(timeframe)

        self.check_chart(timeframe)

    def close_oneday_tab(self):
        self.driver_volx.switch_to.window(handles_volx["D"])
        log_volx_browser.info("Closing D tab on volx")
        self.driver_volx.close()
        self.volx_oneday_isopened = False
        log_volx_browser.info("volx D tab closed")

    def oneweek_opener(self):
        friday_opentime_list = ["21:40:30",
                                "21:40:31",
                                "21:40:32",
                                "21:40:33",
                                "21:40:34",
                                "21:40:35",
                                "21:45:30",
                                "21:45:31",
                                "21:45:32",
                                "21:45:33",
                                "21:45:34",
                                "21:45:35",
                                ]
        friday_closetime_list = ["22:04:00",
                                 "22:04:01",
                                 "22:04:02",
                                 "22:04:03",
                                 "22:04:04",
                                 "22:04:05",
                                 "22:07:00",
                                 "22:07:01",
                                 "22:07:02",
                                 "22:07:03",
                                 "22:07:04",
                                 "22:07:05",
                                 ]

        log_volx_browser.info("VOLX oneweek opener thread started")
        while True:
            if time_now() in friday_opentime_list and self.its_friday and not self.volx_oneweek_isopened:
                self.open_oneweek()
                self.volx_oneweek_isopened = True

            if time_now() in friday_closetime_list and self.its_friday and self.volx_oneday_isopened:
                self.close_oneweek_tab()
            time.sleep(1)

    def open_oneweek(self):
        timeframe = "W"
        log_volx_browser.info(f"Opening chart for timeframe {timeframe}")

        self.driver_volx.execute_script(f'window.open("{chart_url}")')
        self.handle_num = self.handle_num + 1
        handles_volx.update({timeframe: self.driver_volx.window_handles[self.handle_num]})

        self.driver_volx.switch_to.window(handles_volx[timeframe])
        self.switch_chart_to_timeframe(timeframe)

        self.check_chart(timeframe)

    def close_oneweek_tab(self):
        self.driver_volx.switch_to.window(handles_volx["W"])
        log_volx_browser.info("Closing W tab on volx")
        self.driver_volx.close()
        self.volx_oneweek_isopened = False
        log_volx_browser.info("volx W tab closed")

    def close_def_tab(self):
        self.driver_volx.switch_to.window(handles_volx["def"])
        log_volx_browser.info("Closing def tab on VOLX")
        self.driver_volx.close()

    def switch_chart_to_timeframe(self, timeframe):
        if timeframe in timeframe_list_volx:
            x = False
            while not x:
                try:
                    self.selected_timeframe = self.driver_volx.find_element(By.XPATH,
                                                                            timeframe_button_xpaths[timeframe])
                    x = True
                except:
                    pass
            while not self.selected_timeframe.is_displayed():
                self.driver_volx.implicitly_wait(1)
                log_volx_browser.warning("%s %s %s", "!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe,
                                    "timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            log_volx_browser.info("%s %s %s", "Selecting", timeframe, "chart")
            self.selected_timeframe.click()

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)

        val_ok = False
        while not val_ok:
            value = self.driver_volx.find_element(By.XPATH, value_xpath)
            while not value.is_displayed():
                log_volx_browser.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
                time.sleep(2)
            log_volx_browser.info("%s %s %s", "Checking chart VOLX", timeframe, "- key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    log_volx_browser.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                else:
                    key_value = float(value.text)
                    val_ok = True
                    log_volx_browser.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                log_volx_browser.info("-----------------------------------------")
            except ValueError:
                time.sleep(1)

    def try_to_assert(self):
        def select_volx():
            y = 0
            while y == 0:
                log_volx_browser.info("Waiting for chart to load completely - trying to assert (selecting VOLX)")
                try:
                    button = self.driver_volx.find_element(By.XPATH, volx_button_xpath)
                    button.click()
                    y = 1
                except Exception as e:
                    log_volx_browser.warning("Can't find VOLX button - 3s sleep!")
                    time.sleep(3)
        x = 0
        while x == 0:
            try:
                assert self.title_to_assert_volx["symbol"] in self.driver_volx.title
                assert self.title_to_assert_volx["chart_name"] in self.driver_volx.title
                x = 1
                log_volx_browser.info("%s %s %s", self.title_to_assert_volx["symbol"], self.title_to_assert_volx["chart_name"],
                                 "in title confirmed!")
            except:
                select_volx()
                # while y == 0:
                #     try:
                #         print("Waiting for chart to load completely - trying to assert (selecting VIX)")
                #         select_us500 = self.driver_vix.find_element(By.XPATH, us500_button_xpath)
                #         select_us500.click()
                #         y = 1
                #     except:
                #         # print("fail2")
                #         time.sleep(3)

    def check_timeframe_number(self, timeframe):
        tf_ok = False
        while not tf_ok:
            try:
                number = self.driver_volx.find_element(By.XPATH, timeframe_number_xpath)
                if number.text == timeframe_numbers[timeframe]:
                    log_volx_browser.info("%s %s %s", "Timeframe", timeframe, "confirmed!")
                    tf_ok = True
                # else:
                #     print("Timeframe of the chart is", number.text, "...should be", timeframe)
                #     self.switch_chart_to_timeframe(timeframe)
                #     time.sleep(1)
            except:
                raise TypeError("Nesedi timeframe cislo! Tu by sme sa nemali dostat")

    def get_key_value(self, timeframe):
        val_ok = False
        log_volx_browser.info("%s %s", "Selecting tab with chart", timeframe)
        self.driver_volx.switch_to.window(handles_volx[timeframe])

        while not val_ok:
            value = self.driver_volx.find_element(By.XPATH, value_xpath)
            current_price = float(self.driver_volx.find_element(By.XPATH, current_price_xpath).text)
            atrb_takeprofit = float(self.driver_volx.find_element(By.XPATH, atrb_up_xpath).text)
            atrb_stoploss = float(self.driver_volx.find_element(By.XPATH, atrb_low_xpath).text)

            if not value.is_displayed():
                log_volx_browser.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
                time.sleep(0.5)
            else:
                self.check_timeframe_number(timeframe)
                self.try_to_assert()
                try:
                    if "−" in value.text:
                        key_value = float(value.text.replace("−", '-'))
                        val_ok = True
                    else:
                        key_value = float(value.text)
                        val_ok = True
                    log_volx_browser.info("%s %s %s %s", "* Key value on selected chart and timeframe", timeframe + ":", key_value,
                                          "\n***************************************")
                    return [key_value, current_price, atrb_takeprofit, atrb_stoploss]

                except Exception as err:
                    log_volx_browser.error(f"Dajaky error -> Ctrl F: X485 {err}")
                    print(f"Dajaky error -> Ctrl F: X485 {err}")
                    time.sleep(1)


class GOLD:
    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.driver_gold = None
        self.executable = "/home/michal/geckodriver-v0.30.0-linux32/geckodriver"
        self.title_to_assert_gold = {"symbol": "GOLD",
                                     "chart_name": "INDEXY Fritrade", }
        self.gold_oneday_isopened = None
        self.gold_oneweek_isopened = None

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
            out = "Deploying GOLD browser in HEADLESS mode"
            log_gold_browser.info(out)
            print(out)
        else:
            out = "Deploying GOLD browser in VISIBLE mode"
            log_gold_browser.info(out)
            print(out)

        try:
            cookies = get_cookies_values("/home/remote/PycharmProjects/trade/tradingview_cookies_fritrade.csv")
        except FileNotFoundError:
            cookies = get_cookies_values("/home/fritrade/PycharmProjects/trade/tradingview_cookies_fritrade.csv")

        self.driver_gold = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=self.options)
        self.driver_gold.get("https://www.tradingview.com/chart")
        log_gold_browser.info("Adding cookies to GOLD driver")
        for cook in cookies:
            self.driver_gold.add_cookie(cook)
        log_gold_browser.info("Refreshing GOLD driver\n-----------------------------------------")
        self.driver_gold.refresh()

        self.handle_num = 0
        for timeframe in timeframe_list_gold:
            if timeframe not in long_timeframes:
                self.handle_num = self.handle_num + 1
                log_gold_browser.info("Opening chart for timeframe {tf}".format(tf=timeframe))
                self.driver_gold.execute_script('window.open("{charturl}")'.format(charturl=chart_url))
                handles_gold.update({timeframe: self.driver_gold.window_handles[self.handle_num]})
                # print(handles)
                self.driver_gold.switch_to.window(handles_gold[timeframe])

                self.switch_chart_to_timeframe(timeframe)
                self.check_chart(timeframe)

            else:
                log_gold_browser.warning(f"Timeframe {timeframe} will be opened only at specified time")

        self.close_def_tab()

        print(f"\n{date_now()} {time_now()}")
        out = "GOLD driver succesfully deployed!"
        log_gold_browser.info(out)
        print(out)

    def oneday_opener(self):
        day_opentime_list = ["22:40:30",
                             "22:40:31",
                             "22:40:32",
                             "22:40:33",
                             "22:40:34",
                             "22:40:35",
                             "22:45:30",
                             "22:45:31",
                             "22:45:32",
                             "22:45:33",
                             "22:45:34",
                             "22:45:35",
                             ]
        friday_opentime_list = ["21:40:30",
                                "21:40:31",
                                "21:40:32",
                                "21:40:33",
                                "21:40:34",
                                "21:40:35",
                                "21:45:30",
                                "21:45:31",
                                "21:45:32",
                                "21:45:33",
                                "21:45:34",
                                "21:45:35",
                                ]
        day_closetime_list = ["23:04:00",
                              "23:04:01",
                              "23:04:02",
                              "23:04:03",
                              "23:04:04",
                              "23:04:05",
                              "23:07:00",
                              "23:07:01",
                              "23:07:02",
                              "23:07:03",
                              "23:07:04",
                              "23:07:05",
                              ]
        friday_closetime_list = ["22:04:00",
                                 "22:04:01",
                                 "22:04:02",
                                 "22:04:03",
                                 "22:04:04",
                                 "22:04:05",
                                 "22:07:00",
                                 "22:07:01",
                                 "22:07:02",
                                 "22:07:03",
                                 "22:07:04",
                                 "22:07:05",
                                 ]
        log_gold_browser.info("GOLD oneday opener thread started")
        while True:
            if (time_now() in day_opentime_list and not self.its_friday and not self.gold_oneday_isopened) or \
                    (time_now() in friday_opentime_list and self.its_friday and not self.gold_oneday_isopened):
                self.open_oneday()
                self.gold_oneday_isopened = True

            if (time_now() in day_closetime_list and not self.its_friday and self.gold_oneday_isopened) or \
                    (time_now() in friday_closetime_list and self.its_friday and self.gold_oneday_isopened):
                self.close_oneday_tab()
            time.sleep(1)

    def open_oneday(self):
        timeframe = "D"
        log_gold_browser.info(f"Opening chart for timeframe {timeframe}")

        self.driver_gold.execute_script(f'window.open("{chart_url}")')
        self.handle_num = self.handle_num + 1
        handles_gold.update({timeframe: self.driver_gold.window_handles[self.handle_num]})

        self.driver_gold.switch_to.window(handles_gold[timeframe])
        self.switch_chart_to_timeframe(timeframe)

        self.check_chart(timeframe)

    def close_oneday_tab(self):
        self.driver_gold.switch_to.window(handles_gold["D"])
        log_gold_browser.info("Closing D tab on gold")
        self.driver_gold.close()
        self.gold_oneday_isopened = False
        log_gold_browser.info("gold D tab closed")

    def oneweek_opener(self):
        friday_opentime_list = ["21:40:30",
                                "21:40:31",
                                "21:40:32",
                                "21:40:33",
                                "21:40:34",
                                "21:40:35",
                                "21:45:30",
                                "21:45:31",
                                "21:45:32",
                                "21:45:33",
                                "21:45:34",
                                "21:45:35",
                                ]
        friday_closetime_list = ["22:04:00",
                                 "22:04:01",
                                 "22:04:02",
                                 "22:04:03",
                                 "22:04:04",
                                 "22:04:05",
                                 "22:07:00",
                                 "22:07:01",
                                 "22:07:02",
                                 "22:07:03",
                                 "22:07:04",
                                 "22:07:05",
                                 ]

        log_gold_browser.info("GOLD oneweek opener thread started")
        while True:
            if time_now() in friday_opentime_list and self.its_friday and not self.gold_oneweek_isopened:
                self.open_oneweek()
                self.gold_oneweek_isopened = True

            if time_now() in friday_closetime_list and self.its_friday and self.gold_oneday_isopened:
                self.close_oneweek_tab()
            time.sleep(1)

    def open_oneweek(self):
        timeframe = "W"
        log_gold_browser.info(f"Opening chart for timeframe {timeframe}")

        self.driver_gold.execute_script(f'window.open("{chart_url}")')
        self.handle_num = self.handle_num + 1
        handles_gold.update({timeframe: self.driver_gold.window_handles[self.handle_num]})

        self.driver_gold.switch_to.window(handles_gold[timeframe])
        self.switch_chart_to_timeframe(timeframe)

        self.check_chart(timeframe)

    def close_oneweek_tab(self):
        self.driver_gold.switch_to.window(handles_gold["W"])
        log_gold_browser.info("Closing W tab on gold")
        self.driver_gold.close()
        self.gold_oneweek_isopened = False
        log_gold_browser.info("gold W tab closed")

    def close_def_tab(self):
        self.driver_gold.switch_to.window(handles_gold["def"])
        log_gold_browser.info("Closing def tab on GOLD")
        self.driver_gold.close()

    def switch_chart_to_timeframe(self, timeframe):
        if timeframe in timeframe_list_gold:
            x = False
            while not x:
                try:
                    self.selected_timeframe = self.driver_gold.find_element(By.XPATH,
                                                                            timeframe_button_xpaths[timeframe])
                    x = True
                except:
                    pass
            while not self.selected_timeframe.is_displayed():
                self.driver_gold.implicitly_wait(1)
                log_gold_browser.warning("%s %s %s", "!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe,
                                         "timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            log_gold_browser.info("%s %s %s", "Selecting", timeframe, "chart")
            self.selected_timeframe.click()

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)

        val_ok = False
        while not val_ok:
            value = self.driver_gold.find_element(By.XPATH, value_xpath)
            while not value.is_displayed():
                log_gold_browser.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
                time.sleep(2)
            log_gold_browser.info("%s %s %s", "Checking chart GOLD", timeframe, "- key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    log_gold_browser.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                else:
                    key_value = float(value.text)
                    val_ok = True
                    log_gold_browser.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                log_gold_browser.info("-----------------------------------------")
            except ValueError:
                time.sleep(1)

    def try_to_assert(self):
        def select_gold():
            y = 0
            while y == 0:
                log_gold_browser.info("Waiting for chart to load completely - trying to assert (selecting GOLD)")
                try:
                    button = self.driver_gold.find_element(By.XPATH, gold_button_xpath)
                    button.click()
                    y = 1
                except Exception as e:
                    log_gold_browser.warning("Can't find GOLD button - 3s sleep!")
                    time.sleep(3)
        x = 0
        while x == 0:
            try:
                assert self.title_to_assert_gold["symbol"] in self.driver_gold.title
                assert self.title_to_assert_gold["chart_name"] in self.driver_gold.title
                x = 1
                log_gold_browser.info("%s %s %s", self.title_to_assert_gold["symbol"],
                                      self.title_to_assert_gold["chart_name"],
                                      "in title confirmed!")
            except:
                select_gold()

    def check_timeframe_number(self, timeframe):
        tf_ok = False
        while not tf_ok:
            try:
                number = self.driver_gold.find_element(By.XPATH, timeframe_number_xpath)
                if number.text == timeframe_numbers[timeframe]:
                    log_gold_browser.info("%s %s %s", "Timeframe", timeframe, "confirmed!")
                    tf_ok = True
                # else:
                #     print("Timeframe of the chart is", number.text, "...should be", timeframe)
                #     self.switch_chart_to_timeframe(timeframe)
                #     time.sleep(1)
            except:
                raise TypeError("Nesedi timeframe cislo! Tu by sme sa nemali dostat")

    def get_key_value(self, timeframe):
        val_ok = False
        log_gold_browser.info(f"Selecting tab with chart {timeframe}")
        self.driver_gold.switch_to.window(handles_gold[timeframe])

        while not val_ok:
            value = self.driver_gold.find_element(By.XPATH, value_xpath)
            current_price = float(self.driver_gold.find_element(By.XPATH, current_price_xpath).text)
            atrb_takeprofit = float(self.driver_gold.find_element(By.XPATH, atrb_up_xpath).text)
            atrb_stoploss = float(self.driver_gold.find_element(By.XPATH, atrb_low_xpath).text)

            if not value.is_displayed():
                log_gold_browser.info(f"Waiting for key value to load on {timeframe} chart")
                time.sleep(0.5)
            else:
                self.check_timeframe_number(timeframe)
                self.try_to_assert()
                try:
                    if "−" in value.text:
                        key_value = float(value.text.replace("−", '-'))
                        val_ok = True
                    else:
                        key_value = float(value.text)
                        val_ok = True
                    log_gold_browser.info("%s %s %s %s", "* Key value on selected chart and timeframe",
                                          timeframe + ":", key_value,
                                          "\n***************************************")
                    return [key_value, current_price, atrb_takeprofit, atrb_stoploss]

                except Exception as err:
                    log_gold_browser.error(f"Dajaky error -> Ctrl F: X485 {err}")
                    print(f"Dajaky error -> Ctrl F: X485 {err}")
                    time.sleep(1)


class valuegrabber_US500:
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

        self.target_secs = 55
        self.target_mins = 59
        friday_day = 4


        # zoznamy su vzdy o 1 nizsie ako na tradingview, aby sa hodnota kontrolovala este v
        # danej sviecke
        self.dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="US/Pacific")
        self.dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="Europe/Bratislava")
        log_writer.info(f"DST - USA {self.dst_usa}     DST - SVK {self.dst_svk}")

        if check_current_day() == friday_day:
            self.its_friday = True
            print("US500 - Its friday!!!")
            self.end_target_time = "21:59:40"
        else:
            self.its_friday = False
            # tu je end_target_time zadefinovany len aby tu bol, lebo to vzdy cekuje aj ked neni piatok ale nepouzije ho
            self.end_target_time = "21:59:40"

        # TODO: if its friday - a pridat spešl rozsahy pre piatok, ak nebude piatok tak nechat tieto normalne
        #  co tu su <3
        if self.dst_usa and not self.dst_svk:
            self.day_target_hour = 23
            self.day_range = [0, 1, 2, 3, 4, 6]
            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23]
            self.twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            self.threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            self.fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif (not self.dst_usa and not self.dst_svk) or (self.dst_usa and self.dst_svk):
            self.day_target_hour = 22
            self.day_range = [0, 1, 2, 3, 4]

            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
            self.twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            self.threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            self.fourhour_hour_list = [3, 7, 11, 15, 19, 22]

    # -----------------------------------------------------------------------------------------------
    def onehour(self):
        if self.its_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                      self.mins == self.target_mins and
                                                                      self.day in self.day_range and
                                                                      self.hrs in self.hour_range):
            get_vals = us500_browser.get_key_value(timeframe="1h")
            self.key_val.update({"1h": get_vals[0], })
            self.atrb_values.update({"1h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def twohour(self):
        if self.its_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                      self.mins == self.target_mins and
                                                                      self.day in self.day_range and
                                                                      self.hrs in self.twohour_hour_list):
            get_vals = us500_browser.get_key_value(timeframe="2h")
            self.key_val.update({"2h": get_vals[0], })
            self.atrb_values.update({"2h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def threehour(self):
        if self.its_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                      self.mins == self.target_mins and
                                                                      self.day in self.day_range and
                                                                      self.hrs in self.threehour_hour_list):
            get_vals = us500_browser.get_key_value(timeframe="3h")
            self.key_val.update({"3h": get_vals[0], })
            self.atrb_values.update({"3h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def fourhour(self):
        if self.its_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                      self.mins == self.target_mins and
                                                                      self.day in self.day_range and
                                                                      self.hrs in self.fourhour_hour_list):
            get_vals = us500_browser.get_key_value(timeframe="4h")
            self.key_val.update({"4h": get_vals[0], })
            self.atrb_values.update({"4h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def oneday(self):
        day_target_time = "22:59:50"

        if self.its_friday and time_now() == self.end_target_time or (time_now() == day_target_time and
                                                                      not self.its_friday and
                                                                      self.day in self.day_range):
            get_vals = us500_browser.get_key_value(timeframe="D")
            self.key_val.update({"D": get_vals[0], })
            self.atrb_values.update({"D": [get_vals[1],
                                           get_vals[2],
                                           get_vals[3]
                                           ]})

    def week(self):
        if self.dst_usa and not self.dst_svk:
            target_time = self.end_target_time
        elif (not self.dst_usa and not self.dst_svk) or (self.dst_usa and self.dst_svk):
            target_time = self.end_target_time

        if self.its_friday and time_now() == target_time:
            get_vals = us500_browser.get_key_value(timeframe="W")
            self.key_val.update({"W": get_vals[0], })
            self.atrb_values.update({"W": [get_vals[1],
                                           get_vals[2],
                                           get_vals[3]
                                           ]})
            out = "\nUS500 - HAVE A NICE WEEKEND!"
            print(out)
            log_us500_writing.info(out)
            log_us500_browser.info(out)

    # obsolete!!!
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
            log_us500_browser.info("%s %s", "---", time_now())
            func = us500_browser.get_key_value(timeframe="W")
            self.key_val.update({"W": func[0], })
            self.atrb_values.update({"W": [func[1],
                                           func[2],
                                           func[3]
                                           ]})

    def reinitialize_init_variables(self):
        # toto je kvoli tomu posunu casu DST a inym veciam co sa zistuju v inite
        if time_now() == "00:00:20":
            self.__init__()
            log_us500_browser.info("__init__ variables reinitialized!")

    def right_time_finder_us500(self):
        while True:
            threads_done.update({"US500": False})
            self.reinitialize_init_variables()

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
            self.hrs = check_current_hour()
            self.mins = check_current_minute()
            self.secs = check_current_second()
            self.day = check_current_day()

            self.onehour()
            self.twohour()
            self.threehour()
            self.fourhour()
            self.oneday()
            self.week()
            self.month()

            if len(self.key_val) != 0:
                print(f"US500: key vals: {self.key_val}")

                out = f"*** US500 key vals: {self.key_val}"
                log_us500_browser.info(out)
                log_us500_writing.info(out)

                active_us500.update(self.key_val)
                symbol_atrb["US500"].update(self.atrb_values)
                threads_done.update({"US500": True})


                # print("\n\n---------------------------------------------------------------------"
                #       "\nvaluegrabber_us500\n",
                #       date_now(),
                #       time_now(),
                #       "\nUS500 thread done:", threads_done["US500"])
            else:
                # print(time_now(), "US500 - No key vals!")
                pass
            time.sleep(1)


class valuegrabber_volx:
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

        self.target_secs = 55
        self.target_mins = 59
        self.friday_day = 4

        if check_current_day() == self.friday_day:
            self.is_friday = True
            print("Its friday!!!")
            self.end_target_time = "21:59:40"
        else:
            self.is_friday = False
            # tu je end_target_time zadefinovany len aby tu bol, lebo to vzdy cekuje aj ked neni piatok ale nepouzije ho
            self.end_target_time = "21:59:40"

        # zoznamy su vzdy o 1 nizsie ako na trading view, aby sa hodnota kontrolovala este v danej sviecke
        # aktualne som to daval podla VOLX - Mini VIX Future
        self.dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="US/Pacific")
        self.dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="Europe/Bratislava")
        log_writer.info(f"DST - USA {self.dst_usa}     DST - SVK {self.dst_svk}")

        if self.dst_usa and not self.dst_svk:
            self.day_target_hour = 23
            self.day_range = [0, 1, 2, 3, 4, 6]
            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23]
            self.twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            self.threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            self.fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif (not self.dst_usa and not self.dst_svk) or (self.dst_usa and self.dst_svk):
            self.day_target_hour = 22
            self.day_range = [0, 1, 2, 3, 4]

            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
            self.twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            self.threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            self.fourhour_hour_list = [3, 7, 11, 15, 19, 22]

    def onehour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.hour_range):
            get_vals = volx_browser.get_key_value(timeframe="1h")
            self.key_val.update({"1h": get_vals[0], })
            self.atrb_values.update({"1h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def twohour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.twohour_hour_list):
            get_vals = volx_browser.get_key_value(timeframe="2h")
            self.key_val.update({"2h": get_vals[0], })
            self.atrb_values.update({"2h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def threehour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.threehour_hour_list):
            get_vals = volx_browser.get_key_value(timeframe="3h")
            self.key_val.update({"3h": get_vals[0], })
            self.atrb_values.update({"3h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def fourhour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.fourhour_hour_list):
            get_vals = volx_browser.get_key_value(timeframe="4h")
            self.key_val.update({"4h": get_vals[0], })
            self.atrb_values.update({"4h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def oneday(self):
        day_target_time = "22:59:50"

        if self.is_friday and time_now() == self.end_target_time or (time_now() == day_target_time and
                                                                     not self.is_friday and
                                                                     self.day in self.day_range):
            get_vals = volx_browser.get_key_value(timeframe="D")
            self.key_val.update({"D": get_vals[0], })
            self.atrb_values.update({"D": [get_vals[1],
                                           get_vals[2],
                                           get_vals[3]
                                           ]})

    def week(self):
        if self.dst_usa and not self.dst_svk:
            target_time = self.end_target_time
        elif (not self.dst_usa and not self.dst_svk) or (self.dst_usa and self.dst_svk):
            target_time = self.end_target_time

        if self.is_friday and time_now() == target_time:
            get_vals = volx_browser.get_key_value(timeframe="W")
            self.key_val.update({"W": get_vals[0], })
            self.atrb_values.update({"W": [get_vals[1],
                                           get_vals[2],
                                           get_vals[3]
                                           ]})
            out = "\nVOLX - HAVE A NICE WEEKEND"
            print(out)
            log_volx_writing.info(out)
            log_volx_browser.info(out)

    # month VOLX sa zatial nepouziva lebo nie je dostatok mesacnych dát pre indikator
    # obsolete!!!
    def month(self):
        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            target_time = "21:57:59"
        elif (not dst_usa and not dst_svk) or (dst_usa and dst_svk):
            target_time = "21:57:59"

        year = int(date_now()[6:])
        month = int(date_now()[3:5])
        last_day_of_month = calendar.monthrange(year=year, month=month)
        if (int(date_now()[3:5] == int(last_day_of_month[1])) and
                time_now() == target_time):
            log_volx_browser.info("%s %s", "---", time_now())
            func = volx_browser.get_key_value(timeframe="M")
            self.key_val.update({"M": func[0], })
            self.atrb_values.update({"M": [func[1],
                                           func[2],
                                           func[3]
                                           ]})

    def reinitialize_init_variables(self):
        # toto je kvoli tomu americkemu posunu casu DST, kazdy den to kontroluje ci sa DST (de)aktivovalo
        if time_now() == "00:00:20":
            self.__init__()
            log_volx_browser.info("VOLX __init__ variables reinitialized!")

    def right_time_finder_volx(self):
        while True:
            threads_done.update({"VIX": False})
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
            self.oneday()
            self.week()

            if len(self.key_val) != 0:
                print("VOLX: key vals:",
                      self.key_val)
                log_volx_browser.info("*** VOLX key vals: {keyval}".format(keyval=self.key_val))
                log_volx_writing.info("*** VOLX key vals: {keyval}".format(keyval=self.key_val))

                active_vix.update(self.key_val)
                symbol_atrb["VIX"].update(self.atrb_values)
                threads_done.update({"VIX": True})

                # print("\n\n---------------------------------------------------------------------"
                #       "\nvaluegrabber_volx\n",
                #       date_now(),
                #       time_now(),
                #       "\nVOLX thread done:", threads_done["VIX"])
            else:
                # print(time_now(), "VIX - No key vals!")
                pass
            time.sleep(1)


class valuegrabber_gold:
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

        self.target_mins = 59
        self.target_secs = 55
        self.friday_day = 4

        if check_current_day() == self.friday_day:
            self.is_friday = True
            print("Its friday!!!")
            self.end_target_time = "21:59:40"
        else:
            self.is_friday = False
            # tu je end_target_time zadefinovany len aby tu bol, lebo to vzdy cekuje aj ked neni piatok ale nepouzije ho
            self.end_target_time = "21:59:40"

        # zoznamy su vzdy o 1 nizsie ako na trading view, aby sa hodnota kontrolovala este v danej sviecke
        # aktualne som to daval podla GOLD - Mini GOLD Future
        self.dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="US/Pacific")
        self.dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                                 timezone="Europe/Bratislava")
        log_writer.info(f"DST - USA {self.dst_usa}     DST - SVK {self.dst_svk}")

        if self.dst_usa and not self.dst_svk:
            self.day_target_hour = 23
            self.day_range = [0, 1, 2, 3, 4, 6]
            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23]
            self.twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            self.threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            self.fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif (not self.dst_usa and not self.dst_svk) or (self.dst_usa and self.dst_svk):
            self.day_target_hour = 22
            self.day_range = [0, 1, 2, 3, 4]

            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]
            self.twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            self.threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            self.fourhour_hour_list = [3, 7, 11, 15, 19, 22]

    def onehour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.hour_range):
            get_vals = gold_browser.get_key_value(timeframe="1h")
            self.key_val.update({"1h": get_vals[0], })
            self.atrb_values.update({"1h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def twohour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.twohour_hour_list):
            get_vals = gold_browser.get_key_value(timeframe="2h")
            self.key_val.update({"2h": get_vals[0], })
            self.atrb_values.update({"2h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def threehour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.threehour_hour_list):
            get_vals = gold_browser.get_key_value(timeframe="3h")
            self.key_val.update({"3h": get_vals[0], })
            self.atrb_values.update({"3h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def fourhour(self):
        if self.is_friday and time_now() == self.end_target_time or (self.secs == self.target_secs and
                                                                     self.mins == self.target_mins and
                                                                     self.day in self.day_range and
                                                                     self.hrs in self.fourhour_hour_list):
            get_vals = gold_browser.get_key_value(timeframe="4h")
            self.key_val.update({"4h": get_vals[0], })
            self.atrb_values.update({"4h": [get_vals[1],
                                            get_vals[2],
                                            get_vals[3]
                                            ]})

    def oneday(self):
        day_target_time = "22:59:50"

        if self.is_friday and time_now() == self.end_target_time or (time_now() == day_target_time and
                                                                     not self.is_friday and
                                                                     self.day in self.day_range):
            get_vals = gold_browser.get_key_value(timeframe="D")
            self.key_val.update({"D": get_vals[0], })
            self.atrb_values.update({"D": [get_vals[1],
                                           get_vals[2],
                                           get_vals[3]
                                           ]})

    def week(self):
        if self.dst_usa and not self.dst_svk:
            target_time = self.end_target_time
        elif (not self.dst_usa and not self.dst_svk) or (self.dst_usa and self.dst_svk):
            target_time = self.end_target_time

        if self.is_friday and time_now() == target_time:
            get_vals = gold_browser.get_key_value(timeframe="W")
            self.key_val.update({"W": get_vals[0], })
            self.atrb_values.update({"W": [get_vals[1],
                                           get_vals[2],
                                           get_vals[3]
                                           ]})
            out = "\nGOLD - HAVE A NICE WEEKEND"
            print(out)
            log_gold_writing.info(out)
            log_gold_browser.info(out)

    # month GOLD sa zatial nepouziva lebo nie je dostatok mesacnych dát pre indikator
    # obsolete!!!
    def month(self):
        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            target_time = "21:57:59"
        elif (not dst_usa and not dst_svk) or (dst_usa and dst_svk):
            target_time = "21:57:59"

        year = int(date_now()[6:])
        month = int(date_now()[3:5])
        last_day_of_month = calendar.monthrange(year=year, month=month)
        if (int(date_now()[3:5] == int(last_day_of_month[1])) and
                time_now() == target_time):
            log_gold_browser.info("%s %s", "---", time_now())
            func = gold_browser.get_key_value(timeframe="M")
            self.key_val.update({"M": func[0], })
            self.atrb_values.update({"M": [func[1],
                                           func[2],
                                           func[3]
                                           ]})

    def reinitialize_init_variables(self):
        # toto je kvoli tomu americkemu posunu casu DST, kazdy den to kontroluje ci sa DST (de)aktivovalo
        if time_now() == "00:00:20":
            self.__init__()
            log_gold_browser.info("GOLD __init__ variables reinitialized!")

    def right_time_finder_gold(self):
        while True:
            threads_done.update({"GOLD": False})
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
            self.oneday()
            self.week()

            if len(self.key_val) != 0:
                print("GOLD: key vals:",
                      self.key_val)
                log_gold_browser.info("*** GOLD key vals: {keyval}".format(keyval=self.key_val))
                log_gold_writing.info("*** GOLD key vals: {keyval}".format(keyval=self.key_val))

                active_gold.update(self.key_val)
                symbol_atrb["GOLD"].update(self.atrb_values)
                threads_done.update({"GOLD": True})

                # print("\n\n---------------------------------------------------------------------"
                #       "\nvaluegrabber_gold\n",
                #       date_now(),
                #       time_now(),
                #       "\nGOLD thread done:", threads_done["GOLD"])
            else:
                # print(time_now(), "GOLD - No key vals!")
                pass
            time.sleep(1)




def writer_new():
    try:
        out = "\n!!! WRITER STARTED !!!\n"
        print(out)
        log_writer.info(out)

        """HLAVNY CYKLUS========================================================"""
        while True:
            us500_thread_done = threads_done["US500"]
            vix_thread_done = threads_done["VIX"]
            gold_thread_done = threads_done["GOLD"]

            # ========================  US500  ========================
            if us500_thread_done:
                # us500_values = active_symbols["US500"]
                us500_values = active_us500
                if len(us500_values) != 0:
                    # print(f"\n\n{time_now()} {date_now()} ---------------------------------------------------------------------")
                    out = f"\n=========  US500 results {time_now()} {date_now()}  ========="
                    print(out)
                    # log_us500_writing.info(out)
                    time_of_val = time_now()

                    for registered_timeframe in us500_values:
                        value = us500_values[registered_timeframe]
                        symbol = "US500"

                        qpart1 = "insert into fri_trade."
                        qpart2 = "_"
                        qpart3 = " (key_value, dateOfValue, timeOfValue, processed, price, atrb_tp, atrb_sl) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                        q = qpart1 + "US500" + qpart2 + registered_timeframe + qpart3

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
                            print("{time} {date} {symb} {tf} - added to database!".format(symb=symbol,
                                                                                          tf=registered_timeframe,
                                                                                          date=date_now(),
                                                                                          time=time_now()))
                            log_us500_writing.info("{symb} {tf} - added to database!".format(symb=symbol,
                                                                                             tf=registered_timeframe))


                        # DEBUG
                        except IndexError as error:
                            print("US500    CHYBA!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            print("-symbol_atrb:-\n", symbol_atrb["US500"])
                            print("us500 values,", us500_values)
                            print("tf", registered_timeframe,
                                  "\nsymbol", symbol,
                                  "\nlen of symbolatrb(symbol+tf)", len(symbol_atrb[symbol][registered_timeframe]))

                            log_writer.critical("{error} {tf} {symbol}".format(error=error,
                                                                               tf=registered_timeframe,
                                                                               symbol=symbol))
                            print("Error:", error)
                    us500_values.clear()

            # ========================  VIX  ========================
            if vix_thread_done:
                # vix_values = active_symbols["VIX"]
                vix_values = active_vix
                if len(vix_values) != 0:
                    out = f"\n=========  VIX results {time_now()} {date_now()}  ========="
                    print(out)
                    # log_volx_writing.info(out)
                    time_of_val = time_now()

                    for registered_timeframe in vix_values:
                        value = vix_values[registered_timeframe]
                        symbol = "VIX"

                        qpart1 = "insert into fri_trade."
                        qpart2 = "_"
                        qpart3 = " (key_value, dateOfValue, timeOfValue, processed, price, atrb_tp, atrb_sl) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                        q = qpart1 + "VIX" + qpart2 + registered_timeframe + qpart3

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
                            print("{time} {date} {symb} {tf} - added to database!".format(symb=symbol,
                                                                                          tf=registered_timeframe,
                                                                                          date=date_now(),
                                                                                          time=time_now()))
                            log_volx_writing.info("{symb} {tf} - added to database!".format(symb=symbol,
                                                                                            tf=registered_timeframe))


                        # DEBUG
                        except IndexError as error:
                            print("VIX    CHYBA!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            print("-symbol_atrb:-\n", symbol_atrb["VIX"])
                            print("VIX values", vix_values)
                            print("tf", registered_timeframe,
                                  "\nsymbol", symbol,
                                  "\nlen of symbolatrb(symbol+tf)", len(symbol_atrb[symbol][registered_timeframe]))

                            log_writer.critical("{error} {tf} {symbol}".format(error=error,
                                                                               tf=registered_timeframe,
                                                                               symbol=symbol))
                            print("Error:", error)
                    vix_values.clear()

            # ========================  GOLD  ========================
            if gold_thread_done:
                # gold_values = active_symbols["GOLD"]
                gold_values = active_gold
                if len(gold_values) != 0:
                    out = f"\n=========  GOLD results {time_now()} {date_now()}  ========="
                    print(out)
                    # log_gold_writing.info(out)
                    time_of_val = time_now()

                    for registered_timeframe in gold_values:
                        value = gold_values[registered_timeframe]
                        symbol = "GOLD"

                        qpart1 = "insert into fri_trade."
                        qpart2 = "_"
                        qpart3 = " (key_value, dateOfValue, timeOfValue, processed, price, atrb_tp, atrb_sl) VALUES(%s, %s, %s, %s, %s, %s, %s)"
                        q = qpart1 + "GOLD" + qpart2 + registered_timeframe + qpart3

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
                            print("{time} {date} {symb} {tf} - added to database!".format(symb=symbol,
                                                                                          tf=registered_timeframe,
                                                                                          date=date_now(),
                                                                                          time=time_now()))
                            log_gold_writing.info("{symb} {tf} - added to database!".format(symb=symbol,
                                                                                            tf=registered_timeframe))


                        # DEBUG
                        except IndexError as error:
                            print("GOLD    CHYBA!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                            print("-symbol_atrb:-\n", symbol_atrb["GOLD"])
                            print("GOLD values", gold_values)
                            print("tf", registered_timeframe,
                                  "\nsymbol", symbol,
                                  "\nlen of symbolatrb(symbol+tf)", len(symbol_atrb[symbol][registered_timeframe]))

                            log_writer.critical("{error} {tf} {symbol}".format(error=error,
                                                                               tf=registered_timeframe,
                                                                               symbol=symbol))
                            print("Error:", error)
                    gold_values.clear()

            time.sleep(0.1)

    except RuntimeError:
        print("CRITICAL - Writer ERROR!!! {error}".format(error=traceback.print_exc()))
        log_writer.critical("Writer ERROR!!! {error}".format(error=traceback.print_exc()))

        print("Writer STOPPED! ************\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")
        log_writer.critical("Writer STOPPED! ************n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")


# ======================================================================================================================

# --- class definitons ---
us500_browser = US500()
us500_grabber = valuegrabber_US500()
volx_browser = VOLX()
volx_grabber = valuegrabber_volx()
gold_browser = GOLD()
gold_grabber = valuegrabber_gold()





# --- DAEMON thread definition ---
us500_thread = threading.Thread(target=us500_grabber.right_time_finder_us500,
                                name="us500_thread",
                                daemon=True)
volx_thread = threading.Thread(target=volx_grabber.right_time_finder_volx,
                               name="volx_thread",
                               daemon=True)
gold_thread = threading.Thread(target=gold_grabber.right_time_finder_gold,
                               name="gold_thread",
                               daemon=True)
mysql_keepalive_thread = threading.Thread(target=mysql_keepalive,
                                          name="mysql_keepalive_thread",
                                          daemon=True)

oneday_us500_thread = threading.Thread(target=us500_browser.oneday_opener,
                                       name="oneday_us500_thread",
                                       daemon=True)
oneweek_us500_thread = threading.Thread(target=us500_browser.oneweek_opener,
                                       name="oneweek_us500_thread",
                                       daemon=True)

oneday_volx_thread = threading.Thread(target=volx_browser.oneday_opener,
                                      name="oneday_volx_thread",
                                      daemon=True)
oneweek_volx_thread = threading.Thread(target=volx_browser.oneweek_opener,
                                       name="oneweek_volx_thread",
                                       daemon=True)

oneday_gold_thread = threading.Thread(target=gold_browser.oneday_opener,
                                       name="oneday_gold_thread",
                                       daemon=True)
oneweek_gold_thread = threading.Thread(target=gold_browser.oneweek_opener,
                                       name="oneweek_gold_thread",
                                       daemon=True)


writer_thread = threading.Thread(target=writer_new,
                                 name="MAIN_writer_thread")


# --- open browsers ---
us500_browser.open_browser()
volx_browser.open_browser()
gold_browser.open_browser()


# --- threads launch ---
us500_thread.start()
volx_thread.start()
gold_thread.start()

if "D" in timeframe_list_us500:
    oneday_us500_thread.start()
if "W" in timeframe_list_us500:
    oneweek_us500_thread.start()

if "D" in timeframe_list_volx:
    oneday_volx_thread.start()
if "W" in timeframe_list_volx:
    oneweek_volx_thread.start()

if "D" in timeframe_list_gold:
    oneday_gold_thread.start()
if "W" in timeframe_list_gold:
    oneweek_gold_thread.start()

mysql_keepalive_thread.start()

writer_thread.start()
# writer_new()


# TODO: vyriesit co to je ta CHYBA!!! a preco ju to teda vypisuje, preco tam vznika ten error furt
# TODO pridat viac info do logu ako program postupuje pri zapisovani
# TODO GUI!!!!!!!!!!!!!!!!!!!!!!!!!


# TO-DONE writer spustat normalne v maine a nie ako thread? Lebo vsak ak by spadol, tak je zvysok programu k hovnu
#  takto to jebne cele a budem vediet, ze to nejde
#  alebo writer bude v maine aostatne budu daemon thready, ked jebne writer tak jebnu asi asi daemony...?
# TO-DONE prerobit to nech us500 keyvals writer zapise samostatne a volx keyvals samostatne,
#   nebude to cakat na threads done!!!!!!
# TO-DONE a upravit to vizualne rozdelenie -------
# TO-DONE prestalo to zapisovat po vikende, preco?
# TO-DONE pridat na konci piatka do printu a logu nieco ako have a nice weekend
