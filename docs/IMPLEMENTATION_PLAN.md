# Instruction Bot — Implementation & Setup Guide

Clear guide for setting up the Zoom AI Meeting Bot (Instruction Bot): how it joins calls, required API keys, and whitelisting.

---

## 1. How Instruction Bot Joins Calls

### Overview

The bot **automatically joins** Zoom meetings when they start. It does **not** need to be invited. The flow is:

```
Meeting starts → Zoom sends webhook → Your server receives it → Bot joins (if whitelisted)
```

### Step-by-Step Join Flow

| Step | What Happens |
|------|--------------|
| 1 | Host starts a Zoom meeting |
| 2 | Zoom sends `meeting.started` webhook to your webhook URL |
| 3 | Your server receives the webhook (meeting ID, host ID, etc.) |
| 4 | **Whitelist check**: Is this meeting allowed? (see Section 3) |
| 5 | If **yes**: Get OAuth token → Get join token → Join via Meeting SDK |
| 6 | If **no**: Ignore; do not join |
| 7 | Bot appears as **"Instruction Bot (Recording)"** in the participant list |
| 8 | Bot stays until `meeting.ended` webhook |

### Technical Details

- **Join method**: Zoom Meeting SDK for Linux (headless) — the API gateway obtains the join token; the actual join is done by the Meeting SDK binary
- **Auth**: Server-to-Server OAuth (no user login)
- **Bot identity**: Appears as a normal participant; muted, no video
- **Compliance**: Display name includes "(Recording)" so participants know they are being recorded

### Implementation Note

This project's API gateway receives webhooks, checks the whitelist, and obtains the join token from Zoom. The **actual meeting join** requires the [Zoom Meeting SDK for Linux](https://github.com/zoom/meetingsdk-headless-linux-sample). You can run that SDK in a separate container and configure it with the join token from this service.

### What the Bot Needs to Join

| Item | Source |
|------|--------|
| Meeting ID | From webhook payload |
| Meeting passcode | Zoom API `GET /meetings/:id` (if required) |
| Join token | Zoom API `POST /meetings/:meetingId/jointoken/local_recording` |
| SDK credentials | Your Zoom app (Client ID, Client Secret) |

---

## 2. API Keys & Credentials Required

### Zoom (Required)

| Variable | Where to Get | Purpose |
|----------|--------------|---------|
| `ZOOM_ACCOUNT_ID` | Zoom Marketplace → Your App → App Credentials | Server-to-Server OAuth |
| `ZOOM_CLIENT_ID` | Same | App identification |
| `ZOOM_CLIENT_SECRET` | Same | OAuth token generation |
| `ZOOM_WEBHOOK_SECRET_TOKEN` | Zoom Marketplace → Feature → Webhooks → Secret Token | Verify webhook signatures |

**How to get them:**

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/)
2. Sign in → **Develop** → **Build App**
3. Create **Server-to-Server OAuth** app
4. Add **Meeting SDK** and **Webhooks** under Features
5. Copy credentials from **App Credentials** tab
6. Under **Webhooks**, set your Event notification endpoint URL and copy the Secret Token

### AI / Transcription (Required for full pipeline)

| Variable | Where to Get | Purpose |
|----------|--------------|---------|
| `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) | LLM summaries, action items |

### Optional (for production)

| Variable | Purpose |
|----------|---------|
| `DEEPGRAM_API_KEY` or `ASSEMBLYAI_API_KEY` | Streaming STT (if you add Live Call Assist later) |
| `DATABASE_URL` | PostgreSQL connection string |
| `REDIS_URL` | Message queue for pipeline |
| `STORAGE_*` | MinIO/S3 for audio files |

### Example `.env`

```env
# Zoom (required)
ZOOM_ACCOUNT_ID=xxxxxxxx
ZOOM_CLIENT_ID=xxxxxxxx
ZOOM_CLIENT_SECRET=xxxxxxxx
ZOOM_WEBHOOK_SECRET_TOKEN=xxxxxxxx

# Bot display name
ZOOM_BOT_DISPLAY_NAME=Instruction Bot (Recording)

# OpenAI (for summaries)
OPENAI_API_KEY=sk-xxxxxxxx

