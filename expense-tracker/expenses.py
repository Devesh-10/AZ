#!/usr/bin/env python3
"""
Personal Expense Tracker & Savings Analyzer
Tracks subscriptions, personal expenses, and loan repayments.
Shows where you can save money.
"""

import json
import os
from datetime import datetime
from pathlib import Path

DATA_FILE = Path(__file__).parent / "expense_data.json"

# ── Default data template ──────────────────────────────────────────────
DEFAULT_DATA = {
    "currency": "EUR",
    "monthly_income": 0,
    "subscriptions": [],
    "personal_expenses": [],
    "loans": [],
}

# ── Helper functions ───────────────────────────────────────────────────

def load_data():
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    return DEFAULT_DATA.copy()


def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def fmt(amount, currency="EUR"):
    return f"€{amount:,.2f}" if currency == "EUR" else f"{currency} {amount:,.2f}"


def input_float(prompt):
    while True:
        try:
            return float(input(prompt))
        except ValueError:
            print("  Please enter a valid number.")


def input_int(prompt):
    while True:
        try:
            return int(input(prompt))
        except ValueError:
            print("  Please enter a valid number.")


# ── Menu actions ───────────────────────────────────────────────────────

def set_income(data):
    print(f"\n  Current monthly income: {fmt(data['monthly_income'])}")
    data["monthly_income"] = input_float("  Enter your monthly net income: €")
    save_data(data)
    print(f"  ✓ Income set to {fmt(data['monthly_income'])}")


def add_subscription(data):
    print("\n── Add Subscription ──")
    name = input("  Name (e.g. Claude Max, Netflix): ").strip()
    cost = input_float("  Monthly cost: €")
    category = input("  Category (ai_tools / streaming / software / other): ").strip() or "other"
    essential = input("  Essential? (y/n): ").strip().lower() == "y"

    data["subscriptions"].append({
        "name": name,
        "monthly_cost": cost,
        "category": category,
        "essential": essential,
        "added": datetime.now().strftime("%Y-%m-%d"),
    })
    save_data(data)
    print(f"  ✓ Added {name} at {fmt(cost)}/month")


def add_personal_expense(data):
    print("\n── Add Monthly Personal Expense ──")
    name = input("  Name (e.g. Rent, Groceries, Transport): ").strip()
    cost = input_float("  Monthly cost: €")
    category = input("  Category (housing / food / transport / utilities / insurance / other): ").strip() or "other"
    essential = input("  Essential? (y/n): ").strip().lower() == "y"

    data["personal_expenses"].append({
        "name": name,
        "monthly_cost": cost,
        "category": category,
        "essential": essential,
        "added": datetime.now().strftime("%Y-%m-%d"),
    })
    save_data(data)
    print(f"  ✓ Added {name} at {fmt(cost)}/month")


def add_loan(data):
    print("\n── Add Loan / Money Owed ──")
    person = input("  Who did you borrow from? ").strip()
    total = input_float("  Total amount borrowed: €")
    paid = input_float("  Amount already paid back: €")
    monthly = input_float("  Monthly repayment amount: €")
    purpose = input("  Purpose (house / car / personal / other): ").strip() or "other"

    data["loans"].append({
        "person": person,
        "total_borrowed": total,
        "amount_paid": paid,
        "monthly_repayment": monthly,
        "purpose": purpose,
        "added": datetime.now().strftime("%Y-%m-%d"),
    })
    save_data(data)
    remaining = total - paid
    months_left = remaining / monthly if monthly > 0 else float("inf")
    print(f"  ✓ Added loan from {person}: {fmt(remaining)} remaining (~{months_left:.0f} months)")


