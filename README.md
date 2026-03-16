# plugin-flights

A [Stavrobot](https://github.com/stavrobot) plugin for searching Google Flights and checking flight status via AeroDataBox. Provides four tools:

- **search_flights** — search for flights on a specific date, with filters for cabin class, stops, airlines, and sorting
- **search_dates** — find the cheapest travel dates across a date range
- **flight_status** — get the current status of a flight by flight number, including schedule, gate, terminal, and aircraft information
- **flight_delays** — get average delay statistics for a flight based on the last 90 days of tracked data, useful for knowing if a flight is chronically late before booking

Both search tools accept one or more comma-separated IATA airport codes for origin and destination (e.g. `LHR,LGW,STN,LTN,LCY` to search all London airports at once).

## Installation

Ask Stavrobot to install `https://github.com/stavrobot/plugin-flights.git`.

## Configuration

`flight_status` and `flight_delays` require a RapidAPI key for [AeroDataBox](https://rapidapi.com/aedbx-aedbx/api/aerodatabox). After installation, set the key via `configure_plugin`. The search tools (`search_flights`, `search_dates`) work without it.
