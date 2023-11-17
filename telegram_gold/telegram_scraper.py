# =================================================================
# TELEGRAM SCRAPER for GoldSignals
# =================================================================
# import json
# import pickle
import traceback
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import mysql.connector
from datetime import date
from datetime import datetime
import time
import logging
import os
import dotenv
from selenium.common.exceptions import *

dotenv.load_dotenv(".env")
mysql_user = os.environ["mysql_user"]
mysql_passw = os.environ["mysql_passw"]
phone_number = os.environ["phone_number"]

options = webdriver.FirefoxOptions()
options.binary_location = "/usr/bin/firefox"
driverService = Service("/usr/local/bin/geckodriver")

url = "https://web.telegram.org/a"

xpaths = {
    "login_button": "/html/body/div[2]/div/div/div/div/button",
    "phonenumber": '//*[@id="sign-in-phone-number"]',
    "ripplecontainer": "/html/body/div[2]/div/div[1]/div/div[1]/div/div[1]/button/div[2]",
    "message": "//*[@id='message",

    "text": "/html/body/div[2]/div/div[2]/div[4]/div[2]/div/div[1]/div/div[2]/div[9]/div[4]/div/div/div[2]",

    "xpath_chat1": "/html/body/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[2]/div[1]",
    "xpath_checkchat1": "/html/body/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[2]/div[1]/a/div[2]/div[1]/div[1]/h3",

    "xpath_chat2": "/html/body/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[2]/div[2]",
    "xpath_checkchat2": "/html/body/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[2]/div[2]/a/div[2]/div[1]/div[1]/h3",

    "xpath_chat3": "/html/body/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[2]/div[3]",
    "xpath_checkchat3": "/html/body/div[2]/div/div[1]/div/div[2]/div/div/div/div/div[2]/div[3]/a/div[2]/div[1]/div[1]/h3",
}

db_connection = mysql.connector.connect(host="localhost",
                                        user=mysql_user,
                                        passwd=mysql_passw,
                                        database="fri_trade",
                                        autocommit=True)
cursor = db_connection.cursor(buffered=True)

# ---------------- LOGGING ----------------
log_telegram_gold = logging.getLogger("logger")
log_telegram_gold.setLevel(logging.INFO)
log_formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s",
                                  "%d.%m.%Y %H:%M:%S")
file_handler = logging.FileHandler("log_scraper.log")
file_handler.setFormatter(log_formatter)
log_telegram_gold.addHandler(file_handler)


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


print(f"{date_now()} {time_now_hms()} Opening browser")
log_telegram_gold.info("*****   Opening browser   **********************")
driver = webdriver.Firefox(service=driverService,
                           options=options)
driver.get(url)


def main():
    print("Waiting for login button")
    ok = False
    while not ok:
        try:
            login_button = driver.find_element(By.XPATH, xpaths["login_button"])
            login_button.click()
            ok = True
        except:
            time.sleep(1)

    print("Waiting for phone number field")
    ok = False
    keys_to_send = ["+", "4", "2", "1", phone_number, Keys.ENTER]
    while not ok:
        try:
            phonenumber = driver.find_element(By.XPATH, xpaths["phonenumber"])
            time.sleep(2)
            for n in range(0, 5):
                phonenumber.send_keys(Keys.BACKSPACE)
            for k in keys_to_send:
                phonenumber.send_keys(k)
            time.sleep(5)
            ok = True
        except:
            time.sleep(1)

    print("Waiting for MANUAL code input")
    ok = False
    while not ok:
        try:
            driver.find_element(By.XPATH, xpaths["ripplecontainer"])
            print("Code OK")
            ok = True
        except:
            time.sleep(3)

    print("Opening chat")
    check_if_correct_chat()

    print("Wating for message to load, selecting last message number in database")
    q = """select message_number from fri_trade.gold_messages order by message_number desc limit 1"""
    cursor.execute(q)
    last_msg_num = cursor.fetchone()[0]
    num_tried = 0
    ok = False

    while not ok:
        try:
            driver.find_element(By.XPATH, xpaths["message"] + str(last_msg_num) + "']")
            input(f"Message number {last_msg_num} is visible. Check if its still the last message and update "
                  f"database manually if needed, then press ENTER.")
            checker()
            ok = True

        # this element does not exist (or not loaded yet)
        except NoSuchElementException:
            # print("ERR:", traceback.print_exc())
            if num_tried < 10:
                # last_msg_num = last_msg_num + 1
                num_tried = num_tried + 1
                # print("last_msg_num", last_msg_num)
                time.sleep(1)
            else:
                input(f"Cant find message number {last_msg_num}! Update database manually and press ENTER.")
                cursor.execute(q)
                last_msg_num = cursor.fetchone()[0]
                num_tried = 0


