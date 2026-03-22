# I built a Claude Code skill that checks any USCIS case status -- one command, plain-English explanation

Tired of logging in, doing 2FA, and clicking around just to stare at a status you don't fully understand. Built a skill for Claude Code that does it in one command and actually tells you what's happening.

---

## What you get

Type `/uscis-case-status` in Claude Code and it:
- Logs into myaccount.uscis.gov automatically
- Reads the SMS verification code from Mac Messages -- you don't touch anything
- Fetches your case data from the USCIS API
- Claude explains what it all means: current stage, what happened, what's next, whether anything is stuck or requires action from you

Works for any receipt number -- I-485, I-130, I-765, I-131, I-90, N-400, EAD, whatever you're tracking.

Total time: ~20 seconds.

---

## Setup (one time)

**Requirements:** macOS, Python 3, [Claude Code](https://claude.ai/download)

1. Download the files from [link]
2. Open your terminal, navigate to your Claude Code project folder
3. Run:
```bash
python3 setup.py
```
4. Follow the prompts -- it asks for your USCIS email, password, and receipt number, then handles everything else automatically

After that, just open Claude Code and type `/uscis-case-status`.

---

## How it works (for the curious)

USCIS blocks plain API calls with an AWS WAF JavaScript challenge. The script spins up a headless (invisible) browser for ~3 seconds just to solve that, grabs the auth cookie, then closes it. Everything else -- login, OTP, fetching the case -- is direct API calls.

The auth also bridges two separate USCIS systems (`myaccount.uscis.gov` handles login, `my.uscis.gov` has the actual case data) via a SAML redirect that the script handles automatically.

Your credentials stay in a local `.env` file and never leave your machine.

---

Let me know if you run into issues. Happy to help debug.
