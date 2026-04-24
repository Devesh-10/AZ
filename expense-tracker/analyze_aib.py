#!/usr/bin/env python3
"""
AIB Bank Statement Analyzer
Parses exported CSVs and categorizes all transactions.
"""

import csv
import re
from collections import defaultdict
from datetime import datetime

FILE = "/Users/devesh.b.sharma/Downloads/Transaction_Export_01.03.2026_10.48.csv"

# ── Category rules ─────────────────────────────────────────────────────
CATEGORY_RULES = [
    # Mortgage / Rent
    (r"Bankinter SA", "MORTGAGE (Bankinter)"),
    (r"MOBI JOSEPH KANE|MOBI RENT", "RENT (Joseph Kane)"),

    # Utilities
    (r"PINERGY", "ELECTRICITY (Pinergy)"),
    (r"Electric Irela", "ELECTRICITY (Electric Ireland)"),
    (r"VIRGIN MEDIA", "BROADBAND (Virgin Media)"),
    (r"GOMO", "MOBILE (GoMo)"),

    # Insurance
    (r"Zurich Life", "INSURANCE (Zurich Life)"),
    (r"PREMIUM CREDIT", "INSURANCE (Premium Credit)"),
    (r"QUOTE DEVIL", "INSURANCE (Quote Devil)"),

    # Subscriptions - AI/Tech
    (r"CLAUDE\.AI", "SUB: Claude AI"),
    (r"OPENAI.*CHATGP", "SUB: OpenAI ChatGPT"),
    (r"REPLIT", "SUB: Replit"),
    (r"Microsoft|MICROSOFT", "SUB: Microsoft"),

    # Subscriptions - Entertainment
    (r"NETFLIX", "SUB: Netflix"),
    (r"APPLE\.COM/BILL", "SUB: Apple"),
    (r"SKY DIGITAL|SKY TV|Sky Spor", "SUB: Sky TV/Sports"),
    (r"PLUS SUBS", "SUB: Plus (Channel)"),
    (r"Shaadi", "SUB: Shaadi.com"),

    # Gym
    (r"WESTWOOD|WEST WOOD", "GYM (Westwood)"),

    # Revolut transfers
    (r"Revolut", "TRANSFER: Revolut"),

    # Food & Coffee
    (r"Insomnia", "COFFEE (Insomnia)"),
    (r"STARBUCKS|TATA STARBUCKS", "COFFEE (Starbucks)"),
    (r"CARPO COFFEE|COFFE AND BEAN|BelfryandCo", "COFFEE (Other)"),
    (r"Joe And The Ju", "COFFEE (Joe & Juice)"),
    (r"TESCO", "GROCERIES (Tesco)"),
    (r"LIDL", "GROCERIES (Lidl)"),
    (r"CENTRA", "GROCERIES (Centra)"),
    (r"DUNNES", "GROCERIES (Dunnes)"),
    (r"DELIVEROO", "FOOD DELIVERY (Deliveroo)"),
    (r"UBER.*EATS", "FOOD DELIVERY (Uber Eats)"),
    (r"MCDONALDS|MC DONALDS", "EATING OUT (McDonalds)"),
    (r"BOOJUM", "EATING OUT (Boojum)"),
    (r"Base Pizza", "EATING OUT"),
    (r"EURASIA", "EATING OUT"),
    (r"Lilians", "EATING OUT"),
    (r"SAPPHIRE FOODS|SAPTAGIRI", "EATING OUT (India)"),
    (r"BIGTREE", "EATING OUT (India)"),
    (r"TST-The Tram C", "EATING OUT (Tram Cafe)"),

    # Transport
    (r"UBER.*TRIP", "TRANSPORT (Uber)"),
    (r"MAXOL", "TRANSPORT (Petrol)"),
    (r"EFLOW", "TRANSPORT (eFlow Tolls)"),
    (r"LUAS", "TRANSPORT (Luas)"),

    # Shopping
    (r"ADIDAS", "SHOPPING (Adidas)"),
    (r"PUMA", "SHOPPING (Puma)"),
    (r"Woodies", "SHOPPING (Woodies)"),
    (r"HOME STORE", "SHOPPING (Home Store & More)"),
    (r"HARVEY NORMAN", "SHOPPING (Harvey Norman)"),
    (r"IKEA", "SHOPPING (IKEA)"),
    (r"ELVERYS", "SHOPPING (Elvery's Sports)"),
    (r"Etsy", "SHOPPING (Etsy)"),
    (r"MCCABES PHARMA", "HEALTH (McCabes Pharmacy)"),

    # Hotels & Travel
    (r"RADISSON", "TRAVEL: Hotel (Radisson)"),
    (r"HOTEL|YOTEL|Yotel|MARVEL RESIDEN|M S JAMES|HOTEL WILLOW|BKG\*HOTEL", "TRAVEL: Hotel"),
    (r"Go ibibo|Interglobe|lastminute", "TRAVEL: Flights/Booking"),

    # Sports & Leisure
    (r"CRICKET LEINST", "SPORTS (Cricket Leinster)"),
    (r"PVR INOX", "ENTERTAINMENT (Cinema)"),
    (r"PHOENIX PARK", "ENTERTAINMENT"),
    (r"MCEVOYS PUB", "PUB"),

    # People - Money In
    (r"RAKESH CHAND", "INCOME: Rakesh Chand"),
    (r"Mrs\. INDU.*SHARMA|INDU SHARMA", "INCOME: Indu Sharma"),
    (r"LAL CHAND SHARMA", "INCOME: Lal Chand Sharma"),
    (r"DEVESH SHARMA.*Credit", "INCOME: Self Transfer"),

    # Salary
    (r"11378326", "SALARY"),

    # Motor tax
    (r"ONLINE MOTOR T", "CAR: Motor Tax"),

    # Fees
    (r"FEE-QTR|STAMP DUTY|PYMT FEE|FEE-UNPAID", "BANK FEES"),

    # Testing/Exams
    (r"TESTING EXAM", "EDUCATION (Exam)"),

    # Other
    (r"WITHDRAWAL", "CASH WITHDRAWAL"),
    (r"SQ \*WOOD FLOOR", "HOME (Wood Floor - Refund)"),
    (r"AN POST", "POST"),
    (r"WH Smith", "SHOPPING"),
    (r"HMS Host", "EATING OUT (Airport)"),
    (r"SumUp.*Martin", "OTHER"),
    (r"Liffey Valley", "SHOPPING"),
    (r"BUS STOP", "SHOPPING"),
    (r"BUTLERS CHOCOL", "SHOPPING"),
    (r"CLAYTON HOTEL", "EATING OUT"),
    (r"PAY\*Grafton", "EATING OUT"),
    (r"O'BRIENS WINES", "ALCOHOL"),
    (r"COSTA", "COFFEE"),
    (r"NYA\*", "VENDING"),
    (r"TPP Devesh", "OTHER"),
    (r"HHH", "INCOME: Other"),
    (r"HONGTAO ZHAO", "OTHER (Payment)"),
    (r"UNPAY D/DEBIT", "BANK: Unpaid DD Refund"),
]