def checker():
    count = 0
    to_sleep = 40
    s = f"Checker started... interval {to_sleep}s"
    print(s)
    log_telegram_gold.info(s)
    while True:
        q = """select message_number from fri_trade.gold_messages order by message_number desc limit 1"""
        cursor.execute(q)
        last_msg_num = int(cursor.fetchone()[0])

        if count == 45:
            log_telegram_gold.info("Still alive!")
            count = 0

        try:
            new_msg_num = last_msg_num + 1
            val_message = driver.find_element(By.XPATH, xpaths["message"] + str(new_msg_num) + "']")

            message_list = val_message.text.split(" ")
            message_list.append(new_msg_num)
            values = get_values(message_list, new_msg_num)

            # IF NEW SIGNAL IN TELEGRAM
            if values is not None:
                print(f"New values:\n{values}")
                log_telegram_gold.warning(f"New values: {values}")
                count = count + 1
                time.sleep(to_sleep)

            else:
                err = "* get_values returned None!"
                print(err)
                log_telegram_gold.error(err)
                input("Press ENTER to break checker cycle and stop program")
                break

        except NoSuchElementException:
            count = count + 1
            time.sleep(to_sleep)


def check_if_correct_chat():
    ok = False
    chat_name = "GoldSignals"
    # chat_name = "Kanal"
    print("chat_name:", chat_name)
    while not ok:
        try:
            chat1 = driver.find_element(By.XPATH, xpaths["xpath_chat1"])
            checkchat1 = driver.find_element(By.XPATH, xpaths["xpath_checkchat1"]).text
            if checkchat1 == chat_name:
                chat1.click()
                print(f"{chat_name} selected")
                ok = True

            chat2 = driver.find_element(By.XPATH, xpaths["xpath_chat2"])
            checkchat2 = driver.find_element(By.XPATH, xpaths["xpath_checkchat2"]).text
            if checkchat2 == chat_name:
                chat2.click()
                print(f"{chat_name} selected")
                ok = True

            chat3 = driver.find_element(By.XPATH, xpaths["xpath_chat3"])
            checkchat3 = driver.find_element(By.XPATH, xpaths["xpath_checkchat3"]).text
            if checkchat3 == chat_name:
                chat3.click()
                print(f"{chat_name} selected")
                ok = True
        except:
            time.sleep(1)


