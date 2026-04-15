"""
Flight Search Agent — finds cheapest flights from India to Dublin
Uses Amadeus API (primary) and SerpApi Google Flights (fallback).
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from amadeus import Client, ResponseError
from dotenv import load_dotenv

load_dotenv()

# Major Indian airports to search from
INDIA_AIRPORTS = [
    ("DEL", "Delhi"),
    ("BOM", "Mumbai"),
    ("BLR", "Bangalore"),
    ("MAA", "Chennai"),
    ("HYD", "Hyderabad"),
    ("CCU", "Kolkata"),
    ("COK", "Kochi"),
    ("AMD", "Ahmedabad"),
]

DUBLIN = "DUB"


def get_amadeus_client() -> Client:
    return Client(
        client_id=os.getenv("AMADEUS_CLIENT_ID"),
        client_secret=os.getenv("AMADEUS_CLIENT_SECRET"),
    )


def search_flights_amadeus(
    origin: str,
    destination: str,
    departure_date: str,
    max_results: int = 5,
    adults: int = 1,
) -> list[dict]:
    """Search flights using the Amadeus Flight Offers API."""
    client = get_amadeus_client()
    try:
        response = client.shopping.flight_offers_search.get(
            originLocationCode=origin,
            destinationLocationCode=destination,
            departureDate=departure_date,
            adults=adults,
            currencyCode="EUR",
            max=max_results,
            nonStop=False,
        )
        return _parse_amadeus_results(response.data, origin)
    except ResponseError as e:
        print(f"  [Amadeus error for {origin}]: {e}")
        return []


def _parse_amadeus_results(data: list, origin: str) -> list[dict]:
    results = []
    for offer in data:
        price = float(offer["price"]["grandTotal"])
        currency = offer["price"]["currency"]
        itineraries = offer.get("itineraries", [])

        segments_info = []
        total_duration = ""
        stops = 0

        if itineraries:
            itin = itineraries[0]
            total_duration = itin.get("duration", "")
            segments = itin.get("segments", [])
            stops = len(segments) - 1

            for seg in segments:
                segments_info.append({
                    "departure": seg["departure"]["iataCode"],
                    "arrival": seg["arrival"]["iataCode"],
                    "departure_time": seg["departure"]["at"],
                    "arrival_time": seg["arrival"]["at"],
                    "carrier": seg["carrierCode"],
                    "flight_number": f"{seg['carrierCode']}{seg['number']}",
                    "duration": seg.get("duration", ""),
                })

        # Flag if route goes through Middle East
        middle_east_codes = {
            "DOH", "DXB", "AUH", "BAH", "KWI", "MCT", "RUH", "JED",
            "AMM", "BEY", "TLV", "BGW", "THR", "IST", "SAW",
        }
        via_middle_east = any(
            seg["arrival"] in middle_east_codes or seg["departure"] in middle_east_codes
            for seg in segments_info
        )

        results.append({
            "origin": origin,
            "destination": DUBLIN,
            "price": price,
            "currency": currency,
            "duration": total_duration,
            "stops": stops,
            "segments": segments_info,
            "via_middle_east": via_middle_east,
            "source": "Amadeus",
        })
    return results


def search_flights_serpapi(
    origin: str,
    departure_date: str,
) -> list[dict]:
    """Fallback: search using SerpApi Google Flights."""
    api_key = os.getenv("SERPAPI_KEY")
    if not api_key:
        return []

    import requests

    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": DUBLIN,
        "outbound_date": departure_date,
        "currency": "EUR",
        "hl": "en",
        "api_key": api_key,
        "type": "2",  # one-way
    }

    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  [SerpApi error for {origin}]: {e}")
        return []

    results = []
    for flight in data.get("best_flights", []) + data.get("other_flights", []):
        legs = flight.get("flights", [])
        price = flight.get("price", 0)

        middle_east_codes = {
            "DOH", "DXB", "AUH", "BAH", "KWI", "MCT", "RUH", "JED",
            "AMM", "BEY", "TLV", "BGW", "THR", "IST", "SAW",
        }

        segments_info = []
        via_middle_east = False
        for leg in legs:
            dep_airport = leg.get("departure_airport", {}).get("id", "")
            arr_airport = leg.get("arrival_airport", {}).get("id", "")
            if dep_airport in middle_east_codes or arr_airport in middle_east_codes:
                via_middle_east = True
            segments_info.append({
                "departure": dep_airport,
                "arrival": arr_airport,
                "departure_time": leg.get("departure_airport", {}).get("time", ""),
                "arrival_time": leg.get("arrival_airport", {}).get("time", ""),
                "carrier": leg.get("airline", ""),
                "flight_number": leg.get("flight_number", ""),
                "duration": f"{leg.get('duration', 0)} min",
            })

        results.append({
            "origin": origin,
            "destination": DUBLIN,
            "price": price,
            "currency": "EUR",
            "duration": f"{flight.get('total_duration', 0)} min",
            "stops": len(legs) - 1,
            "segments": segments_info,
            "via_middle_east": via_middle_east,
            "source": "Google Flights",
        })
    return results


def find_cheapest_flights(
    departure_date: Optional[str] = None,
    date_range_days: int = 7,
    adults: int = 1,
) -> list[dict]:
    """
    Search across all major Indian airports for the cheapest flights to Dublin.
    Searches from tomorrow through date_range_days.
    """
    if departure_date:
        dates = [departure_date]
    else:
        tomorrow = datetime.now() + timedelta(days=1)
        dates = [
            (tomorrow + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(date_range_days)
        ]

    all_flights = []

    for date in dates:
        print(f"\n🔍 Searching flights for {date}...")
        for code, city in INDIA_AIRPORTS:
            print(f"  Checking {city} ({code}) → Dublin...")
            flights = search_flights_amadeus(code, DUBLIN, date, max_results=3, adults=adults)
            if not flights:
                flights = search_flights_serpapi(code, date)
            all_flights.extend(flights)

    # Sort by price
    all_flights.sort(key=lambda f: f["price"])
    return all_flights
