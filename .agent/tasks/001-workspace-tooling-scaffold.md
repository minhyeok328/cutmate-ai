# Subagent Task Card: Workspace And Tooling Scaffold

## Activation

- Active workspace: `workspaces/cutmate-ai`
- Workspace profile: `.agent/profile.md`
- Task / Subtask: `001-workspace-tooling-scaffold`
- Role: Implementation Agent
- Workflow mode: Full Delivery, contract-first implementation

## Required Read Context

- `AGENTS.md`
- `docs/agent-rules/workspaces.md`
- `docs/agent-rules/subagent-execution.md`
- `docs/agent-rules/security-review.md`
- `workspaces/cutmate-ai/.agent/profile.md`
- `workspaces/cutmate-ai/.agent/specs/spec.md`
- `workspaces/cutmate-ai/.agent/contracts/api.md`
- `workspaces/cutmate-ai/.agent/contracts/data-model.md`
- `workspaces/cutmate-ai/.agent/contracts/analysis-pipeline.md`
- `workspaces/cutmate-ai/.agent/contracts/media-storage.md`
- `workspaces/cutmate-ai/.agent/contracts/worker-ownership.md`

## Allowed Write Scope

- `package.json`
- `pnpm-workspace.yaml`
- `tsconfig.base.json`
- `apps/web/**`
- `apps/api/**`
- `.env.example`
- app-local root config files required by the scaffold

## Read-Only Context

- `.agent/profile.md`
- `.agent/specs/**`
- `.agent/contracts/**`
- `.agent/tasks/**`
- `.gitignore`

## Forbidden Paths

- `docs/**`
- `workspaces/*` outside `workspaces/cutmate-ai`
- `.git/**`
- `.env`, `.env.local`, credentials, local databases, generated secrets
- `.cutmate/**`, uploaded media, generated outputs, model weights

## Mission

Create the initial CutMate AI app scaffold for a pnpm TypeScript monorepo with:

- `apps/web`: Next.js + React + TypeScript shell.
- `apps/api`: Python FastAPI backend shell.
- Local-first configuration surfaced through dummy `.env.example` values.
- Health/config endpoints and minimal tests that do not require real video files, real model weights, external APIs, or real env files.

## Acceptance Criteria

- Root package scripts exist for `dev`, `lint`, `typecheck`, `test`, and `build`.
- Frontend scaffold renders the actual CutMate AI product workspace, not a marketing landing page.
- Backend scaffold exposes safe health/config surfaces only.
- Backend config defaults match `.agent/profile.md` dummy env values.
- No source code reads real `.env` files directly.
- No scaffold writes generated media, DB files, model files, or `.cutmate/**`.
- No OpenAI API key is required or referenced for local quality mode.
- `gpt-oss-20b` is represented only as a local self-hosted model identifier.
- Tests cover at least frontend config constants and backend config/health behavior.

## Verification

Run from `workspaces/cutmate-ai`.

- `node --version`
- `python --version`
- If available: `pnpm --version`
- If available: `uv --version`
- If package tools are unavailable, do not install them. Report them as blocked.
- Run syntax-only checks that are available without dependency installation:
  - validate JSON package files
  - validate TOML with Python `tomllib`
  - compile Python files with `python -m py_compile`

## Stop Conditions

Stop and report if:

- implementation requires network access or installing dependencies
- implementation requires reading real `.env` files
- implementation requires files outside allowed write scope
- implementation requires changing app-local contracts
- implementation needs Git commands or Git metadata changes

## Output Required

- Status: Completed | Blocked | Needs Confirmation
- Changed files:
- Summary:
- Verification:
- Contract impact:
- Security impact:
- Assumptions:
- Follow-up required:
  - Git steward required: yes/no/Needs Confirmation
  - Suggested commit target: shell/active app/none/Needs Confirmation
