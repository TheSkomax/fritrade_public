from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import datetime
import mysql.connector
import os
import dotenv

dotenv.load_dotenv("../.env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]


username = None
pw = None
email_button_xpath = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div[1]/div[4]/div/span"
login_button = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/form/div[5]/div[2]/button/span[2]"
value_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[3]/td[2]/div/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/div"
chart_url = "https://www.tradingview.com/chart"
time_on_chart_xpath = "/html/body/div[2]/div[1]/div[1]/div/div[3]/div[1]/div/span/button/span"
timeframe_number_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[1]/div/div[1]/div[1]/div[1]/div[2]"


# timeframe_list = ["1m", "3m", "5m", "15m", "30m", "45m", "1h", "2h", "3h", "4h", "D"]
timeframe_list = ["1m", "3m", "5m"]

timeframe_button_xpaths = {
    "1m": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]",
    "3m": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[2]",
    "5m": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[3]",
    "15m": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[4]",
    "30m": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[5]",
    "45m": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[6]",
    "1h": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[7]",
    "2h": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[8]",
    "3h": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[9]",
    "4h": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[10]",
    "D": "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[11]",
    "check": "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[1]/div/div[1]/div[1]/div[1]/div[2]",
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
    "D": "1D"
}
handles = {
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
    "D": ""
}

# mysql - fri_trade schema
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


