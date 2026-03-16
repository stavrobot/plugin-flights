#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import json
import sys

import requests


def format_airport(airport: dict | None) -> dict | None:
    if airport is None:
        return None
    return {
        "iata": airport.get("iata"),
        "name": airport.get("name"),
    }


def format_flight(flight: dict) -> dict:
    """Extract the useful fields from a FlightContract object."""
    departure = flight.get("departure") or {}
    arrival = flight.get("arrival") or {}
    aircraft = flight.get("aircraft")

    result: dict = {
        "status": flight.get("status"),
        "number": flight.get("number"),
        "airline": (flight.get("airline") or {}).get("name"),
        "departure": {
            "airport": format_airport(departure.get("airport")),
            "scheduledTime": (departure.get("scheduledTime") or {}).get("local"),
            "revisedTime": (departure.get("revisedTime") or {}).get("local"),
            "terminal": departure.get("terminal"),
            "gate": departure.get("gate"),
        },
        "arrival": {
            "airport": format_airport(arrival.get("airport")),
            "scheduledTime": (arrival.get("scheduledTime") or {}).get("local"),
            "revisedTime": (arrival.get("revisedTime") or {}).get("local"),
            "terminal": arrival.get("terminal"),
            "gate": arrival.get("gate"),
            "baggageBelt": arrival.get("baggageBelt"),
        },
    }

    if aircraft is not None:
        result["aircraft"] = {
            "model": aircraft.get("model"),
            "registration": aircraft.get("reg"),
        }
    else:
        result["aircraft"] = None

    return result


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
    date = params.get("date")

    if date:
        url = f"https://aerodatabox.p.rapidapi.com/flights/Number/{flight_number}/{date}"
    else:
        url = f"https://aerodatabox.p.rapidapi.com/flights/Number/{flight_number}"

    response = requests.get(
        url,
        headers={"X-RapidAPI-Key": rapidapi_key},
    )

    if response.status_code != 200:
        print(
            f"AeroDataBox API error {response.status_code}: {response.text}",
            file=sys.stderr,
        )
        sys.exit(1)

    flights = [format_flight(f) for f in response.json()]
    json.dump({"flights": flights, "count": len(flights)}, sys.stdout)


main()
