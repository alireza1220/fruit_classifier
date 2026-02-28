# Zoom AI Meeting Bot — Full Implementation Plan

## Executive Summary

This document provides a comprehensive implementation plan for building an AI-powered meeting bot that joins Zoom meetings, captures audio via Real-Time Meeting Streaming (RTMS), transcribes conversations, and generates intelligent summaries with action items, decisions, and next steps.

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ZOOM AI MEETING BOT PIPELINE                         │
└─────────────────────────────────────────────────────────────────────────────┘

  Zoom Meeting Scheduled
           │
           ▼
  ┌─────────────────┐
  │  Webhook Event  │  meeting.started
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │   Bot Service   │  Joins meeting as "AI Note Taker (Recording)"
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  RTMS Service   │  Subscribes to audio.raw, audio.individual
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │  Audio Service  │  Buffers PCM → Assembles → Writes WAV files
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │   STT Service   │  WAV → Timestamped transcript (speaker + text)
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │ Summary Service │  Transcript → LLM → Summary, actions, decisions, risks
  └────────┬────────┘
           │
           ▼
  ┌─────────────────┐
  │     Storage     │  Database + Object Storage (audio, transcripts, summaries)
  └─────────────────┘
```

---

## 2. Architecture

### 2.1 Service Breakdown

| Service | Responsibility | Tech Stack | Port |
|---------|----------------|------------|------|
| **bot-service** | Join meetings via Zoom SDK, identify as recorder, trigger RTMS | Node.js/TypeScript or Python | 3001 |
| **rtms-service** | Receive RTMS WebSocket stream, forward audio chunks | Node.js (WebSocket) or Python | 3002 |
| **audio-service** | Reconstruct PCM chunks into WAV files (mixed + per-speaker) | Node.js or Python | 3003 |
| **stt-service** | Speech-to-text transcription (Whisper, AssemblyAI, or Zoom) | Python (Whisper) or Node.js | 3004 |
| **summary-service** | LLM-based meeting intelligence (summary, actions, decisions) | Python (LangChain) or Node.js | 3005 |
| **api-gateway** | REST API, webhooks, orchestration | Node.js (Express) or Python (FastAPI) | 3000 |
| **database** | PostgreSQL for meetings, transcripts, summaries | PostgreSQL 15 | 5432 |
| **object-storage** | MinIO or S3 for WAV files | MinIO/S3 | 9000 |

### 2.2 Communication Patterns

- **Synchronous**: REST for webhooks, API calls, service-to-service
- **Asynchronous**: Message queue (Redis/RabbitMQ) for pipeline stages
- **Real-time**: WebSocket for RTMS stream ingestion

### 2.3 Data Flow

```
Webhook (HTTP) → Bot Service → Zoom SDK
RTMS (WebSocket) → RTMS Service → Audio Service (via queue or direct)
Audio Service → Object Storage (WAV) + Event
Event → STT Service → Transcript
Transcript → Summary Service → LLM
All outputs → Database + Object Storage
```

---

## 3. Phase 1 — Zoom Setup

### 3.1 Create Server-to-Server OAuth App

1. **Zoom Marketplace**: https://marketplace.zoom.us/
2. **Create App** → Server-to-Server OAuth
3. **Basic Info**:
   - App name: `AI Meeting Bot`
   - Short description: `Joins meetings to record, transcribe, and summarize`
   - Company name, developer contact

### 3.2 Enable Required Features

| Feature | Purpose |
|---------|---------|
| **Meeting SDK** | Programmatic meeting join, bot presence |
| **RTMS (Real-Time Meeting Streaming)** | Live audio/video stream from meetings |

**Note**: RTMS requires explicit access request from Zoom. Submit via Zoom Developer Support or account representative.

### 3.3 OAuth Scopes

| Scope | Purpose |
|-------|---------|
| `meeting:read` | Read meeting details, participants |
| `meeting:write` | Create/update meetings, join as bot |
| `user:read` | User profile for bot identity |
| `recording:read` | (Optional) Access cloud recordings |
| `webhook` | Receive meeting lifecycle events |

### 3.4 Webhook Subscription

Subscribe to:

| Event | Use Case |
|-------|----------|
| `meeting.started` | Trigger bot join |
| `meeting.ended` | Finalize audio, trigger STT pipeline |
| `meeting.participant_joined` | Track participants |
| `meeting.participant_left` | Update participant list |

### 3.5 Environment Variables (Phase 1)

```env
ZOOM_ACCOUNT_ID=xxx
ZOOM_CLIENT_ID=xxx
ZOOM_CLIENT_SECRET=xxx
ZOOM_WEBHOOK_SECRET_TOKEN=xxx
ZOOM_BOT_USER_EMAIL=bot@yourdomain.com
```

### 3.6 Deliverables

- [ ] Zoom app created and approved
- [ ] RTMS access granted
- [ ] Webhook endpoint deployed and verified
- [ ] Credentials stored securely (e.g., AWS Secrets Manager, Vault)

---

## 4. Phase 2 — Bot Service

### 4.1 Responsibilities

- Receive `meeting.started` webhook
- Authenticate via Server-to-Server OAuth
- Join meeting using Zoom Meeting SDK or REST API
- Identify as **"AI Note Taker (Recording)"**
- Trigger RTMS session for the meeting
- Handle `meeting.ended` to leave gracefully

### 4.2 Join Flow

```
1. Webhook: meeting.started
2. Extract: meeting_id, host_id, join_url
3. Get OAuth token (Server-to-Server)
4. Call Zoom API: Start RTMS session (if available)
5. Join meeting via SDK/API as bot
6. Set display name: "AI Note Taker (Recording)"
7. Stay in meeting until meeting.ended
```

### 4.3 Bot Configuration

| Setting | Value |
|---------|-------|
| Display name | `AI Note Taker (Recording)` |
| Join as | Bot / Service account |
| Mute on join | Yes |
| Video off | Yes |
| Participant type | Recorder |

### 4.4 API Endpoints (Bot Service)

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/webhooks/zoom` | Receive Zoom webhooks |
| POST | `/meetings/:id/join` | Manual trigger to join meeting |
| GET | `/meetings/:id/status` | Bot join status |

