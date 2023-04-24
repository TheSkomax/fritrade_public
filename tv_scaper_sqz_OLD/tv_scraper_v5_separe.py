import calendar
import datetime
import threading
import time
from csv import DictReader
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

email_button_xpath = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div[1]/div[4]/div/span"
login_button = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/form/div[5]/div[2]/button/span[2]"

value_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[3]/td[2]/div/div[2]/div/div[2]/div[2]/div[2]/div/div[1]/div"
chart_url = "https://www.tradingview.com/chart"
time_on_chart_xpath = "/html/body/div[2]/div[1]/div[1]/div/div[3]/div[1]/div/span/button/span"
timeframe_number_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[2]/div/div[1]/div[1]/div[1]/div[3]"


us500_button_xpath = "/html/body/div[2]/div[6]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[2]/div/div/div[2]/span"
volx_button_xpath = "/html/body/div[2]/div[6]/div/div[1]/div[1]/div[1]/div[1]/div[2]/div/div[2]/div/div/div[2]/div/div[5]/div/div/div[2]/span"

# TODO: pri uprave timeframeov treba upravit aj spustanie metod v right_time_finder-och!!!!!!!!!!!!!!!
timeframe_list_us500 = ["1m", "3m", "5m", "15m", "30m", "45m", "1h", "2h", "3h", "4h", "D"]
timeframe_list_volx = ["1m", "3m", "5m", "15m", "30m", "45m", "1h", "2h", "3h", "4h", "D"]

threads_done = {"US500": False, "VIX": False}
active_symbols = {
    "US500": {},
    "VIX": {}
    }

timeframe_button_xpaths = {
    "1m": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[1]",
    "3m": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[2]",
    "5m": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[3]",
    "15m": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[4]",
    "30m": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[5]",
    "45m": "/html/body/div[2]/div[3]/div/div/div[1]/div[1]/div/div/div/div/div[4]/div/div[6]",
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
    "1m": "1",
    "3m": "3",
    "5m": "5",
    "15m": "15",
    "30m": "30",
    "45m": "45",
    "1h": "1h",
    "2h": "2h",
    "3h": "3h",
    "4h": "4h",
    "D": "1D",
    "W": "1W",
    "M": "1M"
}

handles_us500 = {
    "def": "",
    "1m": "",
    "3m": "",
    "5m": "",
    "15m": "",
    "30m": "",
    "45m": "",
    "1h": "",
    "2h": "",
    "3h": "",
    "4h": "",
    "D": "",
    "W": "",
    "M": ""
}

handles_volx = {
    "def": "",
    "1m": "",
    "3m": "",
    "5m": "",
    "15m": "",
    "30m": "",
    "45m": "",
    "1h": "",
    "2h": "",
    "3h": "",
    "4h": "",
    "D": "",
    "W": "",
    "M": ""
}

event1 = threading.Event()

