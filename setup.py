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

def run(cmd, description, stream=False):
    """Run a shell command. stream=True shows live output for slow steps."""
    print(f"  {description}...")
    if stream:
        # Long downloads need visible progress or the installer looks hung.
        result = subprocess.run(cmd, shell=True, text=True)
        if result.returncode != 0:
            print(f"  ✗ Failed (exit {result.returncode})")
            sys.exit(1)
    else:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ✗ Failed: {result.stderr.strip()}")
            sys.exit(1)
    print("  ✓ Done")

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

    venv_dir = project_root / ".venv"
    if not venv_dir.exists():
        run(f"{sys.executable} -m venv {venv_dir}", "Creating virtual environment")

    venv_python = venv_dir / "bin" / "python3"
    run(f"{venv_python} -m pip install requests python-dotenv playwright -q",
        "Installing Python packages")
    run(f"{venv_python} -m playwright install chromium",
        "Downloading headless browser (one-time, ~150MB -- this takes a minute)",
        stream=True)

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

    # Make sure .env can never be committed. Create .gitignore if absent --
    # a project without one is exactly where credentials get pushed by accident.
    gitignore = project_root / ".gitignore"
    if gitignore.exists():
        content = gitignore.read_text()
        if ".env" not in content:
            gitignore.write_text(content.rstrip() + "\n.env\n")
    else:
        gitignore.write_text(".env\n")
        print("  ✓ Created .gitignore so .env is never committed")

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

    # Install SKILL.md from the file shipped alongside this installer, patching
    # in the real run command for this machine.
    #
    # Do NOT inline a copy of the skill text here. SKILL.md on disk is the single
    # source of truth for interpretation guidance -- duplicating it means the
    # installer silently ships stale instructions.
    skill_src = Path(__file__).parent / "SKILL.md"
    if not skill_src.exists():
        print("  ✗ SKILL.md not found next to setup.py.")
        print("    Unzip the whole folder (not just setup.py) and rerun.")
        sys.exit(1)

    skill_md = skill_src.read_text()

    # Replace the placeholder run command with the venv-aware absolute one.
    run_cmd = f'cd "{project_root}" && .venv/bin/python3 scripts/uscis_check.py'
    if "python3 /path/to/uscis_check.py" in skill_md:
        skill_md = skill_md.replace("python3 /path/to/uscis_check.py", run_cmd)
    else:
        print("  ! Could not find the run-command placeholder in SKILL.md.")
        print(f"    Verify the skill runs: {run_cmd}")

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
