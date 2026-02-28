# User Stories — Zoom Contact Center (Not Zoom Meeting)

User stories for the Instruction Bot when integrated with **Zoom Contact Center** instead of Zoom Meeting. The contact center flow differs: no meeting ID, temporary sessions, and agents must accept calls.

---

## Feature Comparison

| Feature | Zoom Meeting | Zoom Contact Center |
|---------|--------------|---------------------|
| Meeting ID | ✅ Yes | ❌ No |
| Password | ✅ Yes | ❌ No |
| Persistent Room | Sometimes | ❌ Never |
| Temporary Session | ❌ | ✅ Always |
| Agent Accept Button | ❌ | ✅ |

---

## User Stories

### 1. Customer Calls In

**As a** customer  
**I want to** call the contact center and be connected to an agent  
**So that** I can get help with my issue  

**Acceptance criteria:**
- Customer dials the contact center number
- Call enters queue or IVR
- System creates a temporary session (no meeting ID)
- Session exists only for the duration of the call

**Notes:** No meeting ID or password; the session is ephemeral.

---

### 2. Agent Accepts Call

**As a** contact center agent  
**I want to** see incoming calls and click "Accept" to join  
**So that** I can assist the customer  

**Acceptance criteria:**
- Agent sees incoming call notification
- Agent clicks "Accept" to join the call
- Call connects only after agent accepts
- Agent and customer are in the same temporary session

**Notes:** The bot cannot join until the agent has accepted. The "join" trigger is different from Zoom Meeting (no `meeting.started` with a meeting ID).

---

### 3. Bot Joins After Agent Accepts

**As a** contact center manager  
**I want to** the Instruction Bot to join the call automatically after the agent accepts  
**So that** we can transcribe and summarize support conversations  

**Acceptance criteria:**
- Bot joins the call only after agent has accepted
- Bot joins using Contact Center API (not Meeting SDK)
- Bot appears as a silent participant (or via SIP/barge-in if supported)
- Bot is visible to agent (e.g., "Recording in progress" indicator)

**Notes:** Trigger event is likely `call.agent_joined` or `session.started` instead of `meeting.started`. No meeting ID to whitelist; whitelist may be by queue, skill, or agent group.

---

### 4. Real-Time Transcription for Agent

**As a** contact center agent  
**I want to** see a live transcript of the conversation while I'm on the call  
**So that** I can reference what was said or catch details I may have missed  

**Acceptance criteria:**
- Transcript appears in real time during the call
- Speaker labels: Customer vs Agent
- Agent can view transcript in a side panel or overlay

**Notes:** Contact center calls are often shorter and more transactional; real-time support may be more valuable than post-call summary.

---

### 5. LLM Suggestions for Agent

**As a** contact center agent  
**I want to** receive AI-suggested responses based on what the customer said  
**So that** I can respond more quickly and consistently  

**Acceptance criteria:**
- As customer speaks, LLM suggests relevant responses
- Suggestions appear in agent UI (e.g., "You could say: ...")
- Agent can copy, adapt, or ignore suggestions
- Suggestions are based on FAQ, knowledge base, or conversation context

**Notes:** This aligns with the "Live Call Assist" feature we removed from Meeting flow—it may be more valuable for Contact Center.

---

### 6. Post-Call Summary and Notes

**As a** contact center agent  
**I want to** receive a summary and action items after the call ends  
**So that** I can complete follow-up tasks and update tickets  

**Acceptance criteria:**
- When call ends, transcript is finalized
- LLM generates summary, action items, decisions
- Agent receives summary in CRM or agent dashboard
- Summary is linked to the call/session (not meeting ID)

**Notes:** Session identifier is different (e.g., `session_id`, `interaction_id`) instead of `meeting_id`.

---

### 7. Whitelist by Queue or Skill

**As a** contact center administrator  
**I want to** whitelist which queues or skills the bot joins  
**So that** we only record and transcribe certain types of calls (e.g., support, not sales)  

**Acceptance criteria:**
- Configure whitelist by: queue name, skill name, agent group, or campaign
- Bot joins only calls that match whitelist
- No meeting ID—use queue/skill/session attributes

**Notes:** Whitelist logic differs from Meeting (no meeting ID).

---

### 8. Recording Disclosure

**As a** customer  
**I want to** be informed that the call is being recorded and transcribed  
**So that** I am aware of how my data is used  

**Acceptance criteria:**
- IVR or agent states: "This call may be recorded for quality and training"
- Bot presence is disclosed (e.g., "AI-powered transcription in use")
- Compliant with local recording consent laws

---

### 9. Browse Contact Center Recordings

**As a** supervisor or QA analyst  
**I want to** browse recordings and transcripts from contact center calls  
**So that** I can review agent performance and customer issues  

**Acceptance criteria:**
- List calls by date, agent, queue, or customer
- View transcript, summary, action items per call
- Filter by: date, agent name, queue, duration
- Play audio or download recording

**Notes:** Same Web UI as Meeting flow, but data model uses `session_id` / `interaction_id` instead of `meeting_id`.

---

### 10. Search Across Transcripts

**As a** contact center manager  
**I want to** search across all call transcripts  
**So that** I can find calls about specific topics or issues  

**Acceptance criteria:**
- Full-text search across transcripts
- Filter by date range, agent, queue
- Results show matching snippet and link to full call

---

## Summary: Key Differences from Zoom Meeting

| Aspect | Zoom Meeting | Zoom Contact Center |
|--------|--------------|---------------------|
| **Join trigger** | `meeting.started` | Agent accepts → `call.connected` or similar |
| **Session ID** | Meeting ID | Session ID / Interaction ID |
| **Whitelist** | Meeting ID, host email | Queue, skill, agent group |
| **Persistent** | Sometimes (recurring) | Never |
| **Real-time** | Optional | Often preferred (agent assist) |

---

## Implementation Notes

- Zoom Contact Center API and webhooks differ from Zoom Meeting API
- Contact Center SDK and events: [Contact Center Webhooks](https://developers.zoom.us/docs/api/contact-center/events/)
- Bot join may require: SIP integration, Contact Center API, or Zoom-provided recording/transcription add-on
- Verify with Zoom support for bot/recording integration options in Contact Center

---

*Last updated: February 2025*
