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
chart_url = "https://www.tradingview.com/chart/"
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
# handles = {
#     "def": "",
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
# }

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
        self.timeframe_3m = "3m"

    def aaaa(self):
        self.aaaaa_min = webdriver.Firefox(options=self.options, executable_path=self.executable)

        if self.options.headless:
            print("Opening tradingview website in HEADLESS mode")
        else:
            print("Opening tradingview website in VISIBLE mode")

        self.aaaaa_min.get("https://www.tradingview.com/accounts/signin/")

        # check if sign in page is loaded - checks email button, asserts title and clicks email button
        email_button = self.aaaaa_min.find_element_by_xpath(email_button_xpath)
        while not email_button.is_displayed():
            self.aaaaa_min.implicitly_wait(1)
            print("Waiting for sign in page to load")
        assert "Authentication — TradingView" in self.aaaaa_min.title
        email_button.click()
        print("- Sign in page loaded successfully!")

        # waits for username text field to load and fills in username
        username_tf = self.aaaaa_min.find_element_by_name("username")
        while not username_tf.is_displayed():
            self.aaaaa_min.implicitly_wait(1)
            print("Waiting for username text field to load")
        username_tf.send_keys(username)

        # waits for password text field to load and fills in password
        password_tf = self.aaaaa_min.find_element_by_name("password")
        while not password_tf.is_displayed():
            self.aaaaa_min.implicitly_wait(1)
            print("Waiting for password text field to load")
        password_tf.send_keys(pw)

        # clicks login button and waits for login to be completed
        self.aaaaa_min.find_element_by_xpath(login_button).click()
        y = 0
        while y == 0:
            html_code = self.aaaaa_min.page_source
            if "is-authenticated" in html_code:
                print("- Login successful!")
                y = 1
            else:
                print("Waiting for login to be completed")
                y = 0
                time.sleep(1)

        # otvorit tv chart
        self.aaaaa_min.get(chart_url)

        # try to assert
        confirm_assert = False
        while not confirm_assert:
            try:
                assert self.title_to_assert_us500["symbol"] in self.three_min.title
                assert self.title_to_assert_us500["chart_name"] in self.three_min.title
                confirm_assert = True
                print(self.title_to_assert_us500["symbol"], self.title_to_assert_us500["chart_name"], "in title confirmed!")
            except:
                print("Waiting for chart to load completely - trying to assert")
                time.sleep(2)

    def three_min_chart(self):
        # selenium three_min
        self.three_min = webdriver.Firefox(options=self.options, executable_path=self.executable)

        # self.three_min.maximize_window()

        # opens tradingview sign in page
        if self.options.headless:
            print("Opening tradingview website in HEADLESS mode")
        else:
            print("Opening tradingview website in VISIBLE mode")

        self.three_min.get("https://www.tradingview.com/accounts/signin/")

        # check if sign in page is loaded - checks email button, asserts title and clicks email button
        email_button = self.three_min.find_element_by_xpath(email_button_xpath)
        while not email_button.is_displayed():
            self.three_min.implicitly_wait(1)
            print("Waiting for sign in page to load")
        assert "Authentication — TradingView" in self.three_min.title
        email_button.click()
        print("- Sign in page loaded successfully!")

        # waits for username text field to load and fills in username
        username_tf = self.three_min.find_element_by_name("username")
        while not username_tf.is_displayed():
            self.three_min.implicitly_wait(1)
            print("Waiting for username text field to load")
        username_tf.send_keys(username)

        # waits for password text field to load and fills in password
        password_tf = self.three_min.find_element_by_name("password")
        while not password_tf.is_displayed():
            self.three_min.implicitly_wait(1)
            print("Waiting for password text field to load")
        password_tf.send_keys(pw)

        # clicks login button and waits for login to be completed
        self.three_min.find_element_by_xpath(login_button).click()
        y = 0
        while y == 0:
            html_code = self.three_min.page_source
            if "is-authenticated" in html_code:
                print("- Login successful!")
                y = 1
            else:
                print("Waiting for login to be completed")
                y = 0
                time.sleep(1)

        # otvorit tv chart
        self.three_min.get(chart_url)

        # try to assert
        confirm_assert = False
        while not confirm_assert:
            try:
                assert self.title_to_assert_us500["symbol"] in self.three_min.title
                assert self.title_to_assert_us500["chart_name"] in self.three_min.title
                confirm_assert = True
                print(self.title_to_assert_us500["symbol"], self.title_to_assert_us500["chart_name"], "in title confirmed!")
            except:
                print("Waiting for chart to load completely - trying to assert")
                time.sleep(2)

        # najst a kliknut dany timeframe_3m button
        print("Vyberam timeframe", self.timeframe_3m)
        tf_button_found = False
        while not tf_button_found:
            try:
                self.selected_timeframe = self.three_min.find_element_by_xpath(timeframe_button_xpaths[self.timeframe_3m])
                tf_button_found = True
            except:
                pass
        while not self.selected_timeframe.is_displayed():
            self.three_min.implicitly_wait(1)
            print("!!!!!!!!!!!!!!!!!!!!!! Waiting for", self.timeframe_3m,
                  "timeframe_3m button to show up... shouldnt need to")
        self.selected_timeframe.click()
        # self.check_chart(timeframe_3m)

        # kontrola timeframe_3m cisla
        try:
            number = self.three_min.find_element_by_xpath(timeframe_number_xpath)
            if number.text == timeframe_numbers[self.timeframe_3m]:
                print("Timeframe", self.timeframe_3m, "confirmed!")
            # else:
            #     print("Timeframe is different than it should be, switching...")
            #     self.switch_chart_to_timeframe(timeframe_3m)
            #     x = True
        except:
            raise TypeError("Nesedi timeframe_3m cislo! Tu by sme sa nemali dostat")

        # vytiahni hodnotu
        print("Looking for key value")
        val_ok = False
        while not val_ok:
            value = self.three_min.find_element_by_xpath(value_xpath)
            while not value.is_displayed():
                self.three_min.implicitly_wait(1)
                print("Waiting for key value to load on 3m chart")
            print("Key value found!")
            try:
                if "−" in value.text:
                    key_value = float(value.text.replace("−", '-'))
                    val_ok = True
                    print("Actual (not usable) key value is:", key_value)
                else:
                    key_value = float(value.text)
                    val_ok = True
                    print("Actual (not usable) key value is:", key_value)
            except ValueError:
                time.sleep(1)

    def three_min_get_value(self):
        print("Grabbin' key value on 3m")
        value = self.three_min.find_element_by_xpath(value_xpath)
        while not value.is_displayed():
            self.three_min.implicitly_wait(1)
            print("Waiting for key value to load on 3m chart")
        if "−" in value.text:
            key_value = float(value.text.replace("−", '-'))
        else:
            key_value = float(value.text)
        print("Key value on 3m is:", key_value)

        # kontrola predoslej hodnoty
        # zapisane = self.check_last_value_params(key_value=key_value, symbol=title_to_assert_us500["symbol"],
        #                                         timeframe_3m=timeframe_3m)
        last_added_value_query = 'select dateOfValue, timeOfValue from fri_trade.%s_%s order by id desc limit 1'
        fri_trade_cursor.execute(last_added_value_query, self.title_to_assert_us500["symbol"], self.timeframe_3m)
        params = fri_trade_cursor.fetchone()
        if params is not None:
            date_of_last_value = params[0]
            hour_of_last_value = params[1][:2]
            minute_of_last_value = params[1][3:5]
            second_of_last_value = params[1][2:]
            time_of_last_value = params[1]

            print("Params from last value: hodina", hour_of_last_value, "   ", date_of_last_value)
            print("Current params:  hodina", self.check_current_hour(), "   ", self.date_now())

            if self.time_now() == time_of_last_value and self.date_now() == date_of_last_value:
                print("Datum a cas novej hodnoty na grafe", self.timeframe_3m,
                      " je rovnaky ako na minulej - nezapisujem!")
                zapisat = False
            else:
                print("Hodnota na grafe", self.timeframe_3m, "s parametrami", self.date_now(), self.time_now(),
                      "este nebola zapisana - zapisujem!")
                zapisat = True

            if int(self.check_current_minute()) - 3 == int(minute_of_last_value):
                print("Hodnota je v 3-minútovom poradí - potvrdzujem zapísanie!")

            elif self.check_current_day() == 0 and int(hour_of_last_value) == 22:
                print("*Rozdiel v čase minulej a novej hodnoty je VÍKENDOVÝ - potvrdzujem zapísanie!")
                zapisat = True

            elif int(self.check_current_hour()) == 0 and int(hour_of_last_value) == 22 and int(
                    minute_of_last_value) == 57:
                print("Rozdiel v čase poslednej a novej hodnoty je NOČNÝ - potvrdzujem zapísanie!")
                zapisat = True

            else:
                print("*** Čas najnovšej hodnoty nie je v poradí - ruším zapísanie!")
                zapisat = False

            if zapisat:
                print("ZAPISUJEM")
                self.insert_value_to_db(key_value=key_value, symbol=self.title_to_assert_us500["symbol"],
                                        timeframe=self.timeframe_3m)
                self.look_for_red_wave_break(self.title_to_assert_us500["symbol"], self.timeframe_3m)
            else:
                print("NEZAPISUJEM")
        # TODO: skontrolovat ako to bude reagovat pocas behu, ci su tie casove podmienky vyssie dobre nastavene na 3m
        else:
            print("Prazdna databaza! / Hodnota je prva/druha v databaze!",
                  "\nNehľadám obchodnú príležitosť!",
                  "\nZAPISUJEM")
            self.insert_value_to_db(key_value=key_value, symbol=self.title_to_assert_us500["symbol"],
                                    timeframe=self.timeframe_3m)

        # screenshot
        self.three_min.save_screenshot("/home/linuxfri/PycharmProjects/trade/{symbol}/{tf}/chart"
                                       .format(symbol=self.title_to_assert_us500["symbol"], tf=self.timeframe_3m)
                                       + "_" + self.date_now() + "_" + self.time_now() + ".png")
        print("Screenshot saved!")

    def insert_value_to_db(self, key_value, symbol, timeframe):
        query = "insert into fri_trade." + symbol + "_" + timeframe + "(key_value, dateOfValue, timeOfValue) " \
                                                                      "VALUES(%s, %s, %s)"
        fri_trade_cursor.execute(query, (key_value, self.date_now(), self.time_now(),))
        print("Key value from {tf} added to database!".format(tf=timeframe))

    def look_for_red_wave_break(self, symbol, timeframe):
        print("Hľadám obchodnú príležitosť...")
        # vyberie posledne 3 hodnoty vratane novej zapisanej - ak sa nova nezapisala, tak sa tato metoda nespusti!
        values_query = 'select key_value from fri_trade.%s_%s order by id desc limit 3'
        print("piss-----------------------")
        fri_trade_cursor.execute(values_query, symbol, timeframe)
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
        print("Červená vlna sa zlomila! ------------------------------------------------------------ BUY!")
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
        # print(time_actual)
        return time_actual

    def date_now(self):
        date_object = datetime.date.today()
        date_actual = date_object.strftime("%d.%m.%Y")
        # print(date_actual)
        return date_actual


