#!/usr/bin/env -S uv run
# /// script
# dependencies = ["flights"]
# ///

import json
import sys
from typing import Any

from fli.models import (
    Airport,
    FlightSearchFilters,
    FlightSegment,
    MaxStops,
    PassengerInfo,
    SeatType,
    SortBy,
    TripType,
)
from fli.search import SearchFlights

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

SORT_BY_MAP: dict[str, SortBy] = {
    "CHEAPEST": SortBy.CHEAPEST,
    "DURATION": SortBy.DURATION,
    "DEPARTURE_TIME": SortBy.DEPARTURE_TIME,
    "ARRIVAL_TIME": SortBy.ARRIVAL_TIME,
}


def parse_airports(value: str) -> list[list]:
    """Parse a comma-separated list of IATA codes into [Airport, 0] pairs.

    The fli library accepts multiple airports per segment endpoint, allowing
    the caller to search across several airports in one request (e.g. all
    London airports: 'LHR,LGW,STN,LTN,LCY').
    """
    codes = [code.strip().upper() for code in value.split(",")]
    return [[Airport[code], 0] for code in codes]


def format_flight(flight: Any) -> dict:
    """Serialize a FlightResult into a plain dict for JSON output."""
    legs = []
    for leg in flight.legs:
        legs.append({
            "airline": leg.airline.value,
            "flight_number": leg.flight_number,
            "departure_airport": leg.departure_airport.value,
            "arrival_airport": leg.arrival_airport.value,
            "departure_time": str(leg.departure_datetime),
            "arrival_time": str(leg.arrival_datetime),
            "duration_minutes": leg.duration,
        })
    return {
        "price": flight.price,
        "duration_minutes": flight.duration,
        "stops": flight.stops,
        "legs": legs,
    }


def main() -> None:
    params = json.load(sys.stdin)

    origin_airports = parse_airports(params["origin"])
    destination_airports = parse_airports(params["destination"])

    seat_type = SEAT_TYPE_MAP.get(params.get("cabin_class", "ECONOMY"), SeatType.ECONOMY)
    max_stops = MAX_STOPS_MAP.get(params.get("max_stops", "ANY"), MaxStops.ANY)
    sort_by = SORT_BY_MAP.get(params.get("sort_by", "CHEAPEST"), SortBy.CHEAPEST)
    passengers = int(params.get("passengers", 1))
    departure_date = params["departure_date"]
    return_date = params.get("return_date")

    trip_type = TripType.ROUND_TRIP if return_date else TripType.ONE_WAY

    segments = [
        FlightSegment(
            departure_airport=origin_airports,
            arrival_airport=destination_airports,
            travel_date=departure_date,
        )
    ]
    if return_date:
        segments.append(
            FlightSegment(
                departure_airport=destination_airports,
                arrival_airport=origin_airports,
                travel_date=return_date,
            )
        )

    filters = FlightSearchFilters(
        trip_type=trip_type,
        passenger_info=PassengerInfo(adults=passengers),
        flight_segments=segments,
        seat_type=seat_type,
        stops=max_stops,
        sort_by=sort_by,
    )

    search = SearchFlights()
    results = search.search(filters)

    # One-way searches return a flat list of FlightResult. Round-trip searches
    # return a list of (outbound_FlightResult, return_FlightResult) tuples.
    if return_date:
        flights = [
            {"outbound": format_flight(out), "return": format_flight(ret)}
            for out, ret in results
        ] if results else []
    else:
        flights = [format_flight(f) for f in results] if results else []
    json.dump({"flights": flights, "count": len(flights)}, sys.stdout)


main()
