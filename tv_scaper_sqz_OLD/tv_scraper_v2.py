from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import time
import datetime

username = None
pw = None
email_button_xpath = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/div[1]/div[4]/div/span"
login_button = "/html/body/div[2]/div/div[2]/div/div/div/div/div/div/form/div[5]/div[2]/button/span[2]"
value_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[3]/td[2]/div/div[1]/div/div[2]/div[2]/div[2]/div/div[1]/div"
chart_url = "https://www.tradingview.com/chart"
time_on_chart_xpath = "/html/body/div[2]/div[1]/div[1]/div/div[3]/div[1]/div/span/button/span"
timeframe_number_xpath = "/html/body/div[2]/div[1]/div[2]/div[1]/div/table/tr[1]/td[2]/div/div[1]/div/div[1]/div[1]/div[1]/div[2]"

title_to_assert = {"symbol": "US500",
                   "chart_name" : "INDEXY Majchl",}

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





class Tradingview:
    def tradingview_login(self):
        # selenium one_min
        options = Options()
        options.headless = False
        executable = "/home/linuxfri/Downloads/geckodriver-v0.29.0-linux64/geckodriver"
        self.driver = webdriver.Firefox(options=options, executable_path=executable)
        # self.one_min.maximize_window()


        # opens tradingview sign in page
        if options.headless:
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

        # # opens tradingview chart and waits for it to completely load - asserts symbol and chart name in title
        # print("---- Opening chart")
        # self.one_min.get(chart_url)
        # self.check_chart()
        handles.update({"def": self.driver.window_handles[0]})

    def open_charts(self):
        i = 0
        for timeframe in timeframe_list:
            i = i + 1
            print("---- Opening chart for timeframe", timeframe)
            self.driver.execute_script('window.open("{charturl}")'.format(charturl=chart_url))
            handles.update({timeframe: self.driver.window_handles[i]})
            # print(handles)
            self.driver.switch_to.window(handles[timeframe])
            self.switch_chart_to_timeframe(timeframe)
        self.close_def_tab()

    def close_def_tab(self):
        self.driver.switch_to.window(handles["def"])
        self.close_actual_tab()

    def select_tab_chart_with_timeframe(self, timeframe):
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
            print("---- Selecting", timeframe, "chart")
            self.selected_timeframe.click()
            self.check_chart(timeframe)
        else:
            print("Timeframe not in the list... how the fuck did we even get here?")

    def check_chart(self, timeframe):
        self.try_to_assert()
        self.check_timeframe_number(timeframe)
        value = self.driver.find_element_by_xpath(value_xpath)
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
        value = self.driver.find_element_by_xpath(value_xpath)
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
                assert title_to_assert["symbol"] in self.driver.title
                assert title_to_assert["chart_name"] in self.driver.title
                x = 1
                print("- Chart title confirmed!")
                # print("US500 confirmed")
                # print("Waiting for specified time...")
            except:
                print("Waiting for chart to load completely - trying to assert")
                time.sleep(3)

    def check_timeframe_number(self, timeframe):
        try:
            number = self.driver.find_element_by_xpath(timeframe_number_xpath)
            if number.text == timeframe_numbers[timeframe]:
                print("Timeframe number confirmed!")
            # else:
            #     print("Timeframe is different than it should be, switching...")
            #     self.switch_chart_to_timeframe(timeframe)
            #     x = True
        except:
            raise TypeError("Nesedi timeframe cislo!")

    def close_actual_tab(self):
        self.driver.close()

    def print_time(self):
        time_on_chart = self.driver.find_element_by_xpath(time_on_chart_xpath)
        while True:
            # print(time_on_chart.text)
            self.time_now()
            time.sleep(1)

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

    # def

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




tv = Tradingview()
tv.tradingview_login()
tv.open_charts()
tv.select_tab_chart_with_timeframe(timeframe="1m")
tv.get_key_value(timeframe="1m")

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
