from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import datetime
import mysql.connector
import tv_credentials
from apscheduler.schedulers.blocking import BlockingScheduler
# import trader
import os
import dotenv

dotenv.load_dotenv("../.env")

mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
xtb_userId = os.environ["xtb_userId"]
xtb_passw = os.environ["xtb_pw"]

# scheduler
sched = BlockingScheduler()

# paths & credentials
username = tv_credentials.username
pw = tv_credentials.pw
email_button = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div[1]/div[4]/div/span"
login_button = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/form/div[5]/div[2]/button/span[2]"
value_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[3]/td[2]/div/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/div"

# mysql - fri_trade schema
db = mysql.connector.connect(host="localhost",
                             user=mysql_user,
                             passwd=mysql_passw,
                             database="fri_trade",
                             autocommit=True)
fri_trade_cursor = db.cursor(buffered=True)


class Tradingview:
    def open_tradingview(self):
        # selenium one_min
        options = Options()
        options.headless = True
        executable = "/home/linuxfri/Downloads/geckodriver-v0.29.0-linux64/geckodriver"
        self.driver = webdriver.Firefox(options=options, executable_path=executable)
        # self.one_min.maximize_window()

        # opens tradingview sign in page
        if options.headless:
            print("- Opening tradingview website in HEADLESS mode")
        else:
            print("- Opening tradingview website in VISIBLE mode")
        self.driver.get("https://www.tradingview.com/accounts/signin/")

        # check if sign in page is loaded - checks email button, asserts title and clicks email button
        email = self.driver.find_element_by_xpath(email_button)
        while not email.is_displayed():
            self.driver.implicitly_wait(1)
            print("Waiting for sign in page to load")
        assert "Authentication — TradingView" in self.driver.title
        email.click()
        print("- Sign in page loaded successfully!")

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
                print("- Login successful!")
                y = 1
            else:
                print("Waiting for login to be completed")
                y = 0
                time.sleep(1)

        # opens tradingview chart and waits for it to completely load - asserts title
        self.driver.get("https://www.tradingview.com/chart/K7fopCTL/")
        x = 0
        while x == 0:
            try:
                assert "INDEXY Friday" in self.driver.title
                assert "US500" in self.driver.title
                x = 1
                print("- Chart loaded successfully!")
                print("US500 confirmed")
                print("Waiting for specified time...")
            except:
                print("Waiting for chart to load completely")
                x = 0
                time.sleep(1)
                # one_min.implicitly_wait(5)

    def get_key_value(self):
        print(time_now())
        print("- Getting key value")

        # waits for key value to show up, then prints it and adds it to database
        value = self.driver.find_element_by_xpath(value_xpath)
        while not value.is_displayed():
            self.driver.implicitly_wait(1)
            print("Waiting for key value to load")
        print("- Key value loaded successfully!")
        if "−" in value.text:
            key_value = float(value.text.replace("−", '-'))
        else:
            key_value = float(value.text)
        # key_value = -40.0
        print("Key value is:", key_value)

        # self.insert_value_to_db(key_value=key_value)
        self.take_screenshot()

        zapisane = self.check_last_value_params(key_value=key_value)
        """
        if zapisane and key_value > 0:
            self.wait_for_green_wave_end()
        elif zapisane and key_value < 0:
            self.look_for_red_wave_bottom()
        """
        if zapisane:
            self.look_for_red_wave_bottom()
        else:
            pass

    def database_insert_value(self, key_value):
        q = "insert into fri_trade.US500_key_values(key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
        fri_trade_cursor.execute(q, (key_value, date_now(), time_now(),))
        print("- Key value added to database!")

    def take_screenshot(self):
        self.driver.save_screenshot("/home/linuxfri/PycharmProjects/trade/screenshots/chart" + "_" + date_now() + "_" + time_now() + ".png")
        print("- Screenshot saved!")

    # checks if hour of last value is LOWER than hour of current value by 1
    # def check__

    def check_last_value_params(self, key_value):
        last_added_value = 'select dateOfValue, timeOfValue from fri_trade.US500_key_values order by id desc limit 1'
        fri_trade_cursor.execute(last_added_value)
        params = fri_trade_cursor.fetchone()

        if params is not None:
            dateOfLastValue = params[0]
            hourOfLastValue = params[1][:2]

            print("Params from last value: hodina", hourOfLastValue, dateOfLastValue)
            print("Current params:  hodina", check_current_hour(), date_now())

            # checks params of new value for duplicates - hour and date
            if str(check_current_hour()) == hourOfLastValue and date_now() == dateOfLastValue:
                print("Hodnota s tymito parametrami uz existuje - nezapisujem!")
                zapisat = False
            else:
                print("Hodnota hodiny", check_current_hour(), "dňa", date_now(), "este nebola zapisana - zapisujem!")
                zapisat = True

            # checks if new value's hour is HIGHER by 1 than last value - weekends and break between 22:00-23:00,
            # hour difference 23:00 and 0:00, weekend (sunday is the first day of trading) are accounted for
            if int(check_current_hour()) - 1 == int(hourOfLastValue):
                print("Hodnota je v hodinovom poradí - potvrdzujem zapísanie!")

            elif int(check_current_hour()) == 0 and int(hourOfLastValue) == 22:
                print("Rozdiel v čase poslednej a novej hodnoty je NOČNÝ - potvrdzujem zapísanie!")
                zapisat = True

            # elif int(check_current_hour()) == 0 and int(hourOfLastValue) == 23:
            #     print("Rozdiel v čase poslednej a novej hodnoty je POLNOČNÝ - potvrdzujem zapísanie!")
            #     zapisat = True

            elif check_current_day() == 0 and int(hourOfLastValue) == 21:
                print("*Rozdiel v čase poslednej a novej hodnoty je VÍKENDOVÝ - potvrdzujem zapísanie!")
                zapisat = True
            else:
                print("*** Hodina najnovšej hodnoty nie je v hodinovom poradí - ruším zapísanie!")
                zapisat = False

            if zapisat:
                print("ZAPISUJEM")
                self.database_insert_value(key_value=key_value)
                return zapisat
            else:
                print("NEZAPISUJEM")
                return zapisat
        else:
            print("Prazdna databaza - hodnota je prva/druha v databaze!")
            print("ZAPISUJEM")
            self.database_insert_value(key_value=key_value)
            zapisat = True
            return zapisat

    def look_for_red_wave_bottom(self):
        # vyberie posledne 3 hodnoty vratane novej zapisanej - ak sa nova nezapisala, tak sa tato metoda nespusti!
        values = 'select key_value from fri_trade.US500_key_values order by id desc limit 3'
        fri_trade_cursor.execute(values)
        params = fri_trade_cursor.fetchall()

        try:
            # konvertuje tuple z databazy na string a ten na float ciselnu hodnotu
            C = new_value = float("".join(params[0]))  # C
            B = previous_value = float("".join(params[1]))  # B
            A = prev_previous_value = float("".join(params[2]))  # A
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


        # pridat stlpec  databazy, kde sa bude zapisovat buy/sell/nič + den slovom?... potom to nejak prepojit, ze
        # k jednotlivym zapisom s buy/sell bude aj pridavat realizovany zisk?.. ze to nejak bude vediet vybraz z xAPI?

        """
        if 0 > new_value > previous_value and previous_value < 0:
            print("koniec červenej vlny!!!  BUY!")
            red_wave_end = True
            self.wait_for_green_wave_end()
        else:
            print("nič!")
            red_wave_end = False
        # return red_wave_end

        # while red_wave_end == True and new_value < 0 or red_wave_end == True and new_value > 0:
        #     pass
        """


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

    # ----------------------------------------------------------------

    def green_wave_starting(self):
        print("******** Nič - začína zelená vlna.")

    def green_wave_break(self):
        print("******** Nič - zelená vlna sa zlomila.")





    def aaa(self):
        # time_actual = time_now()
        return "testovaci string"


