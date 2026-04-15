#!/usr/bin/env python3
"""
✈ Flight Agent — Cheapest India → Dublin flights with disruption monitoring.

Usage:
    python agent.py                  # Search next 7 days, all Indian airports
    python agent.py --date 2026-03-15  # Search specific date
    python agent.py --from DEL       # Search from Delhi only
    python agent.py --days 14        # Search next 14 days
"""

import argparse
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

from flight_search import find_cheapest_flights, INDIA_AIRPORTS
from disruption_monitor import check_news_disruptions, assess_flight_risk

console = Console()


def format_duration(iso_dur: str) -> str:
    """Convert ISO duration like PT12H30M to readable format."""
    d = iso_dur.replace("PT", "").replace("P", "")
    hours = minutes = 0
    if "H" in d:
        parts = d.split("H")
        hours = int(parts[0])
        d = parts[1]
    if "M" in d:
        minutes = int(d.replace("M", "").strip() or 0)
    if "min" in iso_dur:
        return iso_dur
    return f"{hours}h {minutes}m"


def display_disruption_alerts(alerts: list[dict]) -> None:
    console.print()
    console.rule("[bold red]⚠ DISRUPTION ALERTS — Middle East Tensions[/]")
    console.print()

    if not alerts:
        console.print("[green]No active flight disruption alerts found.[/]")
        return

    for alert in alerts[:10]:
        severity = alert["severity"]
        color = {"HIGH": "red", "MEDIUM": "yellow", "ADVISORY": "cyan"}.get(severity, "white")

        console.print(Panel(
            f"[bold]{alert['title']}[/]\n\n"
            f"{alert['description']}\n\n"
            f"[dim]{alert.get('url', '')}[/]\n"
            f"[dim]Published: {alert.get('published', 'N/A')}[/]",
            title=f"[{color}]{severity}[/]",
            border_style=color,
        ))


def display_flights(flights: list[dict], top_n: int = 20) -> None:
    console.print()
    console.rule("[bold green]✈ Cheapest Flights: India → Dublin[/]")
    console.print()

    if not flights:
        console.print("[yellow]No flights found. Check your API keys in .env[/]")
        return

    table = Table(
        title=f"Top {min(top_n, len(flights))} Cheapest Flights",
        box=box.ROUNDED,
        show_lines=True,
    )
    table.add_column("Rank", style="bold", width=5)
    table.add_column("From", style="cyan", width=12)
    table.add_column("Price", style="green bold", width=10)
    table.add_column("Date", width=12)
    table.add_column("Duration", width=10)
    table.add_column("Stops", width=6)
    table.add_column("Route", width=30)
    table.add_column("Risk", width=8)
    table.add_column("Source", style="dim", width=10)

    for i, flight in enumerate(flights[:top_n], 1):
        # Build route string
        route_parts = []
        for seg in flight.get("segments", []):
            route_parts.append(f"{seg['departure']}→{seg['arrival']} ({seg.get('carrier', '')})")
        route = " | ".join(route_parts) or "N/A"

        # Risk assessment
        risk = assess_flight_risk(flight)
        risk_color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(risk["risk_level"], "white")

        # Date from first segment
        dep_date = ""
        if flight.get("segments"):
            dep_time = flight["segments"][0].get("departure_time", "")
            if "T" in dep_time:
                dep_date = dep_time.split("T")[0]
            else:
                dep_date = dep_time

        table.add_row(
            str(i),
            flight["origin"],
            f"€{flight['price']:.0f}",
            dep_date,
            format_duration(flight.get("duration", "")),
            str(flight["stops"]),
            route,
            f"[{risk_color}]{risk['risk_level']}[/{risk_color}]",
            flight.get("source", ""),
        )

    console.print(table)

    # Show risk details for top 5
    console.print()
    console.rule("[bold]Risk Assessment — Top 5 Flights[/]")
    for i, flight in enumerate(flights[:5], 1):
        risk = assess_flight_risk(flight)
        color = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "green"}.get(risk["risk_level"], "white")
        console.print(f"\n  [{color}]#{i} — {flight['origin']}→DUB (€{flight['price']:.0f})[/{color}]")
        for reason in risk["reasons"]:
            console.print(f"    • {reason}")
        console.print(f"    {risk['recommendation']}")


def main():
    parser = argparse.ArgumentParser(description="Flight Agent: India → Dublin")
    parser.add_argument("--date", help="Specific departure date (YYYY-MM-DD)")
    parser.add_argument("--from", dest="origin", help="Airport code (e.g. DEL, BOM)")
    parser.add_argument("--days", type=int, default=7, help="Number of days to search (default: 7)")
    parser.add_argument("--adults", type=int, default=1, help="Number of adult passengers")
    parser.add_argument("--top", type=int, default=20, help="Show top N results")
    parser.add_argument("--skip-news", action="store_true", help="Skip disruption news check")
    args = parser.parse_args()

    console.print(Panel.fit(
        "[bold]✈ Flight Agent — India → Dublin[/]\n"
        f"[dim]Searching cheapest flights with disruption monitoring[/]\n"
        f"[dim]{datetime.now().strftime('%Y-%m-%d %H:%M')}[/]",
        border_style="blue",
    ))

    # Step 1: Check disruptions
    if not args.skip_news:
        console.print("\n[bold]Step 1:[/] Checking flight disruption alerts...")
        alerts = check_news_disruptions()
        display_disruption_alerts(alerts)

    # Step 2: Search flights
    console.print(f"\n[bold]Step 2:[/] Searching flights across Indian airports...")
    flights = find_cheapest_flights(
        departure_date=args.date,
        date_range_days=args.days,
        adults=args.adults,
    )

    # Filter by origin if specified
    if args.origin:
        flights = [f for f in flights if f["origin"] == args.origin.upper()]

    display_flights(flights, top_n=args.top)

    # Step 3: Recommendation
    console.print()
    console.rule("[bold blue]📋 Recommendation[/]")

    safe_flights = [f for f in flights if not f.get("via_middle_east")]
    me_flights = [f for f in flights if f.get("via_middle_east")]

    if safe_flights:
        best_safe = safe_flights[0]
        console.print(
            f"\n  [green bold]Best safe route (avoids Middle East):[/]\n"
            f"  {best_safe['origin']} → DUB | €{best_safe['price']:.0f} | "
            f"{format_duration(best_safe.get('duration', ''))} | {best_safe['stops']} stop(s)\n"
        )

    if me_flights:
        best_me = me_flights[0]
        console.print(
            f"  [yellow bold]Cheapest via Middle East (higher cancellation risk):[/]\n"
            f"  {best_me['origin']} → DUB | €{best_me['price']:.0f} | "
            f"{format_duration(best_me.get('duration', ''))} | {best_me['stops']} stop(s)\n"
        )

    if flights:
        cheapest = flights[0]
        console.print(
            f"  [bold]Overall cheapest:[/] {cheapest['origin']} → DUB | "
            f"€{cheapest['price']:.0f} | {cheapest.get('source', '')}\n"
        )

    console.print("[dim]Tip: Book directly on the airline website for best prices.[/]\n")


if __name__ == "__main__":
    main()
