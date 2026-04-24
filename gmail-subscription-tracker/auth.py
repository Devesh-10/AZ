"""
Gmail OAuth2 authentication module.
Handles authentication for multiple Gmail accounts.
"""

import os
import json
from pathlib import Path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_DIR = Path(__file__).parent / "tokens"
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"


def get_gmail_service(account_name: str):
    """
    Authenticate and return a Gmail API service for the given account.
    Each account gets its own token file so you can stay logged into all 3.
    """
    TOKEN_DIR.mkdir(exist_ok=True)
    token_path = TOKEN_DIR / f"token_{account_name}.json"

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not CREDENTIALS_FILE.exists():
                print(f"\n{'='*60}")
                print("ERROR: credentials.json not found!")
                print("You need to create a Google Cloud project and download")
                print("OAuth 2.0 credentials. See README for instructions.")
                print(f"{'='*60}\n")
                raise FileNotFoundError(
                    f"Missing {CREDENTIALS_FILE}. "
                    "Download OAuth credentials from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            print(f"\n>>> Authenticating account: {account_name}")
            print(">>> A browser window will open. Log in with the correct account.\n")
            creds = flow.run_local_server(port=0)

        with open(token_path, "w") as f:
            f.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


def authenticate_all(accounts: list[str]) -> dict:
    """Authenticate all accounts and return {account_name: service} dict."""
    services = {}
    for account in accounts:
        print(f"Connecting to {account}@gmail.com ...")
        services[account] = get_gmail_service(account)
        print(f"  ✓ Connected to {account}@gmail.com")
    return services