tv = Tradingview()
tv.three_min_chart()
tv.three_min_get_value()
# tv.aaaa()
"""
while True:
    act_time = tv.time_now()
    hrs = int(tv.check_current_hour())
    mins = int(tv.check_current_minute())
    secs = int(tv.check_current_second())
    day = int(tv.check_current_day())
    print(act_time)

    target_secs = 57
    three_min_list = [0, 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36, 39, 42, 45, 48, 51, 54, 57]
    five_min_list = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    fifteen_min_list = [0, 15, 30, 45]

    # 1m
    if day in range(0, 4) and hrs in range(0, 22) and mins in range(0, 59) and secs == target_secs:
        pass
    # 3m
    elif day in range(0, 4) and hrs in range(0, 22) and mins in three_min_list and secs == target_secs:
        tv.three_min_get_value()
    # 5m
    elif day in range(0, 4) and hrs in range(0, 22) and mins in five_min_list and secs == target_secs:
        pass
    # 15m
    elif day in range(0, 4) and hrs in range(0, 22) and mins in fifteen_min_list and secs == target_secs:
        pass
    else:
        pass
    time.sleep(1)

"""
# time.sleep(5)
# tv.select_tab_chart_with_timeframe(timeframe_3m="1m")
# tv.get_key_value()


# time.sleep(5)
# tv.three_minute_tab()
# time.sleep(5)
# tv.three_minute_tab()

# tv.switch_chart_to_timeframe("2h")
# time.sleep(5)
# tv.switch_chart_to_timeframe("15m")

# self.three_min.execute_script('window.open("https://duckduckgo.com")')
# print("window handles:", self.three_min.window_handles)
# self.three_min.switch_to.window(self.three_min.window_handles[0])
