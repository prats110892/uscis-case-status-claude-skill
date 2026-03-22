# I built a Claude Code skill that checks your USCIS case status automatically

Tired of logging into myaccount.uscis.gov, doing 2FA, clicking around, and still not knowing what any of it means. So I built a Claude Code skill that handles the whole thing with one command.

---

## What it does

Type `/uscis-case-status` and Claude will:
- Log into myaccount.uscis.gov on your behalf
- Read the SMS verification code from Mac Messages automatically -- you don't touch anything
- Pull your case data from the USCIS API
- Explain what it all means in plain English: current stage, recent events, what's next, whether anything is stuck or needs your attention

Works for any receipt number -- I-485, I-130, I-765, I-131, I-90, N-400, EAD, whatever you're tracking.

Takes about 20 seconds start to finish.

---

## How to set it up

**You'll need:** macOS, Python 3, and [Claude Code](https://claude.ai/download)

1. Clone or download the repo: https://github.com/prats110892/uscis-case-status-claude-skill
2. Open Terminal, navigate to your Claude Code project folder
3. Run:
```bash
python3 /path/to/setup.py
```
4. It'll ask for your USCIS email, password, and receipt number -- that's it. Everything else is automatic.

After that, open Claude Code and type `/uscis-case-status`.

To uninstall, run `bash uninstall.sh` from the same folder.

---

## How it actually works

USCIS blocks plain HTTP clients with an AWS WAF JavaScript challenge. The script opens a headless (invisible) browser for about 3 seconds just to solve that challenge, grabs the auth cookie, then immediately closes. Everything else -- the login, the SMS code, fetching the case data -- is direct API calls, no browser involved.

There's also a quirk where USCIS uses two separate systems: `myaccount.uscis.gov` handles authentication and `my.uscis.gov` has the actual case data. They're linked via a SAML redirect that the script handles automatically.

Your credentials are saved in a local `.env` file and never leave your machine.

---

Happy to answer questions or help debug if something doesn't work for your setup.
