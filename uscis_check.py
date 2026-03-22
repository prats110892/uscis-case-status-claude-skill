#!/usr/bin/env python3
"""
USCIS Case Status Checker

Logs into myaccount.uscis.gov, reads your SMS OTP automatically from
Mac Messages, and returns your case status as JSON.

Setup:
  pip install requests python-dotenv playwright
  playwright install chromium
  Create a .env file in the same directory:
    USCIS_EMAIL=your@email.com
    USCIS_PASSWORD=yourpassword
    USCIS_RECEIPT_NUMBER=IOE1234567890
"""

import asyncio
import requests
import re
import json
import os
import time
import sqlite3
import getpass
from pathlib import Path

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv(usecwd=True))
except ImportError:
    pass

RECEIPT_NUMBER = os.environ.get("USCIS_RECEIPT_NUMBER", "").strip()
BASE_URL       = "https://myaccount.uscis.gov"
SIGN_IN_PAGE   = f"{BASE_URL}/sign-in"
SIGN_IN_API    = f"{BASE_URL}/v1/authentication/sign_in"
OTP_API        = f"{BASE_URL}/v1/authentication/verification_code"
CASE_API       = f"https://my.uscis.gov/account/case-service/api/cases/{RECEIPT_NUMBER}"

BASE_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/26.2 Safari/605.1.15",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin":          BASE_URL,
    "Sec-Fetch-Dest":  "empty",
    "Sec-Fetch-Mode":  "cors",
    "Sec-Fetch-Site":  "same-origin",
}


# ---------------------------------------------------------------------------
# Step 1: solve AWS WAF JS challenge via headless browser (~3s)
# ---------------------------------------------------------------------------

