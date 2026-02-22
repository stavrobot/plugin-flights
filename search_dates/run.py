#!/usr/bin/env -S uv run
# /// script
# dependencies = ["flights"]
# ///

import json
import sys
from typing import Any

from fli.models import (
    Airport,
    DateSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    TripType,
)
from fli.search import SearchDates

SEAT_TYPE_MAP: dict[str, SeatType] = {
    "ECONOMY": SeatType.ECONOMY,
    "PREMIUM_ECONOMY": SeatType.PREMIUM_ECONOMY,
    "BUSINESS": SeatType.BUSINESS,
    "FIRST": SeatType.FIRST,
}

MAX_STOPS_MAP: dict[str, MaxStops] = {
    "ANY": MaxStops.ANY,
    "NON_STOP": MaxStops.NON_STOP,
    "ONE_STOP_OR_FEWER": MaxStops.ONE_STOP_OR_FEWER,
    "TWO_OR_FEWER_STOPS": MaxStops.TWO_OR_FEWER_STOPS,
}


def parse_airports(value: str) -> list[list]:
    """Parse a comma-separated list of IATA codes into [Airport, 0] pairs.

    The fli library accepts multiple airports per segment endpoint, allowing
    the caller to search across several airports in one request (e.g. all
    London airports: 'LHR,LGW,STN,LTN,LCY').
    """
    codes = [code.strip().upper() for code in value.split(",")]
    return [[Airport[code], 0] for code in codes]


def format_date_result(result: Any) -> dict:
    """Serialize a date search result into a plain dict for JSON output.

    result.date is a tuple containing a single datetime, e.g. (datetime(2026, 3, 1),).
    We extract the datetime and format it as a plain date string.
    """
    return {
        "date": result.date[0].strftime("%Y-%m-%d"),
        "price": result.price,
    }


def main() -> None:
    params = json.load(sys.stdin)

    origin_airports = parse_airports(params["origin"])
    destination_airports = parse_airports(params["destination"])

    seat_type = SEAT_TYPE_MAP.get(params.get("cabin_class", "ECONOMY"), SeatType.ECONOMY)
    max_stops = MAX_STOPS_MAP.get(params.get("max_stops", "ANY"), MaxStops.ANY)
    passengers = int(params.get("passengers", 1))
    is_round_trip = bool(params.get("is_round_trip", False))
    duration = params.get("duration")

    trip_type = TripType.ROUND_TRIP if is_round_trip else TripType.ONE_WAY

    # DateSearchFilters requires a placeholder travel_date on each FlightSegment.
    # The actual dates searched are controlled by from_date/to_date on the filter.
    # For round trips, the second segment's travel_date is offset by duration days,
    # as required by the model validator.
    from_date = params["from_date"]

    segments: list[FlightSegment] = [
        FlightSegment(
            departure_airport=origin_airports,
            arrival_airport=destination_airports,
            travel_date=from_date,
        )
    ]
    if is_round_trip:
        from datetime import datetime, timedelta
        return_date = (
            datetime.strptime(from_date, "%Y-%m-%d") + timedelta(days=int(duration))
        ).strftime("%Y-%m-%d")
        segments.append(
            FlightSegment(
                departure_airport=destination_airports,
                arrival_airport=origin_airports,
                travel_date=return_date,
            )
        )

    filters = DateSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(adults=passengers),
        flight_segments=segments,
        seat_type=seat_type,
        stops=max_stops,
        from_date=from_date,
        to_date=params["to_date"],
        duration=int(duration) if duration is not None else None,
    )

    search = SearchDates()
    results = search.search(filters)

    dates = [format_date_result(r) for r in results] if results else []
    json.dump({"dates": dates, "count": len(dates)}, sys.stdout)


main()
