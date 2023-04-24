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
chart_url = "https://www.tradingview.com/chart/nA99bl13/"
time_on_chart_xpath = "/html/body/div[2]/div[1]/div[1]/div/div[3]/div[1]/div/span/button/span"
timeframe_number_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[1]/div/div[1]/div[1]/div[1]/div[2]"



one_minute_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[1]"
three_minute_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[2]"
five_minute_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[3]"
fifteen_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[4]"
thirty_minute_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[5]"
fortyfive_minute_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[6]"
one_hour_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[7]"
two_hour_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[8]"
three_hour_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[9]"
four_hour_button_xpath = "/html/body/div[2]/div[2]/div/div/div[1]/div[1]/div/div/div/div/div[2]/div/div[10]"

# timeframe_list = ["1m", "3m", "5m", "15m", "30m", "45m", "1h", "2h", "3h", "4h"]
timeframe_list = ["1m", "3m"]
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

    def tradingview_login(self):
        # selenium one_min

        self.one_min = webdriver.Firefox(options=self.options, executable_path=self.executable)
        # self.three_min = webdriver.Firefox(options=self.options, executable_path=self.executable)

        # self.one_min.maximize_window()

        # opens tradingview sign in page
        if self.options.headless:
            print("Opening tradingview website in HEADLESS mode")
        else:
            print("Opening tradingview website in VISIBLE mode")

        self.one_min.get("https://www.tradingview.com/accounts/signin/")
        # print("window handle:", self.one_min.current_window_han

        # check if sign in page is loaded - checks email button, asserts title and clicks email button
        email_button = self.one_min.find_element_by_xpath(email_button_xpath)
        while not email_button.is_displayed():
            self.one_min.implicitly_wait(1)
            print("Waiting for sign in page to load")
        assert "Authentication — TradingView" in self.one_min.title
        email_button.click()
        print("- Sign in page loaded successfully!")

        # waits for username text field to load and fills in username
        username_tf = self.one_min.find_element_by_name("username")
        while not username_tf.is_displayed():
            self.one_min.implicitly_wait(1)
            print("Waiting for username text field to load")
        username_tf.send_keys(username)

        # waits for password text field to load and fills in password
        password_tf = self.one_min.find_element_by_name("password")
        while not password_tf.is_displayed():
            self.one_min.implicitly_wait(1)
            print("Waiting for password text field to load")
        password_tf.send_keys(pw)

        # clicks login button and waits for login to be completed
        self.one_min.find_element_by_xpath(login_button).click()
        y = 0
        while y == 0:
            html_code = self.one_min.page_source
            if "is-authenticated" in html_code:
                print("- Login successful!")
                y = 1
            else:
                print("Waiting for login to be completed")
                y = 0
                time.sleep(1)

        # # opens tradingview chart and waits for it to completely load - asserts symbol and chart name in title
        # print("---- Opening chart")
        # self.one_min.get(chart_url)
        # self.check_chart()
        handles.update({"def": self.one_min.window_handles[0]})

    def chart_three_m(self):
        title_to_assert = {"symbol": "US500",
                           "chart_name": "INDEXY Majchl", }

        # otvorit nove okno
        driver_three_m = webdriver.Firefox(options=self.options, executable_path=self.executable)

        # otvorit tv chart
        driver_three_m.get(chart_url)
        timeframe = "3m"

        # try to assert
        confirm_assert = False
        while not confirm_assert:
            try:
                assert title_to_assert["symbol"] in driver_three_m.title
                assert title_to_assert["chart_name"] in driver_three_m.title
                confirm_assert = True
                print(title_to_assert["symbol"], " in title confirmed!")
            except:
                print("Waiting for chart to load completely - trying to assert")
                time.sleep(2)

        # najst a kliknut dany timeframe button
        tf_button_found = False
        while not tf_button_found:
            try:
                self.selected_timeframe = driver_three_m.find_element_by_xpath(timeframe_button_xpaths[timeframe])
                tf_button_found = True
            except:
                pass
        while not self.selected_timeframe.is_displayed():
            driver_three_m.implicitly_wait(1)
            print("!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe, "timeframe button to show up... shouldnt need to")
        self.selected_timeframe.click()
        self.check_chart(timeframe)

        # kontrola timeframe cisla
        try:
            number = driver_three_m.find_element_by_xpath(timeframe_number_xpath)
            if number.text == timeframe_numbers[timeframe]:
                print("Timeframe", timeframe, "confirmed!")
            # else:
            #     print("Timeframe is different than it should be, switching...")
            #     self.switch_chart_to_timeframe(timeframe)
            #     x = True
        except:
            raise TypeError("Nesedi timeframe cislo! Tu by sme sa nemali dostat")

        # vytiahni, skontroluj cas a zapis hodnotu
        print("Grabbing key value")
        value = driver_three_m.find_element_by_xpath(value_xpath)
        while not value.is_displayed():
            driver_three_m.implicitly_wait(1)
            print("Waiting for key value to load")
        # print("- Key value loaded successfully!")
        if "−" in value.text:
            key_value = float(value.text.replace("−", '-'))
        else:
            key_value = float(value.text)
        print("Key value is:", key_value)

        # screenshot
        driver_three_m.save_screenshot("/home/linuxfri/PycharmProjects/trade/{symbol}/{tf}/chart"
                                       .format(symbol=title_to_assert["symbol"], tf=timeframe)
                                       + "_" + self.date_now() + "_" + self.time_now() + ".png")
        print("Screenshot saved!")

        # kontrola predoslej hodnoty
        # zapisane = self.check_last_value_params(key_value=key_value, symbol=title_to_assert["symbol"],
        #                                         timeframe=timeframe)
        last_added_value = 'select dateOfValue, timeOfValue from fri_trade.{symbol}' + '_' + '{tf}' +\
                           'order by id desc limit 1'.format(symbol=title_to_assert["symbol"], tf=timeframe)
        fri_trade_cursor.execute(last_added_value)
        params = fri_trade_cursor.fetchone()
        if params is not None:
            date_of_last_value = params[0]
            hour_of_last_value = params[1][:2]
            minute_of_last_value = params[1][3:5]
            second_of_last_value = params[1][2:]
            time_of_last_value = params[1]

            print("Params from last value: hodina", hour_of_last_value, date_of_last_value)
            print("Current params:  hodina", self.check_current_hour(), self.date_now())

            if self.time_now() == time_of_last_value and self.date_now() == date_of_last_value:
                print("Datum a cas novej hodnoty na grafe", timeframe, " je rovnaky ako na minulej - nezapisujem!")
                zapisat = False
            else:
                print("Hodnota na grafe", timeframe, "s parametrami", self.date_now(), self.time_now(),
                      "este nebola zapisana - zapisujem!")
                zapisat = True


            if int(self.check_current_minute()) - 3 == int(minute_of_last_value):
                print("Hodnota je v 3-minútovom poradí - potvrdzujem zapísanie!")

            elif self.check_current_day() == 0 and int(hour_of_last_value) == 22:
                print("*Rozdiel v čase minulej a novej hodnoty je VÍKENDOVÝ - potvrdzujem zapísanie!")
                zapisat = True

            elif int(self.check_current_hour()) == 0 and int(hour_of_last_value) == 22 and int(minute_of_last_value) == 57:
                print("Rozdiel v čase poslednej a novej hodnoty je NOČNÝ - potvrdzujem zapísanie!")
                zapisat = True

            else:
                print("*** Čas najnovšej hodnoty nie je v poradí - ruším zapísanie!")
                zapisat = False

            if zapisat:
                print("ZAPISUJEM")
                self.insert_value_to_db(key_value=key_value, symbol=title_to_assert["symbol"], timeframe=timeframe)

            else:
                print("NEZAPISUJEM")

        else:
            print("Prazdna databaza! / Hodnota je prva/druha v databaze!")
            print("ZAPISUJEM")
            self.insert_value_to_db(key_value=key_value, symbol=title_to_assert["symbol"], timeframe=timeframe)







    def insert_value_to_db(self, key_value, symbol, timeframe):
        q = "insert into fri_trade.{symbol}" + '_{tf}' + "(key_value, dateOfValue, timeOfValue) " \
                                                              "VALUES(%s, %s, %s)".format(symbol=symbol, tf=timeframe)
        fri_trade_cursor.execute(q, (key_value, self.date_now(), self.time_now(),))
        print("Key value from {tf} added to database!".format(tf=timeframe))
        self.look_for_red_wave_break(symbol, timeframe)

    def look_for_red_wave_break(self, symbol, timeframe):
        # vyberie posledne 3 hodnoty vratane novej zapisanej - ak sa nova nezapisala, tak sa tato metoda nespusti!
        values_query = 'select key_value from fri_trade.{symbol}_{tf} order by id desc limit 3'.format(symbol=symbol,
                                                                                                       tf=timeframe)
        fri_trade_cursor.execute(values_query)
        values = fri_trade_cursor.fetchall()

        try:
            # konvertuje tuple z databazy na string a ten na float ciselnu hodnotu
            C = new_value = float("".join(values[0]))  # C
            B = previous_value = float("".join(values[1]))  # B
            A = prev_previous_value = float("".join(values[2]))  # A
            print(new_value, previous_value, prev_previous_value)

            """HLAVNÁ BUY PODMIENKA
            if C > B and B < A and C < 0: ------------------------- BUY!"""
            if previous_value < new_value < 0 and previous_value < prev_previous_value:
                self.red_wave_break()
            elif A == B and B < C < 0:
                self.red_wave_break()

            # ostatné podmienky na print
            # if C > B and B < A and C < 0: nič - červená sa zlomila
            elif 0 > C > B > A:
                self.red_wave_rising()
            # nič - začína zelená vlna
            elif C > B > A and C > 0:
                self.green_wave_starting()
            # nič - zlomila sa zelená
            elif B > C > 0 and A < B:
                self.green_wave_break()
            # nič - začala sa červená
            elif C < B < A and C < 0:
                self.red_wave_starting()
            # nič - klesajúca červená
            elif C < B < A and C < 0:
                self.red_wave_falling()
            else:
                print("******** Nič - čakám na obchodnú príležitosť.")
        except IndexError:
            print("******** Nič - čakám na obchodnú príležitosť - nedostatok hodnôt v databáze.")

    def red_wave_break(self):
        print("Červená vlna sa zlomila! --------------------------------------------------- BUY!")
        # trader.x.trade(to_trade_args=trader.x.args_us500_sl_tp_standard_buy)
        soundfile = "/home/linuxfri/PycharmProjects/trade/trade_beep.mp3"
        os.system("mpg123 -q " + soundfile)

    def red_wave_rising(self):
        print("******** Nič - červená vlna stúpa.")

    def red_wave_starting(self):
        print("******** Nič - začína červená vlna.")

    def red_wave_falling(self):
        print("******** Nič - červená vlna klesá.")

    def green_wave_starting(self):
        print("******** Nič - začína zelená vlna.")

    def green_wave_break(self):
        print("******** Nič - zelená vlna sa zlomila.")








    def check_current_day(self):
        # 0 = monday...
        weekno = int(datetime.datetime.today().weekday())
        return weekno

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
        print(time_actual)
        return time_actual

    def date_now(self):
        date_object = datetime.date.today()
        date_actual = date_object.strftime("%d.%m.%Y")
        print(date_actual)
        return date_actual








    """

    def open_charts(self):
        i = 0
        for timeframe in timeframe_list:
            i = i + 1
            print("---- Opening chart for timeframe", timeframe)
            self.one_min.execute_script('window.open("{charturl}")'.format(charturl=chart_url))
            handles.update({timeframe: self.one_min.window_handles[i]})
            # print(handles)
            self.one_min.switch_to.window(handles[timeframe])
            self.switch_chart_to_timeframe(timeframe)
        self.close_def_tab()

    def close_def_tab(self):
        self.one_min.switch_to.window(handles["def"])
        self.close_actual_tab()

    def select_tab_chart_with_timeframe(self, timeframe):
        print("Selecting tab with chart", timeframe)
        self.one_min.switch_to.window(handles[timeframe])

    def switch_chart_to_timeframe(self, timeframe):
        if timeframe in timeframe_list:
            x = False
            while not x:
                try:
                    self.selected_timeframe = self.one_min.find_element_by_xpath(timeframe_button_xpaths[timeframe])
                    x = True
                except:
                    pass
            while not self.selected_timeframe.is_displayed():
                self.one_min.implicitly_wait(1)
                print("!!!!!!!!!!!!!!!!!!!!!! Waiting for", timeframe,
                      "timeframe button to show up... shouldnt need to")
            self.try_to_assert()
            print("---- Selecting", timeframe, "chart")
            self.selected_timeframe.click()
            self.check_chart(timeframe)
        else:
            print("Timeframe not in the list... how the fuck did we even get here?")

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)
        value = self.one_min.find_element_by_xpath(value_xpath)
        while not value.is_displayed():
            print("Waiting for chart to load completely - loading key value")
            time.sleep(5)
        if "−" in value.text:
            key_value = float(value.text.replace("−", '-'))
        else:
            key_value = float(value.text)
        print("- Key value found:", key_value)
        print("- Chart loaded successfully!")
        # time.sleep(1)
        # one_min.implicitly_wait(5)

    def get_key_value(self, timeframe):
        self.select_tab_chart_with_timeframe(timeframe)
        value = self.one_min.find_element_by_xpath(value_xpath)
        while not value.is_displayed():
            print("Waiting for chart to load completely - loading key value")
            time.sleep(2)
        if "−" in value.text:
            key_value = float(value.text.replace("−", '-'))
        else:
            key_value = float(value.text)
        print("* Key value in selected chart and timeframe:", key_value)

    def try_to_assert(self):
        x = 0
        while x == 0:
            try:
                assert title_to_assert["symbol"] in self.one_min.title
                assert title_to_assert["chart_name"] in self.one_min.title
                x = 1
                print("- Chart title confirmed!")
                # print("US500 confirmed")
                # print("Waiting for specified time...")
            except:
                print("Waiting for chart to load completely - trying to assert")
                time.sleep(3)

    def check_timeframe_number(self, timeframe):
        try:
            number = self.one_min.find_element_by_xpath(timeframe_number_xpath)
            if number.text == timeframe_numbers[timeframe]:
                print("Timeframe number confirmed!")
            # else:
            #     print("Timeframe is different than it should be, switching...")
            #     self.switch_chart_to_timeframe(timeframe)
            #     x = True
        except:
            raise TypeError("Nesedi timeframe cislo!")

    def close_actual_tab(self):
        self.one_min.close()

    def print_time(self):
        time_on_chart = self.one_min.find_element_by_xpath(time_on_chart_xpath)
        while True:
            # print(time_on_chart.text)
            self.time_now()
            time.sleep(1)



    # def

    
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
tv = Tradingview()
tv.tradingview_login()
tv.chart_three_m()

# time.sleep(5)
# tv.select_tab_chart_with_timeframe(timeframe="1m")
# tv.get_key_value()

"""
time.sleep(5)
tv.one_minute_tab()
time.sleep(5)
tv.three_minute_tab()
"""
# tv.switch_chart_to_timeframe("2h")
# time.sleep(5)
# tv.switch_chart_to_timeframe("15m")

# self.one_min.execute_script('window.open("https://duckduckgo.com")')
# print("window handles:", self.one_min.window_handles)
# self.one_min.switch_to.window(self.one_min.window_handles[0])