### 4.5 Compliance

- **Visibility**: Bot appears in participant list
- **Disclosure**: Display name includes "(Recording)"
- **Consent**: Ensure meeting host/organization has recording consent policy

### 4.6 Deliverables

- [ ] Bot service deployed
- [ ] Webhook handler validates and processes events
- [ ] Bot successfully joins test meeting
- [ ] RTMS session initiated on join

---

## 5. Phase 3 — RTMS Stream Service

### 5.1 Responsibilities

- Establish WebSocket connection to Zoom RTMS
- Subscribe to audio streams:
  - `audio.raw` — mixed audio from all participants
  - `audio.individual` — per-participant audio tracks
- Forward PCM chunks to Audio Service
- Handle reconnection, backoff on failures

### 5.2 RTMS Stream Types

| Stream | Format | Use Case |
|--------|--------|----------|
| `audio.raw` | PCM 16kHz, 16-bit mono | Mixed meeting audio |
| `audio.individual` | PCM 16kHz, 16-bit mono per participant | Speaker-diarized audio |

### 5.3 Message Format (Expected)

```json
{
  "event": "audio.raw",
  "meeting_id": "xxx",
  "participant_id": "optional_for_individual",
  "timestamp": 1234567890,
  "payload": "<base64_encoded_pcm>"
}
```

*Actual format depends on Zoom RTMS API documentation.*

### 5.4 Processing Logic

```
1. Connect to RTMS WebSocket (auth via OAuth token)
2. Subscribe to audio.raw, audio.individual
3. On message:
   - Decode base64 PCM
   - Route to Audio Service (HTTP or message queue)
   - Include meeting_id, participant_id, timestamp
4. On meeting.ended: close connection, signal Audio Service to finalize
```

### 5.5 Deliverables

- [ ] RTMS service connects and subscribes
- [ ] PCM chunks forwarded to Audio Service
- [ ] Reconnection logic for dropped connections
- [ ] Graceful shutdown on meeting end

---

## 6. Phase 4 — Audio Service

### 6.1 Responsibilities

- Receive PCM audio chunks from RTMS Service
- Buffer chunks per meeting and per speaker
- Assemble into complete WAV files
- Write to Object Storage
- Emit event when audio is finalized (trigger STT)

### 6.2 Input Specification

| Parameter | Value |
|-----------|-------|
| Sample rate | 16 kHz |
| Bit depth | 16-bit |
| Channels | Mono |
| Format | PCM (raw) |

### 6.3 Processing Pipeline

```
Receive chunk → Validate meeting_id → Append to buffer
                                    → (mixed buffer)
                                    → (speaker_X buffer)
Meeting ended → Finalize all buffers → Convert to WAV → Upload to storage
                                    → Emit "audio_ready" event
```

