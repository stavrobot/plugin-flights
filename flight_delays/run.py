#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys

import requests


def format_delay_entry(entry: dict) -> dict:
    return {
        "airport": entry["airportIcao"],
        "scheduled_hour_utc": entry.get("scheduledHourUtc"),
        "median_delay": entry["medianDelay"],
        "flights_considered": entry["numConsideredFlights"],
        "from_date": entry["fromUtc"],
        "to_date": entry["toUtc"],
    }


def main() -> None:
    params = json.load(sys.stdin)

    try:
        with open("../config.json") as config_file:
            config = json.load(config_file)
        rapidapi_key = config["rapidapi_key"]
    except (FileNotFoundError, KeyError):
        print(
            "rapidapi_key not configured. Set it via configure_plugin."
            " Sign up at https://rapidapi.com/aedbx-aedbx/api/aerodatabox",
            file=sys.stderr,
        )
        sys.exit(1)

    flight_number = params["flight_number"]

    response = requests.get(
        f"https://aerodatabox.p.rapidapi.com/flights/{flight_number}/delays",
        headers={"X-RapidAPI-Key": rapidapi_key},
    )

    if response.status_code != 200:
        print(
            f"AeroDataBox API error {response.status_code}: {response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    data = response.json()
    result = {
        "flight_number": data["number"],
        "origins": [format_delay_entry(e) for e in (data.get("origins") or [])],
        "destinations": [format_delay_entry(e) for e in (data.get("destinations") or [])],
    }
    json.dump(result, sys.stdout)


main()
