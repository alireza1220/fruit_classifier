# Zoom Contact Center Integration Guide

How to integrate with **Zoom Contact Center** (different from Zoom Meeting). Contact Center uses different APIs, webhooks, and concepts—no meeting ID, temporary sessions, and engagement-based flow.

---

## 1. Key Differences from Zoom Meeting

| Aspect | Zoom Meeting | Zoom Contact Center |
|--------|--------------|---------------------|
| **Session ID** | Meeting ID | Engagement ID / Interaction ID |
| **Trigger** | `meeting.started` | Engagement created / agent connected |
| **Recording** | Bot joins + records, or host records | Often built-in; access via Recordings API |
| **Auth** | Server-to-Server OAuth | Server-to-Server OAuth (Contact Center scopes) |
| **Webhooks** | `meeting.*`, `webinar.*` | `contact_center.*` events |

---

## 2. Zoom Contact Center APIs

### 2.1 Create a Contact Center App

1. Go to [Zoom Marketplace](https://marketplace.zoom.us/) → **Develop** → **Build App**
2. Create **Server-to-Server OAuth** app
3. Add **Contact Center** under Features
4. Request required scopes (see below)

### 2.2 Required Scopes

| Scope | Purpose |
|-------|---------|
| `contact_center:read:list_recordings:admin` | List recordings |
| `contact_center:read:list_engagements:admin` | List engagements (interactions) |
| `contact_center:read:engagement_recording_control:admin` | Recording control |
| `contact_center:read:engagement_recording_status:admin` | Recording status |
| `contact_center:read:engagement_transcripts:admin` | Access transcripts |

**Reference:** [Zoom Contact Center API](https://developers.zoom.us/docs/api/rest/reference/contact-center/methods/)

---

## 3. Two Approaches: Native Recording vs Bot

### Approach A: Use Zoom's Built-in Recording (Recommended)

Zoom Contact Center can record calls natively. You do **not** need a bot to join.

**Flow:**
1. Enable recording in Contact Center (admin settings)
2. Subscribe to Contact Center webhooks (e.g., engagement ended)
3. When engagement ends, call Recordings API to get the recording
4. Download recording/transcript and run your STT/summary pipeline

**Endpoints:**
- `GET /contact_center/recordings` — List recordings
- `GET /contact_center/recordings/transcripts/download` — Download transcript
- `GET /contact_center/engagements` — List engagements

**Reference:** [Contact Center Webhooks](https://developers.zoom.us/docs/api/contact-center/events/)

### Approach B: Bot Joins Call (If Native Recording Unavailable)

If you need a bot to join (e.g., no native recording, or custom capture):

- Contact Center uses **different media/join APIs** than Meeting SDK
- May require **SIP integration** or **Contact Center SDK**
- Check with Zoom for bot/third-party join options

**Reference:** [Using Zoom Contact Center with third-party AI Agent (Voicebot)](https://community.zoom.com/contact-center-15/using-zoom-contact-center-to-contact-to-a-third-party-ai-agent-voicebot-64466)

---

## 4. Integration Flow (Using Native Recording)

```
1. Customer calls → Contact Center creates engagement
2. Agent accepts → Call connected (engagement active)
3. Call ends → Zoom records (if enabled)
4. Webhook: engagement.ended (or similar)
5. Your app: GET /contact_center/recordings?engagement_id=xxx
6. Download recording/transcript
7. Run STT (if needed) → Summary → Store
```

---

## 5. Contact Center Webhooks

Subscribe to Contact Center events (exact names may vary; check [Contact Center Events](https://developers.zoom.us/docs/api/contact-center/events/)):

| Event (example) | When | Use |
|-----------------|------|-----|
| `engagement.created` | New interaction | Track start |
| `engagement.agent_joined` | Agent accepted | Call is live |
| `engagement.ended` | Call ended | Trigger recording fetch, run pipeline |

**Webhook URL:** Same pattern as Meeting webhooks; Zoom sends to your endpoint. Validate with `endpoint.url_validation` if required.

---

## 6. Data Model Mapping

| Zoom Meeting | Zoom Contact Center |
|--------------|---------------------|
| `meeting_id` | `engagement_id` / `interaction_id` |
| `meeting.started` | `engagement.agent_joined` or `engagement.connected` |
| `meeting.ended` | `engagement.ended` |
| Host | Assigned agent |
| Participants | Consumer (customer) + Agent |

---

## 7. Whitelist for Contact Center

No meeting ID. Whitelist by:

| Criteria | Example |
|----------|---------|
| Queue name | `support`, `sales` |
| Skill | `billing`, `technical` |
| Agent group | `tier1`, `tier2` |
| Campaign | Outbound campaign ID |

Use engagement metadata from webhooks or API to filter.

---

## 8. Implementation Checklist

- [ ] Create Zoom app with Contact Center feature
- [ ] Add Contact Center scopes
- [ ] Subscribe to Contact Center webhooks
- [ ] Implement webhook handler (validate signature, parse events)
- [ ] On `engagement.ended`: call Recordings API
- [ ] Download recording/transcript
- [ ] Run STT (if Zoom transcript insufficient) → Summary → Store
- [ ] Adapt Web UI to use `engagement_id` instead of `meeting_id`

---

## 9. Official Documentation

| Resource | URL |
|----------|-----|
| Contact Center API | https://developers.zoom.us/docs/api/rest/reference/contact-center/methods/ |
| Contact Center Events | https://developers.zoom.us/docs/api/contact-center/events/ |
| Contact Center Webhooks | https://developers.zoom.us/docs/api/rest/reference/contact-center/events/ |

---

## 10. Summary

| Question | Answer |
|----------|--------|
| **Do I need a bot to join?** | Usually no—use native Contact Center recording and Recordings API. |
| **Different from Meeting?** | Yes—engagement ID, different webhooks, different API endpoints. |
| **Same OAuth?** | Same app type (S2S OAuth), but Contact Center scopes and features. |
| **This app today?** | Built for Zoom Meeting. Contact Center needs a separate integration path. |

---

*Last updated: February 2025*
