# Zoom AI Meeting Bot (Instruction Bot)

An AI-powered meeting bot that joins Zoom meetings, records audio, transcribes conversations, and generates summaries with action items and decisions.

## Quick Start

1. **Configure API keys** — Copy `.env.example` to `.env` and fill in your Zoom credentials
2. **Whitelist meetings** — Set `ZOOM_WHITELIST_MEETING_IDS` and/or `ZOOM_WHITELIST_HOST_EMAILS` in `.env`
3. **Run**:
   ```bash
   # Local
   pip install -r requirements.txt
   uvicorn src.main:app --reload --port 8000

   # Docker
   docker compose up
   ```
4. **Set webhook URL** — In Zoom Marketplace, set Event notification endpoint to `https://your-domain.com/webhooks/zoom` (use [ngrok](https://ngrok.com/) for local dev)

## Documentation

- **[Implementation Plan](docs/IMPLEMENTATION_PLAN.md)** — Setup guide: how the bot joins calls, API keys, whitelisting
- **[Full Architecture](docs/ZOOM_AI_MEETING_BOT_IMPLEMENTATION_PLAN.md)** — Detailed system design and phases

## Features

- Joins whitelisted Zoom meetings automatically when they start
- Records audio (mixed + per-speaker)
- Transcribes with speaker diarization
- LLM-generated summaries, action items, decisions
- Web UI to browse recordings and notes
