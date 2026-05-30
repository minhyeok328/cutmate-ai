# Worker Ownership Contract

This contract defines how CutMate AI implementation work is split across agents.
It must be reviewed with the API, data-model, analysis-pipeline, and media-storage contracts before parallel product implementation begins.

## Active Workspace

- Active workspace: `workspaces/cutmate-ai`
- Workspace profile: `.agent/profile.md`
- Contract directory: `.agent/contracts`
- Workflow mode: Full Delivery, contract-first coordination
- Git steward: required before commit

## Global Rules

- Implementation workers must not run Git commands.
- Implementation workers must not edit `.git/**`, real env files, local DBs, uploaded media, generated outputs, model weights, or another worker's owned files.
- Workers must treat shell governance docs outside `workspaces/cutmate-ai` as read-only.
- Workers must not read `.env`, `.env.local`, or app-local env files with real values.
- Security-sensitive implementation must follow `.agent/contracts/media-storage.md` and the security checklist in `docs/agent-rules/security-review.md`.
- Shared behavior changes require contract updates before implementation proceeds.

## Implementation Slices

### Slice 1: Workspace And Tooling Scaffold

- Role: Implementation Agent
- Owns:
  - `package.json`
  - `pnpm-workspace.yaml`
  - `tsconfig.base.json`
  - `apps/web/**` scaffold only
  - `apps/api/**` scaffold only
  - `.env.example`
  - app-local root config files needed by the scaffold
- Does not own:
  - feature API endpoints beyond health/config stubs
  - real worker implementation
  - media-processing logic
  - generated files
- Must run or report:
  - `pnpm install`
  - `pnpm lint`
  - `pnpm typecheck`
  - `pnpm test`
  - `pnpm build`
  - `uv sync --project apps/api`
  - `uv run --project apps/api ruff check .`
  - `uv run --project apps/api pyright`
  - `uv run --project apps/api pytest`

### Slice 2: Backend API And SQLite Persistence

- Role: Backend + Database Implementation Agent
- Owns:
  - `apps/api/app/api/**`
  - `apps/api/app/db/**`
  - `apps/api/app/models/**`
  - `apps/api/app/schemas/**`
  - `apps/api/tests/api/**`
  - `apps/api/tests/db/**`
- Requires:
  - `.agent/contracts/api.md`
  - `.agent/contracts/data-model.md`
  - `.agent/contracts/media-storage.md`
- Does not own:
  - frontend UI
  - analysis algorithm internals
  - subprocess/model-runtime adapters
  - project root tooling
- Must stop if:
  - ownership/auth semantics differ from the contract
  - an endpoint needs a DTO or status not covered by the API contract
  - storage helper behavior is missing from the media contract

### Slice 3: Local Analysis Worker

- Role: Backend Worker Implementation Agent
- Owns:
  - `apps/api/app/analysis/**`
  - `apps/api/app/worker/**`
  - `apps/api/tests/analysis/**`
  - `apps/api/tests/worker/**`
- Requires:
  - `.agent/contracts/analysis-pipeline.md`
  - `.agent/contracts/media-storage.md`
  - `.agent/contracts/data-model.md`
- Does not own:
  - frontend UI
  - public API DTO changes unless contract-updated first
  - storage paths outside the storage helper
- Must stop if:
  - implementation needs shell command strings, `shell=True`, or user-controlled command interpolation
  - implementation needs arbitrary model download URLs
  - worker output requires API or DB fields not covered by contracts

### Slice 4: Frontend Review Workflow

- Role: Frontend Implementation Agent
- Owns:
  - `apps/web/src/**`
  - `apps/web/tests/**`
  - frontend-only fixtures under `apps/web/**`
- Requires:
  - `.agent/contracts/api.md`
  - `.agent/contracts/analysis-pipeline.md`
- Does not own:
  - backend endpoint behavior
  - DB schema
  - media storage paths
  - secrets or server-only env values
- Must stop if:
  - UI needs a new API field/status not covered by the API contract
  - UI would expose internal numeric thumbnail scores, raw local paths, stack traces, or raw tool errors

### Slice 5: QA Fixtures And Smoke Verification

- Role: QA/Test Implementation Agent
- Owns:
- `tests/**`
  - `fixtures/**`
  - `scripts/verify-*`
  - `apps/api/tests/integration/**`
  - `apps/web/tests/integration/**`
- Requires:
  - all app-local contracts
- Does not own:
  - production behavior changes unless assigned in a separate task card
  - generated large media files
- Must stop if:
  - sample media would be large or license-unclear
  - verification needs external network, paid API, GPU-only runtime, or real secrets

## Execution Order

1. Review and freeze app-local contracts.
2. Run Slice 1 workspace/tooling scaffold.
3. Run Slice 2 and Slice 3 after API/data/media/analysis contracts are stable.
4. Run Slice 4 after API DTOs and progress/event schema are stable.
5. Run Slice 5 once scaffold and first backend/frontend surfaces exist.

Parallel implementation is allowed only when write scopes do not overlap and shared contracts are already reviewed.

## Security Review Triggers

Assign a Security Review Agent when implementation touches:

- upload, download, generated files, local paths, or deletion
- SQLite schema, queries, migrations, or sensitive metadata
- subprocess calls, FFmpeg, model runners, dynamic imports, or external dependencies
- environment variables, `.env.example`, optional API keys, or model download configuration
- user-controlled text rendered in the UI, including subtitles, filenames, errors, and AI rationale

## Confirmed Decisions

- MVP max upload size is 2 GB (`2_147_483_648` bytes), with centralized validation so a future coordinated change can raise it.
- MVP starts as single-user local-first, while preserving `user_id` and ownership checks for future multi-user auth.
- CPU-only is supported for light/no-LLM mode; GPU or Apple Silicon is recommended for standard and quality modes.
- Model downloads are manual or explicit user-triggered allowlist downloads only.