LOG_FORMAT = "%(levelname)s %(asctime)s - %(message)s"
logging.basicConfig(filename="tv_scraper.log", level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger()


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
        # executable = "/home/michal/geckodriver-v0.30.0-linux32/geckodriver"
        # self.ffoxservice = Service(executable)
        self.title_to_assert_us500 = {"symbol": "US500", "chart_name": "INDEXY Fritrade", }

    def open_browser(self):
        def get_cookies_values(file):
            with open(file) as f:
                dict_reader = DictReader(f)
                list_of_dicts = list(dict_reader)
            return list_of_dicts

        if self.options.headless:
            logger.info("Opening US500 in HEADLESS mode")
        else:
            logger.info("Opening US500 in VISIBLE mode")
        cookies = get_cookies_values("/home/remote/PycharmProjects/trade/tradingview_cookies_fritrade.csv")
        self.driver_us500 = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=self.options)
        self.driver_us500.get("https://www.tradingview.com/chart")
        logger.info("Adding cookies to US500 driver")
        for cook in cookies:
            self.driver_us500.add_cookie(cook)
        logger.info("Refreshing US500 driver\n-----------------------------------------")
        self.driver_us500.refresh()

        i = 0
        for timeframe in timeframe_list_us500:
            i = i + 1
            logger.info("%s %s", "Opening chart for timeframe", timeframe)
            self.driver_us500.execute_script('window.open("{charturl}")'.format(charturl=chart_url))
            handles_us500.update({timeframe: self.driver_us500.window_handles[i]})
            # print(handles)
            self.driver_us500.switch_to.window(handles_us500[timeframe])

            self.switch_chart_to_timeframe(timeframe)
            self.check_chart(timeframe)

        self.close_def_tab()
        logger.info("US500 driver successfuly deployed!")

    def open_week_chart(self):
        timeframe = "W"
        self.driver_us500.switch_to.window(handles_volx["D"])
        self.switch_chart_to_timeframe(timeframe)
        self.check_chart(timeframe)

    def open_month_chart(self):
        timeframe = "M"
        self.driver_us500.switch_to.window(handles_volx["D"])
        self.switch_chart_to_timeframe(timeframe)
        self.check_chart(timeframe)

    def return_to_daily(self):
        timeframe = "D"
        self.driver_us500.switch_to.window(handles_volx["D"])
        self.switch_chart_to_timeframe(timeframe)
        self.check_chart(timeframe)

    def close_def_tab(self):
        self.driver_us500.switch_to.window(handles_us500["def"])
        logger.info("Closing def tab on US500")
        self.driver_us500.close()

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
                logger.error("%s %s %s", "!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe,
                             "timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            logger.info("%s %s %s", "Selecting", timeframe, "chart")
            self.selected_timeframe.click()

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)

        val_ok = False
        while not val_ok:
            x = 0
            logger.info("Selecting element value_xpath - if stuck in loop ctrlF E48613")
            while x == 0:
                try:
                    value = self.driver_us500.find_element(By.XPATH, value_xpath)
                    x = 1
                except:
                    print("E48613")
                    time.sleep(1)

            while not value.is_displayed():
                logger.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
                time.sleep(2)
            logger.info("Key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    logger.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                else:
                    key_value = float(value.text)
                    val_ok = True
                    logger.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                logger.info("-----------------------------------------")
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
                logger.info("%s %s %s", self.title_to_assert_us500["symbol"], self.title_to_assert_us500["chart_name"],
                             "in title confirmed!")
            except Exception as e:
                # print(e)
                while y == 0:
                    try:
                        logger.info("Waiting for chart to load completely - trying to assert (selecting US500)")
                        select_us500 = self.driver_us500.find_element(By.XPATH, us500_button_xpath)
                        select_us500.click()
                        y = 1
                    except:
                        logger.warning("Failed asserting/selecting US500")
                        time.sleep(3)

    def check_timeframe_number(self, timeframe):
        tf_ok = False
        while not tf_ok:
            try:
                number = self.driver_us500.find_element(By.XPATH, timeframe_number_xpath)

                if number.text == timeframe_numbers[timeframe]:
                    logger.info("%s %s %s", "Timeframe", timeframe, "confirmed!")
                    tf_ok = True
                else:
                    logger.warning("%s %s %s %s %s", "Timeframe of the chart is", number.text, "...should be",
                                   timeframe, "- trying to switch")
                    self.switch_chart_to_timeframe(timeframe)
                    time.sleep(1)
                    if number.text == timeframe_numbers[timeframe]:
                        logger.info("%s %s %s", "Timeframe", timeframe, "confirmed!")
                        tf_ok = True
            except Exception as e:
                # print(e)
                raise TypeError("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! Nesedi timeframe cislo! Tu by sme sa nemali dostat")
                # pass

    def get_key_value(self, timeframe):
        val_ok = False
        logger.info("%s %s", "Selecting tab with chart", timeframe)
        self.driver_us500.switch_to.window(handles_us500[timeframe])

        while not val_ok:
            value = self.driver_us500.find_element(By.XPATH, value_xpath)
            if not value.is_displayed():
                logger.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
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
                    logger.info("%s %s %s %s", "* Key value on selected chart and timeframe", timeframe + ":", key_value,
                          "\n***************************************")
                    return key_value
                except ValueError:
                    time.sleep(1)


class VOLX:
    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.driver_volx = None
        self.executable = "/home/michal/geckodriver-v0.30.0-linux32/geckodriver"
        self.title_to_assert_volx = {"symbol": "VOLX", "chart_name": "INDEXY Fritrade", }

    def open_browser(self):
        def get_cookies_values(file):
            with open(file) as f:
                dict_reader = DictReader(f)
                list_of_dicts = list(dict_reader)
            return list_of_dicts

        if self.options.headless:
            logger.info("Opening VOLX in HEADLESS mode")
        else:
            logger.info("Opening VOLX in VISIBLE mode")
        cookies = get_cookies_values("/home/remote/PycharmProjects/trade/tradingview_cookies_fritrade.csv")

        self.driver_volx = webdriver.Firefox(service=Service(GeckoDriverManager().install()), options=self.options)
        self.driver_volx.get("https://www.tradingview.com/chart")
        logger.info("Adding cookies to VOLX driver")
        for cook in cookies:
            self.driver_volx.add_cookie(cook)
        logger.info("Refreshing VOLX driver\n-----------------------------------------")
        self.driver_volx.refresh()

        i = 0
        for timeframe in timeframe_list_volx:
            i = i + 1
            logger.info("%s %s", "Opening chart for timeframe", timeframe)
            self.driver_volx.execute_script('window.open("{charturl}")'.format(charturl=chart_url))
            handles_volx.update({timeframe: self.driver_volx.window_handles[i]})
            # print(handles)
            self.driver_volx.switch_to.window(handles_volx[timeframe])

            self.switch_chart_to_timeframe(timeframe)
            self.check_chart(timeframe)

        self.close_def_tab()
        logger.info("VOLX driver succesfully deployed!")

    def open_week_chart(self):
        timeframe = "W"
        self.driver_volx.switch_to.window(handles_volx["D"])
        self.switch_chart_to_timeframe(timeframe)
        self.check_chart(timeframe)

    def open_month_chart(self):
        timeframe = "M"
        self.driver_volx.switch_to.window(handles_volx["D"])
        self.switch_chart_to_timeframe(timeframe)
        self.check_chart(timeframe)

    def return_to_daily(self):
        timeframe = "D"
        self.driver_volx.switch_to.window(handles_volx["D"])
        self.switch_chart_to_timeframe(timeframe)
        self.check_chart(timeframe)

    def close_def_tab(self):
        self.driver_volx.switch_to.window(handles_volx["def"])
        logger.info("Closing def tab on VOLX")
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
                logger.warning("%s %s %s", "!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe,
                               "timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            logger.info("%s %s %s", "Selecting", timeframe, "chart")
            self.selected_timeframe.click()

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)

        val_ok = False
        while not val_ok:
            value = self.driver_volx.find_element(By.XPATH, value_xpath)
            while not value.is_displayed():
                logger.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
                time.sleep(2)
            logger.info("Key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    logger.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                else:
                    key_value = float(value.text)
                    val_ok = True
                    logger.info("%s %s %s %s", "Actual (not usable) key value on", timeframe, "is:", key_value)
                logger.info("-----------------------------------------")
            except ValueError:
                time.sleep(1)

    def try_to_assert(self):
        def select_volx():
            y = 0
            while y == 0:
                logger.info("Waiting for chart to load completely - trying to assert (selecting VOLX)")
                try:
                    button = self.driver_volx.find_element(By.XPATH, volx_button_xpath)
                    button.click()
                    y = 1
                except Exception as e:
                    logger.warning("nemozem najst VOLX button!!!!!!!!! 3s sleep")
                    time.sleep(3)
        x = 0
        while x == 0:
            try:
                assert self.title_to_assert_volx["symbol"] in self.driver_volx.title
                assert self.title_to_assert_volx["chart_name"] in self.driver_volx.title
                x = 1
                logger.info("%s %s %s", self.title_to_assert_volx["symbol"], self.title_to_assert_volx["chart_name"],
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
                    logger.info("%s %s %s", "Timeframe", timeframe, "confirmed!")
                    tf_ok = True
                # else:
                #     print("Timeframe of the chart is", number.text, "...should be", timeframe)
                #     self.switch_chart_to_timeframe(timeframe)
                #     time.sleep(1)
            except:
                raise TypeError("Nesedi timeframe cislo! Tu by sme sa nemali dostat")

    def get_key_value(self, timeframe):
        val_ok = False
        logger.info("%s %s", "Selecting tab with chart", timeframe)
        self.driver_volx.switch_to.window(handles_volx[timeframe])

        while not val_ok:
            value = self.driver_volx.find_element(By.XPATH, value_xpath)
            if not value.is_displayed():
                logger.info("%s %s %s", "Waiting for key value to load on", timeframe, "chart")
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
                    logger.info("%s %s %s %s", "* Key value on selected chart and timeframe", timeframe + ":", key_value,
                          "\n***************************************")
                    return key_value
                except ValueError:
                    logger.error("Dajaky error -> Ctrl F: X485")
                    print("Dajaky error -> Ctrl F: X485")
                    time.sleep(1)


class valuegrabber_US500:
    def __init__(self):
        self.target_secs = 57
        self.target_mins = 59
        self.key_val = {}

        # zoznamy su vzdy o 1 nizsie ako na tradingview, aby sa hodnota kontrolovala este v
        # danej sviecke
        self.three_min_list = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59]
        self.five_min_list = [4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59]
        self.fifteen_min_list = [14, 29, 44, 59]
        self.thirty_min_list = [29, 59]

        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            self.day_target_hour = 23
            self.day_range = [0, 1, 2, 3, 4, 6]
            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23]

            self.fortyfive_min_dic = {
                "0": "29",
                "1": ["14", "59"],
                "2": "44",
                "3": "29",
                "4": ["14", "59"],
                "5": "44",
                "6": "29",
                "7": ["14", "59"],
                "8": "44",
                "9": "29",
                "10": ["14", "59"],
                "11": "44",
                "12": "29",
                "13": ["14", "59"],
                "14": "44",
                "15": "29",
                "16": ["14", "59"],
                "17": "44",
                "18": "29",
                "19": ["14", "59"],
                "20": "44",
                "21": ["29", "59"],
                "23": "44",
            }

            self.twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            self.threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            self.fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif not dst_usa and not dst_svk or dst_usa and dst_svk:
            self.day_target_hour = 22
            self.day_range = [0, 1, 2, 3, 4]
            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

            self.fortyfive_min_dic = {
                "0": "44",
                "1": "29",
                "2": ["14", "59"],
                "3": "44",
                "4": "29",
                "5": ["14", "59"],
                "6": "44",
                "7": "29",
                "8": ["14", "59"],
                "9": "44",
                "10": "29",
                "11": ["14", "59"],
                "12": "44",
                "13": "29",
                "14": ["14", "59"],
                "15": "44",
                "16": "29",
                "17": ["14", "59"],
                "18": "44",
                "19": "29",
                "20": ["14", "59"],
                "21": "44",
                "22": "29",
            }

            self.twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            self.threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            self.fourhour_hour_list = [3, 7, 11, 15, 19, 22]



    # metody su zoradene podla prvotneho prioritneho zoradenia, podla ktoreho by sa mali aj vyvolavat, ale ak nejake
    # ine poradie bude lepsie, tak ich treda vyvolavat podla neho - definuje sa v metode "right_time_finder"
    def onehour(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"1h": us500_browser.get_key_value(timeframe="1h")})

    def thirtymin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.thirty_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"30m": us500_browser.get_key_value(timeframe="30m")})

    def fortyfivemin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                str(self.mins) in self.fortyfive_min_dic[str(self.hrs)] and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"45m": us500_browser.get_key_value(timeframe="45m")})

    def onemin(self):
        # print(self.day, self.hrs, self.mins, self.secs)
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in range(0, 60) and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"1m": us500_browser.get_key_value(timeframe="1m")})

    def threemin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.three_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"3m": us500_browser.get_key_value(timeframe="3m")})

    def fivemin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.five_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"5m": us500_browser.get_key_value(timeframe="5m")})

    def fifteenmin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.fifteen_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"15m": us500_browser.get_key_value(timeframe="15m")})

    def twohour(self):
        if (self.day in self.day_range and
                self.hrs in self.twohour_hour_list and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"2h": us500_browser.get_key_value(timeframe="2h")})

    def threehour(self):
        if (self.day in self.day_range and
                self.hrs in self.threehour_hour_list and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"3h": us500_browser.get_key_value(timeframe="3h")})

    def fourhour(self):
        if (self.day in self.day_range and
                self.hrs in self.fourhour_hour_list and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"4h": us500_browser.get_key_value(timeframe="4h")})

    def oneday(self):
        if (self.day in self.day_range and
                self.hrs == self.day_target_hour and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"D": us500_browser.get_key_value(timeframe="D")})

    def week(self):
        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            target_time = "22:00:30"
        elif not dst_usa and not dst_svk or dst_usa and dst_svk:
            target_time = "23:00:30"

        if (check_current_day() == 4 and
                time_now() == target_time):
            print("---", time_now())
            us500_browser.open_week_chart()

            self.key_val.update({"W": us500_browser.get_key_value(timeframe="D")})

            # keyval = us500_browser.get_key_value(timeframe="D")
            # q = "insert into fri_trade.US500_W (key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
            # fri_trade_cursor.execute(q, (keyval, date_now(), time_now(),))
            # print("Key value from US500 W added to database!")
            us500_browser.return_to_daily()
        else:
            pass

    def month(self):
        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            target_time = "22:00:30"
        elif not dst_usa and not dst_svk or dst_usa and dst_svk:
            target_time = "23:00:30"

        year = int(date_now()[6:])
        month = int(date_now()[3:5])
        last_day_of_month = calendar.monthrange(year=year, month=month)
        if (int(date_now()[3:5] == int(last_day_of_month[1])) and
                time_now() == target_time):
            print("---", time_now())
            us500_browser.open_month_chart()

            self.key_val.update({"M": us500_browser.get_key_value(timeframe="D")})

            # keyval = us500_browser.get_key_value(timeframe="D")
            # q = "insert into fri_trade.US500_M (key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
            # fri_trade_cursor.execute(q, (keyval, date_now(), time_now(),))
            # print("Key value from US500 M added to database!")
            us500_browser.return_to_daily()

    def reinitialize_init_variables(self):
        # toto je kvoli tomu posunu casu DST
        if time_now() == "00:00:20":
            self.__init__()
        else:
            pass

    def right_time_finder(self):
        while True:
            # print("******************* US500 čakám na event!!!!!!!!!!!!!!!")
            # event1.wait()

            threads_done.update({"US500": False})
            # active_symbols["US500"].clear()

            self.reinitialize_init_variables()

            self.key_val = {}
            self.hrs = check_current_hour()
            self.mins = check_current_minute()
            self.secs = check_current_second()
            self.day = check_current_day()

            self.onehour()
            self.thirtymin()
            self.fortyfivemin()
            self.onemin()
            self.threemin()
            self.fivemin()
            self.fifteenmin()
            self.twohour()
            self.threehour()
            self.fourhour()
            self.oneday()
            self.week()  # TODO: uvidime ako to bude fungovat
            self.month()  # TODO: uvidime ako to bude fungovat

            if len(self.key_val) != 0:
                print("*** US500 key vals:", self.key_val)
                logger.info("%s %s", "*** US500 key vals:", self.key_val)
                # self.value_writer()

                active_symbols["US500"].update(self.key_val)
                threads_done.update({"US500": True})
            else:
                # print(time_now(), "US500 - No key vals!")
                pass
            time.sleep(1)


