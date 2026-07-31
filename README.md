# USCIS Case Status — Claude Code Skill

Check any USCIS case from your terminal in about 20 seconds. Auto-login, auto-OTP, plain-English explanation of what your case data actually means.

Works for any receipt number: I-485, I-130, I-765, I-131, I-90, N-400, and so on.

---

## Requirements

- **macOS** (the OTP auto-read uses Mac Messages; everything else is cross-platform)
- **Python 3**
- **[Claude Code](https://claude.ai/download)**
- A myaccount.uscis.gov login with SMS 2FA

---

## Install

**Get the files** — either way works:

```bash
git clone https://github.com/prats110892/uscis-case-status-claude-skill.git
```

or download the ZIP (green **Code** button → **Download ZIP**, or grab it from
[Releases](https://github.com/prats110892/uscis-case-status-claude-skill/releases)) and unzip it.

**Run the installer from your Claude Code project root** — the folder where you
want the skill available, *not* the folder you just cloned:

```bash
cd /path/to/your/claude-code-project
python3 /path/to/uscis-case-status-claude-skill/setup.py
```

Then in Claude Code:

```
/uscis-case-status
```

To remove everything: `bash uninstall.sh` from the same project root.

### What the installer actually does

1. Creates a `.venv/` in your project and installs `requests`, `python-dotenv`, `playwright`
2. Downloads headless Chromium (~150MB, one time — used for ~3s per run to clear the WAF challenge)
3. Prompts for your USCIS email, password, and receipt number
4. Writes them to `.env` in your project root, and creates a `.gitignore` containing `.env` if you don't have one
5. Copies `uscis_check.py` to `scripts/`
6. Installs `SKILL.md` to `.claude/skills/uscis-case-status/`, patching in the correct venv Python path

> **Keep the folder intact.** `setup.py` reads `SKILL.md` from the directory next to it. If you move `setup.py` somewhere on its own it will stop and tell you.

### Manual install

If you'd rather not run the installer:

1. `pip install requests python-dotenv playwright && playwright install chromium`
2. Create `.env` in your project root — and make sure `.env` is gitignored:
   ```
   USCIS_EMAIL=your@email.com
   USCIS_PASSWORD=yourpassword
   USCIS_RECEIPT_NUMBER=IOE1234567890
   ```
3. Copy `uscis_check.py` to `scripts/`
4. Copy `SKILL.md` to `.claude/skills/uscis-case-status/SKILL.md`
5. Edit the run command in that `SKILL.md` — replace `python3 /path/to/uscis_check.py`
   with the actual path, e.g. `python3 scripts/uscis_check.py`

### Upgrading from an earlier version

Versions before this one shipped a bug: `setup.py` wrote its own inline copy of the
skill instead of installing `SKILL.md`, so it ignored the shipped interpretation
guidance. Among other things it treated `APRD` as the only approval code and would
report an **`H008`-approved case as still pending**.

Re-run `setup.py` to overwrite the installed skill. Your `.env` is preserved.

### OTP auto-read

System Settings → Privacy & Security → Full Disk Access → enable your terminal app. This lets the script read the SMS code from Messages. Requires SMS forwarding from your iPhone.

Skip it if you prefer — the script falls back to asking you to type the code.

---

## About your credentials

They're written to a local `.env` file on your machine and never sent anywhere except USCIS. It's your own account and the same login you'd do in a browser.

That said: **read the code before running it.** It's about 300 lines and deliberately boring. You should apply that standard to any tool asking for your USCIS password, this one included.

---

## What this tool can and can't tell you

**The USCIS case API has no plain-English status field.** The string you see on my.uscis.gov ("Case Approved", "New Card Is Being Produced") is not in the API response. This script derives a status from event codes instead. That's the best available, but **the portal is the authoritative source — always confirm there.**

**Several JSON fields are unreliable.** Observed on a real approved I-485:

| Field | Behavior |
|-------|----------|
| `closed` | Stayed `false` for 4 days after approval |
| `notices[]` | Never contained the approval notice at all |
| `documents[]` | Stayed empty throughout |
| `areAllGroupStatusesComplete` | Still `false` on an approved case with a printed card |

Event codes are the only reliable signal in the payload. An empty `notices[]` means the channel isn't populated, not that nothing happened.

**On event codes:** the map in `uscis_check.py` tags each meaning with a confidence level.

- `verified` — observed directly on a real case and cross-checked against the portal
- `indexed` — from a public ELIS code index, individually plausible
- `family` — the index groups these without per-code meanings, so the family is right but the specific gloss is a guess

Notably, **`H008` means approved.** A widely-circulated code index calls it "Biometrics Reused." On a real case, two H008 events posted and the portal read "Case Approved" the same day. Also corrected here: `FTA0` is database checks received (not biometrics), `IAF` is receipt letter emailed, `LDA` is card produced.

**Events are often backdated.** `createdAt` is when USCIS wrote the row; `eventDateTime` is the date they assign it. These can differ by months. `createdAt` is what tells you when something actually happened. The script flags backdated rows.

**Silent updates are real.** `updatedAtTimestamp` sometimes moves with no new event. On a real case, three such silent touches each turned out to be genuine activity — a field-office transfer and officer reviews — that never appeared as events.

**Call USCIS if you're stuck.** Contact-center agents can see a "last action" date and the responsible office. On a real case, a field-office transfer and an interview waiver were both disclosed by phone and never appeared in the API.

---

## Files

| File | Purpose |
|------|---------|
| `SKILL.md` | The Claude Code skill definition and interpretation guidance |
| `uscis_check.py` | The checker script (auth, WAF bypass, OTP, API call, formatting) |
| `setup.py` | One-time installer |
| `uninstall.sh` | Removes the skill, script, and credentials |

---

## How it works

USCIS blocks plain HTTP clients with an AWS WAF JavaScript challenge. The script opens a headless browser for ~3 seconds purely to solve that challenge and grab the token cookie, then closes it. Everything after that is direct API calls.

There's also a split-system quirk: `myaccount.uscis.gov` handles authentication while `my.uscis.gov` holds the case data. They're bridged by a SAML redirect, which the script follows automatically.

---

MIT licensed. Issues and PRs welcome:
https://github.com/prats110892/uscis-case-status-claude-skill
