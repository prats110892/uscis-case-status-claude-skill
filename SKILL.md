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

### ⚠️ Read this before interpreting anything

**This API has no plain-English status field.** The authoritative status string ("Case Approved", "New Card Is Being Produced") exists only on the my.uscis.gov web page. The script derives a headline from event codes instead, which is the best the API allows. **Always tell the user to confirm on the portal.**

**These JSON fields are unreliable. Do not read them as evidence:**

| Field | Why you can't trust it |
|-------|------------------------|
| `closed` | Lags approval by days. Observed `false` for 4 days after a confirmed approval. |
| `notices[]` | May never populate. On a real approved I-485 it contained only a biometrics appointment from 9 months earlier — the I-797 approval notice never appeared at all. |
| `documents[]` | Frequently empty even on approved cases. |
| `areAllGroupStatusesComplete` | Observed `false` on a case that was approved *and* had its card produced. Effectively noise. |

**Event codes are the only reliable signal in this payload.** An empty `notices[]` is an unpopulated channel, not evidence that nothing happened.

**Backdating:** events carry both `createdAt` (when USCIS wrote the row) and `eventDateTime` (the date USCIS assigns it). These often differ by months. `createdAt` is what tells you when something actually happened. The script flags backdated rows.

**Silent updates matter.** `updatedAtTimestamp` can move with no new event. On a real case, three such silent touches each turned out to be real adjudicative activity (a field-office transfer, an officer review) that never surfaced as an event. Treat a moved timestamp with no new event as meaningful, not noise.

**Calling USCIS surfaces things the API hides.** A contact-center agent disclosed a field-office transfer and an interview waiver that were completely invisible in the JSON. If a user is stuck with no visible movement, suggest calling.

### Event codes

The script decodes these and prints plain-English meanings with confidence tags. Key ones:

| Code | Meaning | Confidence |
|------|---------|-----------|
| `H008` | **APPROVED** | verified |
| `LDA` | Card produced | verified |
| `FTA0` | Database checks received (**not** biometrics) | indexed |
| `IAF` | Receipt letter emailed (**not** initial filing accepted) | indexed |
| `FSA0` | Database checks requested | indexed |
| `FT0` | Officer processing begun | indexed |
| `MA70` | Biometrics received from ASC | indexed |
| `DA` `DB` `IEA` `IEE` `IEC` `APRD` | Approval family | family |
| `LAA` `LBA` `LEA` `LFA` | Card production family | family |
| `RFE` `DNID` `FBA` `IK` `II` `EA` `IFA` | RFE / denial | mixed |
| `BC` `BA` `FS` `FR` `KH` | Transfer or hold | family |

**`H008` is the one to know.** A widely-cited public code index glosses it as "Biometrics Reused." That is wrong in practice — on a real I-485, two H008 events posted and the my.uscis.gov portal read "Case Approved" the same day. **Do not tell a user their case is pending just because you don't see `APRD`.**

Confidence tags matter: `indexed` and `family` meanings are best guesses, not established fact. Say so when it affects the conclusion.

### Then summarize

- Lead with the derived status, and say plainly that it's derived and should be confirmed on the portal
- `actionRequired: true` → flag prominently at the top
- Events most-recent-first, using the decoded meanings the script prints, noting which are backdated
- Respect the confidence tags: `[indexed]` and `[family]` meanings are best guesses, not facts. Say so.
- If still pending: what typically comes next, and whether the gap looks normal or stuck
- For employment-based cases, check whether the priority date is current against the visa bulletin — an approval can be gated on visa number availability rather than adjudication speed

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