### 6.4 Output Files

| File | Path | Description |
|------|------|-------------|
| Mixed | `/audio/{meeting_id}/mixed.wav` | All participants combined |
| Speaker A | `/audio/{meeting_id}/speaker_001.wav` | First speaker |
| Speaker B | `/audio/{meeting_id}/speaker_002.wav` | Second speaker |
| ... | ... | Per-participant tracks |

### 6.5 WAV Header

- Format: 16-bit PCM, 16kHz, mono
- RIFF header with correct chunk sizes

### 6.6 Deliverables

- [ ] Audio Service receives and buffers PCM
- [ ] WAV files generated correctly
- [ ] Files uploaded to Object Storage
- [ ] Event emitted for downstream STT

---

## 7. Phase 5 — Transcription Service (STT)

### 7.1 Responsibilities

- Consume "audio_ready" events
- Download WAV files from Object Storage
- Run Speech-to-Text (Whisper, AssemblyAI, or Zoom)
- Produce timestamped transcript with speaker labels
- Store in database

### 7.2 STT Options

| Provider | Pros | Cons |
|----------|------|------|
| **OpenAI Whisper** | High quality, self-hostable | CPU/GPU intensive |
| **AssemblyAI** | Speaker diarization built-in | Cost per minute |
| **Zoom** | Native integration | May require Zoom transcription add-on |
| **Deepgram** | Fast, real-time | API cost |

**Recommendation**: Start with **Whisper** (self-hosted or API) for MVP; consider AssemblyAI for production speaker diarization.

### 7.3 Transcript Schema

```json
{
  "meeting_id": "xxx",
  "segments": [
    {
      "speaker": "speaker_001",
      "start_time": 0.5,
      "end_time": 3.2,
  "text": "Let's discuss the Q4 roadmap."
    },
    {
      "speaker": "speaker_002",
      "start_time": 3.5,
      "end_time": 6.1,
      "text": "I think we should prioritize the API migration."
    }
  ]
}
```

### 7.4 Processing Flow

```
1. Receive event: { meeting_id, mixed_audio_path, speaker_audio_paths }
2. Download mixed.wav (or use speaker files for diarization)
3. Run STT:
   - Option A: Transcribe mixed, use speaker files for diarization
   - Option B: Transcribe each speaker file, merge by timestamp
4. Output: segments with speaker, start_time, end_time, text
5. Store in `transcripts` table
6. Emit "transcript_ready" event for Summary Service
```

### 7.5 Deliverables

- [ ] STT pipeline processes WAV files
- [ ] Transcripts stored with timestamps and speakers
- [ ] Event emitted for Summary Service

---

## 8. Phase 6 — Summary Service

### 8.1 Responsibilities

- Consume "transcript_ready" events
- Send full transcript to LLM
- Extract: summary, action items, decisions, risks, next steps
- Store in database

### 8.2 LLM Integration

| Provider | Model | Use Case |
|----------|-------|----------|
| OpenAI | GPT-4o / GPT-4o-mini | Summary, extraction |
| Anthropic | Claude 3.5 | Alternative |
| Local | Llama 3, Mistral | Self-hosted option |

### 8.3 Prompt Structure

```
You are a meeting analyst. Given the following transcript from a Zoom meeting,
produce a structured output:

1. **Summary**: 2-3 paragraph executive summary
2. **Action Items**: List of tasks with assignee (if mentioned) and due date (if mentioned)
3. **Decisions**: Key decisions made
4. **Risks**: Identified risks or concerns
5. **Next Steps**: Recommended follow-up actions

Transcript:
{transcript}
```

### 8.4 Output Schema

```json
{
  "meeting_id": "xxx",
  "summary": "The team discussed...",
  "action_items": [
    { "task": "Send proposal to client", "assignee": "John", "due": "2025-03-05" }
  ],
  "decisions": ["Approved Q4 budget increase"],
  "risks": ["Timeline may slip if design review is delayed"],
  "next_steps": ["Schedule follow-up for March 10"]
}
```

### 8.5 Deliverables

- [ ] Summary Service consumes transcript events
- [ ] LLM prompt produces structured output
- [ ] Results stored in `summaries` table
- [ ] API endpoint to retrieve summary by meeting_id

---

## 9. Phase 7 — Storage

### 9.1 Object Storage Layout

```
/audio/
  {meeting_id}/
    mixed.wav
    speaker_001.wav
    speaker_002.wav
    ...
```

### 9.2 Database Schema

