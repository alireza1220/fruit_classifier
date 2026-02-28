# Bot Join Verification: Meeting SDK vs Zoom Agents

Verification of whether a bot can join Zoom calls, what this app can do, and when to use Zoom Agents instead.

---

## 1. Can a Bot Join a Zoom Call?

**Yes — for Zoom Meetings.**

| Zoom Product | Bot Can Join? | How |
|--------------|---------------|-----|
| **Zoom Meeting** | ✅ Yes | Zoom Meeting SDK for Linux (headless bot) |
| **Zoom Contact Center** | ⚠️ Different | Contact Center API; no meeting ID; different flow |
| **Zoom Webinar** | ✅ Yes (with SDK) | Meeting SDK supports webinars |

---

## 2. How Bot Join Works (Zoom Meeting)

**Official Zoom approach:**

1. **Meeting SDK** — Zoom’s Meeting SDK for Linux lets you run a headless bot that joins meetings.
2. **Join token** — Use the REST API `/meetings/:meetingId/jointoken/local_recording` to get a local recording token.
3. **Join flow** — The bot uses the token with the SDK to join as a participant with recording.

**Zoom docs:** [Meeting Bots: Accessing Media Streams](https://developers.zoom.us/docs/zoom-apps/guides/meeting-bots-sdk-media-streams/)

**Sample:** [meetingsdk-headless-linux-sample](https://github.com/zoom/meetingsdk-headless-linux-sample)
- Runs in Docker
- Uses Meeting SDK for Linux
- Config-driven (meeting ID, token, etc.)

---

## 3. What This App Can Do Today

| Capability | Status | Notes |
|------------|--------|-------|
| Receive webhooks | ✅ Implemented | `meeting.started`, `meeting.ended`, participant events |
| Whitelist check | ✅ Implemented | Meeting ID, host email |
| Get OAuth token | ✅ Implemented | Server-to-Server OAuth |
| Get meeting details | ✅ Implemented | `GET /meetings/:id` |
| Get join token | ✅ Implemented | `GET /meetings/:id/jointoken/local_recording` |
| **Actually join** | ❌ Not implemented | Requires Meeting SDK for Linux |

**Current state:** The app fetches the join token and logs it. The actual join is done by the **Zoom Meeting SDK for Linux** binary, which is not integrated yet.

**To complete:**  
Integrate the [Zoom Meeting SDK for Linux](https://github.com/zoom/meetingsdk-headless-linux-sample) (e.g. via Docker) and pass it the join token from this app when a whitelisted meeting starts.

---

## 4. Zoom Agents vs Meeting Bot

| Aspect | Zoom Virtual Agent (ZVA) | This App (Meeting Bot) |
|--------|-------------------------|-------------------------|
| **Role** | Handles calls directly | Joins calls to record/transcribe |
| **Use case** | First-line AI support | Recording and transcription |
| **When it joins** | N/A — it answers the call | After meeting starts (webhook) |
| **Product** | Zoom Contact Center add-on | Custom app using Meeting SDK |
| **Customer** | Talks to AI first | Talks to humans; bot is silent |

**Zoom Virtual Agent (ZVA)**  
- AI virtual agent that answers calls.
- Handles issues before escalation.
- Handoff to humans when needed.
- Not for recording/transcribing human conversations.

**This app (Meeting Bot)**  
- Bot joins as a participant.
- Records and transcribes.
- Generates summaries and action items.
- Does not replace humans.

---

## 5. When to Use Which

| Use case | Use |
|----------|-----|
| Record and transcribe Zoom Meetings | ✅ This app + Meeting SDK |
| AI first-line support for Contact Center | Zoom Virtual Agent |
| Record Contact Center calls | Contact Center APIs + Zoom recording/transcription |

---

## 6. Zoom Contact Center

Contact Center calls are different from Meetings:

- No meeting ID.
- Temporary sessions.
- Agent must accept.
- Different APIs and SDKs.

**This app does not support Contact Center.** It would need Contact Center–specific APIs and flows.

**How to do Contact Center:** See [ZOOM_CONTACT_CENTER_INTEGRATION.md](ZOOM_CONTACT_CENTER_INTEGRATION.md) for:
- Native recording (no bot needed) + Recordings API
- Contact Center webhooks and scopes
- Engagement ID vs meeting ID
- Implementation checklist

See also [USER_STORIES_CONTACT_CENTER.md](USER_STORIES_CONTACT_CENTER.md) for user stories.

---

## 7. Summary

| Question | Answer |
|----------|--------|
| **Can a bot join a Zoom call?** | Yes, for Zoom Meetings, via Meeting SDK for Linux. |
| **Can this app do that?** | Partially. It fetches the join token; the actual join is done by the Meeting SDK, which is not yet integrated. |
| **Should we use Zoom Agents?** | Use Zoom Virtual Agent if you want AI to handle calls. Use this app if you want a bot to join meetings to record and transcribe. |

---

## 8. Next Steps to Complete Bot Join

1. Download the Meeting SDK for Linux from the Zoom Developer Portal.
2. Use or adapt the [meetingsdk-headless-linux-sample](https://github.com/zoom/meetingsdk-headless-linux-sample).
3. When a whitelisted meeting starts, pass the join token from this app to the SDK container.
4. Run the SDK container so it joins the meeting and records the audio stream.

---

*Last updated: February 2025*
