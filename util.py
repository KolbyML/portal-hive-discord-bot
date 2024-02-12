import requests
import json
import datetime
import time


def load_state():
    try:
        file = open('state.json')
        data = json.load(file)
        file.close()
        return data
    except:
        return {"admins": [240180844130598912, 425615769280315392, 439193900096290816, 843971820994822184],
                "glados_channels": [],
                "hive_channels": []}


def save_state(state):
    with open("state.json", "w") as outfile:
        json.dump(state, outfile)


def get_today_vs_yesterday_portal_hive_test_data():
    response = requests.get('https://portal-hive.ethdevops.io/listing.jsonl')
    data = [json.loads(line) for line in response.text.splitlines()]

    epoch_time = int(time.time())
    day_in_seconds = 24 * 60 * 60
    todays_data_overview = []
    yesterdays_data_overview = []
    for i in data:
        if datetime.datetime.fromisoformat(i["start"]).timestamp() > epoch_time - day_in_seconds:
            todays_data_overview.append(i)
        elif epoch_time - day_in_seconds > datetime.datetime.fromisoformat(i["start"]).timestamp() > epoch_time - (
                day_in_seconds * 2):
            yesterdays_data_overview.append(i)
        else:
            # we can break because the jsonl is in sorted order
            break

    # We do today/yesterday in 2 different loops so that we know if a test suite doesn't run which would be -1.
    # this can also mean the test suite is new
    return_data = []
    for i in todays_data_overview:
        if i["name"] in [value.get('name') for value in return_data]:
            for k in return_data:
                if i["name"] == k["name"]:
                    k["tp"] = i["passes"] / i["ntests"]
                    k["today_percent"] = '{:.2%}'.format(i["passes"] / i["ntests"])
        else:
            return_data.append({"name": i["name"], "today_percent": '{:.2%}'.format(i["passes"] / i["ntests"]), "tp": i["passes"] / i["ntests"],
                                "yesterday_percent": "Didn't run", "emoji": ":zombie:"})
    for i in yesterdays_data_overview:
        if i["name"] in [value.get('name') for value in return_data]:
            for k in return_data:
                if i["name"] == k["name"]:
                    k["yp"] = i["passes"] / i["ntests"]
                    k["yesterday_percent"] = '{:.2%}'.format(i["passes"] / i["ntests"])
        else:
            return_data.append({"name": i["name"], "today_percent": "Didn't run",
                                "yesterday_percent": '{:.2%}'.format(i["passes"] / i["ntests"]), "yp": i["passes"] / i["ntests"], "emoji": ":zombie:"})

    for i in return_data:
        if i["today_percent"] != "Didn't run" and i["yesterday_percent"] != "Didn't run":
            if i["tp"] > i["yp"]:
                i["emoji"] = ":chart_with_upwards_trend:"
            elif i["tp"] < i["yp"]:
                i["emoji"] = ":chart_with_downwards_trend:"
            else:
                i["emoji"] = ":infinity:"
        if i["today_percent"] != "Didn't run" and int(i["tp"]) == 1:
            i["emoji"] = ":rocket:"

    return return_data

def get_glados_hourly_success_rate():
    response = requests.get('https://glados.ethdevops.io/api/hourly-success-rate/')
    return float(response.text)