#### `meetings`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| zoom_meeting_id | VARCHAR | Zoom's meeting ID |
| title | VARCHAR | Meeting topic |
| start_time | TIMESTAMP | When meeting started |
| end_time | TIMESTAMP | When meeting ended |
| host_id | VARCHAR | Zoom host user ID |
| participants | JSONB | List of participant IDs/names |
| status | VARCHAR | scheduled, in_progress, completed, failed |
| created_at | TIMESTAMP | Record creation |
| updated_at | TIMESTAMP | Last update |

#### `transcripts`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| meeting_id | UUID | FK to meetings |
| speaker | VARCHAR | speaker_001, etc. |
| start_time | FLOAT | Seconds from start |
| end_time | FLOAT | Seconds from start |
| text | TEXT | Transcript segment |
| created_at | TIMESTAMP | Record creation |

#### `summaries`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| meeting_id | UUID | FK to meetings |
| summary | TEXT | Executive summary |
| action_items | JSONB | Array of action items |
| decisions | JSONB | Array of decisions |
| risks | JSONB | Array of risks |
| next_steps | JSONB | Array of next steps |
| created_at | TIMESTAMP | Record creation |

#### `recordings`

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| meeting_id | UUID | FK to meetings |
| mixed_audio_path | VARCHAR | Path to mixed.wav |
| speaker_audio_paths | JSONB | Array of paths to speaker WAVs |
| duration_seconds | INT | Total duration |
| created_at | TIMESTAMP | Record creation |

### 9.3 Deliverables

- [ ] PostgreSQL schema created (migrations)
- [ ] Object Storage bucket configured
- [ ] All services write/read from storage correctly

---

## 10. Phase 8 — Workflow Orchestration

### 10.1 End-to-End Flow

```
1. Meeting starts
   └─> Webhook: meeting.started
       └─> Bot Service: Join meeting, start RTMS

2. Bot in meeting
   └─> RTMS Service: Receiving audio chunks
       └─> Audio Service: Buffering PCM

3. Meeting ends
   └─> Webhook: meeting.ended
       └─> Bot Service: Leave meeting
       └─> RTMS Service: Close connection
       └─> Audio Service: Finalize buffers → Write WAV → Upload → Emit "audio_ready"

4. Post-meeting pipeline
   └─> STT Service: audio_ready → Transcribe → Store transcript → Emit "transcript_ready"
   └─> Summary Service: transcript_ready → LLM → Store summary

5. Complete
   └─> All data in DB + Object Storage
   └─> API: GET /meetings/:id/summary
```

### 10.2 Error Handling

| Failure Point | Recovery |
|---------------|----------|
| Bot fails to join | Retry up to 3x; alert; mark meeting as failed |
| RTMS disconnect | Reconnect with backoff; if meeting ended, use partial audio |
| Audio buffer overflow | Chunk into segments; process partial |
| STT failure | Retry; fallback to raw transcript if available |
| LLM failure | Retry; store partial summary |

### 10.3 Idempotency

- Use `meeting_id` as idempotency key for pipeline stages
- Avoid duplicate transcripts/summaries for same meeting

---

## 11. Compliance

### 11.1 Bot Visibility

- Bot must appear in Zoom participant list
- Display name: **"AI Note Taker (Recording)"**
- No hidden or disguised participation

### 11.2 Recording Disclosure

- Display name explicitly indicates recording
- Consider: Zoom in-meeting notification when bot joins (if supported)
- Organization should have recording consent policy

### 11.3 Data Retention

- Define retention policy for audio and transcripts
- Support deletion requests (GDPR, etc.)
- Encrypt audio at rest

---

## 12. Deployment

### 12.1 Docker Compose (MVP)

```yaml
services:
  api-gateway:
    build: ./api-gateway
    ports: ["3000:3000"]
    environment:
      - DATABASE_URL
      - ZOOM_*
    depends_on: [postgres, redis]

  bot-service:
    build: ./bot-service
    environment:
      - ZOOM_*
      - REDIS_URL
    depends_on: [redis]

  rtms-service:
    build: ./rtms-service
    environment:
      - ZOOM_*
      - AUDIO_SERVICE_URL
    depends_on: [redis]

  audio-service:
    build: ./audio-service
    environment:
      - STORAGE_ENDPOINT
      - STORAGE_ACCESS_KEY
      - REDIS_URL
    depends_on: [minio, redis]

  stt-service:
    build: ./stt-service
    environment:
      - OPENAI_API_KEY
      - DATABASE_URL
      - STORAGE_*
    depends_on: [postgres, minio, redis]

  summary-service:
    build: ./summary-service
    environment:
      - OPENAI_API_KEY
      - DATABASE_URL
    depends_on: [postgres, redis]

  postgres:
    image: postgres:15
    volumes: [pgdata:/var/lib/postgresql/data]
    environment:
      POSTGRES_USER: zoombot
      POSTGRES_PASSWORD: secret
      POSTGRES_DB: zoombot

  redis:
    image: redis:7-alpine

  minio:
    image: minio/minio
    command: server /data
    volumes: [miniodata:/data]
```