class valuegrabber_volx:
    def __init__(self):
        self.target_secs = 57
        self.target_mins = 59
        self.key_val = {}

        # zoznamy su vzdy o 1 nizsie ako na trading view, aby sa hodnota kontrolovala este v danej sviecke
        # aktualne som to daval podla VOLX - Mini VIX Future
        self.three_min_list = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59]
        self.five_min_list = [4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59]
        self.fifteen_min_list = [14, 29, 44, 59]
        self.thirty_min_list = [29, 59]

        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            self.day_target_hour = 23
            self.day_range = [0, 1, 2, 3, 4, 6]
            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23]

            self.fortyfive_min_dic = {
                "0": "29",
                "1": ["14", "59"],
                "2": "44",
                "3": "29",
                "4": ["14", "59"],
                "5": "44",
                "6": "29",
                "7": ["14", "59"],
                "8": "44",
                "9": "29",
                "10": ["14", "59"],
                "11": "44",
                "12": "29",
                "13": ["14", "59"],
                "14": "44",
                "15": "29",
                "16": ["14", "59"],
                "17": "44",
                "18": "29",
                "19": ["14", "59"],
                "20": "44",
                "21": ["29", "59"],
                "23": "44",
            }

            self.twohour_hour_list = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
            self.threehour_hour_list = [1, 4, 7, 10, 13, 16, 19, 22]
            self.fourhour_hour_list = [2, 6, 10, 14, 18, 22]

        elif not dst_usa and not dst_svk or dst_usa and dst_svk:
            self.day_target_hour = 22
            self.day_range = [0, 1, 2, 3, 4]
            self.hour_range = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]

            self.fortyfive_min_dic = {
                "0": "44",
                "1": "29",
                "2": ["14", "59"],
                "3": "44",
                "4": "29",
                "5": ["14", "59"],
                "6": "44",
                "7": "29",
                "8": ["14", "59"],
                "9": "44",
                "10": "29",
                "11": ["14", "59"],
                "12": "44",
                "13": "29",
                "14": ["14", "59"],
                "15": "44",
                "16": "29",
                "17": ["14", "59"],
                "18": "44",
                "19": "29",
                "20": ["14", "59"],
                "21": "44",
                "22": "29",
            }

            self.twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 22]
            self.threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 22]
            self.fourhour_hour_list = [3, 7, 11, 15, 19, 22]



    # metody su zoradene podla prvotneho prioritneho zoradenia, podla ktoreho by sa mali aj vyvolavat, ale ak nejake
    # ine poradie bude lepsie, tak ich treda vyvolavat podla neho - to sa definuje v metode "right_time_finder"
    def onehour(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"1h": volx_browser.get_key_value(timeframe="1h")})

    def thirtymin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.thirty_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"30m": volx_browser.get_key_value(timeframe="30m")})

    def fortyfivemin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                str(self.mins) in self.fortyfive_min_dic[str(self.hrs)] and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"45m": volx_browser.get_key_value(timeframe="45m")})

    def onemin(self):
        # print(self.day, self.hrs, self.mins, self.secs)
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in range(0, 60) and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"1m": volx_browser.get_key_value(timeframe="1m")})

    def threemin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.three_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"3m": volx_browser.get_key_value(timeframe="3m")})

    def fivemin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.five_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"5m": volx_browser.get_key_value(timeframe="5m")})

    def fifteenmin(self):
        if (self.day in self.day_range and
                self.hrs in self.hour_range and
                self.mins in self.fifteen_min_list and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"15m": volx_browser.get_key_value(timeframe="15m")})

    def twohour(self):
        if (self.day in self.day_range and
                self.hrs in self.twohour_hour_list and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"2h": volx_browser.get_key_value(timeframe="2h")})

    def threehour(self):
        if (self.day in self.day_range and
                self.hrs in self.threehour_hour_list and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"3h": volx_browser.get_key_value(timeframe="3h")})

    def fourhour(self):
        if (self.day in self.day_range and
                self.hrs in self.fourhour_hour_list and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"4h": volx_browser.get_key_value(timeframe="4h")})

    def oneday(self):
        if (self.day in self.day_range and
                self.hrs == self.day_target_hour and
                self.mins == self.target_mins and
                self.secs == self.target_secs):
            logger.info("%s %s", "---", time_now())
            self.key_val.update({"D": volx_browser.get_key_value(timeframe="D")})

    def week(self):
        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            target_time = "22:00:30"
        elif not dst_usa and not dst_svk or dst_usa and dst_svk:
            target_time = "23:00:30"

        if (check_current_day() == 4 and
                time_now() == target_time):
            print("---", time_now())
            volx_browser.open_week_chart()

            self.key_val.update({"W": volx_browser.get_key_value(timeframe="D")})

            # keyval = vix_browser.get_key_value(timeframe="D")
            # q = "insert into fri_trade.VIX_W (key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
            # fri_trade_cursor.execute(q, (keyval, date_now(), time_now(),))
            # print("Key value from W added to database!")
            volx_browser.return_to_daily()
        else:
            pass

    def month(self):
        dst_usa = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="US/Pacific")
        dst_svk = dst_check(datetime(date.today().year, date.today().month, date.today().day),
                            timezone="Europe/Bratislava")
        if dst_usa and not dst_svk:
            target_time = "22:00:30"
        elif not dst_usa and not dst_svk or dst_usa and dst_svk:
            target_time = "23:00:30"

        year = int(date_now()[6:])
        month = int(date_now()[3:5])
        last_day_of_month = calendar.monthrange(year=year, month=month)
        if (int(date_now()[3:5] == int(last_day_of_month[1])) and
                time_now() == target_time):
            print("---", time_now())
            volx_browser.open_month_chart()

            self.key_val.update({"M": us500_browser.get_key_value(timeframe="D")})

            # keyval = vix_browser.get_key_value(timeframe="D")
            # q = "insert into fri_trade.VIX_M (key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
            # fri_trade_cursor.execute(q, (keyval, date_now(), time_now(),))
            # print("Key value from M added to database!")
            volx_browser.return_to_daily()

    def reinitialize_init_variables(self):
        # toto je kvoli tomu americkemu posunu casu DST, kazdy den to kontroluje ci sa DST (de)aktivovalo
        if time_now() == "00:00:20":
            self.__init__()
        else:
            pass

    def right_time_finder(self):
        while True:
            # print("******************* VIX čakám na event!!!!!!!!!!!!!!!")
            # event1.wait()

            threads_done.update({"VIX": False})
            # active_symbols["VIX"].clear()

            self.reinitialize_init_variables()

            self.key_val = {}
            self.hrs = check_current_hour()
            self.mins = check_current_minute()
            self.secs = check_current_second()
            self.day = check_current_day()

            self.onehour()
            self.thirtymin()
            self.fortyfivemin()
            self.onemin()
            self.threemin()
            self.fivemin()
            self.fifteenmin()
            self.twohour()
            self.threehour()
            self.fourhour()
            self.oneday()
            self.week()  # TODO: uvidime ako to bude fungovat

            if len(self.key_val) != 0:
                print("*** VOLX key vals:", self.key_val)
                logger.info("%s %s", "*** VOLX key vals:", self.key_val)
                # self.value_writer()

                active_symbols["VIX"].update(self.key_val)
                threads_done.update({"VIX": True})
            else:
                # print(time_now(), "VIX - No key vals!")
                pass
            time.sleep(1)

    # check_last_value_params
    # zastarale, nepouzivane!
    """def nepouzivane_value_writer(self):
        for used_timeframe in self.key_val:
            qpart1 = "select dateOfValue, timeOfValue from fri_trade.VIX_"
            qpart2 = " order by id desc limit 1"
            q = qpart1 + used_timeframe + qpart2
            fri_trade_cursor.execute(q)
            params = fri_trade_cursor.fetchone()

            if params is not None:
                dateOfLastValue = params[0]
                timeOfLastValue = params[1]
                hourOfLastValue = params[1][:2]
                minuteOfLastValue = params[1][3:5]
                secondOfLastValue = params[1][6:8]

                print("Params from last value on", used_timeframe, timeOfLastValue, dateOfLastValue)
                print("Current value params on", used_timeframe, time_now(), date_now())

            qpart1 = "insert into fri_trade.VIX_"
            qpart2 = " (key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
            q = qpart1 + used_timeframe + qpart2

            fri_trade_cursor.execute(q, (self.key_val[used_timeframe], date_now(), time_now(),))
            print("Key value from {tf} added to database!".format(tf=used_timeframe))
            breakfinder.look_for_red_wave_break(used_timeframe)
        # threads_done.update({"VIX": True})
    """


