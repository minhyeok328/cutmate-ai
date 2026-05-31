# CutMate AI MVP2-MVP4 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or targeted worker delegation for independent tasks. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the MVP1 upload foundation through reviewable analysis results, thumbnail selection, and local export jobs.

**Architecture:** Keep the local-first FastAPI backend as the source of truth for project state, persisted in SQLite and local workspace storage. Use deterministic worker modules first, with local LLM fields represented as metadata only until model execution is explicitly enabled.

**Tech Stack:** FastAPI, stdlib SQLite, FFmpeg/FFprobe subprocess calls with fixed argv, Next.js, React, TypeScript, Vitest, pytest, ruff, pyright.

---

## Current Baseline

- MVP1 foundation has upload validation, 2 GB size guard, FFprobe metadata extraction, SQLite project/job creation, and a web upload workspace.
- The current analysis job is queued only. No deterministic analysis result, timeline review, thumbnail, export, or metrics persistence exists yet.
- The API currently returns FastAPI default `detail.error` envelopes. MVP2 should add a small exception handler if endpoint expansion makes consistent client parsing necessary.

## File Ownership Map

- API routes: `apps/api/app/api/projects.py`, new `apps/api/app/api/media.py`, new `apps/api/app/api/exports.py`, and `apps/api/app/main.py`.
- Analysis worker: new `apps/api/app/analysis/` modules for deterministic subtitles, silence cuts, highlights, thumbnail frame requests, and result assembly.
- Export worker: new `apps/api/app/exporting/` modules for FFmpeg render/download job records.
- Database: `apps/api/app/db/schema.py`, `apps/api/app/db/repositories.py`, and targeted tests under `apps/api/tests/`.
- Web workspace: `apps/web/src/app/page.tsx`, `apps/web/src/app/globals.css`, and new focused helpers under `apps/web/src/lib/`.
- Environment structure: `.env.example` only. Never read or commit `.env`.

## MVP2: Analysis Results And Review

- [ ] Add SQLite tables for `analysis_results`, `subtitles`, `video_segments`, and `review_actions`.
- [ ] Add repository methods to persist and fetch analysis result snapshots with subtitles, cut candidates, and highlight candidates.
- [ ] Add deterministic worker module that can produce safe draft subtitles/cuts/highlights from metadata and optional transcript-like inputs without any LLM.
- [ ] Add API endpoints:
  - `POST /api/v1/projects/{project_id}/analysis/run`
  - `GET /api/v1/projects/{project_id}`
  - `GET /api/v1/projects/{project_id}/analysis`
  - `PATCH /api/v1/projects/{project_id}/segments/{segment_id}`
  - `PATCH /api/v1/projects/{project_id}/subtitles/{subtitle_id}`
- [ ] Update the web workspace to render analysis results, accept/reject candidate segments, and edit subtitle text against the API shape.
- [ ] Verification:
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
  - `pnpm build`
- [ ] Commit as focused MVP2 commits and push `codex/mvp-delivery`.

## MVP3: Thumbnail Candidates And Direct Frame Selection

- [ ] Add SQLite table for `thumbnail_candidates` and selected thumbnail fields.
- [ ] Add thumbnail storage helpers that keep generated images under `.cutmate/storage/thumbnails/<project_id>/`.
- [ ] Add deterministic thumbnail candidate worker:
  - Extracts real frames with FFmpeg when source media is available.
  - Uses a test fake for unit tests without real media.
  - Stores internal score only in the database and omits it from client responses.
- [ ] Add API endpoints:
  - `POST /api/v1/projects/{project_id}/thumbnails/generate`
  - `PATCH /api/v1/projects/{project_id}/thumbnails/{thumbnail_id}`
  - `POST /api/v1/projects/{project_id}/thumbnails/direct-frame`
  - `GET /api/v1/media/{asset_id}`
- [ ] Update the web workspace to show 3-5 candidates, select one, and request direct frame selection by timestamp.
- [ ] Verification:
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
  - `pnpm build`
- [ ] Commit as focused MVP3 commits and push `codex/mvp-delivery`.

## MVP4: Export Jobs, Metrics, And Cleanup

- [ ] Add SQLite tables for `export_jobs`, `metric_events`, and cleanup markers needed for failed-job log/file cleanup.
- [ ] Add export worker module:
  - Original aspect ratio copy/render path.
  - 9:16 center crop render path.
  - Subtitle inclusion option stored even if burn-in is deferred to a later rendering task.
  - Fixed FFmpeg argv, no shell.
- [ ] Add API endpoints:
  - `POST /api/v1/projects/{project_id}/exports`
  - `GET /api/v1/projects/{project_id}/exports/{export_job_id}`
  - `GET /api/v1/downloads/{asset_id}`
  - `POST /api/v1/metrics/events`
  - `POST /api/v1/maintenance/cleanup`
- [ ] Update the web workspace export panel to queue original or 9:16 export jobs, display render status, and surface download URLs.
- [ ] Verification:
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
  - `pnpm build`
- [ ] Commit as focused MVP4 commits and push `codex/mvp-delivery`.

## Security Review Checklist

- Do not expose raw local filesystem paths, storage refs, internal scores, raw stderr, prompts, or secrets in client responses.
- Resolve all file access through workspace-relative storage helpers.
- Use fixed subprocess argv arrays with `shell=False`.
- Keep `.env`, `.cutmate`, media files, local DBs, caches, and model files ignored.
- All user-controllable IDs in paths must be generated opaque IDs or validated against a strict safe-token regex.
- Public media and download endpoints must validate asset IDs and project ownership before returning files.