def view_summary(data):
    currency = data.get("currency", "EUR")
    income = data["monthly_income"]

    print("\n" + "=" * 60)
    print("  MONTHLY EXPENSE SUMMARY")
    print("=" * 60)

    # ── Income ──
    print(f"\n  Monthly Income: {fmt(income)}")
    print("-" * 60)

    # ── Subscriptions ──
    sub_total = 0
    if data["subscriptions"]:
        print(f"\n  {'SUBSCRIPTIONS':<35} {'Monthly':>10}  Essential?")
        print("  " + "-" * 55)
        for s in sorted(data["subscriptions"], key=lambda x: x["monthly_cost"], reverse=True):
            tag = "YES" if s["essential"] else "NO"
            print(f"  {s['name']:<35} {fmt(s['monthly_cost']):>10}  {tag}")
            sub_total += s["monthly_cost"]
        print(f"  {'SUBTOTAL':<35} {fmt(sub_total):>10}")

    # ── Personal Expenses ──
    personal_total = 0
    if data["personal_expenses"]:
        print(f"\n  {'PERSONAL EXPENSES':<35} {'Monthly':>10}  Essential?")
        print("  " + "-" * 55)
        for e in sorted(data["personal_expenses"], key=lambda x: x["monthly_cost"], reverse=True):
            tag = "YES" if e["essential"] else "NO"
            print(f"  {e['name']:<35} {fmt(e['monthly_cost']):>10}  {tag}")
            personal_total += e["monthly_cost"]
        print(f"  {'SUBTOTAL':<35} {fmt(personal_total):>10}")

    # ── Loans ──
    loan_total = 0
    if data["loans"]:
        print(f"\n  {'LOANS / DEBTS':<25} {'Remaining':>12} {'Monthly':>10} {'Months Left':>12}")
        print("  " + "-" * 60)
        for l in data["loans"]:
            remaining = l["total_borrowed"] - l["amount_paid"]
            months = remaining / l["monthly_repayment"] if l["monthly_repayment"] > 0 else float("inf")
            print(f"  {l['person']:<25} {fmt(remaining):>12} {fmt(l['monthly_repayment']):>10} {months:>10.0f} mo")
            loan_total += l["monthly_repayment"]
        print(f"  {'SUBTOTAL (monthly)':<25} {'':>12} {fmt(loan_total):>10}")

    # ── Grand Total ──
    total_expenses = sub_total + personal_total + loan_total
    remaining_income = income - total_expenses

    print("\n" + "=" * 60)
    print(f"  Total Subscriptions:       {fmt(sub_total):>12}")
    print(f"  Total Personal Expenses:   {fmt(personal_total):>12}")
    print(f"  Total Loan Repayments:     {fmt(loan_total):>12}")
    print(f"  ─────────────────────────────────────")
    print(f"  TOTAL MONTHLY EXPENSES:    {fmt(total_expenses):>12}")
    print(f"  MONTHLY INCOME:            {fmt(income):>12}")
    print(f"  REMAINING (Savings):       {fmt(remaining_income):>12}")
    if income > 0:
        pct = (remaining_income / income) * 100
        print(f"  Savings Rate:              {pct:>11.1f}%")
    print("=" * 60)


def savings_analysis(data):
    income = data["monthly_income"]

    print("\n" + "=" * 60)
    print("  SAVINGS ANALYSIS & RECOMMENDATIONS")
    print("=" * 60)

    suggestions = []
    potential_savings = 0

    # ── Subscription analysis ──
    non_essential_subs = [s for s in data["subscriptions"] if not s["essential"]]
    if non_essential_subs:
        print("\n  ** Non-Essential Subscriptions (consider cutting):")
        for s in non_essential_subs:
            print(f"     - {s['name']}: {fmt(s['monthly_cost'])}/mo ({fmt(s['monthly_cost'] * 12)}/year)")
            potential_savings += s["monthly_cost"]
            suggestions.append(f"Cancel {s['name']} to save {fmt(s['monthly_cost'])}/mo")

    # ── Subscription tier downgrades ──
    expensive_subs = [s for s in data["subscriptions"] if s["monthly_cost"] > 50]
    if expensive_subs:
        print("\n  ** Expensive Subscriptions (consider downgrading):")
        for s in expensive_subs:
            print(f"     - {s['name']}: {fmt(s['monthly_cost'])}/mo — check if a cheaper tier exists")
            suggestions.append(f"Look for a cheaper tier of {s['name']}")

    # ── Duplicate category check ──
    from collections import Counter
    sub_categories = Counter(s["category"] for s in data["subscriptions"])
    for cat, count in sub_categories.items():
        if count > 1:
            items = [s["name"] for s in data["subscriptions"] if s["category"] == cat]
            total = sum(s["monthly_cost"] for s in data["subscriptions"] if s["category"] == cat)
            print(f"\n  ** Multiple '{cat}' subscriptions ({count}): {', '.join(items)}")
            print(f"     Combined cost: {fmt(total)}/mo — do you need all of them?")

    # ── Non-essential personal expenses ──
    non_essential_personal = [e for e in data["personal_expenses"] if not e["essential"]]
    if non_essential_personal:
        print("\n  ** Non-Essential Personal Expenses:")
        for e in non_essential_personal:
            print(f"     - {e['name']}: {fmt(e['monthly_cost'])}/mo")
            potential_savings += e["monthly_cost"]

    # ── Loan prioritization ──
    if data["loans"]:
        print("\n  ** Loan Repayment Strategy:")
        sorted_loans = sorted(data["loans"], key=lambda x: x["total_borrowed"] - x["amount_paid"])
        print("     Recommended: Pay off smallest debts first (debt snowball):")
        for l in sorted_loans:
            remaining = l["total_borrowed"] - l["amount_paid"]
            print(f"     {l['person']} ({l['purpose']}): {fmt(remaining)} remaining")

    # ── Income ratio analysis ──
    if income > 0:
        sub_total = sum(s["monthly_cost"] for s in data["subscriptions"])
        personal_total = sum(e["monthly_cost"] for e in data["personal_expenses"])
        loan_total = sum(l["monthly_repayment"] for l in data["loans"])
        total = sub_total + personal_total + loan_total

        print("\n  ** Expense Breakdown (% of income):")
        print(f"     Subscriptions:    {sub_total / income * 100:5.1f}%  ({fmt(sub_total)})")
        print(f"     Personal:         {personal_total / income * 100:5.1f}%  ({fmt(personal_total)})")
        print(f"     Loan Repayments:  {loan_total / income * 100:5.1f}%  ({fmt(loan_total)})")
        print(f"     Total:            {total / income * 100:5.1f}%  ({fmt(total)})")

        if total / income > 0.80:
            print("\n     ⚠ WARNING: You're spending over 80% of your income!")
            print("     Aim to keep total expenses under 70-80% for healthy savings.")
        elif total / income > 0.50:
            print("\n     ℹ You're spending 50-80% of income — room to optimize.")
        else:
            print("\n     ✓ Good! You're keeping expenses under 50% of income.")

    # ── Summary ──
    if potential_savings > 0:
        print(f"\n  ** POTENTIAL MONTHLY SAVINGS: {fmt(potential_savings)}")
        print(f"     That's {fmt(potential_savings * 12)} per year!")

    if not suggestions and not non_essential_personal:
        print("\n  Everything looks essential — consider increasing income or")
        print("  negotiating better rates on existing expenses.")

    print("=" * 60)


