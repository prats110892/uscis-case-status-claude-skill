---
name: uscis-case-status
description: Check any USCIS case status from the command line -- auto-login, auto-OTP, returns structured case data
disable-model-invocation: false
user-invocable: true
---

## What this does

Runs a Python script that:
1. Solves the AWS WAF challenge headlessly (~3s)
2. Logs into myaccount.uscis.gov via API
3. Auto-reads the SMS OTP from Mac Messages
4. Fetches your case status from the USCIS API
5. Returns a plain-English summary with status, events, notices, and action items

## Run it

```bash
python3 /path/to/uscis_check.py
```

After the script completes, give a plain-English summary:
- Current status and what it means for this specific form type
- When it was last updated
- Most recent events in plain English (not just codes)
- Whether anything is required from the user
- What the next expected step typically is for this form type and stage
- If the case appears stuck, how long is normal to wait at this stage

If the script fails, diagnose and suggest a fix.

## Setup

**1. Install dependencies:**
```bash
pip install requests python-dotenv playwright
playwright install chromium
```

**2. Create a `.env` file next to the script:**
```
USCIS_EMAIL=your@email.com
USCIS_PASSWORD=yourpassword
USCIS_RECEIPT_NUMBER=IOE1234567890
```

**3. Mac only -- OTP auto-read:**
Go to System Settings > Privacy & Security > Full Disk Access and enable your terminal app. This lets the script read from Mac Messages to grab the SMS code automatically. If you skip this, the script will pause and ask you to type the code manually.

**4. Drop the files into your Claude Code project:**
- `uscis_check.py` → anywhere (update the path in SKILL.md to match)
- `SKILL.md` → `.claude/skills/uscis-case-status/SKILL.md`

**5. Run it:**
```
/uscis-case-status
```

## Notes
- Works for any USCIS receipt number -- I-485, I-130, I-765, I-131, I-90, N-400, etc.
- OTP auto-read requires macOS + iMessage with SMS forwarding enabled on iPhone
- If OTP auto-read fails, it falls back to manual entry -- still works
- No credentials are stored beyond your local `.env` file
