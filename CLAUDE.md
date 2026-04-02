# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Portal Pregões** is a SaaS platform that centralizes Brazilian government procurement opportunities (pregões) from PNCP (Portal Nacional de Contratações Públicas). This repository currently contains the PNCP sync worker; the Next.js application is planned per the SDD.

## Architecture

The system has two main layers:

1. **Sync Worker** (this repo) — Python service that continuously pulls data from the PNCP API and stores it in PostgreSQL. Runs every 15 minutes via a shell loop inside a Docker container.

2. **Next.js App** (planned per `docs/SDD.md`) — Next.js 15 with App Router, Prisma ORM, NextAuth.js v5, Tailwind CSS, shadcn/ui. Will use the same PostgreSQL database populated by the sync worker.

### Sync Worker Flow

`entrypoint.sh` → infinite loop → `sync.py` → PNCP API → PostgreSQL

The sync uses an incremental sliding-window approach:
- Tracks position in `sync_cursor` table (`last_data`, `last_page`)
- Scans backwards from today up to year 2021 (PNCP creation year)
- Fetches 20 records/API call (API max), processes 200 records/batch
- Upserts into `contratacoes` table using `ON CONFLICT (numero_controle_pncp)`
- Logs each run in `sync_log` table

## Commands

### Run sync worker locally
```bash
pip install -r requirements.txt
DATABASE_URL="postgresql://..." python sync.py
```

### Build and run Docker container
```bash
docker build -t portal-pregoes-sync:latest .
docker run -e DATABASE_URL="postgresql://..." portal-pregoes-sync:latest
```

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `DATABASE_URL` | Yes | PostgreSQL connection string |

## Database

PostgreSQL 17. Key tables managed by the sync worker:

- `contratacoes` — All procurement opportunities from PNCP (40+ columns + `raw_json` for full API response)
- `sync_cursor` — Tracks current sync position (`last_data`, `last_page`)
- `sync_log` — Audit log per sync run (timestamps, record counts, status)

The planned Next.js app will add: `usuarios`, `oportunidades`, `analises_tecnicas`, `cotacoes`, `propostas`, `filtros_salvos`.

## Key Files

- [sync.py](sync.py) — Core sync logic; `sync_batch()` is the main orchestrator
- [entrypoint.sh](entrypoint.sh) — Container loop runner (replaces crontab)
- [Dockerfile](Dockerfile) — Uses `python:3.12-slim`
- [docs/PRD.md](docs/PRD.md) — Product requirements and feature specs
- [docs/SDD.md](docs/SDD.md) — Full system design: DB schema, API endpoints, Next.js project structure

## Deployment

Deployed via **Dokploy Swarm**. The container runs as a long-lived service; logs go to stdout for Swarm log collection.

## PNCP API

Base URL: `https://pncp.gov.br/api/consulta/v1`  
Key endpoint: `GET /contratacoes/publicacao` — paginated, max 20 records/page, filters by `modalidade_id=6` (pregão eletrônico).  
Rate limiting: handled with 3 retries + 5s backoff on 429/network errors.
