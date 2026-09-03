# This file contains the logic for logging permit availability over time

import json
import datetime
from pathlib import Path

LOG_FILE = Path("availability_log.json")

def load_log():
    if not LOG_FILE.exists():
        return {
            "version": 1,
            "last_checked": None,
            "events": [],
            "gaps": [],
        }

    with LOG_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_log(log):
    temp_file = LOG_FILE.with_suffix(".tmp")

    with temp_file.open("w", encoding="utf-8") as file:
        json.dump(log, file, indent=2)

    temp_file.replace(LOG_FILE)


# Idea, we should format it for running logging format (but keep track of number of polls and start and end time for given event states)
# We need to track dates and locations when events come back positive.
# Its worth considering whether we want to allow the user to modify the config file in between and have it adapt, if so we should also log when theres a change to what events we are polling for.

# I think it makes sense to group by location then dates of interest, but the other way around could also be valid