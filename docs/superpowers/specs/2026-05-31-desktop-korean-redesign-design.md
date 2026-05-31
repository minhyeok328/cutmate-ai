# CutMate AI Desktop Korean Redesign Design

## Summary

CutMate AI will move from a browser-first MVP into a desktop-app-oriented product while preserving the current Next.js frontend and FastAPI backend. The user experience will follow the selected A direction: a Vrew-inspired script-first editing workspace with a black liquid-glass visual style, Korean interface copy, and improved readability.

The first desktop delivery target is an unsigned macOS `.dmg` produced by GitHub Actions from the public `minhyeok328/cutmate-ai` repository. The Windows machine remains the development and test environment through `pnpm dev`. Apple Developer signing and notarization are intentionally deferred until a paid Apple Developer Program membership is available.

## Goals

- Redesign the main workspace into a Korean script-first editor that feels close to Vrew's text-based video editing concept.
- Improve readability through clearer hierarchy, larger Korean-friendly typography, stronger contrast, and fewer competing panels.
- Keep the app usable for one Korean end user without requiring them to open terminals or run servers manually.
- Add a cross-platform desktop structure that can run on macOS and remain testable on Windows.
- Add GitHub Actions automation that manually builds an unsigned macOS `.dmg` without automatic billing-prone runs on every push.
- Preserve the local-first privacy posture: videos, subtitles, thumbnails, and metadata remain local by default.

## Non-Goals

- No Apple Developer signing or notarization in the first pass.
- No Mac App Store distribution.
- No Windows installer build requirement in the first desktop pass, although the structure should not block it.
- No real faster-whisper, FFmpeg render, or model-bundling completion in this UI/desktop packaging pass.
- No external API upload of user media.

## User Flow

1. Developer works on Windows and runs `pnpm dev` for local testing.
2. User-facing UI opens as a Korean editing workspace.
3. The editor emphasizes video preview plus script/subtitle blocks, where each line can become an edit decision.
4. Upload, analysis, draft review, thumbnail choice, and export controls remain available, but labels and status text are Korean.
5. When a macOS build is needed, the developer manually starts a GitHub Actions workflow.
6. GitHub Actions runs on a macOS runner and uploads an unsigned `.dmg` artifact.
7. The recipient installs or opens the unsigned app with expected macOS security prompts.

## Requirements

- Frontend UI:
  - Use the selected A layout: left navigation, central video preview plus Korean script editor, right AI suggestion/action panel.
  - Use black liquid-glass styling with restrained translucency, crisp borders, and readable contrast.
  - Use Korean labels, statuses, empty states, and action text throughout the primary workspace.
  - Avoid marketing-page layout. The first screen must be the editing workspace.
  - Keep text within controls readable on desktop and mobile widths.

- Desktop architecture:
  - Prefer Tauri v2 as the desktop shell because it is lighter than Electron and can package macOS `.app`/`.dmg`.
  - Keep the existing web app as the UI source.
  - Keep the existing FastAPI backend as the local API source.
  - Design for a Python sidecar path later, likely via a macOS-built executable, so the final app can launch the API without a visible terminal.
  - For early desktop scaffolding, support both development mode against `localhost` and production mode against an app-managed local endpoint.

- GitHub Actions:
  - Add a manually triggered workflow for macOS builds using `workflow_dispatch`.
  - Avoid running macOS builds automatically on every push.
  - Keep artifact retention short.
  - Build unsigned artifacts first.
  - Leave signing/notarization secrets out of the workflow until paid membership is confirmed.

- Security and privacy:
  - Do not commit `.env`, credentials, Apple secrets, local databases, uploaded videos, generated thumbnails, or build artifacts.
  - Do not add real Apple account values to source.
  - Use GitHub Secrets only when signing is introduced later.

## Acceptance Criteria

- The main workspace UI is fully Korean for the primary workflow.
- The workspace visually follows the chosen black liquid-glass, script-first direction.
- Existing API-backed upload, analysis, subtitle, segment, thumbnail, and export controls still have reachable UI affordances.
- `pnpm lint`, `pnpm typecheck`, `pnpm test`, and `pnpm build` pass after UI changes.
- A desktop packaging scaffold exists without breaking browser development.
- A manual GitHub Actions macOS build workflow exists and does not run on every push.
- The workflow is documented as unsigned-first and safe to upgrade to signing later.

## Constraints

- Active workspace: `workspaces/cutmate-ai`.
- Workspace profile: `.agent/profile.md`.
- Contract location: `.agent/contracts`.
- Allowed write scope: app-local source, config, docs, scripts, and workflow files inside `workspaces/cutmate-ai`.
- Forbidden paths: `.env`, `.env.*` except `.env.example`, uploaded media, model weights, local databases, `.cutmate`, generated build outputs, and other workspaces.
- Git steward: required before commit and push.

## Risks

- Tauri plus Python sidecar packaging can be more complex than a pure web wrapper.
- macOS unsigned builds will still trigger security prompts for the recipient.
- GitHub Actions macOS minutes are free for public standard runners, but accidental automatic builds can waste runner time.
- Current API export/download behavior is still a scaffold, so a desktop shell can package the app before the real media engine is finished.
- Korean text may require typography and spacing QA beyond automated tests.

## Task Breakdown

1. Redesign and localize the web workspace.
2. Add desktop packaging scaffold with Tauri-oriented configuration.
3. Add manual macOS unsigned build workflow.
4. Document local dev and macOS artifact download steps.
5. Run verification and commit in logical slices.

## Verification

- `pnpm lint`
- `pnpm typecheck`
- `pnpm test`
- `pnpm build`
- Manual browser smoke test on Windows dev server.
- Workflow syntax review for GitHub Actions.
- When available, run the manual macOS workflow and confirm a `.dmg` artifact is produced.

## Security Review

Security review is required before implementation completes because the work touches packaging, GitHub Actions, future signing secrets, local process launch behavior, and user-controlled media paths. The first pass must verify that no real secrets are committed and that signing/notarization placeholders remain documented rather than hardcoded.