class Writer:
    def writer_latest(self):
        try:
            print("Writer started *********************************************************************")
            logger.info("Writer started *********************************************************************")
            while True:

                while False in threads_done.values():
                    time.sleep(.1)
                for symbol, symbol_data in active_symbols.items():
                    if len(symbol_data) != 0:
                        # print("Ticker:", symbol)

                        time_of_val = time_now()
                        for timeframe in symbol_data:
                            # print(timeframe + ":", symbol_data[timeframe])

                            qpart1 = "insert into fri_trade."
                            qpart2 = "_"
                            qpart3 = " (key_value, dateOfValue, timeOfValue, processed) VALUES(%s, %s, %s, %s)"
                            q = qpart1 + symbol + qpart2 + timeframe + qpart3

                            fri_trade_cursor.execute(q, (symbol_data[timeframe], date_now(), time_of_val, False))

                            print("Key value from {symb} {tf} added to database!".format(symb=symbol, tf=timeframe))
                            logger.info("Key value from {symb} {tf} added to database!".format(symb=symbol,
                                                                                                tf=timeframe))

                            # spustac breakfinderu z non-separe verzie
                            """
                            # breakfinder.look_for_wave_buy_break(symbol=symbol, timeframe=timeframe)
                            breakfinder_thread = threading.Thread(target=breakfinder.look_for_wave_buy_break,
                                                                  name="breakfinder_thread", args=(symbol, timeframe))
                            breakfinder_thread.start()
                            """

                        symbol_data.clear()
                        event1.set()
                time.sleep(0.1)

        except RuntimeError:
            # problem je, ze to clearuje ten dict??????
            # print("=======================================================", symbol, symbol_data)
            print("CRITICAL - Writer ERROR!!!", traceback.print_exc())
            logger.critical("%s %s", "CRITICAL - Writer ERROR!!!", traceback.print_exc())
            print("Writer STOPPED! ******\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")
            logger.critical("Writer STOPPED! ******\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*\n*")

    # zastarale, nepouzivane!
    """def value_writer(self):
        for used_timeframe in self.key_val:
            qpart1 = "select dateOfValue, timeOfValue from fri_trade.US500_"
            qpart2 = " order by id desc limit 1"
            q = qpart1 + used_timeframe + qpart2
            fri_trade_cursor.execute(q)
            params = fri_trade_cursor.fetchone()

            if params is not None:
                dateOfLastValue = params[0]
                timeOfLastValue = params[1]
                hourOfLastValue = params[1][:2]
                minuteOfLastValue = params[1][3:5]
                secondOfLastValue = params[1][6:8]

                print("Params from last value on", used_timeframe, timeOfLastValue, dateOfLastValue)
                print("Current value params on", used_timeframe, time_now(), date_now())

            qpart1 = "insert into fri_trade.US500_"
            qpart2 = " (key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
            q = qpart1 + used_timeframe + qpart2

            fri_trade_cursor.execute(q, (self.key_val[used_timeframe], date_now(), time_now(),))
            print("Key value from {tf} added to database!".format(tf=used_timeframe))
    """

    # tiez jakesi cosi zastarale
    """def new_writer(self):
        print("Writer started *******************************************************************************")
        while True:
            for symbol, value in symbols.items():
                if len(value) != 0:
                    print("\n1111111111111111111111111111111111111111111111111111111111111111111111111111111111111111111")
                    print("Ticker:", symbol)

                    for tf in value:
                        print(tf + ":", value[tf])
                    print("222222222222222222222222222222222222222222222222222222222222222222222222222222222222222\n")
                    value.clear()
            time.sleep(0.1)
    """


# ======================================================================================================================

# --- class definitons ---
us500_browser = US500()
us500_grabber = valuegrabber_US500()
volx_browser = VOLX()
volx_grabber = valuegrabber_volx()
writer = Writer()

# --- thread definition ---
us500_thread = threading.Thread(target=us500_grabber.right_time_finder, name="us500_thread")
volx_thread = threading.Thread(target=volx_grabber.right_time_finder, name="volx_thread")
writer_thread = threading.Thread(target=writer.writer_latest, name="writer_thread")

# --- open browsers ---
us500_browser.open_browser()
volx_browser.open_browser()


# --- thread launch ---
us500_thread.start()
volx_thread.start()

# TODO: writer spustat normalne v maine a nie ako thread? Lebo vsak ak by spadol, tak je zvysok programu k hovnu
# TODO: takto to jebne cele a budem vediet, ze to nejde
# writer_thread.start()
writer.writer_latest()