async def get_waf_token() -> dict:
    """
    Load the sign-in page headlessly. AWS WAF auto-solves its JS challenge
    and sets aws-waf-token. We grab all seeded cookies and close the browser.
    """
    from playwright.async_api import async_playwright

    print("Solving WAF challenge (headless, ~3s)...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent=BASE_HEADERS["User-Agent"])
        page    = await context.new_page()
        await page.goto(SIGN_IN_PAGE)

        for _ in range(20):
            cookies = {c["name"]: c["value"] for c in await context.cookies()}
            if "aws-waf-token" in cookies:
                break
            await asyncio.sleep(0.5)

        cookies = {c["name"]: c["value"] for c in await context.cookies()}
        await browser.close()

    if "aws-waf-token" not in cookies:
        print("  Warning: aws-waf-token not found -- WAF may still block")
    else:
        print("  WAF token acquired.")
    return cookies


# ---------------------------------------------------------------------------
# OTP from Mac Messages (macOS only)
# ---------------------------------------------------------------------------

def read_otp_from_messages(max_age_seconds=120):
    """Read a recent 6-digit OTP from Mac Messages."""
    db_path = Path.home() / "Library/Messages/chat.db"
    if not db_path.exists():
        return None
    try:
        conn   = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        apple_epoch_offset = 978307200
        cutoff_ns = (time.time() - apple_epoch_offset - max_age_seconds) * 1e9
        cursor.execute("""
            SELECT m.text FROM message m
            WHERE m.date > ?
              AND m.is_from_me = 0
              AND (
                m.text LIKE '%verification code%'
                OR m.text LIKE '%your code%'
                OR m.text LIKE '%one-time%'
                OR m.text LIKE '%USCIS%'
              )
            ORDER BY m.date DESC
            LIMIT 10
        """, (cutoff_ns,))
        rows = cursor.fetchall()
        conn.close()
        for (text,) in rows:
            match = re.search(r'\b(\d{6})\b', text or "")
            if match:
                return match.group(1)
    except Exception as e:
        print(f"  [Messages read error: {e}]")
    return None


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

EVENT_CODES = {
    "IAF":  "Initial filing accepted",
    "FTA0": "Biometrics appointment completed",
    "RFE":  "Request for Evidence issued",
    "RFES": "Response to RFE received",
    "APRD": "Approved",
    "DNID": "Denied",
    "INTV": "Interview scheduled",
}

def format_output(data):
    case = data.get("data", data)
    lines = [
        "=" * 55,
        f"USCIS Case: {case.get('receiptNumber', RECEIPT_NUMBER)}",
        f"Form:       {case.get('formType', '')} -- {case.get('formName', '')}",
        "=" * 55,
    ]

    lines.append(f"Filed:        {case.get('submissionDate', 'N/A')}")
    lines.append(f"Last updated: {case.get('updatedAt', 'N/A')}")
    lines.append(f"Action required: {'YES' if case.get('actionRequired') else 'No'}")
    lines.append(f"All stages complete: {'Yes' if case.get('areAllGroupStatusesComplete') else 'No'}")

    notices = case.get("notices", [])
    if notices:
        lines.append(f"\nNotices ({len(notices)}):")
        for n in notices:
            lines.append(f"  {n.get('actionType', '')} -- {n.get('appointmentDateTime', n.get('generationDate', ''))}")

    evidence = case.get("evidenceRequests", [])
    if evidence:
        lines.append(f"\nEvidence Requests ({len(evidence)}):")
        for e in evidence:
            lines.append(f"  {e}")

    events = case.get("events", [])
    if events:
        lines.append(f"\nEvents ({len(events)}, most recent first):")
        for evt in sorted(events, key=lambda x: x.get("eventTimestamp", ""), reverse=True):
            code = evt.get("eventCode", "")
            desc = EVENT_CODES.get(code, code)
            date = evt.get("eventDateTime", "")
            lines.append(f"  {date}  {desc}")

    lines.append("\n--- Full JSON ---")
    lines.append(json.dumps(data, indent=2))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def get_credentials():
    email    = os.environ.get("USCIS_EMAIL")
    password = os.environ.get("USCIS_PASSWORD")
    if not email:
        email = input("USCIS email: ").strip()
    if not password:
        password = getpass.getpass("USCIS password: ")
    return email, password


def main():
    if not RECEIPT_NUMBER:
        print("Error: set USCIS_RECEIPT_NUMBER in your .env file (e.g. IOE1234567890)")
        return

    email, password = get_credentials()

    # Step 1: WAF token via headless browser
    seed_cookies = asyncio.run(get_waf_token())

    # Step 2: requests session, pre-loaded with WAF + seed cookies
    session = requests.Session()
    session.headers.update(BASE_HEADERS)
    for name, value in seed_cookies.items():
        session.cookies.set(name, value, domain="myaccount.uscis.gov")

    # Step 3: GET sign-in page to seed CSRF
    print("Fetching sign-in page...")
    resp       = session.get(SIGN_IN_PAGE)
    match      = re.search(r'<meta name="csrf-token" content="([^"]+)"', resp.text)
    csrf_token = match.group(1) if match else ""

    # Step 4: Sign in
    print("Signing in...")
    resp = session.post(
        SIGN_IN_API,
        json={"email": email, "password": password},
        headers={"Content-Type": "application/json", "Referer": SIGN_IN_PAGE, "X-CSRF-Token": csrf_token},
    )
    if resp.status_code != 200:
        print(f"Sign-in failed: HTTP {resp.status_code}\n{resp.text[:500]}")
        return

    auth = resp.json()
    if auth.get("authentication_state") != "awaiting_two_factor":
        print(f"Unexpected auth state: {auth}")
        return

    xcsrf = auth["xcsrf"]
    print(f"SMS sent to {auth.get('mobile', '???')}")

    # Step 5: Wait for OTP
    print("Waiting for SMS code (up to 45s)...")
    otp = None
    for attempt in range(15):
        time.sleep(3)
        otp = read_otp_from_messages(max_age_seconds=90)
        if otp:
            print(f"Got OTP from Messages: {otp}")
            break
        print(f"  Waiting... ({(attempt + 1) * 3}s)")

    if not otp:
        otp = input("Could not auto-read OTP. Enter manually: ").strip()

    # Step 6: Submit OTP
    print("Submitting OTP...")
    resp = session.post(
        OTP_API,
        json={"verification_code": otp, "remember_me": False, "current2fa": ""},
        headers={"Content-Type": "application/json", "Referer": f"{BASE_URL}/auth", "X-CSRF-Token": xcsrf},
    )
    if resp.status_code != 200:
        print(f"OTP failed: HTTP {resp.status_code}\n{resp.text[:500]}")
        return

    print("Authenticated.")

    # Step 7: Bridge to my.uscis.gov via SAML redirect
    print("Establishing my.uscis.gov session...")
    session.get("https://my.uscis.gov/account/applicant", allow_redirects=True, headers={
        "Accept": "text/html,application/xhtml+xml,*/*",
        "Referer": f"{BASE_URL}/dashboard",
    })

    # Step 8: Fetch case status
    print("Fetching case status...")
    resp = session.get(
        CASE_API,
        headers={"Accept": "application/json, text/plain, */*", "Referer": "https://my.uscis.gov/account/applicant"},
    )

    if resp.status_code == 200 and "application/json" in resp.headers.get("Content-Type", ""):
        print("\n" + format_output(resp.json()))
    else:
        print(f"Case API returned HTTP {resp.status_code}\n{resp.text[:300]}")


if __name__ == "__main__":
    main()