def time_now():
    time_object = datetime.datetime.now()
    time_actual = time_object.strftime("%H:%M:%S")
    # print(time_actual)
    return time_actual


def date_now():
    date_object = datetime.date.today()
    date_actual = date_object.strftime("%d.%m.%Y")
    # print(date_actual)
    return date_actual


def check_current_day():
    # 0 = monday...
    weekno = int(datetime.datetime.today().weekday())
    return weekno


def check_current_hour():
    hour_actual = datetime.datetime.now().hour
    return hour_actual


def check_current_minute():
    minute_actual = datetime.datetime.now().minute
    return minute_actual


def debug_db_insert(key_value, datum, cas):
    q = "insert into fri_trade.US500_key_values(key_value, dateOfValue, timeOfValue) VALUES(%s, %s, %s)"
    fri_trade_cursor.execute(q, (key_value, datum, cas,))
    print("Testovacia hodnota pridana do DB!")


# --------------- DEBUG!!!
# tv.check_last_value_params()
# debug_db_insert(-44.9, "20.09.2021", "18:59")
# tv.look_for_red_wave_bottom()

# --------------- testy
# print(check_current_hour())
# print(time_now())
# print(date_now())


tv = Tradingview()
tv.open_tradingview()

# x = trader.Xtb()

minute = 59
second = 57
# cez tyzden
@sched.scheduled_job('cron', day_of_week='mon-thu', hour="0-22", minute=minute, second=second)
def scheduled_job():
    print('\n*******************************************************************')
    tv.get_key_value()

# @sched.scheduled_job('cron', day_of_week='mon-thu', hour="23", minute=minute, second=second)
# def scheduled_job():
#     print('\n*******************************************************************')
#     tv.get_key_value()

# piatok
@sched.scheduled_job('cron', day_of_week='fri', hour="0-21", minute=minute, second=second)
def scheduled_job():
    print('\n*******************************************************************')
    tv.get_key_value()

# nedela
# @sched.scheduled_job('cron', day_of_week='sun', hour="23", minute=minute, second=second)
# def scheduled_job():
#     print('\n*******************************************************************')
#     tv.get_key_value()


sched.configure()
sched.start()