class Tradingview:
    def __init__(self):
        self.options = Options()
        self.options.headless = False
        self.executable = "/home/linuxfri/Downloads/geckodriver-v0.29.0-linux64/geckodriver"
        self.title_to_assert_us500 = {"symbol": "US500",
                                      "chart_name": "INDEXY Majchl", }
        # self.timeframe_3m = "3m"

    def tradingview_login(self):
        # selenium one_min
        self.driver = webdriver.Firefox(options=self.options, executable_path=self.executable)
        # self.one_min.maximize_window()

        # opens tradingview sign in page
        if self.options.headless:
            print("Opening tradingview website in HEADLESS mode")
        else:
            print("Opening tradingview website in VISIBLE mode")

        self.driver.get("https://www.tradingview.com/accounts/signin/")
        # print("window handle:", self.one_min.current_window_han

        # check if sign in page is loaded - checks email button, asserts title and clicks email button
        email_button = self.driver.find_element_by_xpath(email_button_xpath)
        while not email_button.is_displayed():
            self.driver.implicitly_wait(1)
            print("Waiting for sign in page to load")
        assert "Authentication — TradingView" in self.driver.title
        email_button.click()
        print("Sign in page loaded successfully!")

        # waits for username text field to load and fills in username
        username_tf = self.driver.find_element_by_name("username")
        while not username_tf.is_displayed():
            self.driver.implicitly_wait(1)
            print("Waiting for username text field to load")
        username_tf.send_keys(username)

        # waits for password text field to load and fills in password
        password_tf = self.driver.find_element_by_name("password")
        while not password_tf.is_displayed():
            self.driver.implicitly_wait(1)
            print("Waiting for password text field to load")
        password_tf.send_keys(pw)

        # clicks login button and waits for login to be completed
        self.driver.find_element_by_xpath(login_button).click()
        y = 0
        while y == 0:
            html_code = self.driver.page_source
            if "is-authenticated" in html_code:
                print("Login successful!")
                y = 1
            else:
                print("Waiting for login to be completed")
                y = 0
                time.sleep(1)

        # # opens tradingview chart and waits for it to completely load - asserts symbol and chart name in title
        # print("---- Opening chart")
        # self.one_min.get(chart_url)
        # self.check_chart()
        handles.update({"def": self.driver.window_handles[0]})

    def open_charts(self):
        i = 0
        for timeframe in timeframe_list:
            i = i + 1
            print("Opening chart for timeframe", timeframe)
            self.driver.execute_script('window.open("{charturl}")'.format(charturl=chart_url))
            handles.update({timeframe: self.driver.window_handles[i]})
            # print(handles)
            self.driver.switch_to.window(handles[timeframe])
            self.switch_chart_to_timeframe(timeframe)
        self.close_def_tab()

    def close_def_tab(self):
        self.driver.switch_to.window(handles["def"])
        self.close_actual_tab()

    def select_tab_with_timeframe(self, timeframe):
        print("Selecting tab with chart", timeframe)
        self.driver.switch_to.window(handles[timeframe])

    def switch_chart_to_timeframe(self, timeframe):
        if timeframe in timeframe_list:
            x = False
            while not x:
                try:
                    self.selected_timeframe = self.driver.find_element_by_xpath(timeframe_button_xpaths[timeframe])
                    x = True
                except:
                    pass
            while not self.selected_timeframe.is_displayed():
                self.driver.implicitly_wait(1)
                print("!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe, "timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            print("Selecting", timeframe, "chart")
            self.selected_timeframe.click()
            self.check_chart(timeframe)
        else:
            raise ValueError("Timeframe not in the list... how the fuck did we even get here?")

    def check_timeframe_number(self, timeframe):
        x = False
        while not x:
            try:
                number = self.driver.find_element_by_xpath(timeframe_number_xpath)
                if number.text == timeframe_numbers[timeframe]:
                    print("Timeframe", timeframe, "confirmed!")
                    x = True
                # else:
                #     print("Timeframe of the chart is", number.text, "...should be", timeframe)
                #     self.switch_chart_to_timeframe(timeframe)
                #     time.sleep(1)
            except:
                raise TypeError("Nesedi timeframe cislo! Tu by sme sa nemali dostat")

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)
        val_ok = False
        while not val_ok:
            value = self.driver.find_element_by_xpath(value_xpath)
            while not value.is_displayed():
                print("Waiting for key value to load on", timeframe, "chart")
                time.sleep(5)
            print("Key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    print("Actual (not usable) key value on", timeframe, "is:", key_value)
                else:
                    key_value = float(value.text)
                    val_ok = True
                    print("Actual (not usable) key value on", timeframe, "is:", key_value)
                print("-----------------------------------------")
            except ValueError:
                time.sleep(1)

    def try_to_assert(self):
        x = 0
        while x == 0:
            try:
                assert self.title_to_assert_us500["symbol"] in self.driver.title
                assert self.title_to_assert_us500["chart_name"] in self.driver.title
                x = 1
                print(self.title_to_assert_us500["symbol"], self.title_to_assert_us500["chart_name"],
                      "in title confirmed!")
            except:
                print("Waiting for chart to load completely - trying to assert")
                time.sleep(3)

    def get_key_value(self, timeframe):
        val_ok = False
        self.select_tab_with_timeframe(timeframe)
        while not val_ok:
            value = self.driver.find_element_by_xpath(value_xpath)
            if not value.is_displayed():
                print("Waiting for key value to load on", timeframe, "chart")
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
                    print("* Key value on selected chart and timeframe", timeframe + ":", key_value,
                          "\n***************************************")
                    return key_value
                except ValueError:
                    time.sleep(1)

    def close_actual_tab(self):
        self.driver.close()

    def print_time(self):
        time_on_chart = self.driver.find_element_by_xpath(time_on_chart_xpath)
        while True:
            # print(time_on_chart.text)
            self.time_now()
            time.sleep(1)

    def check_current_day(self):
        # 0 = monday...
        daynum = int(datetime.datetime.today().weekday())
        return daynum

    def check_current_hour(self):
        hour_actual = datetime.datetime.now().hour
        return hour_actual

    def check_current_minute(self):
        minute_actual = datetime.datetime.now().minute
        return minute_actual

    def check_current_second(self):
        second_actual = datetime.datetime.now().second
        return second_actual

    def time_now(self):
        time_object = datetime.datetime.now()
        time_actual = time_object.strftime("%H:%M:%S")
        # print(time_actual)
        return time_actual

    def date_now(self):
        date_object = datetime.date.today()
        date_actual = date_object.strftime("%d.%m.%Y")
        # print(date_actual)
        return date_actual




    """
    def one_minute_tab(self):
        one_minute_button = self.one_min.find_element_by_xpath(one_minute_button_xpath)
        while not one_minute_button.is_displayed():
            self.one_min.implicitly_wait(1)
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!! Waiting for 1 minute button to show up... shouldnt need to")
        assert title_to_assert["symbol"] in self.one_min.title
        assert title_to_assert["chart_name"] in self.one_min.title
        print("Selecting 1m chart")
        one_minute_button.click()
        self.check_chart()
    
    def three_minute_tab(self):
        three_minute_button = self.one_min.find_element_by_xpath(three_minute_button_xpath)
        while not three_minute_button.is_displayed():
            self.one_min.implicitly_wait(1)
            print("!!!!!!!!!!!!!!!!!!!!!!!!!!!! Waiting for 3 minute button to show up... shouldnt need to")
        assert title_to_assert["symbol"] in self.one_min.title
        assert title_to_assert["chart_name"] in self.one_min.title
        print("Selecting 3m chart")
        three_minute_button.click()
        self.check_chart()
    """


class Valuegrabber:
    def __init__(self):
        self.target_secs = 57
        self.target_mins = 59
        self.day_target_hour = 22

        # TODO: dat tam nazad range 0 - 5 ked sa skoncia vikendove testy
        # rozsahy su o 1 vyssie, lebo poslednu hodnotu to zoberie o 1 nizsiu
        self.day_range = 0, 7
        self.hour_range = 0, 23

        # zoznamy su vzdy o 1 nizsie ako na trading view, aby sa hodnota kontrolovala este v
        # danej sviecke
        self.three_min_list = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59]
        self.five_min_list = [4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59]
        self.fifteen_min_list = [14, 29, 44, 59]
        self.thirty_min_list = [29, 59]
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

        self.twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
        self.threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 23]
        self.fourhour_hour_list = [3, 7, 11, 15, 19, 23]

        self.key_val = {}

    def first(self):
        self.key_val = {}
        self.hrs = int(tv.check_current_hour())
        self.mins = int(tv.check_current_minute())
        self.secs = int(tv.check_current_second())
        self.day = int(tv.check_current_day())

        # self.onehour()
        # self.thirtymin()
        # self.fortyfivemin()
        # self.onemin()
        # self.threemin()
        # self.fivemin()
        # self.fifteenmin()
        # self.twohour()
        # self.threehour()
        # self.fourhour()
        # self.oneday()

        self.onemin()
        self.threemin()
        self.fivemin()
        if len(self.key_val) != 0:
            print(self.key_val)
        self.second()

    # check_last_value_params
    def second(self):
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

                print("Params from last value:\nHodina", hourOfLastValue, "\nMinúta", minuteOfLastValue,
                      "\nSekunda", secondOfLastValue, "\nDátum", dateOfLastValue)
                print("Current value params:\nHodina", tv.check_current_hour(), "\nMinúta", tv.check_current_minute(),
                      "\nSekunda", tv.check_current_second(), "\nDátum", tv.date_now())


                # v tejto verzii nebude kontrola postupnosti na ziadnom timeframe, nakolko by to bolo velmi zlozite
                # a mozno aj zbytocne kedze sa inak urcuje cas kedy sa maju spustit jednotlive valuegrabbery
                #TODO: alebo ho dorobim az potom :D
                """
                # checks params of new value for duplicates - hour and date
                if str(tv.check_current_hour()) == hourOfLastValue and str(tv.check_current_minute()) == minuteOfLastValue\
                        and tv.date_now() == dateOfLastValue:
                    print("Hodnota s tymito parametrami na", used_timeframe, "uz existuje - nezapisujem!")
                    zapisat = False
                else:
                    print("Hodnota s tymito parametrami este nebola na", used_timeframe, "zapisana - zapisujem!")
                    zapisat = True


                
                # checks if new value's hour is HIGHER by 1 than last value - weekends and break between 22:00-23:00,
                # hour difference 23:00 and 0:00, weekend (sunday is the first day of trading) are accounted for
                if int(tv.check_current_hour()) - 1 == int(hourOfLastValue):
                    print("Hodnota je v hodinovom poradí - potvrdzujem zapísanie!")

                elif int(check_current_hour()) == 0 and int(hourOfLastValue) == 22:
                    print("Rozdiel v čase poslednej a novej hodnoty je NOČNÝ - potvrdzujem zapísanie!")
                    zapisat = True

                if used_timeframe == "1m":
                    if int(tv.check_current_minute()) - int(minuteOfLastValue) == 1 or int(tv.check_current_minute()) - int(minuteOfLastValue) == 2:
                        print("Hodnota na", used_timeframe, " je v minútovom poradí - potvrdzujem zapísanie!")
                        zapisat = True
                    elif int(minuteOfLastValue) == 59 and int(tv.check_current_minute()) == 0 or int(tv.check_current_minute()) == 1:
                        print("Hodnota na", used_timeframe, " je v minútovom poradí, rozdiel je kvôli poslednej minúte "
                                                            "v hodine - potvrdzujem zapísanie!")
                        zapisat = True
                    else:
                        raise ValueError("Neznáma chyba v poradí na 1m!")

                elif used_timeframe == "3m":
                """
            qpart1 = "insert into fri_trade.US500_"
            qpart2 = " (key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
            q = qpart1 + used_timeframe + qpart2
            fri_trade_cursor.execute(q, (self.key_val[used_timeframe], tv.date_now(), tv.time_now(),))
            print("Key value from {tf} added to database!".format(tf=used_timeframe))




            # metody su zoradene podla prvotneho prioritneho zoradenia, podla ktoreho by sa mali aj vyvolavat, ale ak nejake
    # ine poradie bude lepsie, tak ich treda vyvolavat podla neho - definuje sa v metode "first"
    def onehour(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in range(self.hour_range[0], self.hour_range[1]) and self.mins == self.target_mins and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="1h")
            self.key_val.update({"1h": tv.get_key_value(timeframe="1h")})

    def thirtymin(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in range(self.hour_range[0], self.hour_range[1]) and self.mins in self.thirty_min_list and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="30m")
            self.key_val.update({"30m": tv.get_key_value(timeframe="30m")})

    def fortyfivemin(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in range(self.hour_range[0], self.hour_range[1]) and str(self.mins) in self.fortyfive_min_dic[str(self.hrs)] and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="45m")
            self.key_val.update({"45m": tv.get_key_value(timeframe="45m")})

    def onemin(self):
        # print(self.day, self.hrs, self.mins, self.secs)
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in range(self.hour_range[0], self.hour_range[1]) and self.mins in range(0, 60) and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="1m")
            self.key_val.update({"1m": tv.get_key_value(timeframe="1m")})

    def threemin(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in range(self.hour_range[0], self.hour_range[1]) and self.mins in self.three_min_list and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="3m")
            self.key_val.update({"3m": tv.get_key_value(timeframe="3m")})

    def fivemin(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in range(self.hour_range[0], self.hour_range[1]) and self.mins in self.five_min_list and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="5m")
            self.key_val.update({"5m": tv.get_key_value(timeframe="5m")})

    def fifteenmin(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in range(self.hour_range[0], self.hour_range[1]) and self.mins in self.fifteen_min_list and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="15m")
            self.key_val.update({"15m": tv.get_key_value(timeframe="15m")})

    def twohour(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in self.twohour_hour_list and self.mins == self.target_mins and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="2h")
            self.key_val.update({"2h": tv.get_key_value(timeframe="2h")})

    def threehour(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in self.threehour_hour_list and self.mins == self.target_mins and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="3h")
            self.key_val.update({"3h": tv.get_key_value(timeframe="3h")})

    def fourhour(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs in self.fourhour_hour_list and self.mins == self.target_mins and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="4h")
            self.key_val.update({"4h": tv.get_key_value(timeframe="4h")})

    def oneday(self):
        if self.day in range(self.day_range[0], self.day_range[1]) and self.hrs == self.day_target_hour and self.mins == self.target_mins and self.secs == self.target_secs:
            print("---", tv.time_now())
            # tv.get_key_value(timeframe="D")
            self.key_val.update({"D": tv.get_key_value(timeframe="D")})




