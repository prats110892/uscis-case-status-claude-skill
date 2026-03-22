#!/usr/bin/env python3
"""
USCIS Case Status -- One-time setup script

Run this from your Claude Code project root:
  python3 setup.py

It will:
  1. Install required Python packages
  2. Install the headless browser (used once per run to bypass WAF)
  3. Ask for your USCIS login and receipt number
  4. Save credentials to .env (never committed)
  5. Install the /uscis-case-status skill into Claude Code
"""

import subprocess
import sys
import os
import getpass
from pathlib import Path

# ── Helpers ──────────────────────────────────────────────────────────────────

def run(cmd, description):
    print(f"  {description}...")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ✗ Failed: {result.stderr.strip()}")
        sys.exit(1)
    print(f"  ✓ Done")

def section(title):
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    project_root = Path.cwd()

    print()
    print("  USCIS Case Status Checker -- Setup")
    print("  This will take about 2 minutes.")

    # ── Step 1: Dependencies ──────────────────────────────────────────────────
    section("Step 1/4: Installing dependencies")
    run(f"{sys.executable} -m pip install requests python-dotenv playwright -q",
        "Installing Python packages")
    run(f"{sys.executable} -m playwright install chromium",
        "Downloading headless browser (one-time, ~150MB)")

    # ── Step 2: Credentials ───────────────────────────────────────────────────
    section("Step 2/4: Your USCIS account")
    print("""
  You'll need:
    - The email and password you use to log in at myaccount.uscis.gov
    - Your receipt number (starts with IOE, MSC, EAC, WAC, etc.)

  These are saved locally in a .env file and never leave your machine.
""")

    email = input("  USCIS account email: ").strip()
    while not email:
        email = input("  Please enter your email: ").strip()

    password = getpass.getpass("  USCIS account password: ")
    while not password:
        password = getpass.getpass("  Please enter your password: ")

    print()
    print("  Your receipt number is on your filing confirmation or any USCIS notice.")
    print("  Examples: IOE1234567890  /  MSC2190123456  /  EAC2112345678")
    receipt = input("  Receipt number: ").strip().upper()
    while not receipt:
        receipt = input("  Please enter your receipt number: ").strip().upper()

    # Write .env
    env_path = project_root / ".env"
    existing = env_path.read_text() if env_path.exists() else ""

    # Remove any existing USCIS lines and append fresh ones
    filtered = "\n".join(
        line for line in existing.splitlines()
        if not line.startswith("USCIS_")
    )
    new_content = filtered.rstrip() + f"""
USCIS_EMAIL={email}
USCIS_PASSWORD={password}
USCIS_RECEIPT_NUMBER={receipt}
"""
    env_path.write_text(new_content.lstrip())

    # Add .env to .gitignore if a .gitignore exists
    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" not in content:
            gitignore.write_text(content.rstrip() + "\n.env\n")

    print(f"  ✓ Credentials saved to .env")

    # ── Step 3: OTP setup ─────────────────────────────────────────────────────
    section("Step 3/4: SMS code (OTP) setup")
    print("""
  The script reads your USCIS verification code automatically from
  Mac Messages, so you don't have to type it in.

  To enable this:
    1. Open System Settings
    2. Go to Privacy & Security → Full Disk Access
    3. Enable your terminal app (Terminal, iTerm2, etc.)

  If you skip this, the script will just ask you to type the code
  manually when it arrives -- it still works either way.
""")
    input("  Press Enter when done (or just Enter to skip)...")

    # ── Step 4: Install Claude skill ──────────────────────────────────────────
    section("Step 4/4: Installing the Claude Code skill")

    skill_dir = project_root / ".claude" / "skills" / "uscis-case-status"
    skill_dir.mkdir(parents=True, exist_ok=True)

    scripts_dir = project_root / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Copy uscis_check.py to scripts/
    script_src = Path(__file__).parent / "uscis_check.py"
    script_dst = scripts_dir / "uscis_check.py"
    script_dst.write_text(script_src.read_text())

    # Write SKILL.md with the correct script path baked in
    skill_md = f"""---
name: uscis-case-status
description: Check any USCIS case status -- auto-login, auto-OTP, plain-English explanation
disable-model-invocation: false
user-invocable: true
---

## What this does

Runs a script that logs into USCIS, reads the SMS code from Mac Messages automatically,
fetches your case data, and returns it for interpretation.

## Run it

```bash
cd "{project_root}" && python3 scripts/uscis_check.py
```

After the script completes, give a plain-English explanation:
- What the current status means in human terms
- When it was last updated
- What each event means (translate codes: FTA0 = biometrics done, IAF = filing accepted, RFE = evidence requested, APRD = approved, INTV = interview scheduled)
- Whether any action is required from the user
- What typically happens next at this stage, and roughly how long it takes
- If the case looks stuck, say so clearly and what options exist (e.g. making an InfoPass appointment, filing a case inquiry)

If the script fails or exits with an error, diagnose and suggest a fix.
"""
    (skill_dir / "SKILL.md").write_text(skill_md)

    print(f"  ✓ Script installed at scripts/uscis_check.py")
    print(f"  ✓ Skill installed at .claude/skills/uscis-case-status/")

    # ── Done ──────────────────────────────────────────────────────────────────
    print(f"""
{'─' * 50}
  All done.

  Open Claude Code and type:
    /uscis-case-status

  That's it.
{'─' * 50}
""")


if __name__ == "__main__":
    main()