def remove_item(data):
    print("\n── Remove an Entry ──")
    print("  1. Remove a subscription")
    print("  2. Remove a personal expense")
    print("  3. Remove a loan")
    choice = input("  Choose (1-3): ").strip()

    if choice == "1":
        items = data["subscriptions"]
        label = "subscriptions"
    elif choice == "2":
        items = data["personal_expenses"]
        label = "personal expenses"
    elif choice == "3":
        items = data["loans"]
        label = "loans"
    else:
        print("  Invalid choice.")
        return

    if not items:
        print(f"  No {label} to remove.")
        return

    for i, item in enumerate(items):
        name = item.get("name") or item.get("person")
        cost = item.get("monthly_cost") or item.get("monthly_repayment")
        print(f"  {i + 1}. {name} ({fmt(cost)}/mo)")

    idx = input_int(f"  Enter number to remove (1-{len(items)}): ") - 1
    if 0 <= idx < len(items):
        removed = items.pop(idx)
        save_data(data)
        name = removed.get("name") or removed.get("person")
        print(f"  ✓ Removed {name}")
    else:
        print("  Invalid selection.")


def update_loan_payment(data):
    if not data["loans"]:
        print("\n  No loans recorded.")
        return

    print("\n── Update Loan Payment ──")
    for i, l in enumerate(data["loans"]):
        remaining = l["total_borrowed"] - l["amount_paid"]
        print(f"  {i + 1}. {l['person']}: {fmt(remaining)} remaining")

    idx = input_int(f"  Select loan (1-{len(data['loans'])}): ") - 1
    if 0 <= idx < len(data["loans"]):
        amount = input_float("  Payment amount: €")
        data["loans"][idx]["amount_paid"] += amount
        remaining = data["loans"][idx]["total_borrowed"] - data["loans"][idx]["amount_paid"]
        save_data(data)
        if remaining <= 0:
            print(f"  ✓ LOAN PAID OFF to {data['loans'][idx]['person']}!")
        else:
            print(f"  ✓ Payment recorded. Remaining: {fmt(remaining)}")
    else:
        print("  Invalid selection.")


# ── Main menu ──────────────────────────────────────────────────────────

def main():
    data = load_data()

    print("\n" + "=" * 60)
    print("  EXPENSE TRACKER & SAVINGS ANALYZER")
    print("=" * 60)

    while True:
        print("\n  ┌─────────────────────────────────┐")
        print("  │  1. Set monthly income           │")
        print("  │  2. Add subscription              │")
        print("  │  3. Add personal expense          │")
        print("  │  4. Add loan / money owed         │")
        print("  │  5. View expense summary          │")
        print("  │  6. Savings analysis              │")
        print("  │  7. Record loan payment           │")
        print("  │  8. Remove an entry               │")
        print("  │  9. Exit                          │")
        print("  └─────────────────────────────────┘")

        choice = input("\n  Choose (1-9): ").strip()

        if choice == "1":
            set_income(data)
        elif choice == "2":
            add_subscription(data)
        elif choice == "3":
            add_personal_expense(data)
        elif choice == "4":
            add_loan(data)
        elif choice == "5":
            view_summary(data)
        elif choice == "6":
            savings_analysis(data)
        elif choice == "7":
            update_loan_payment(data)
        elif choice == "8":
            remove_item(data)
        elif choice == "9":
            print("\n  Goodbye! Keep tracking those expenses. 💰\n")
            break
        else:
            print("  Invalid choice, try again.")


if __name__ == "__main__":
    main()
