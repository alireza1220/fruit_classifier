# Zoom AI Meeting Bot — Architecture

This document describes the system architecture for the Instruction Bot (Zoom AI Meeting Bot): components, data flow, technology choices, and deployment.

---

## 1. Overview

The system automatically joins whitelisted Zoom meetings, records audio, transcribes conversations, and generates AI summaries. Users browse recordings and notes via a web application.

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              EXTERNAL SYSTEMS                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Zoom Platform                                                                   │
│  ├── Webhooks (meeting.started, meeting.ended, participant_joined/left)          │
│  ├── REST API (OAuth, meetings, join tokens)                                     │
│  └── Meeting SDK for Linux (bot join) / RTMS (audio stream)                       │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              APPLICATION LAYER                                    │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                   │
│   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                       │
│   │   Web App   │────▶│  API Gateway│◀────│   Zoom      │                       │
│   │  (Next.js)  │     │  (FastAPI)   │     │  Webhooks   │                       │
│   │  Port 3000  │     │  Port 8000  │     │             │                       │
│   └─────────────┘     └──────┬──────┘     └─────────────┘                       │
│         │                    │                                                     │
│         │                    │  (Planned)                                         │
│         │                    ├──────────────▶ Bot Service (Meeting SDK)           │
│         │                    ├──────────────▶ RTMS Service                        │
│         │                    ├──────────────▶ Audio Service                        │
│         │                    ├──────────────▶ STT Service                         │
│         │                    └──────────────▶ Summary Service                     │
│         │                                                                          │
└─────────┼────────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                           │
├─────────────────────────────────────────────────────────────────────────────────┤
│  Database (PostgreSQL / SQLite)  │  Object Storage (MinIO / S3)                  │
│  meetings, transcripts,         │  /audio/{date}/{meeting_id}/*.wav               │
│  summaries, recordings          │  metadata.json                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Components

### 2.1 Implemented (Current)

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **API Gateway** | FastAPI (Python) | Webhook receiver, Zoom API client, whitelist logic, recordings API |
| **Web App** | Next.js 16, TypeScript, Tailwind | Recording list, meeting detail, transcript, summary display |
| **Config** | Pydantic Settings | Environment-based configuration |

### 2.2 Planned (Pipeline)

| Component | Technology | Responsibility |
|-----------|------------|----------------|
| **Bot Service** | Zoom Meeting SDK for Linux | Join meetings as bot, trigger RTMS |
| **RTMS Service** | WebSocket client | Receive real-time audio stream from Zoom |
| **Audio Service** | Python/Node | Buffer PCM, assemble WAV, upload to storage |
| **STT Service** | Whisper / AssemblyAI | Speech-to-text, speaker diarization |
| **Summary Service** | LangChain + OpenAI | LLM summaries, action items, decisions |

### 2.3 Infrastructure

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Database** | PostgreSQL (prod) / SQLite (dev) | Meetings, transcripts, summaries, recordings |
| **Object Storage** | MinIO / S3 | WAV files, metadata.json |
| **Message Queue** | Redis (optional) | Async pipeline events |

---

## 3. Data Flow

### 3.1 Meeting Lifecycle

```
1. Meeting starts
   Zoom ──webhook──▶ API Gateway
   API Gateway ──whitelist check──▶ Join if allowed
   API Gateway ──get join token──▶ Zoom REST API
   (Planned) Bot Service ──join──▶ Zoom Meeting SDK

2. During meeting
   (Planned) RTMS ──audio stream──▶ Audio Service
   (Planned) Webhooks ──participant_joined/left──▶ API Gateway (store participants)

3. Meeting ends
   Zoom ──webhook──▶ API Gateway
   (Planned) Audio Service ──finalize──▶ Object Storage
   (Planned) STT Service ──transcribe──▶ Database
   (Planned) Summary Service ──LLM──▶ Database

4. User browses
   Web App ──GET /recordings──▶ API Gateway ──▶ Database
   Web App ──GET /meetings/:id/summary──▶ API Gateway ──▶ Database
```

### 3.2 Request Flow (Web App)

```
Browser ──GET /recordings?date=2025-02-28──▶ API (port 8000)
API ──query──▶ Database (or mock)
API ──JSON──▶ Browser
Next.js ──render──▶ Recording list page
```

---

## 4. API Surface

### 4.1 Webhooks (Inbound)

| Endpoint | Method | Source | Purpose |
|----------|--------|--------|---------|
| `/webhooks/zoom` | POST | Zoom | Receive meeting lifecycle events |

### 4.2 REST API (Outbound)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | GET | Service info |
| `/health` | GET | Health check |
| `/admin/whitelist` | GET | Current whitelist config |
| `/recordings` | GET | List recordings (query: date, participant) |
| `/meetings/:id` | GET | Meeting details |
| `/meetings/:id/summary` | GET | Summary, action items, decisions |
| `/meetings/:id/transcript` | GET | Full transcript |
| `/meetings/:id/recording` | GET | Recording metadata, audio URLs |

---

## 5. Data Model

### 5.1 Core Entities

```
meetings
├── id (UUID)
├── zoom_meeting_id
├── title
├── start_time, end_time, call_date
├── host_id, host_name
├── status
└── created_at, updated_at

meeting_participants
├── id (UUID)
├── meeting_id (FK)
├── zoom_user_id
├── name
├── join_time, leave_time
└── speaker_track_index

transcripts
├── id (UUID)
├── meeting_id (FK)
├── participant_id (FK, nullable)
├── speaker_name
├── start_time, end_time
├── text
└── created_at

summaries
├── id (UUID)
├── meeting_id (FK)
├── summary
├── action_items (JSONB)
├── decisions (JSONB)
├── risks (JSONB)
├── next_steps (JSONB)
└── created_at

recordings
├── id (UUID)
├── meeting_id (FK)
├── call_date
├── storage_path
├── mixed_audio_path
├── participant_audio_paths (JSONB)
├── duration_seconds
├── participant_names (JSONB)
└── created_at
```

### 5.2 Object Storage Layout

```
/audio/
  {YYYY-MM-DD}/
    {meeting_id}/
      metadata.json
      mixed.wav
      {participant_name}.wav
```

---

## 6. Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **API** | FastAPI | Async, OpenAPI, type hints |
| **Web** | Next.js 16, TypeScript, Tailwind | SSR, App Router, fast iteration |
| **Database** | SQLite (dev) / PostgreSQL (prod) | SQLAlchemy-compatible |
| **Auth** | Zoom Server-to-Server OAuth | No user login; server-side only |
| **AI** | OpenAI (planned) | Summaries, action extraction |

---

## 7. Deployment

### 7.1 Docker Compose (Current)

```yaml
services:
  api:    # FastAPI, port 8000
  web:    # Next.js, port 3000
```

### 7.2 Full Stack (Planned)

```yaml
services:
  api
  web
  bot-service
  rtms-service
  audio-service
  stt-service
  summary-service
  postgres
  redis
  minio
```

### 7.3 Ports

| Service | Port | Protocol |
|---------|------|----------|
| API | 8000 | HTTP |
| Web App | 3000 | HTTP |
| PostgreSQL | 5432 | TCP |
| Redis | 6379 | TCP |
| MinIO | 9000 | HTTP |

---

## 8. Security

| Concern | Mitigation |
|---------|------------|
| **Webhook forgery** | Verify `x-zm-signature` with `ZOOM_WEBHOOK_SECRET_TOKEN` |
| **API keys** | Store in `.env`; never commit. Use secrets manager in prod. |
| **CORS** | API allows `*` for dev; restrict in production |
| **Recording disclosure** | Bot display name includes "(Recording)" |
| **Data at rest** | Encrypt object storage; define retention policy |

---

## 9. Whitelist Logic

The bot joins **only** whitelisted meetings. Configuration:

| Source | Format | Example |
|--------|--------|---------|
| Env | `ZOOM_WHITELIST_MEETING_IDS` | `12345678901,98765432109` |
| Env | `ZOOM_WHITELIST_HOST_EMAILS` | `support@company.com` |

Check order: meeting ID → host email → host user ID.

---

## 10. Related Documents

- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) — Setup guide: join flow, API keys, whitelisting
- [ZOOM_AI_MEETING_BOT_IMPLEMENTATION_PLAN.md](ZOOM_AI_MEETING_BOT_IMPLEMENTATION_PLAN.md) — Full implementation plan with phases

---

*Last updated: February 2025*
