import json
from pathlib import Path

import requests
import argparse

CONFIG_FILE = Path("config.json")

with CONFIG_FILE.open("r", encoding="utf-8") as file:
    config = json.load(file)

DISCORD_WEBHOOK = config["discord_webhook"]
PERMIT_ID = config["permit_id"]
TARGET_DATES = sorted(config["target_dates"])

AVAILABILITY_URL = f"https://www.recreation.gov/api/permits/{PERMIT_ID}/availability"

params = {
    "start_date": f"{TARGET_DATES[0]}T00:00:00.000Z",
    "end_date": f"{TARGET_DATES[-1]}T23:59:59.999Z",
    "commercial_acct": "false",
    "is_lottery": "false",
}

def send_discord(message):
    response = requests.post(
        DISCORD_WEBHOOK,
        json={"content": message},
        timeout=10,
    )
    response.raise_for_status()

def check_availability(debug=False):
    response = requests.get(
        AVAILABILITY_URL,
        params=params,
        headers={"User-Agent": "mt-st-helens-availability-checker/1.0"},
        timeout=15,
    )
    response.raise_for_status()

    data = response.json()
    availability = data["payload"]["availability"]

    if debug:
        for division_id, division in availability.items():
            dates = division.get("date_availability", {})
            print(f"Division {division_id}: {dates}")

    # division should be 999
    for date, info in availability.get('999', {}).get("date_availability", {}).items():
        if debug:
            print(date, info)
        if date.split("T")[0] in TARGET_DATES:
            remaining = info.get("remaining")

            if remaining is None:
                raise RuntimeError(f"Missing remaining value for {date}")

            if debug:
                print(f"{date}: {remaining} remaining")

            if remaining > 0:
                send_discord(
                    f"🚨 **MT. ST. HELENS PERMIT AVAILABLE** 🚨\n"
                    f"**Date:** {date.split('T')[0]}\n"
                    f"**Available:** {remaining}\n"
                    f"https://www.recreation.gov/permits/{PERMIT_ID}"
                )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true")
    arguments = parser.parse_args()

    check_availability(arguments.debug)
    if arguments.debug:
        send_discord("✅ Mt. St. Helens checker is working.")