# Database (SQLite for dev, PostgreSQL for prod)
DATABASE_URL=sqlite:///./zoombot.db

# Optional: Redis
REDIS_URL=redis://localhost:6379
```

---

## 3. How to Whitelist Meetings

The bot joins **only** meetings that are whitelisted. All other meetings are ignored.

### Whitelist Methods

| Method | Use Case |
|--------|----------|
| **Meeting ID** | Specific meetings (e.g. `12345678901`) |
| **Host email** | All meetings hosted by `support@company.com` |
| **Host user ID** | All meetings by a Zoom user ID |
| **Recurring meeting ID** | A recurring meeting series |

### Configuration

#### Option A: Environment variable (simple)

```env
# Comma-separated meeting IDs
ZOOM_WHITELIST_MEETING_IDS=12345678901,98765432109

# Comma-separated host emails
ZOOM_WHITELIST_HOST_EMAILS=support@company.com,meetings@company.com
```

#### Option B: Database table (recommended for production)

```sql
CREATE TABLE whitelisted_meetings (
  id UUID PRIMARY KEY,
  meeting_id VARCHAR(50),      -- Zoom meeting ID (optional)
  host_email VARCHAR(255),      -- Host email (optional)
  host_user_id VARCHAR(50),    -- Zoom user ID (optional)
  created_at TIMESTAMP DEFAULT NOW()
);

-- Example: whitelist by meeting ID
INSERT INTO whitelisted_meetings (meeting_id) VALUES ('12345678901');

-- Example: whitelist by host email
INSERT INTO whitelisted_meetings (host_email) VALUES ('support@company.com');
```

#### Option C: Config file (`whitelist.yaml`)

```yaml
meeting_ids:
  - "12345678901"
  - "98765432109"
host_emails:
  - "support@company.com"
  - "meetings@company.com"
```

### Whitelist Logic (pseudocode)

```python
def is_whitelisted(meeting_id: str, host_email: str, host_id: str) -> bool:
    # Check meeting ID
    if meeting_id in whitelist.meeting_ids:
        return True
    # Check host email
    if host_email in whitelist.host_emails:
        return True
    # Check host user ID
    if host_id in whitelist.host_ids:
        return True
    return False
```

### Adding/Removing from Whitelist

| Method | How |
|--------|-----|
| **Env/Config** | Edit `.env` or `whitelist.yaml`, restart service |
| **Database** | `INSERT` / `DELETE` from `whitelisted_meetings` |
| **API** | `POST /admin/whitelist` and `DELETE /admin/whitelist/:id` (if implemented) |

---

## 4. Zoom App Setup Checklist

- [ ] Create Server-to-Server OAuth app at [marketplace.zoom.us](https://marketplace.zoom.us/)
- [ ] Enable **Meeting SDK** (for Linux)
- [ ] Enable **Webhooks**
- [ ] Add scopes: `meeting:read`, `meeting:write`, `user:read`
- [ ] Subscribe to events: `meeting.started`, `meeting.ended`, `meeting.participant_joined`, `meeting.participant_left`
- [ ] Set Event notification endpoint URL (e.g. `https://your-domain.com/webhooks/zoom`)
- [ ] Copy Account ID, Client ID, Client Secret, Webhook Secret Token
- [ ] *(Optional)* Request RTMS access for live audio streaming

---

## 5. Webhook Endpoint

Your server must expose a public URL for Zoom webhooks:

```
POST https://your-domain.com/webhooks/zoom
```

**Requirements:**

- HTTPS (Zoom requires SSL)
- Validates `x-zm-signature` header using `ZOOM_WEBHOOK_SECRET_TOKEN`
- Responds with `200 OK` quickly (process async)
- For local dev: use [ngrok](https://ngrok.com/) to expose `localhost`

---

## 6. Quick Reference

| Question | Answer |
|----------|--------|
| Does the bot need to be invited? | No — it joins automatically when a whitelisted meeting starts |
| Is it a plugin? | No — it's a server-side headless bot |
| How do I restrict which meetings it joins? | Use the whitelist (meeting IDs, host emails) |
| Where do I get Zoom credentials? | Zoom Marketplace → Create Server-to-Server OAuth app |
| What if I don't whitelist anything? | The bot will not join any meetings |