### 12.2 Kubernetes (Production)

- Deploy each service as Deployment
- Use ConfigMaps/Secrets for env
- Ingress for API + webhooks
- Horizontal Pod Autoscaler for STT/Summary (CPU-bound)

### 12.3 Environment Variables (Full)

```env
# Zoom
ZOOM_ACCOUNT_ID=
ZOOM_CLIENT_ID=
ZOOM_CLIENT_SECRET=
ZOOM_WEBHOOK_SECRET_TOKEN=
ZOOM_BOT_USER_EMAIL=

# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/zoombot

# Redis (optional, for queue)
REDIS_URL=redis://redis:6379

# Object Storage (MinIO/S3)
STORAGE_ENDPOINT=http://minio:9000
STORAGE_ACCESS_KEY=
STORAGE_SECRET_KEY=
STORAGE_BUCKET=zoom-audio

# AI
OPENAI_API_KEY=

# Services (internal)
AUDIO_SERVICE_URL=http://audio-service:3003
STT_SERVICE_URL=http://stt-service:3004
SUMMARY_SERVICE_URL=http://summary-service:3005
```

---

## 13. Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|--------------|
| **Week 1** | Zoom setup + Bot | Zoom app, webhooks, bot joins meeting |
| **Week 2** | RTMS | RTMS service ingests audio stream |
| **Week 3** | Audio | WAV files saved to object storage |
| **Week 4** | Transcription | STT produces timestamped transcripts |
| **Week 5** | Summary + Storage | LLM summary, full pipeline, API |

### Milestone Checklist

- [ ] **M1 (Week 1)**: Bot joins test meeting, visible as "AI Note Taker (Recording)"
- [ ] **M2 (Week 2)**: RTMS delivers PCM chunks to Audio Service
- [ ] **M3 (Week 3)**: mixed.wav and speaker WAVs in object storage
- [ ] **M4 (Week 4)**: Transcript in database with speakers and timestamps
- [ ] **M5 (Week 5)**: Summary with actions, decisions, risks, next steps; GET /meetings/:id/summary works

---

## 14. MVP Success Criteria

| Criterion | Verification |
|-----------|---------------|
| ✔ Bot joins meeting | Bot appears in participant list with correct name |
| ✔ Audio saved | mixed.wav and speaker WAVs exist in storage |
| ✔ Transcript generated | Transcripts table has rows for meeting |
| ✔ Summary stored | Summaries table has row; API returns summary |

---

## 15. Future Enhancements

- **Real-time transcript**: Stream transcript as meeting progresses
- **Live summary**: Incremental summary during meeting
- **Integration**: Slack/Teams notifications with summary
- **Search**: Full-text search across transcripts
- **Analytics**: Meeting duration, participant engagement
- **Multi-language**: Support non-English meetings

---

## Appendix A: API Reference (Proposed)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /webhooks/zoom | Zoom webhook receiver |
| GET | /meetings | List meetings |
| GET | /meetings/:id | Meeting details |
| GET | /meetings/:id/transcript | Full transcript |
| GET | /meetings/:id/summary | Summary, actions, decisions |
| GET | /meetings/:id/recording | Recording metadata and download URLs |
| POST | /meetings/:id/join | Manual bot join trigger |

---

## Appendix B: References

- [Zoom Meeting SDK](https://developers.zoom.us/docs/meeting-sdk/)
- [Zoom Server-to-Server OAuth](https://developers.zoom.us/docs/internal-apps/s2s-oauth/)
- [Zoom Webhooks](https://developers.zoom.us/docs/api/rest/webhook-reference/)
- [Zoom RTMS](https://developers.zoom.us/docs/rtms/) *(request access)*
- [OpenAI Whisper](https://github.com/openai/whisper)
- [AssemblyAI](https://www.assemblyai.com/)

---

*Document version: 1.0*  
*Last updated: February 28, 2025*
