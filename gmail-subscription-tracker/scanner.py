"""
Gmail subscription scanner.
Searches emails for subscription receipts, invoices, and billing notifications,
then extracts cost information.
"""

import re
import base64
from datetime import datetime, timedelta
from bs4 import BeautifulSoup


# Search queries to find subscription-related emails
SEARCH_QUERIES = [
    "subject:(subscription OR receipt OR invoice OR billing OR payment OR renewal OR charge)",
    "subject:(monthly plan OR annual plan OR your plan OR membership)",
    "from:(noreply OR billing OR payments OR receipts OR invoice)",
    "subject:(order confirmation) has:noreply",
]

# Known subscription senders and their service names
KNOWN_SERVICES = {
    "netflix": "Netflix",
    "spotify": "Spotify",
    "apple": "Apple",
    "google": "Google",
    "amazon": "Amazon",
    "microsoft": "Microsoft",
    "adobe": "Adobe",
    "dropbox": "Dropbox",
    "slack": "Slack",
    "zoom": "Zoom",
    "github": "GitHub",
    "openai": "OpenAI",
    "chatgpt": "ChatGPT",
    "claude": "Claude / Anthropic",
    "anthropic": "Anthropic",
    "notion": "Notion",
    "figma": "Figma",
    "canva": "Canva",
    "linkedin": "LinkedIn",
    "youtube": "YouTube",
    "disney": "Disney+",
    "hulu": "Hulu",
    "hbo": "HBO Max",
    "paramount": "Paramount+",
    "peacock": "Peacock",
    "audible": "Audible",
    "kindle": "Kindle Unlimited",
    "icloud": "iCloud",
    "1password": "1Password",
    "lastpass": "LastPass",
    "nordvpn": "NordVPN",
    "expressvpn": "ExpressVPN",
    "grammarly": "Grammarly",
    "coursera": "Coursera",
    "udemy": "Udemy",
    "skillshare": "Skillshare",
    "stripe": "Stripe (payment)",
    "paypal": "PayPal",
    "heroku": "Heroku",
    "vercel": "Vercel",
    "netlify": "Netlify",
    "digitalocean": "DigitalOcean",
    "aws": "AWS",
    "cloudflare": "Cloudflare",
}

# Regex patterns for extracting monetary amounts
PRICE_PATTERNS = [
    r"[\$\€\£]\s*\d{1,6}[.,]\d{2}",          # $12.99, €12.99, £12.99
    r"\d{1,6}[.,]\d{2}\s*(?:USD|EUR|GBP|CAD|AUD)",  # 12.99 USD
    r"(?:US\$|CA\$|AU\$)\s*\d{1,6}[.,]\d{2}",       # US$12.99
    r"Total[:\s]*[\$\€\£]?\s*\d{1,6}[.,]\d{2}",     # Total: $12.99
    r"Amount[:\s]*[\$\€\£]?\s*\d{1,6}[.,]\d{2}",    # Amount: $12.99
    r"Charge[:\s]*[\$\€\£]?\s*\d{1,6}[.,]\d{2}",    # Charge: $12.99
]