def categorize(desc1, desc2, desc3, tx_type, credit):
    full = f"{desc1} {desc2} {desc3}".strip()

    # Check if it's a credit (money in)
    if credit and float(credit.replace(",", "")) > 0:
        for pattern, cat in CATEGORY_RULES:
            if re.search(pattern, full, re.IGNORECASE):
                return cat
        return "INCOME: Other"

    for pattern, cat in CATEGORY_RULES:
        if re.search(pattern, full, re.IGNORECASE):
            return cat
    return f"UNCATEGORIZED: {desc1}"


def parse_amount(s):
    if not s or not s.strip():
        return 0.0
    return float(s.strip().replace(",", ""))


def main():
    transactions = []

    with open(FILE) as f:
        reader = csv.reader(f)
        header = next(reader)

        for row in reader:
            if len(row) < 10:
                continue

            date_str = row[1].strip().strip('"')
            desc1 = row[2].strip().strip('"')
            desc2 = row[3].strip().strip('"')
            desc3 = row[4].strip().strip('"')
            debit = row[5].strip().strip('"')
            credit = row[6].strip().strip('"')
            tx_type = row[9].strip().strip('"')

            date = datetime.strptime(date_str, "%d/%m/%Y")
            category = categorize(desc1, desc2, desc3, tx_type, credit)
            debit_amt = parse_amount(debit)
            credit_amt = parse_amount(credit)

            transactions.append({
                "date": date,
                "desc": desc1,
                "category": category,
                "debit": debit_amt,
                "credit": credit_amt,
                "month": date.strftime("%b %Y"),
            })

    # ── Monthly breakdown ──────────────────────────────────────────────
    months = ["Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026"]

    print("=" * 80)
    print("  AIB BANK STATEMENT ANALYSIS (Jan - Apr 2026)")
    print("=" * 80)

    # ── Income vs Expenses per month ───────────────────────────────────
    print(f"\n{'MONTH':<12} {'INCOME':>12} {'EXPENSES':>12} {'NET':>12}")
    print("-" * 50)
    for month in months:
        income = sum(t["credit"] for t in transactions if t["month"] == month)
        expenses = sum(t["debit"] for t in transactions if t["month"] == month)
        net = income - expenses
        print(f"  {month:<10} €{income:>10,.2f} €{expenses:>10,.2f} €{net:>10,.2f}")

    total_income = sum(t["credit"] for t in transactions)
    total_expenses = sum(t["debit"] for t in transactions)
    print("-" * 50)
    print(f"  {'TOTAL':<10} €{total_income:>10,.2f} €{total_expenses:>10,.2f} €{total_income - total_expenses:>10,.2f}")

    # ── Category totals (expenses only) ────────────────────────────────
    print("\n" + "=" * 80)
    print("  EXPENSES BY CATEGORY (Total over period)")
    print("=" * 80)

    cat_totals = defaultdict(float)
    cat_counts = defaultdict(int)
    for t in transactions:
        if t["debit"] > 0:
            cat_totals[t["category"]] += t["debit"]
            cat_counts[t["category"]] += 1

    sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)

    print(f"\n  {'CATEGORY':<40} {'TOTAL':>10} {'COUNT':>6} {'AVG/MO':>10}")
    print("  " + "-" * 68)
    for cat, total in sorted_cats:
        if cat.startswith("INCOME") or cat.startswith("SALARY"):
            continue
        count = cat_counts[cat]
        avg_monthly = total / 4  # ~4 months of data
        print(f"  {cat:<40} €{total:>8,.2f} {count:>6} €{avg_monthly:>8,.2f}")

    expenses_only = sum(v for k, v in cat_totals.items() if not k.startswith("INCOME") and not k.startswith("SALARY"))
    print("  " + "-" * 68)
    print(f"  {'TOTAL EXPENSES':<40} €{expenses_only:>8,.2f}")

    # ── Grouped summary ────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  GROUPED MONTHLY AVERAGES")
    print("=" * 80)

    groups = {
        "HOUSING (Mortgage + Rent)": ["MORTGAGE", "RENT"],
        "UTILITIES (Electric, Broadband, Mobile)": ["ELECTRICITY", "BROADBAND", "MOBILE"],
        "INSURANCE": ["INSURANCE"],
        "AI SUBSCRIPTIONS (Claude, OpenAI, Replit, Microsoft)": ["SUB: Claude", "SUB: OpenAI", "SUB: Replit", "SUB: Microsoft"],
        "ENTERTAINMENT SUBS (Netflix, Apple, Sky, Plus)": ["SUB: Netflix", "SUB: Apple", "SUB: Sky", "SUB: Plus", "SUB: Shaadi"],
        "GYM": ["GYM"],
        "REVOLUT TRANSFERS": ["TRANSFER: Revolut"],
        "COFFEE": ["COFFEE"],
        "GROCERIES": ["GROCERIES"],
        "EATING OUT": ["EATING OUT", "FOOD DELIVERY", "PUB"],
        "TRANSPORT (Uber, Petrol, Tolls, Luas)": ["TRANSPORT"],
        "SHOPPING (Clothes, Home, Electronics)": ["SHOPPING", "HOME"],
        "TRAVEL (Hotels, Flights)": ["TRAVEL"],
        "HEALTH": ["HEALTH"],
        "SPORTS & LEISURE": ["SPORTS", "ENTERTAINMENT"],
    }

    print(f"\n  {'GROUP':<50} {'MONTHLY AVG':>12} {'% OF INCOME':>12}")
    print("  " + "-" * 75)

    monthly_salary = total_income / 4
    grand_total = 0

    for group_name, prefixes in groups.items():
        group_total = sum(
            v for k, v in cat_totals.items()
            if any(k.startswith(p) for p in prefixes)
            and not k.startswith("INCOME") and not k.startswith("SALARY")
        )
        monthly_avg = group_total / 4
        pct = (monthly_avg / monthly_salary * 100) if monthly_salary > 0 else 0
        grand_total += group_total
        if group_total > 0:
            print(f"  {group_name:<50} €{monthly_avg:>10,.2f} {pct:>10.1f}%")

    print("  " + "-" * 75)
    monthly_grand = grand_total / 4
    pct_total = (monthly_grand / monthly_salary * 100) if monthly_salary > 0 else 0
    print(f"  {'TOTAL TRACKED':<50} €{monthly_grand:>10,.2f} {pct_total:>10.1f}%")

    # ── SAVINGS OPPORTUNITIES ──────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  WHERE YOU CAN SAVE MONEY")
    print("=" * 80)

    savings = []

    # 1. AI Subscriptions
    ai_total = sum(v for k, v in cat_totals.items() if k.startswith("SUB: Claude") or k.startswith("SUB: OpenAI") or k.startswith("SUB: Replit") or k.startswith("SUB: Microsoft"))
    ai_monthly = ai_total / 4
    print(f"\n  1. AI TOOL SUBSCRIPTIONS: €{ai_monthly:.2f}/month (€{ai_total:.2f} total)")
    print(f"     - Claude AI: cancelled (was €34-111/mo) ✓ DONE")
    print(f"     - OpenAI ChatGPT: ~€21/mo — do you need BOTH Claude and ChatGPT?")
    print(f"     - Replit: ~€35-43/mo — consider if you use it enough")
    print(f"     - Microsoft: ~€5/mo — likely needed")
    print(f"     POTENTIAL SAVING: Drop OpenAI + Replit = ~€56/mo (€672/yr)")
    savings.append(("Drop OpenAI + Replit", 56))

    # 2. Entertainment subs
    ent_total = sum(v for k, v in cat_totals.items() if k in ["SUB: Netflix", "SUB: Apple", "SUB: Sky TV/Sports", "SUB: Plus (Channel)", "SUB: Shaadi.com"])
    ent_monthly = ent_total / 4
    print(f"\n  2. ENTERTAINMENT SUBSCRIPTIONS: €{ent_monthly:.2f}/month")
    print(f"     - Netflix: €24/mo")
    print(f"     - Apple: €18 + €3/mo")
    print(f"     - Sky TV: €44/mo + Sky Digital €27/mo + Sky Sports €15/mo = €86/mo!")
    print(f"     - Plus Subs: 2x €9/mo = €18/mo")
    print(f"     - Shaadi.com: €48 (one-off?)")
    print(f"     SKY ALONE IS €86/MO! Consider NOW TV instead (~€15-25/mo)")
    print(f"     POTENTIAL SAVING: Downgrade Sky + drop 1 Plus = ~€70/mo (€840/yr)")
    savings.append(("Downgrade Sky package", 70))

    # 3. Coffee habit
    coffee_total = sum(v for k, v in cat_totals.items() if k.startswith("COFFEE"))
    coffee_monthly = coffee_total / 4
    coffee_count = sum(v for k, v in cat_counts.items() if k.startswith("COFFEE"))
    print(f"\n  3. COFFEE: €{coffee_monthly:.2f}/month ({coffee_count} purchases in period)")
    print(f"     That's ~{coffee_count/4:.0f} coffees per month!")
    print(f"     POTENTIAL SAVING: Make coffee at home 50% of time = ~€{coffee_monthly/2:.0f}/mo")
    savings.append(("Reduce coffee spending 50%", coffee_monthly / 2))

    # 4. Eating out
    eating_total = sum(v for k, v in cat_totals.items() if k.startswith("EATING OUT") or k.startswith("FOOD DELIVERY") or k.startswith("PUB"))
    eating_monthly = eating_total / 4
    print(f"\n  4. EATING OUT & DELIVERY: €{eating_monthly:.2f}/month")
    print(f"     Includes restaurants, Deliveroo, Uber Eats, takeaways")
    print(f"     POTENTIAL SAVING: Cook more, reduce by 40% = ~€{eating_monthly * 0.4:.0f}/mo")
    savings.append(("Reduce eating out 40%", eating_monthly * 0.4))

    # 5. Uber
    uber_total = sum(v for k, v in cat_totals.items() if "Uber" in k and "Eats" not in k)
    uber_monthly = uber_total / 4
    print(f"\n  5. UBER/TRANSPORT: €{uber_monthly:.2f}/month on Uber rides alone")
    print(f"     Plus petrol: ~€{sum(v for k, v in cat_totals.items() if 'Petrol' in k)/4:.0f}/mo")
    print(f"     Plus eFlow tolls: €{sum(v for k, v in cat_totals.items() if 'eFlow' in k)/4:.0f}/mo")

    # 6. Revolut transfers
    rev_total = sum(v for k, v in cat_totals.items() if k.startswith("TRANSFER: Revolut"))
    rev_monthly = rev_total / 4
    print(f"\n  6. REVOLUT TRANSFERS: €{rev_monthly:.2f}/month — where is this going?")
    print(f"     Total transferred: €{rev_total:.2f} over ~4 months")
    print(f"     This is a BLIND SPOT — track Revolut spending separately!")

    # 7. India travel spending
    india_spend = sum(t["debit"] for t in transactions if "INR@" in f"{t['desc']}")
    print(f"\n  7. INDIA SPENDING: €{india_spend:.2f} total (paid in INR)")
    print(f"     Hotels, food, shopping — mostly travel expenses")

    # 8. Big fixed costs
    mortgage_total = sum(v for k, v in cat_totals.items() if "MORTGAGE" in k)
    rent_total = sum(v for k, v in cat_totals.items() if "RENT" in k)
    print(f"\n  8. BIGGEST FIXED COSTS:")
    print(f"     - Mortgage (Bankinter): €{mortgage_total/4:,.2f}/mo (€{mortgage_total:,.2f} total)")
    print(f"     - Rent (Joseph Kane): €{rent_total/4:,.2f}/mo (€{rent_total:,.2f} total)")
    print(f"     - Combined: €{(mortgage_total + rent_total)/4:,.2f}/mo — THIS IS YOUR #1 COST")

    # ── Income sources ─────────────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  INCOME SOURCES")
    print("=" * 80)

    income_cats = defaultdict(float)
    for t in transactions:
        if t["credit"] > 0:
            income_cats[t["category"]] += t["credit"]

    for cat, total in sorted(income_cats.items(), key=lambda x: x[1], reverse=True):
        print(f"  {cat:<40} €{total:>10,.2f} (€{total/4:>8,.2f}/mo)")

    # ── TOTAL POTENTIAL SAVINGS ────────────────────────────────────────
    print("\n" + "=" * 80)
    print("  TOTAL POTENTIAL SAVINGS")
    print("=" * 80)
    total_savings = 0
    for name, amount in savings:
        print(f"  {name:<45} €{amount:>8,.2f}/mo")
        total_savings += amount
    print("  " + "-" * 55)
    print(f"  {'TOTAL POTENTIAL SAVINGS':<45} €{total_savings:>8,.2f}/mo")
    print(f"  {'ANNUAL SAVINGS':<45} €{total_savings * 12:>8,.2f}/yr")
    print("=" * 80)


if __name__ == "__main__":
    main()