def get_values(message_list, new_msg_num) -> dict or None:
    temp_list = []

    for i in message_list:
        i = str(i)
        if "\n" in i:
            i.replace("\\n.", " ")
            temp_list.append(i)

    clean_str = " ".join(temp_list).split("\n")
    temp_list.clear()
    for i in clean_str:
        if ":" in i or "." in i or " " in i:
            i.replace(" ", "")
            temp_list.append(i)

    temp_list.append(new_msg_num)
    # print("temp_list", temp_list)
    # input("2enter")

    if "SL" in temp_list[7]:
        values = {
            "date": temp_list[0],
            "price_actual": temp_list[1],
            "operation": temp_list[2],
            "order_range": temp_list[3],
            "TP1": temp_list[4],
            "TP2": temp_list[5],
            "TP3": temp_list[6],
            "SL": temp_list[7],
            "message_number": int(temp_list[8]),
        }

        # msg_ok = False
        # while not msg_ok:
        try:
            # date and time
            date_of_mess, values["time"] = values["date"].split(" ")
            datelist = date_of_mess.split(".")
            values["date"] = f"{datelist[2]}.{datelist[1]}.{datelist[0]}"
            del datelist

            # price_actual
            values["price_actual"] = float(values["price_actual"].replace("XAUUSD: ", ""))
            # operation
            values["operation"] = values["operation"].replace("GOLD ", "").lower()
            # order_range
            values["order_range"] = list(map(float, values["order_range"].replace("[", "").replace("]", "").split("-")))
            # TP
            values["TP1"] = float(values["TP1"].replace("TP: ", ""))
            values["TP2"] = float(values["TP2"])
            values["TP3"] = float(values["TP3"])
            values["SL"] = float(values["SL"].replace("SL: ", ""))

            # print(values)
            q = f"""INSERT INTO fri_trade.gold_messages (message_number, message_time, message_date,
                    price_actual, operation, range_start, range_end, TP1, TP2, TP3, SL, processed)
                    VALUES ({values["message_number"]}, '{values["time"]}', '{values["date"]}', {values["price_actual"]},
                    '{values["operation"]}', {values["order_range"][0]}, {values["order_range"][1]}, {values["TP1"]}, 
                    {values["TP2"]}, {values["TP3"]}, {values["SL"]}, {False})"""
            print("INSERTING 1")
            cursor.execute(q)
            # msg_ok = True
            return values


        except:
            err = "3 TPs - Parsing the values has failed! The format of messages has probably been changed!"
            print(traceback.print_exc(), f"\n{err}")
            log_telegram_gold.critical(err)
            return None

    elif "SL" in temp_list[6]:
        values = {
            "date": temp_list[0],
            "price_actual": temp_list[1],
            "operation": temp_list[2],
            "order_range": temp_list[3],
            "TP1": temp_list[4],
            "TP2": temp_list[5],
            "SL": temp_list[6],
            "message_number": int(temp_list[8]),
        }

        # msg_ok = False
        # while not msg_ok:
        try:
            # date and time
            date_of_mess, values["time"] = values["date"].split(" ")
            datelist = date_of_mess.split(".")
            values["date"] = f"{datelist[2]}.{datelist[1]}.{datelist[0]}"
            del datelist

            # price_actual
            values["price_actual"] = float(values["price_actual"].replace("XAUUSD: ", ""))
            # operation
            values["operation"] = values["operation"].replace("GOLD ", "").lower()
            # order_range
            values["order_range"] = list(map(float, values["order_range"].replace("[", "").replace("]", "").split("-")))
            # TP
            values["TP1"] = float(values["TP1"].replace("TP: ", ""))
            values["TP2"] = float(values["TP2"])
            values["SL"] = float(values["SL"].replace("SL: ", ""))

            # print(values)
            q = f"""INSERT INTO fri_trade.gold_messages (message_number, message_time, message_date,
                    price_actual, operation, range_start, range_end, TP1, TP2, SL, processed)
                    VALUES ({values["message_number"]}, '{values["time"]}', '{values["date"]}', {values["price_actual"]},
                    '{values["operation"]}', {values["order_range"][0]}, {values["order_range"][1]}, {values["TP1"]}, 
                    {values["TP2"]}, {values["SL"]}, {False})"""
            print("INSERTING 2")
            cursor.execute(q)
            # msg_ok = True
            return values


        except:
            err = "2 TPs - Parsing the values has failed! The format of messages has probably been changed!"
            print(traceback.print_exc(), f"\n{err}")
            log_telegram_gold.critical(err)
            return None

    elif "SL" in temp_list[5]:
        values = {
            "date": temp_list[0],
            "price_actual": temp_list[1],
            "operation": temp_list[2],
            "order_range": temp_list[3],
            "TP1": temp_list[4],
            "SL": temp_list[6],
            "message_number": int(temp_list[8]),
        }

        # msg_ok = False
        # while not msg_ok:
        try:
            # date and time
            date_of_mess, values["time"] = values["date"].split(" ")
            datelist = date_of_mess.split(".")
            values["date"] = f"{datelist[2]}.{datelist[1]}.{datelist[0]}"
            del datelist

            # price_actual
            values["price_actual"] = float(values["price_actual"].replace("XAUUSD: ", ""))
            # operation
            values["operation"] = values["operation"].replace("GOLD ", "").lower()
            # order_range
            values["order_range"] = list(map(float, values["order_range"].replace("[", "").replace("]", "").split("-")))
            # TP
            values["TP1"] = float(values["TP1"].replace("TP: ", ""))
            values["SL"] = float(values["SL"].replace("SL: ", ""))

            # print(values)
            q = f"""INSERT INTO fri_trade.gold_messages (message_number, message_time, message_date,
                    price_actual, operation, range_start, range_end, TP1, SL, processed)
                    VALUES ({values["message_number"]}, '{values["time"]}', '{values["date"]}', {values["price_actual"]},
                    '{values["operation"]}', {values["order_range"][0]}, {values["order_range"][1]}, {values["TP1"]}, 
                    {values["SL"]}, {False})"""
            print("INSERTING 3")
            cursor.execute(q)
            # msg_ok = True
            return values

        except:
            err = "1 TP - Parsing the values has failed! The format of messages has probably been changed!"
            print(traceback.print_exc(), f"\n{err}")
            log_telegram_gold.critical(err)
            return None


if __name__ == "__main__":
    main()