def search_emails(service, query: str, max_results: int = 100) -> list:
    """Search Gmail and return matching message IDs."""
    try:
        results = (
            service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        return results.get("messages", [])
    except Exception as e:
        print(f"  Warning: Search failed for query: {e}")
        return []


def get_email_content(service, msg_id: str) -> dict | None:
    """Fetch full email content and extract relevant fields."""
    try:
        msg = (
            service.users()
            .messages()
            .get(userId="me", id=msg_id, format="full")
            .execute()
        )

        headers = msg.get("payload", {}).get("headers", [])
        header_dict = {h["name"].lower(): h["value"] for h in headers}

        subject = header_dict.get("subject", "")
        sender = header_dict.get("from", "")
        date_str = header_dict.get("date", "")

        body_text = extract_body(msg.get("payload", {}))

        return {
            "id": msg_id,
            "subject": subject,
            "from": sender,
            "date": date_str,
            "body": body_text,
        }
    except Exception as e:
        print(f"  Warning: Could not fetch message {msg_id}: {e}")
        return None


def extract_body(payload: dict) -> str:
    """Recursively extract text from email payload."""
    body = ""

    if "body" in payload and payload["body"].get("data"):
        raw = payload["body"]["data"]
        decoded = base64.urlsafe_b64decode(raw).decode("utf-8", errors="replace")
        if payload.get("mimeType", "").startswith("text/html"):
            soup = BeautifulSoup(decoded, "html.parser")
            body = soup.get_text(separator=" ", strip=True)
        else:
            body = decoded

    for part in payload.get("parts", []):
        body += " " + extract_body(part)

    return body.strip()


def identify_service(email: dict) -> str:
    """Identify which subscription service the email is from."""
    sender_lower = email["from"].lower()
    subject_lower = email["subject"].lower()
    combined = sender_lower + " " + subject_lower

    for keyword, service_name in KNOWN_SERVICES.items():
        if keyword in combined:
            return service_name

    # Try to extract domain from sender
    match = re.search(r"@([\w.-]+)", sender_lower)
    if match:
        domain = match.group(1).replace(".com", "").replace(".io", "").replace(".co", "")
        return domain.split(".")[-1].capitalize()

    return "Unknown"


def extract_prices(text: str) -> list[str]:
    """Extract all price-like strings from text."""
    prices = []
    for pattern in PRICE_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        prices.extend(matches)
    return prices


def parse_price(price_str: str) -> float | None:
    """Parse a price string to a float value."""
    cleaned = re.sub(r"[^\d.,]", "", price_str)
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def scan_account(service, account_name: str, months_back: int = 12) -> list[dict]:
    """
    Scan a single Gmail account for subscription emails.
    Returns a list of subscription records.
    """
    print(f"\n  Scanning {account_name}@gmail.com ...")
    since_date = (datetime.now() - timedelta(days=months_back * 30)).strftime("%Y/%m/%d")

    all_msg_ids = set()
    for query in SEARCH_QUERIES:
        full_query = f"{query} after:{since_date}"
        messages = search_emails(service, full_query)
        for m in messages:
            all_msg_ids.add(m["id"])

    print(f"  Found {len(all_msg_ids)} potential subscription emails")

    subscriptions = []
    seen_keys = set()

    for i, msg_id in enumerate(all_msg_ids):
        if (i + 1) % 20 == 0:
            print(f"  Processing {i+1}/{len(all_msg_ids)} ...")

        email = get_email_content(service, msg_id)
        if not email:
            continue

        service_name = identify_service(email)
        all_text = f"{email['subject']} {email['body']}"
        prices = extract_prices(all_text)

        if not prices:
            continue

        # Take the most likely price (first match is usually the total/charge)
        best_price = None
        for p in prices:
            val = parse_price(p)
            if val and 0.5 < val < 10000:  # Filter out unreasonable amounts
                best_price = p
                break

        if not best_price:
            continue

        # De-duplicate: same service + same price in same month
        dedup_key = f"{service_name}|{best_price}|{email['date'][:10]}"
        if dedup_key in seen_keys:
            continue
        seen_keys.add(dedup_key)

        subscriptions.append({
            "account": f"{account_name}@gmail.com",
            "service": service_name,
            "price": best_price,
            "price_value": parse_price(best_price),
            "subject": email["subject"][:80],
            "date": email["date"],
            "from": email["from"],
        })

    print(f"  Found {len(subscriptions)} subscription charges for {account_name}")
    return subscriptions


def scan_all_accounts(services: dict, months_back: int = 12) -> list[dict]:
    """Scan all accounts and return combined subscription list."""
    all_subs = []
    for account_name, service in services.items():
        subs = scan_account(service, account_name, months_back)
        all_subs.extend(subs)
    return all_subs
