import argparse
import tomllib
from datetime import date, timedelta
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG = PROJECT_ROOT / "config.toml"


def parse_dates(entries, label):
    """Flatten bare dates and {start, end} ranges into sorted dates."""
    days = set()
    for i, entry in enumerate(entries):
        if isinstance(entry, date):
            days.add(entry)
        elif isinstance(entry, dict):
            try:
                start, end = entry["start"], entry["end"]
            except KeyError as missing:
                raise ValueError(
                    f"{label}: range at position {i} is missing {missing}"
                ) from None
            if end < start:
                raise ValueError(f"{label}: range {start} to {end} ends before it starts")
            days.update(start + timedelta(n) for n in range((end - start).days + 1))
        else:
            raise TypeError(
                f"{label}: entry {i} is not a date or a start/end range: {entry!r}"
            )
    return sorted(days)


def send_discord(webhook, message):
    requests.post(webhook, json={"content": message}, timeout=10).raise_for_status()
    

def check_availability(watch, webhook, debug=False):
    name = watch.get('permit_name', '?')
    permit_id = watch["permit_id"]
    party_size = watch.get("party_size", 1)
    target_dates= parse_dates(watch.get("dates", []), name)

    if not target_dates:
        return

    response = requests.get(
        f"https://www.recreation.gov/api/permits/{permit_id}/availability",
        params={
            "start_date": f"{target_dates[0]}T00:00:00.000Z",
            "end_date": f"{target_dates[-1]}T23:59:59.999Z",
            "commercial_acct": "false",
            "is_lottery": "false", # FIXME: for enchantment style requests
        },
        headers={"User-Agent": "recwatch/1.0"},
        timeout=15,
    )
    response.raise_for_status()

    availability = response.json()["payload"]["availability"]

    if debug:
        for division_id, division in availability.items():
            print(f"{name} division {division_id}: {division.get('date_availability', {})}")

    divisions = watch.get("divisions") or list(availability)
    for division_id in divisions:
        entries = availability.get(division_id, {}).get("date_availability", {})
        for stamp, info in entries.items():
            day = date.fromisoformat(stamp.split("T")[0])
            if day not in target_dates:
                continue
            remaining = info.get("remaining")
            if remaining is None:
                raise RuntimeError(f"{name}: missing remaining value for {stamp}")
            if debug:
                print(f"{name} {day}: {remaining} remaining")
            if remaining >= party_size:
                send_discord(
                    webhook,
                    f"🚨 **{name.upper()} PERMIT AVAILABLE** 🚨\n"
                    f"**Date:** {day}\n"
                    f"**Available:** {remaining}\n"
                    f"https://www.recreation.gov/permits/{permit_id}",
                )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if not args.config.exists():
        raise SystemExit(
            f"No config file at {args.config}\n"
            f"Copy config.example.toml to config.toml and edit it."
        )

    with args.config.open("rb") as f:
        config = tomllib.load(f)

    webhook = config["discord_webhook"]
    if "/api/webhooks" not in webhook:
        raise SystemExit(f"discord_webhook in {args.config} is not set to a real webhook URL")

    for watch in config.get("watch", []):
        if watch.get("active", True):
            try:
                check_availability(watch, webhook, args.debug)
            except requests.RequestException as e:
                print(f"{watch['permit_name']}: request failed: {e}")

    if args.debug:
        send_discord(webhook, "✅ recwatch is working.")

if __name__ == "__main__":
    main()