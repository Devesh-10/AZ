"""
Flight Disruption Monitor — checks for cancellations due to Middle East tensions.
Uses NewsAPI for real-time news and flags affected routes/airlines.
"""

import os
from datetime import datetime, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

# Airlines that route heavily through Middle East hubs
MIDDLE_EAST_HUB_AIRLINES = {
    "EK": "Emirates (Dubai DXB)",
    "QR": "Qatar Airways (Doha DOH)",
    "EY": "Etihad (Abu Dhabi AUH)",
    "WY": "Oman Air (Muscat MCT)",
    "GF": "Gulf Air (Bahrain BAH)",
    "KU": "Kuwait Airways (Kuwait KWI)",
    "SV": "Saudia (Riyadh/Jeddah)",
    "FZ": "flydubai (Dubai DXB)",
    "G9": "Air Arabia (Sharjah SHJ)",
    "AI": "Air India (some ME routes)",
}

RISK_KEYWORDS = [
    "flight cancelled middle east",
    "airspace closed middle east",
    "flights suspended iran",
    "flights cancelled israel",
    "airspace closure gulf",
    "NOTAM middle east",
    "flight disruption middle east",
    "airline cancellation war",
    "flights rerouted middle east",
    "aviation disruption tensions",
]


def check_news_disruptions() -> list[dict]:
    """Check recent news for flight disruption reports related to Middle East tensions."""
    api_key = os.getenv("NEWS_API_KEY")
    if not api_key:
        print("  ⚠ NEWS_API_KEY not set — using keyword-based risk assessment only.")
        return _static_risk_assessment()

    alerts = []
    query = (
        "(flight OR airline OR airspace) AND "
        "(cancelled OR suspended OR closed OR disruption) AND "
        "(middle east OR iran OR israel OR gulf OR yemen OR red sea)"
    )

    try:
        resp = requests.get(
            "https://newsapi.org/v2/everything",
            params={
                "q": query,
                "language": "en",
                "sortBy": "publishedAt",
                "from": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
                "pageSize": 20,
                "apiKey": api_key,
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  ⚠ NewsAPI error: {e}")
        return _static_risk_assessment()

    for article in data.get("articles", []):
        title = article.get("title", "")
        description = article.get("description", "") or ""
        url = article.get("url", "")
        published = article.get("publishedAt", "")

        # Check relevance
        text = f"{title} {description}".lower()
        matched_keywords = [kw for kw in RISK_KEYWORDS if kw.lower() in text]
        if matched_keywords:
            alerts.append({
                "title": title,
                "description": description[:300],
                "url": url,
                "published": published,
                "matched_keywords": matched_keywords,
                "severity": "HIGH" if len(matched_keywords) >= 2 else "MEDIUM",
            })

    return alerts


def _static_risk_assessment() -> list[dict]:
    """Provide general risk assessment when no API key is available."""
    return [{
        "title": "General Middle East Routing Risk Advisory",
        "description": (
            "Flights routing through Middle Eastern airspace (Iran, Iraq, Yemen, "
            "Red Sea region) may face disruptions due to ongoing geopolitical tensions. "
            "Airlines like Emirates, Qatar Airways, and Etihad that hub through the Gulf "
            "could be affected. Direct European routing (via airlines like Lufthansa, "
            "British Airways, Air France) is generally safer from these disruptions."
        ),
        "url": "",
        "published": datetime.now().isoformat(),
        "matched_keywords": [],
        "severity": "ADVISORY",
    }]


def assess_flight_risk(flight: dict) -> dict:
    """Assess cancellation risk for a specific flight based on its routing."""
    risk_level = "LOW"
    risk_reasons = []

    if flight.get("via_middle_east"):
        risk_level = "HIGH"
        risk_reasons.append("Route transits through Middle Eastern airspace")

    carrier_codes = {seg.get("carrier", "") for seg in flight.get("segments", [])}
    me_carriers = carrier_codes & set(MIDDLE_EAST_HUB_AIRLINES.keys())
    if me_carriers:
        risk_level = "HIGH" if risk_level == "HIGH" else "MEDIUM"
        airlines = [MIDDLE_EAST_HUB_AIRLINES[c] for c in me_carriers]
        risk_reasons.append(f"Operated by Middle East hub airline(s): {', '.join(airlines)}")

    if not risk_reasons:
        risk_reasons.append("Route avoids Middle Eastern hubs — lower disruption risk")

    return {
        "risk_level": risk_level,
        "reasons": risk_reasons,
        "recommendation": (
            "⚠ Consider booking a European-routed alternative to avoid potential cancellations"
            if risk_level in ("HIGH", "MEDIUM")
            else "✅ This route has lower disruption risk from Middle East tensions"
        ),
    }
