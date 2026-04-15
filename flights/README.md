# ✈ Flight Agent — Cheapest India → Dublin with Disruption Monitoring

Finds the cheapest flights from all major Indian airports to Dublin, with real-time disruption monitoring for Middle East tensions that could cause cancellations.

## Features

- **Multi-airport search**: Searches DEL, BOM, BLR, MAA, HYD, CCU, COK, AMD
- **Multi-day search**: Scans next 7 days (configurable) for cheapest options
- **Disruption alerts**: Monitors news for Middle East flight cancellations/airspace closures
- **Risk assessment**: Flags flights routing through Middle East hubs (Emirates, Qatar, Etihad etc.)
- **Smart recommendations**: Suggests safest + cheapest routes separately

## Setup

1. **Get API keys** (free tiers available):
   - [Amadeus for Developers](https://developers.amadeus.com) — sign up, create app, get client ID/secret
   - [NewsAPI](https://newsapi.org) (optional) — for disruption news monitoring
   - [SerpApi](https://serpapi.com) (optional) — Google Flights fallback

2. **Install & configure**:
   ```bash
   cd flights
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Run**:
   ```bash
   python agent.py                    # Search next 7 days, all airports
   python agent.py --date 2026-03-15  # Specific date
   python agent.py --from DEL         # From Delhi only
   python agent.py --days 14          # Search 14 days ahead
   python agent.py --adults 2         # 2 passengers
   python agent.py --skip-news        # Skip disruption check
   ```

## Architecture

```
flights/
├── agent.py               # CLI entry point with rich output
├── flight_search.py       # Amadeus + SerpApi flight search
├── disruption_monitor.py  # News-based disruption alerts + risk assessment
├── requirements.txt
├── .env.example
└── README.md
```

## Middle East Risk Assessment

The agent flags flights as HIGH/MEDIUM/LOW risk based on:
- **HIGH**: Routes through ME airspace + operated by ME hub airline
- **MEDIUM**: Operated by ME hub airline but alternative routing possible
- **LOW**: European/direct routing, avoids ME hubs