tv = Tradingview()
vg = Valuegrabber()

tv.tradingview_login()
tv.open_charts()

while True:
    vg.first()
    time.sleep(1)



# tv.select_tab_with_timeframe(timeframe="3m")
# tv.get_key_value(timeframe="1m")
# tv.get_key_value(timeframe="3m")
# tv.get_key_value(timeframe="5m")
# print("Doné")


"""
target_secs = 57
target_mins = 59
day_target_hour = 22

# TODO: dat tam nazad range 0 - 5 ked sa skoncia vikendove testy
# rozsahy su o 1 vyssie, lebo poslednu hodnotu to zoberie o 1 nizsiu
day_range = 0, 7
hour_range = 0, 23

# zoznamy su vzdy o 1 nizsie ako na trading view, aby sa hodnota kontrolovala este v
# danej sviecke
three_min_list = [2, 5, 8, 11, 14, 17, 20, 23, 26, 29, 32, 35, 38, 41, 44, 47, 50, 53, 56, 59]
five_min_list = [4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 54, 59]
fifteen_min_list = [14, 29, 44, 59]
thirty_min_list = [29, 59]
fortyfive_min_dic = {
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

twohour_hour_list = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23]
threehour_hour_list = [2, 5, 8, 11, 14, 17, 20, 23]
fourhour_hour_list = [3, 7, 11, 15, 19, 23]

while True:
    # key_val = {
    #     "1m": "",
    #     "3m": "",
    #     "5m": "",
    #     "15m": "",
    #     "30m": "",
    #     "45m": "",
    #     "1h": "",
    #     "2h": "",
    #     "3h": "",
    #     "4h": "",
    #     "D": ""
    # }
    key_val = {}
    hrs = int(tv.check_current_hour())
    mins = int(tv.check_current_minute())
    secs = int(tv.check_current_second())
    day = int(tv.check_current_day())
    # print(tv.time_now())

    
    # Timeframe-y su zoradene podla priority - najdolezitejsie idu prve
    # 1h
    if day in range(day_range[0], day_range[1]) and hrs in range(hour_range[0], hour_range[1]) and mins == target_mins and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="1h")
        key_val.update({"1h": tv.get_key_value(timeframe="1h")})
    # 30m
    if day in range(day_range[0], day_range[1]) and hrs in range(hour_range[0], hour_range[1]) and mins in thirty_min_list and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="30m")
        key_val.update({"30m": tv.get_key_value(timeframe="30m")})
    # 45m
    if day in range(day_range[0], day_range[1]) and hrs in range(hour_range[0], hour_range[1]) and str(mins) in fortyfive_min_dic[str(hrs)] and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="45m")
        key_val.update({"45m": tv.get_key_value(timeframe="45m")})
    # 1m
    if day in range(day_range[0], day_range[1]) and hrs in range(hour_range[0], hour_range[1]) and mins in range(0, 59) and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="1m")
        key_val.update({"1m": tv.get_key_value(timeframe="1m")})
    # 3m
    if day in range(day_range[0], day_range[1]) and hrs in range(hour_range[0], hour_range[1]) and mins in three_min_list and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="3m")
        key_val.update({"3m": tv.get_key_value(timeframe="3m")})
    # 5m
    if day in range(day_range[0], day_range[1]) and hrs in range(hour_range[0], hour_range[1]) and mins in five_min_list and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="5m")
        key_val.update({"5m": tv.get_key_value(timeframe="5m")})
    # 15m
    if day in range(day_range[0], day_range[1]) and hrs in range(hour_range[0], hour_range[1]) and mins in fifteen_min_list and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="15m")
        key_val.update({"15m": tv.get_key_value(timeframe="15m")})
    # 2h
    if day in range(day_range[0], day_range[1]) and hrs in twohour_hour_list and mins == target_mins and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="2h")
        key_val.update({"2h": tv.get_key_value(timeframe="2h")})
    # 3h
    if day in range(day_range[0], day_range[1]) and hrs in threehour_hour_list and mins == target_mins and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="3h")
        key_val.update({"3h": tv.get_key_value(timeframe="3h")})
    # 4h
    if day in range(day_range[0], day_range[1]) and hrs in fourhour_hour_list and mins == target_mins and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="4h")
        key_val.update({"4h": tv.get_key_value(timeframe="4h")})
    # D
    if day in range(day_range[0], day_range[1]) and hrs == day_target_hour and mins == target_mins and secs == target_secs:
        print("---", tv.time_now())
        # tv.get_key_value(timeframe="D")
        key_val.update({"D": tv.get_key_value(timeframe="D")})

    if len(key_val) != 0:
        print(key_val)
    time.sleep(1)
"""