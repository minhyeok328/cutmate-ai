# Workspace Profile

This file defines the app-local execution context for agents working inside CutMate AI.

## Identity

- App name: CutMate AI
- App slug: cutmate-ai
- Active root: `workspaces/cutmate-ai`
- Profile owner: User + Codex
- Last reviewed: 2026-05-31

## Stack Snapshot

- Primary languages: TypeScript, Python
- Frontend framework: Next.js + React
- Backend framework: FastAPI
- Local worker/runtime: Python worker process launched by the app backend
- Database: SQLite for MVP local persistence
- Package managers: pnpm for TypeScript, uv for Python
- Runtime versions: Node.js 22 LTS, Python 3.12
- Important lockfiles:
  - `pnpm-lock.yaml`
  - `apps/api/uv.lock`
  - `apps/api/pyproject.toml`

## Commands

Run commands from the active root unless a command states otherwise.
Commands are expected to become available as the app scaffold is created.

| Purpose | Command | Required? | Notes |
| --- | --- | --- | --- |
| Install | `pnpm install` and `uv --cache-dir .uv-cache sync --project apps/api` | Yes | Do not install global dependencies. |
| Lint | `pnpm lint` and `uv --cache-dir .uv-cache run --project apps/api ruff check .` | Yes | Frontend and backend lint gates. |
| Unit tests | `pnpm test` and `uv --cache-dir .uv-cache run --project apps/api pytest` | Yes | Add focused tests before implementation changes. |
| Integration tests | `pnpm test:integration` and `uv --cache-dir .uv-cache run --project apps/api pytest tests/integration` | Yes | Required once API, worker, or file-processing flows exist. |
| Build | `pnpm build` | Yes | Must include Next.js production build. |
| Typecheck | `pnpm typecheck` and `uv --cache-dir .uv-cache run --project apps/api pyright` | Yes | Python typecheck may be adjusted if the backend chooses mypy. |
| Manual smoke | `pnpm dev` plus `uv --cache-dir .uv-cache run --project apps/api fastapi dev app/main.py` | Yes | Upload a small sample video, run local analysis, review recommendations, export output. |

## Environment

- Env example path: `.env.example`
- Dummy keys required:
  - `CUTMATE_APP_URL=http://localhost:3000`
  - `CUTMATE_API_URL=http://localhost:8000`
  - `CUTMATE_STORAGE_DIR=.cutmate/storage`
  - `CUTMATE_SQLITE_PATH=.cutmate/cutmate.db`
  - `CUTMATE_MODEL_DIR=.cutmate/models`
  - `CUTMATE_MAX_UPLOAD_BYTES=2147483648`
  - `CUTMATE_DEFAULT_LLM=Qwen/Qwen3-8B`
  - `CUTMATE_QUALITY_LLM=openai/gpt-oss-20b`
  - `CUTMATE_LLM_RUNTIME=ollama`
  - `CUTMATE_EXTERNAL_API_MODE=disabled`
- Real env files agents must not read:
  - `.env`
  - `.env.local`
  - `apps/web/.env`
  - `apps/web/.env.local`
  - `apps/api/.env`
  - `apps/api/.env.local`
- Secret policy:
  - Do not require an OpenAI API key for MVP local analysis.
  - `gpt-oss-20b` is a self-hosted local quality-mode LLM, not an OpenAI API model.
  - Example env values must remain dummy values only.

## Local AI Model Profile

- Core analysis must work without any LLM installed.
- Default local LLM: `Qwen/Qwen3-8B`
- Quality local LLM: `openai/gpt-oss-20b`
- LLM execution mode: self-hosted local inference, not OpenAI API.
- API key required for local quality mode: No.
- Supported runtime targets: Ollama first, LM Studio, llama.cpp, or vLLM later.
- LLM role:
  - recommendation rationale
  - subtitle cleanup
  - highlight and thumbnail explanation
  - user intent parsing
- LLM must not be the core decision-maker for cut or thumbnail candidate detection.
- No-LLM fallback: required.
- Cost note: model weights may be free to use under their licenses, but compute, storage, and hosting costs are user responsibility.

## Implementation Boundaries

Allowed implementation roots:

- `apps/web/**`
- `apps/api/**`
- `packages/**`
- `tests/**`
- `scripts/**`
- `.agent/contracts/**`
- `.agent/tasks/**`
- `.agent/plans/**`
- `.env.example`
- root project config files inside `workspaces/cutmate-ai/` required by the app scaffold

Forbidden paths:

- `.git/**`
- `.env`
- `.env.local`
- `apps/web/.env`
- `apps/web/.env.local`
- `apps/api/.env`
- `apps/api/.env.local`
- local databases such as `*.db`, `*.sqlite`, `*.sqlite3`
- generated model weights
- uploaded source videos
- exported videos or thumbnails
- `workspaces/*` outside `workspaces/cutmate-ai`
- shell governance docs outside the active workspace unless explicitly assigned

Generated or heavy paths to avoid:

- `.next/**`
- `node_modules/**`
- `.venv/**`
- `.ruff_cache/**`
- `.pytest_cache/**`
- `.cutmate/storage/**`
- `.cutmate/models/**`
- `.cutmate/tmp/**`
- `dist/**`
- `build/**`
- `coverage/**`

## Contracts

- Contract directory: `.agent/contracts`
- Active contract naming pattern: `<domain>-contract.md`
- Shared interface contracts required before parallel work:
  - API: required before frontend/backend parallel implementation
  - DB: required before database-backed API or worker implementation
  - Frontend/backend: required before UI integration with API responses
  - Infra: required before environment, runtime, model download, or packaging work

## Verification Notes

- Minimal smoke verification:
  - Start frontend and backend locally.
  - Upload or select a tiny sample video.
  - Confirm metadata extraction, analysis job creation, and no-LLM fallback recommendation output.
  - Confirm generated files stay under `.cutmate/**` and are not committed.
- Full verification:
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
  - `pnpm build`
  - `uv --cache-dir .uv-cache run --project apps/api ruff check .`
  - `uv --cache-dir .uv-cache run --project apps/api pyright`
  - `uv --cache-dir .uv-cache run --project apps/api pytest`
  - integration tests once API/worker/file-processing flows exist
- Known flaky or long-running checks:
  - full local video analysis with faster-whisper, OpenCLIP, or `gpt-oss-20b`
  - GPU-dependent model inference
  - large video render/export tests

## Git Pointer

This profile only records Git context. Load Git rules separately before commit, branch, push, or PR work.

- Git mode: active app
- Git root: `C:\MinHyeok\secret_agents\workspaces\cutmate-ai`
- Git steward: required before commit and push

## Agent Notes

- Local architecture notes:
  - Treat CutMate AI as a local-first app with a web UI and local analysis backend.
  - MVP max upload size is 2 GB (`2_147_483_648` bytes); keep the limit centralized so future plans can raise it without changing storage or API contracts broadly.
  - Keep video/audio analysis deterministic where possible: FFmpeg, faster-whisper, VAD/audio levels, PySceneDetect, OpenCV, and OpenCLIP before LLM rationale.
  - Do not send user video, audio, subtitles, thumbnails, or project metadata to an external API by default.
  - Use `gpt-oss-20b` only as an optional local quality mode.
- Known risks:
  - user-controlled file paths and uploaded video handling
  - shelling out to FFmpeg or model runtimes
  - large local files and model weights
  - slow CPU-only inference
  - accidental real env or generated artifact commits
- Open `Needs Confirmation` items:
  - official CPU-only support level vs. GPU/Apple Silicon recommendation
  - final Python typechecker choice: pyright vs. mypy
  - final model runtime priority after Ollama
