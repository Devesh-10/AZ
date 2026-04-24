#!/usr/bin/env python3
"""
Gmail Subscription Cost Tracker
Scans multiple Gmail accounts for subscription receipts and generates a cost report.

Usage:
    python main.py                    # Scan all 3 accounts (last 12 months)
    python main.py --months 6         # Scan last 6 months
    python main.py --accounts edwardiandit3 edwardiandit2  # Specific accounts only
"""

import argparse
from auth import authenticate_all
from scanner import scan_all_accounts
from report import generate_report, save_csv

DEFAULT_ACCOUNTS = ["edwardiandit3", "edwardiandit2", "edwardiandit4"]


def main():
    parser = argparse.ArgumentParser(description="Gmail Subscription Cost Tracker")
    parser.add_argument(
        "--accounts",
        nargs="+",
        default=DEFAULT_ACCOUNTS,
        help="Gmail account names (without @gmail.com)",
    )
    parser.add_argument(
        "--months",
        type=int,
        default=12,
        help="How many months back to scan (default: 12)",
    )
    parser.add_argument(
        "--csv",
        type=str,
        default="subscriptions.csv",
        help="Output CSV file path (default: subscriptions.csv)",
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  Gmail Subscription Cost Tracker")
    print(f"  Accounts: {', '.join(a + '@gmail.com' for a in args.accounts)}")
    print(f"  Scanning last {args.months} months")
    print("=" * 60)

    # Step 1: Authenticate all accounts
    print("\n[1/3] Authenticating Gmail accounts...\n")
    services = authenticate_all(args.accounts)

    # Step 2: Scan for subscription emails
    print("\n[2/3] Scanning for subscription emails...\n")
    subscriptions = scan_all_accounts(services, months_back=args.months)

    # Step 3: Generate report
    print("\n[3/3] Generating report...\n")
    report = generate_report(subscriptions)
    print(report)

    # Save CSV
    save_csv(subscriptions, args.csv)

    print(f"\nDone! Found {len(subscriptions)} subscription charges across {len(args.accounts)} accounts.")


if __name__ == "__main__":
    main()
