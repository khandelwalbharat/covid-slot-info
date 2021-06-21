#! /usr/bin/env python3

import json
import requests
import subprocess
import time
import datetime
import telegram_send
from collections import OrderedDict

def sendmessage(message):
    #subprocess.Popen(['notify-send', message])
    return

telegram_API_prefix = "https://api.telegram.org/bot<botID>"
last_update = False
last_text1 = ""
last_text2 = ""

def send_telegram_msg(text, code_format=False):
    global last_text1
    global last_text2
    url = telegram_API_prefix + "/sendMessage"
    params = {}
    params["chat_id"] = "@vaccine_ahmedabad" # telegram channel name
    if code_format:
        params["text"] = "<pre><code class=\"language-python\">{}</code></pre>".format(text)
        if last_text1 == text:
            return
        last_text1 = text
    else:
        params["text"] = "<b>{}</b>".format(text)
        if last_text2 == text:
            return
        last_text2 = text
    params["parse_mode"] = "HTML"
    response = requests.get(url, params=params)
    text = json.loads(response.content)
    if text["ok"]:
        return
    raise ValueError("Couldn't contact Telegram")


def get_relevant_info(results):
    new_results = []
    slot_text = ""
    for result in results:
        new_result = OrderedDict()
        for session in result["sessions"]:
            del session["session_id"]
        for key in ["name", "address", "district_name", "pincode", "fee_type", "sessions"]:
            new_result[key] = result[key]
        slot_text += "{} :- {} slots\n".format(new_result["name"], new_result["sessions"][0]["available_capacity"])
        new_results.append(new_result)
    return new_results, slot_text


def check_for_vaccine(district_id):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.76 Safari/537.36'} # This is chrome, you can set whatever browser you like
    date = datetime.datetime.today().strftime('%d-%m-%Y')
    url = "https://cdn-api.co-vin.in/api/v2/appointment/sessions/public/calendarByDistrict?district_id={}&date={}".format(district_id, date)
    response = requests.get(url, headers=headers)
    global last_update
    try:
        data = json.loads(response.content)
    except Exception as err:
        print(err)
        print(response.content)
        print("Issue in API data fetch")
        sendmessage("Failed to check {}".format(err))
        return 1

    results = []

    for center in data['centers']:
        # print(center['name'])
        real_sessions = []
        if center["fee_type"] == "Paid":
            continue
        for session in center['sessions']:
            if session['min_age_limit'] == 45:
                continue
            if session['available_capacity_dose1'] > 1:
                real_sessions.append(session)
        if not real_sessions:
            continue
        center['sessions'] = real_sessions
        results.append(center)

    if results:
        last_update = True
        results, slot_text = get_relevant_info(results)
        sendmessage("free vaccination slots available {}".format([center["name"] for center in results]))
        print(json.dumps(results, indent=2))
        print("free vaccination slots available\n{}".format(slot_text))
        send_telegram_msg(json.dumps(results, indent=2), code_format=True)
        send_telegram_msg("free vaccination slots available\n{}".format(slot_text))
        return 1
    else:
        if last_update:
            send_telegram_msg("All free vaccination slots gone")
        last_update = False
    return 0

searches = [1]
while(True):
    try:
        print(datetime.datetime.now().strftime("%A %d %B %Y %I:%M:%S %p IST"))
#        searches.append(check_for_vaccine(154))
        searches.append(check_for_vaccine(770)) #relevant district ID
        searches = searches[-20:]
        if sum(searches) >= 1:
            time_to_sleep = 60
        else:
            time_to_sleep = 60
        time.sleep(time_to_sleep)
    except Exception as err:
        print(err)
        sendmessage("Failed to check {}".format(err))
        time.sleep(10)
