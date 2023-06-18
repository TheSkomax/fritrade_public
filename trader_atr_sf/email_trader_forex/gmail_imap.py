#!/usr/bin/env python
# pylint: disable=unused-argument

import base64
import email
import imaplib
import json
import re
import time
import urllib
from urllib import request


GOOGLE_ACCOUNTS_BASE_URL = "https://accounts.google.com"
GOOGLE_CLIENT_ID = "1094522478046-alnj9hhpu22kchck9mhbo2l9c68s29qo.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "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"
GOOGLE_REFRESH_TOKEN = "1//09rsoWfs51OFyCgYIARAAGAkSNwF-L9IrRGwnKOs82vPHa9px4eQbOc74i4PQIvRq_xdOwWvJ2J9aDMFxCaoFKznaY6siqQyxLAI"
GOOGLE_EMAIL = 'michal.jendrisak.knm@gmail.com'  # The e-mail used to obtain the above credentials
VIEW_X_LAST = 1  # Information from the last 10 received e-mails will be displayed


def call_refresh_token(client_id, client_secret, refresh_token):
    params = {}
    params['client_id'] = client_id
    params['client_secret'] = client_secret
    params['refresh_token'] = refresh_token
    params['grant_type'] = 'refresh_token'
    request_url = GOOGLE_ACCOUNTS_BASE_URL + '/o/oauth2/token'
    response = urllib.request.urlopen(request_url, urllib.parse.urlencode(params).encode('UTF-8')).read().decode('UTF-8')
    return json.loads(response)


def refresh_authorization(google_client_id, google_client_secret, refresh_token):
    response = call_refresh_token(google_client_id, google_client_secret, refresh_token)
    return response['access_token'], response['expires_in']


def generate_oauth2_string(username, access_token, as_base64=False):
    auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)
    if as_base64:
        auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    return auth_string


def gmail_auth():
    access_token, expires_in = refresh_authorization(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN) 
    auth_string = generate_oauth2_string(GOOGLE_EMAIL, access_token, as_base64=False)
    imap_conn = imaplib.IMAP4_SSL('imap.gmail.com', port=993)
    imap_conn.debug = 2
    imap_conn.authenticate('XOAUTH2 ', lambda x: auth_string)
    return imap_conn


def parse_uid(data):
    pattern_uid = re.compile(r'\d+ \(UID (?P<uid>\d+)\)')
    match = pattern_uid.match(data)
    return match.group('uid')


def gmail_keepalive(imap_conn):
    e = 0
    while True:
        try:
            resp_code, response = imap_conn.noop() ## Keep connection Alive
            return imap_conn
        except Exception as err:
            e += 1
            print(f"Gmail access error: {err}")
            if "please login again" in str(err): # If you get this error, you'll need to generate a new refresh token
                print(f"Atention! Gmail oauth expired, create a new oaut by typing:\n\npython2 oauth2.py --generate_oauth2_token --client_id={GOOGLE_CLIENT_ID} --client_secret={GOOGLE_CLIENT_SECRET}")
                time.sleep(5*60*60)
            if e > 3:
                print("Error on gmail access, trying to login again.")
                return gmail_auth()
            time.sleep(5)
            continue


def check_email(imap_conn):
    imap_conn.select(mailbox="INBOX", readonly=True)
    retcode, messages = imap_conn.search(None, '(FROM "noreply@tradingview.com" SUBJECT "Alert: EURCHF 1h Values report")')
    if retcode == 'OK':
        # print(f"\tMail count: {len(messages[0].decode().split()[-2:])}")

        selected_messages = messages[0].decode().split()[-VIEW_X_LAST:]
        selected_messages.reverse()

        for mail_id in selected_messages:
            resp_code, mail_data = imap_conn.fetch(mail_id, '(RFC822)')
            message = email.message_from_bytes(mail_data[0][1])

            sender = message.get('From')
            subject = message.get('subject')
            date_raw = message.get('date')
            # print(sender, subject, date_raw)

            timelist = date_raw.split(" ")
            date_dmy = f"{timelist[1]}.{time.strptime(timelist[2], '%b').tm_mon}.{timelist[3]}"
            time_hms = timelist[4]
            time_hms = time_hms.split(":")
            time_hms[0] = int(time_hms[0])

            if time_hms[0] < 22:
                time_hms[0] = str(time_hms[0] + 2)
            elif time_hms[0] == 23:
                time_hms[0] = "1"
            elif time_hms[0] == 22:
                time_hms[0] = "0"
            time_received = ":".join(time_hms)

            message = message.as_string()
            message = message.replace('\n', " ")
            message = message.split(" ")

            atrup_value = round(float(message[message.index("ATR-upper") + 1]), 5)
            atrlow_value = round(float(message[message.index("ATR-lower") + 1][:-4]), 5)
            price_close = round(float(message[message.index('2;">Price') + 1]), 5)
            # print(date_dmy, time_received, atrlow_value, atrlow_value, price_close)

            adict = {
                "msgnum": mail_id,
                "sender": sender,
                "subject": subject,
                "date_dmy": date_dmy,
                "time_received": time_received,
                "atrup_value": atrup_value,
                "atrlow_value": atrlow_value,
                "price_close": price_close,
            }
            return adict
            # print("\n\t------------------------------------------------")
            # print(f"\tMail {a} from {len(selected_messages)}:")
            # print("\t   Date:     {}".format(message.get("Date")))
            # print("\t   Subject:  {}".format(message.get("Subject")))
            # print("\t   From:     {}".format(message.get("From")))
            # print("\t   To:       {}".format(message.get("To")))
            # print("\t   Bcc:      {}".format(message.get("Bcc")))


def start():
    print("Starting Gmail checker.")
    imap_conn = gmail_auth()
    # while True:
    try:
        values = check_email(imap_conn)
        # time.sleep(60)
        # imap_conn = gmail_keepalive(imap_conn)
        # print(values)
        imap_conn.close()
        return values
    except Exception as err:
        if "state NONAUTH" in str(err):
            imap_conn = gmail_auth()
            time.sleep(10)
            # continue
        exit()


# if __name__ == '__main__':
#     start()
