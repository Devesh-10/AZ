"""FastAPI backend for the Flight Agent."""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

# Ensure local imports work
sys.path.insert(0, os.path.dirname(__file__))

from flight_search import find_cheapest_flights, search_flights_amadeus, search_flights_serpapi, INDIA_AIRPORTS, DUBLIN
from disruption_monitor import check_news_disruptions, assess_flight_risk, MIDDLE_EAST_HUB_AIRLINES

app = FastAPI(title="Flight Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Demo data for when API keys are not configured ---

DEMO_FLIGHTS = [
    {
        "origin": "DEL", "destination": "DUB", "price": 342, "currency": "EUR",
        "duration": "PT10H45M", "stops": 1,
        "segments": [
            {"departure": "DEL", "arrival": "LHR", "departure_time": "2026-03-10T22:15:00", "arrival_time": "2026-03-11T03:45:00", "carrier": "AI", "flight_number": "AI111", "duration": "PT9H30M"},
            {"departure": "LHR", "arrival": "DUB", "departure_time": "2026-03-11T07:00:00", "arrival_time": "2026-03-11T08:15:00", "carrier": "EI", "flight_number": "EI153", "duration": "PT1H15M"},
        ],
        "via_middle_east": False, "source": "Demo",
    },
    {
        "origin": "BOM", "destination": "DUB", "price": 298, "currency": "EUR",
        "duration": "PT12H20M", "stops": 1,
        "segments": [
            {"departure": "BOM", "arrival": "DOH", "departure_time": "2026-03-10T19:30:00", "arrival_time": "2026-03-10T21:00:00", "carrier": "QR", "flight_number": "QR557", "duration": "PT3H30M"},
            {"departure": "DOH", "arrival": "DUB", "departure_time": "2026-03-11T01:15:00", "arrival_time": "2026-03-11T05:50:00", "carrier": "QR", "flight_number": "QR017", "duration": "PT7H35M"},
        ],
        "via_middle_east": True, "source": "Demo",
    },
    {
        "origin": "DEL", "destination": "DUB", "price": 275, "currency": "EUR",
        "duration": "PT11H50M", "stops": 1,
        "segments": [
            {"departure": "DEL", "arrival": "DXB", "departure_time": "2026-03-11T04:10:00", "arrival_time": "2026-03-11T06:00:00", "carrier": "EK", "flight_number": "EK513", "duration": "PT3H50M"},
            {"departure": "DXB", "arrival": "DUB", "departure_time": "2026-03-11T08:30:00", "arrival_time": "2026-03-11T12:00:00", "carrier": "EK", "flight_number": "EK161", "duration": "PT8H00M"},
        ],
        "via_middle_east": True, "source": "Demo",
    },
    {
        "origin": "BLR", "destination": "DUB", "price": 389, "currency": "EUR",
        "duration": "PT13H10M", "stops": 1,
        "segments": [
            {"departure": "BLR", "arrival": "FRA", "departure_time": "2026-03-10T23:55:00", "arrival_time": "2026-03-11T05:20:00", "carrier": "LH", "flight_number": "LH755", "duration": "PT10H25M"},
            {"departure": "FRA", "arrival": "DUB", "departure_time": "2026-03-11T08:00:00", "arrival_time": "2026-03-11T09:05:00", "carrier": "LH", "flight_number": "LH980", "duration": "PT2H05M"},
        ],
        "via_middle_east": False, "source": "Demo",
    },
    {
        "origin": "HYD", "destination": "DUB", "price": 315, "currency": "EUR",
        "duration": "PT14H30M", "stops": 1,
        "segments": [
            {"departure": "HYD", "arrival": "AUH", "departure_time": "2026-03-11T02:00:00", "arrival_time": "2026-03-11T04:15:00", "carrier": "EY", "flight_number": "EY277", "duration": "PT4H15M"},
            {"departure": "AUH", "arrival": "DUB", "departure_time": "2026-03-11T08:00:00", "arrival_time": "2026-03-11T12:30:00", "carrier": "EY", "flight_number": "EY041", "duration": "PT8H30M"},
        ],
        "via_middle_east": True, "source": "Demo",
    },
    {
        "origin": "MAA", "destination": "DUB", "price": 410, "currency": "EUR",
        "duration": "PT15H00M", "stops": 1,
        "segments": [
            {"departure": "MAA", "arrival": "CDG", "departure_time": "2026-03-10T22:00:00", "arrival_time": "2026-03-11T04:30:00", "carrier": "AF", "flight_number": "AF395", "duration": "PT11H00M"},
            {"departure": "CDG", "arrival": "DUB", "departure_time": "2026-03-11T09:00:00", "arrival_time": "2026-03-11T10:00:00", "carrier": "AF", "flight_number": "AF694", "duration": "PT1H30M"},
        ],
        "via_middle_east": False, "source": "Demo",
    },
    {
        "origin": "CCU", "destination": "DUB", "price": 465, "currency": "EUR",
        "duration": "PT16H20M", "stops": 2,
        "segments": [
            {"departure": "CCU", "arrival": "DEL", "departure_time": "2026-03-10T18:00:00", "arrival_time": "2026-03-10T20:15:00", "carrier": "AI", "flight_number": "AI020", "duration": "PT2H15M"},
            {"departure": "DEL", "arrival": "AMS", "departure_time": "2026-03-10T23:30:00", "arrival_time": "2026-03-11T05:30:00", "carrier": "KL", "flight_number": "KL872", "duration": "PT9H30M"},
            {"departure": "AMS", "arrival": "DUB", "departure_time": "2026-03-11T08:10:00", "arrival_time": "2026-03-11T08:50:00", "carrier": "KL", "flight_number": "KL935", "duration": "PT1H40M"},
        ],
        "via_middle_east": False, "source": "Demo",
    },
    {
        "origin": "BOM", "destination": "DUB", "price": 255, "currency": "EUR",
        "duration": "PT13H00M", "stops": 1,
        "segments": [
            {"departure": "BOM", "arrival": "DXB", "departure_time": "2026-03-12T01:30:00", "arrival_time": "2026-03-12T03:30:00", "carrier": "EK", "flight_number": "EK501", "duration": "PT3H00M"},
            {"departure": "DXB", "arrival": "DUB", "departure_time": "2026-03-12T08:15:00", "arrival_time": "2026-03-12T12:30:00", "carrier": "EK", "flight_number": "EK161", "duration": "PT8H15M"},
        ],
        "via_middle_east": True, "source": "Demo",
    },
    {
        "origin": "DEL", "destination": "DUB", "price": 378, "currency": "EUR",
        "duration": "PT11H30M", "stops": 1,
        "segments": [
            {"departure": "DEL", "arrival": "AMS", "departure_time": "2026-03-12T01:00:00", "arrival_time": "2026-03-12T06:30:00", "carrier": "KL", "flight_number": "KL872", "duration": "PT9H00M"},
            {"departure": "AMS", "arrival": "DUB", "departure_time": "2026-03-12T08:10:00", "arrival_time": "2026-03-12T08:50:00", "carrier": "KL", "flight_number": "KL935", "duration": "PT1H40M"},
        ],
        "via_middle_east": False, "source": "Demo",
    },
    {
        "origin": "COK", "destination": "DUB", "price": 289, "currency": "EUR",
        "duration": "PT13H45M", "stops": 1,
        "segments": [
            {"departure": "COK", "arrival": "DOH", "departure_time": "2026-03-11T03:00:00", "arrival_time": "2026-03-11T05:30:00", "carrier": "QR", "flight_number": "QR519", "duration": "PT4H30M"},
            {"departure": "DOH", "arrival": "DUB", "departure_time": "2026-03-11T09:00:00", "arrival_time": "2026-03-11T13:45:00", "carrier": "QR", "flight_number": "QR017", "duration": "PT7H45M"},
        ],
        "via_middle_east": True, "source": "Demo",
    },
    {
        "origin": "BLR", "destination": "DUB", "price": 268, "currency": "EUR",
        "duration": "PT12H10M", "stops": 1,
        "segments": [
            {"departure": "BLR", "arrival": "DOH", "departure_time": "2026-03-13T02:30:00", "arrival_time": "2026-03-13T05:15:00", "carrier": "QR", "flight_number": "QR575", "duration": "PT4H45M"},
            {"departure": "DOH", "arrival": "DUB", "departure_time": "2026-03-13T09:00:00", "arrival_time": "2026-03-13T13:40:00", "carrier": "QR", "flight_number": "QR017", "duration": "PT7H40M"},
        ],
        "via_middle_east": True, "source": "Demo",
    },
    {
        "origin": "AMD", "destination": "DUB", "price": 335, "currency": "EUR",
        "duration": "PT14H00M", "stops": 1,
        "segments": [
            {"departure": "AMD", "arrival": "DXB", "departure_time": "2026-03-11T05:00:00", "arrival_time": "2026-03-11T06:30:00", "carrier": "FZ", "flight_number": "FZ442", "duration": "PT2H30M"},
            {"departure": "DXB", "arrival": "DUB", "departure_time": "2026-03-11T10:00:00", "arrival_time": "2026-03-11T14:00:00", "carrier": "EK", "flight_number": "EK161", "duration": "PT8H00M"},
        ],
        "via_middle_east": True, "source": "Demo",
    },
]


def _is_api_configured() -> bool:
    return bool(os.getenv("AMADEUS_CLIENT_ID") and os.getenv("AMADEUS_CLIENT_SECRET"))


@app.get("/")
def health():
    return {"status": "ok", "service": "Flight Agent API", "api_configured": _is_api_configured()}


@app.get("/api/airports")
def get_airports():
    return [{"code": code, "city": city} for code, city in INDIA_AIRPORTS]


@app.get("/api/flights")
def get_flights(
    date: Optional[str] = Query(None, description="YYYY-MM-DD"),
    origin: Optional[str] = Query(None, description="Airport code e.g. DEL"),
    days: int = Query(3, ge=1, le=30),
    adults: int = Query(1, ge=1, le=9),
):
    if not _is_api_configured():
        flights = sorted(DEMO_FLIGHTS, key=lambda f: f["price"])
        if origin:
            flights = [f for f in flights if f["origin"] == origin.upper()]
        # Add risk assessment
        for f in flights:
            f["risk"] = assess_flight_risk(f)
        return {"flights": flights, "demo": True, "total": len(flights)}

    flights = find_cheapest_flights(
        departure_date=date,
        date_range_days=days,
        adults=adults,
    )
    if origin:
        flights = [f for f in flights if f["origin"] == origin.upper()]
    for f in flights:
        f["risk"] = assess_flight_risk(f)
    return {"flights": flights, "demo": False, "total": len(flights)}


@app.get("/api/disruptions")
def get_disruptions():
    alerts = check_news_disruptions()
    return {"alerts": alerts, "total": len(alerts)}


@app.get("/api/risk")
def get_risk_info():
    return {
        "middle_east_airlines": MIDDLE_EAST_HUB_AIRLINES,
        "middle_east_airports": ["DOH", "DXB", "AUH", "BAH", "KWI", "MCT", "RUH", "JED"],
    }
