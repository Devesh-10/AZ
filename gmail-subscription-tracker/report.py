"""
Subscription cost report generator.
Aggregates and displays subscription costs by service and account.
"""

import csv
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from tabulate import tabulate


def generate_report(subscriptions: list[dict]) -> str:
    """Generate a formatted subscription cost report."""
    if not subscriptions:
        return "No subscription charges found across any account."

    lines = []
    lines.append("=" * 70)
    lines.append("       GMAIL SUBSCRIPTION COST REPORT")
    lines.append(f"       Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 70)

    # --- Summary by service (across all accounts) ---
    service_totals = defaultdict(lambda: {"total": 0.0, "count": 0, "accounts": set()})
    for sub in subscriptions:
        svc = sub["service"]
        val = sub.get("price_value", 0) or 0
        service_totals[svc]["total"] += val
        service_totals[svc]["count"] += 1
        service_totals[svc]["accounts"].add(sub["account"])

    sorted_services = sorted(service_totals.items(), key=lambda x: x[1]["total"], reverse=True)

    lines.append("\n\n--- COST BY SERVICE (All Accounts) ---\n")
    table_data = []
    grand_total = 0
    for svc, data in sorted_services:
        accts = ", ".join(sorted(data["accounts"]))
        table_data.append([
            svc,
            f"${data['total']:.2f}",
            data["count"],
            accts,
        ])
        grand_total += data["total"]

    lines.append(tabulate(
        table_data,
        headers=["Service", "Total Spent", "# Charges", "Account(s)"],
        tablefmt="rounded_grid",
    ))
    lines.append(f"\n  GRAND TOTAL: ${grand_total:.2f}")

    # --- Breakdown per account ---
    account_subs = defaultdict(list)
    for sub in subscriptions:
        account_subs[sub["account"]].append(sub)

    for account, subs in sorted(account_subs.items()):
        lines.append(f"\n\n--- {account} ---\n")
        acct_total = 0
        acct_table = []
        for sub in sorted(subs, key=lambda x: x.get("price_value", 0) or 0, reverse=True):
            val = sub.get("price_value", 0) or 0
            acct_table.append([
                sub["service"],
                sub["price"],
                sub["subject"][:50],
                sub["date"][:16] if sub["date"] else "N/A",
            ])
            acct_total += val

        lines.append(tabulate(
            acct_table,
            headers=["Service", "Amount", "Subject", "Date"],
            tablefmt="rounded_grid",
        ))
        lines.append(f"  Account Total: ${acct_total:.2f}")

    # --- Monthly estimate ---
    lines.append("\n\n--- ESTIMATED MONTHLY COST ---\n")
    monthly = defaultdict(float)
    for sub in subscriptions:
        svc = sub["service"]
        val = sub.get("price_value", 0) or 0
        count = service_totals[svc]["count"]
        if count > 0:
            # Rough estimate: total / number of charges = per-charge cost
            monthly[svc] = val  # Use the latest charge as monthly estimate

    monthly_table = []
    monthly_total = 0
    for svc, amount in sorted(monthly.items(), key=lambda x: x[1], reverse=True):
        monthly_table.append([svc, f"${amount:.2f}"])
        monthly_total += amount

    lines.append(tabulate(
        monthly_table,
        headers=["Service", "Est. Monthly Cost"],
        tablefmt="rounded_grid",
    ))
    lines.append(f"\n  ESTIMATED MONTHLY TOTAL: ${monthly_total:.2f}")

    lines.append("\n" + "=" * 70)
    return "\n".join(lines)


def save_csv(subscriptions: list[dict], output_path: str = "subscriptions.csv"):
    """Save subscription data to CSV for further analysis."""
    if not subscriptions:
        print("No data to export.")
        return

    path = Path(output_path)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "account", "service", "price", "price_value", "subject", "date", "from"
        ])
        writer.writeheader()
        writer.writerows(subscriptions)

    print(f"  CSV exported to: {path.resolve()}")
