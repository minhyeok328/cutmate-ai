# Desktop Korean Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Korean, script-first liquid-glass workspace and add a macOS unsigned desktop build path that can later grow into signed/notarized distribution.

**Architecture:** Keep the existing Next.js app as the UI, FastAPI as the local API, and add Tauri as the desktop shell. The first desktop pass launches a bundled Python API sidecar from the Tauri web layer when available, while browser development continues to use `pnpm dev`.

**Tech Stack:** Next.js 16, React 19, TypeScript, Vitest, FastAPI, uv, PyInstaller, Tauri v2, Rust, GitHub Actions.

---

## File Structure

- `apps/web/src/lib/workspace-copy.ts`: Korean UI copy, workflow labels, option labels, and status messages.
- `apps/web/src/lib/workspace-copy.test.ts`: Copy contract tests that prove the primary workspace is Korean and keeps the upload limit messaging.
- `apps/web/src/lib/desktop-runtime.ts`: Browser-safe helpers that detect Tauri and start the API sidecar only inside the desktop shell.
- `apps/web/src/lib/desktop-runtime.test.ts`: Unit tests for Tauri detection and no-op browser behavior.
- `apps/web/src/app/page.tsx`: Script-first Korean workspace layout and desktop sidecar startup hook.
- `apps/web/src/app/globals.css`: Black liquid-glass visual system, Korean-friendly readability, responsive layout.
- `apps/web/next.config.ts`: Static export support for Tauri production builds.
- `apps/web/package.json`: Add Tauri shell plugin dependency if the desktop runtime imports it.
- `apps/api/app/core/config.py`: Add desktop/Tauri allowed origins to CORS settings.
- `apps/api/app/desktop_sidecar.py`: PyInstaller entrypoint that starts the FastAPI app on `127.0.0.1:8000`.
- `apps/api/tests/test_config.py`: Test desktop CORS origins.
- `apps/api/tests/test_desktop_sidecar.py`: Test sidecar default environment and uvicorn launch parameters without starting the server.
- `apps/api/pyproject.toml` and `apps/api/uv.lock`: Add PyInstaller as a dev build dependency.
- `src-tauri/Cargo.toml`: Tauri Rust package manifest.
- `src-tauri/build.rs`: Tauri build script.
- `src-tauri/src/main.rs`: Minimal Tauri shell with the shell plugin.
- `src-tauri/capabilities/default.json`: Capability allowing the bundled API sidecar to spawn.
- `src-tauri/tauri.conf.json`: App metadata, static frontend path, DMG target, external sidecar config.
- `src-tauri/icons/`: Minimal icon assets if required by Tauri bundling.
- `.github/workflows/build-macos.yml`: Manual unsigned macOS `.dmg` workflow.
- `docs/desktop-build.md`: Korean operator guide for manual GitHub Actions build and unsigned macOS opening caveat.
- `package.json` and `pnpm-lock.yaml`: Root desktop scripts and Tauri CLI dependency.

## Task 1: Korean Workspace Copy Contract

**Files:**
- Create: `apps/web/src/lib/workspace-copy.ts`
- Create: `apps/web/src/lib/workspace-copy.test.ts`
- Modify: `apps/web/src/app/page.tsx`

- [ ] **Step 1: Write the failing copy contract test**

Create `apps/web/src/lib/workspace-copy.test.ts`:

```ts
import { describe, expect, it } from "vitest";

import { WORKSPACE_COPY, workflowSteps } from "./workspace-copy";

describe("workspace Korean copy", () => {
  it("keeps the primary workspace labels in Korean", () => {
    expect(WORKSPACE_COPY.appName).toBe("컷메이트 AI");
    expect(WORKSPACE_COPY.sections.script).toBe("대본 편집");
    expect(WORKSPACE_COPY.actions.runAnalysis).toBe("AI 분석 시작");
    expect(WORKSPACE_COPY.actions.render).toBe("내보내기 생성");
    expect(workflowSteps.map((step) => step.label)).toEqual([
      "업로드",
      "분석",
      "대본",
      "내보내기"
    ]);
  });

  it("keeps the MVP media limits visible to the user", () => {
    expect(WORKSPACE_COPY.upload.help).toContain("2GB");
    expect(WORKSPACE_COPY.upload.help).toContain("20분");
    expect(WORKSPACE_COPY.upload.help).toContain("MP4");
  });
});
```

- [ ] **Step 2: Run the test and verify it fails**

Run:

```powershell
$envRoot = 'C:\Users\MIN\miniconda3\envs\cutmate-ai'
$env:Path = "C:\Windows\System32;$envRoot;$envRoot\Library\bin;$envRoot\Scripts;$env:Path"
& "$envRoot\Library\bin\pnpm.bat" --filter @cutmate/web test -- src/lib/workspace-copy.test.ts
```

Expected: FAIL because `workspace-copy.ts` does not exist.

- [ ] **Step 3: Add the copy module**

Create `apps/web/src/lib/workspace-copy.ts`:

```ts
import type { AnalysisMode } from "./config";

export const WORKSPACE_COPY = {
  appName: "컷메이트 AI",
  productMark: "CutMate AI",
  tagline: "대본을 고치듯 영상 초안을 다듬는 로컬 편집 도우미",
  sections: {
    source: "소스 영상",
    preview: "미리보기",
    analysis: "분석 흐름",
    script: "대본 편집",
    suggestions: "AI 제안",
    thumbnails: "썸네일",
    export: "내보내기"
  },
  nav: {
    source: "영상",
    script: "대본",
    thumbnails: "썸네일",
    export: "내보내기"
  },
  upload: {
    title: "영상 가져오기",
    help: "MP4, MOV, M4V | 최대 20분 | 2GB까지 업로드",
    emptyFile: "영상을 선택해 주세요",
    selectedSuffix: "선택됨"
  },
  actions: {
    createProject: "프로젝트 만들기",
    runAnalysis: "AI 분석 시작",
    save: "저장",
    generate: "후보 만들기",
    chooseFrame: "프레임 선택",
    render: "내보내기 생성",
    applySelected: "선택 적용",
    settings: "설정"
  },
  status: {
    ready: "로컬 영상 업로드를 기다리고 있어요.",
    selectVideo: "분석할 영상을 먼저 선택해 주세요.",
    uploading: "로컬 작업공간으로 영상을 가져오는 중...",
    apiUnavailable: "로컬 API에 연결할 수 없어요.",
    analysisReady: "검토할 초안이 준비됐어요.",
    noDraft: "아직 생성된 대본/컷 후보가 없어요.",
    noThumbnails: "아직 썸네일 후보가 없어요.",
    renderDone: "로컬 내보내기 작업이 생성됐어요."
  },
  modeLabels: {
    fast: "빠른 분석",
    standard: "표준 분석",
    quality: "품질 분석"
  } satisfies Record<AnalysisMode, string>
} as const;

export const workflowSteps = [
  { key: "upload", label: "업로드" },
  { key: "analysis", label: "분석" },
  { key: "script", label: "대본" },
  { key: "export", label: "내보내기" }
] as const;
```

- [ ] **Step 4: Run the focused test and verify it passes**

Run the same command from Step 2.

Expected: PASS for `workspace-copy.test.ts`.

- [ ] **Step 5: Wire obvious copy imports without changing layout yet**

In `apps/web/src/app/page.tsx`, import `WORKSPACE_COPY` and use it for the initial `statusMessage` only:

```ts
import { WORKSPACE_COPY, workflowSteps } from "@/lib/workspace-copy";
```

Replace:

```ts
const [statusMessage, setStatusMessage] = useState("Ready for a local upload.");
```

with:

```ts
const [statusMessage, setStatusMessage] = useState(WORKSPACE_COPY.status.ready);
```

- [ ] **Step 6: Commit**

Commit message:

```text
feat(web): add Korean workspace copy contract
```

## Task 2: Script-First Liquid Glass Workspace

**Files:**
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/src/app/globals.css`
- Test: `apps/web/src/lib/workspace-copy.test.ts`

- [ ] **Step 1: Add failing tests for Korean script-first terminology**

Extend `apps/web/src/lib/workspace-copy.test.ts`:

```ts
  it("uses script-first editing language instead of generic dashboard language", () => {
    const allCopy = JSON.stringify(WORKSPACE_COPY);
    expect(allCopy).toContain("대본");
    expect(allCopy).toContain("자막");
    expect(allCopy).toContain("컷");
    expect(allCopy).not.toContain("Review Workspace");
    expect(allCopy).not.toContain("Render Queue");
  });
```

Run the test and verify it fails if the required copy is missing.

- [ ] **Step 2: Complete Korean copy additions**

Add these fields to `WORKSPACE_COPY`:

```ts
script: {
  title: "대본으로 편집하기",
  subtitle: "문장을 고치고 컷 후보를 승인하면 영상 초안이 함께 정리돼요.",
  cutBadge: "컷 후보",
  highlightBadge: "쇼츠 후보",
  subtitlePlaceholder: "자막 문장을 다듬어 주세요"
},
export: {
  title: "내보내기",
  original: "원본 비율",
  vertical: "세로 9:16",
  square: "정사각형",
  includeSubtitles: "자막 포함",
  includeThumbnail: "썸네일 포함"
}
```

- [ ] **Step 3: Rewrite the workspace layout**

Modify `apps/web/src/app/page.tsx` so the rendered structure becomes:

- Left rail: app mark, Korean nav, local mode card.
- Top bar: current project title, status line, settings/analyze/export actions.
- Main editor grid:
  - Video preview workbench.
  - Script editor panel listing timeline items and subtitles.
  - Right AI suggestion panel with workflow progress and thumbnail/export controls.

Keep existing fetch handlers and state transitions. Do not remove API-backed controls.

- [ ] **Step 4: Replace the visual system**

Modify `apps/web/src/app/globals.css` to:

- Set dark background and Korean-friendly font stack.
- Use translucent panels with `backdrop-filter`, subtle borders, and high text contrast.
- Remove the light dashboard palette.
- Keep cards at 8px radius or less where they are repeated items; larger radius is only allowed for app shell glass panels.
- Ensure mobile layout collapses to one column without overlapping text.

- [ ] **Step 5: Verify**

Run:

```powershell
& "$envRoot\Library\bin\pnpm.bat" --filter @cutmate/web test
& "$envRoot\Library\bin\pnpm.bat" --filter @cutmate/web lint
& "$envRoot\Library\bin\pnpm.bat" --filter @cutmate/web typecheck
& "$envRoot\Library\bin\pnpm.bat" --filter @cutmate/web build
```

Expected: all pass.

- [ ] **Step 6: Commit**

Commit message:

```text
feat(web): redesign workspace around Korean script editing
```

## Task 3: Desktop Runtime and API Sidecar Contract

**Files:**
- Create: `apps/web/src/lib/desktop-runtime.ts`
- Create: `apps/web/src/lib/desktop-runtime.test.ts`
- Modify: `apps/web/src/app/page.tsx`
- Modify: `apps/web/package.json`
- Modify: `apps/api/app/core/config.py`
- Create: `apps/api/app/desktop_sidecar.py`
- Create: `apps/api/tests/test_desktop_sidecar.py`
- Modify: `apps/api/tests/test_config.py`
- Modify: `apps/api/pyproject.toml`
- Modify: `apps/api/uv.lock`

- [ ] **Step 1: Add failing frontend desktop runtime tests**

Create `apps/web/src/lib/desktop-runtime.test.ts`:

```ts
import { describe, expect, it, vi } from "vitest";

import { isTauriRuntime, startDesktopApiSidecar } from "./desktop-runtime";

describe("desktop runtime", () => {
  it("does not start a sidecar in a normal browser", async () => {
    expect(isTauriRuntime({})).toBe(false);
    await expect(startDesktopApiSidecar({})).resolves.toEqual({ started: false });
  });

  it("detects a Tauri runtime marker", () => {
    expect(isTauriRuntime({ __TAURI_INTERNALS__: {} })).toBe(true);
  });
});
```

Run it and verify it fails because `desktop-runtime.ts` does not exist.

- [ ] **Step 2: Implement browser-safe desktop runtime**

Create `apps/web/src/lib/desktop-runtime.ts`:

```ts
type TauriWindowLike = {
  __TAURI_INTERNALS__?: unknown;
};

type SidecarStartResult = {
  started: boolean;
  reason?: "not-tauri" | "unavailable";
};

export function isTauriRuntime(value: unknown = globalThis.window): value is TauriWindowLike {
  return typeof value === "object" && value !== null && "__TAURI_INTERNALS__" in value;
}

export async function startDesktopApiSidecar(
  runtimeWindow: unknown = globalThis.window
): Promise<SidecarStartResult> {
  if (!isTauriRuntime(runtimeWindow)) {
    return { started: false, reason: "not-tauri" };
  }

  try {
    const { Command } = await import("@tauri-apps/plugin-shell");
    const command = Command.sidecar("binaries/cutmate-api");
    await command.spawn();
    return { started: true };
  } catch {
    return { started: false, reason: "unavailable" };
  }
}
```

- [ ] **Step 3: Add failing API sidecar tests**

Create `apps/api/tests/test_desktop_sidecar.py`:

```py
from types import SimpleNamespace

from app import desktop_sidecar


def test_desktop_sidecar_sets_local_defaults(monkeypatch):
    calls: list[dict[str, object]] = []

    def fake_run(app: str, **kwargs: object) -> None:
      calls.append({"app": app, **kwargs})

    monkeypatch.delenv("CUTMATE_APP_URL", raising=False)
    monkeypatch.setattr(desktop_sidecar.uvicorn, "run", fake_run)

    desktop_sidecar.main()

    assert calls == [
        {
            "app": "app.main:app",
            "host": "127.0.0.1",
            "port": 8000,
            "log_level": "info",
        }
    ]
    assert desktop_sidecar.os.environ["CUTMATE_APP_URL"] == "tauri://localhost"
```

Run it and verify it fails because `desktop_sidecar.py` does not exist.

- [ ] **Step 4: Implement API sidecar entrypoint**

Create `apps/api/app/desktop_sidecar.py`:

```py
from __future__ import annotations

import os

import uvicorn


def main() -> None:
    os.environ.setdefault("CUTMATE_APP_URL", "tauri://localhost")
    os.environ.setdefault("CUTMATE_STORAGE_DIR", ".cutmate/storage")
    os.environ.setdefault("CUTMATE_SQLITE_PATH", ".cutmate/cutmate.db")
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, log_level="info")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Add desktop CORS origins**

Modify `apps/api/app/core/config.py` so settings expose:

```py
desktop_app_origins: tuple[str, ...] = ("tauri://localhost", "http://tauri.localhost")

@property
def cors_origins(self) -> list[str]:
    return [self.app_url, *self.desktop_app_origins]
```

Modify `apps/api/app/main.py` to use `settings.cors_origins` for `allow_origins`.

Add a focused test in `apps/api/tests/test_config.py`:

```py
def test_settings_include_tauri_desktop_origins() -> None:
    settings = get_settings()
    assert "tauri://localhost" in settings.cors_origins
    assert settings.app_url in settings.cors_origins
```

- [ ] **Step 6: Add dependencies and wire page startup**

Add `@tauri-apps/plugin-shell` to `apps/web/package.json`.
Add `pyinstaller>=6,<7` to `apps/api/pyproject.toml` dev dependencies and run `uv sync --project apps/api --dev`.

In `apps/web/src/app/page.tsx`, call `startDesktopApiSidecar()` from `useEffect` and ignore the result unless it fails inside Tauri:

```ts
useEffect(() => {
  void startDesktopApiSidecar();
}, []);
```

- [ ] **Step 7: Verify**

Run:

```powershell
& "$envRoot\Library\bin\pnpm.bat" test
& "$envRoot\Library\bin\pnpm.bat" lint
& "$envRoot\Library\bin\pnpm.bat" typecheck
& "$envRoot\Library\bin\pnpm.bat" build
```

Expected: all pass.

- [ ] **Step 8: Commit**

Commit message:

```text
feat(desktop): add local API sidecar runtime contract
```

## Task 4: Tauri Desktop Scaffold

**Files:**
- Create: `src-tauri/Cargo.toml`
- Create: `src-tauri/build.rs`
- Create: `src-tauri/src/main.rs`
- Create: `src-tauri/capabilities/default.json`
- Create: `src-tauri/tauri.conf.json`
- Create: `src-tauri/icons/icon.png`
- Modify: `apps/web/next.config.ts`
- Modify: `package.json`
- Modify: `pnpm-lock.yaml`

- [ ] **Step 1: Add Tauri dependencies**

Add root dev dependencies:

```json
"devDependencies": {
  "@tauri-apps/cli": "^2.0.0"
}
```

Add scripts:

```json
"desktop:dev": "tauri dev",
"desktop:build": "tauri build -- --bundles dmg"
```

Run `pnpm install` to update `pnpm-lock.yaml`.

- [ ] **Step 2: Enable static export**

Modify `apps/web/next.config.ts`:

```ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export"
};

export default nextConfig;
```

- [ ] **Step 3: Add Tauri Rust package files**

Create `src-tauri/Cargo.toml`:

```toml
[package]
name = "cutmate-ai"
version = "0.1.0"
description = "CutMate AI desktop shell"
authors = ["CutMate AI"]
edition = "2021"

[build-dependencies]
tauri-build = { version = "2", features = [] }

[dependencies]
tauri = { version = "2", features = [] }
tauri-plugin-shell = "2"
```

Create `src-tauri/build.rs`:

```rust
fn main() {
    tauri_build::build()
}
```

Create `src-tauri/src/main.rs`:

```rust
fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .run(tauri::generate_context!())
        .expect("error while running CutMate AI desktop shell");
}
```

- [ ] **Step 4: Add Tauri config**

Create `src-tauri/tauri.conf.json` with:

```json
{
  "$schema": "https://schema.tauri.app/config/2",
  "productName": "CutMate AI",
  "version": "0.1.0",
  "identifier": "com.minhyeok.cutmate-ai",
  "build": {
    "beforeDevCommand": "pnpm --filter @cutmate/web dev",
    "beforeBuildCommand": "pnpm --filter @cutmate/web build",
    "devUrl": "http://localhost:3000",
    "frontendDist": "../apps/web/out"
  },
  "app": {
    "windows": [
      {
        "title": "CutMate AI",
        "label": "main",
        "width": 1440,
        "height": 920,
        "minWidth": 1120,
        "minHeight": 720,
        "resizable": true
      }
    ],
    "security": {
      "csp": null
    }
  },
  "bundle": {
    "active": true,
    "targets": ["dmg"],
    "externalBin": ["binaries/cutmate-api"],
    "macOS": {
      "minimumSystemVersion": "12.0"
    }
  }
}
```

Create `src-tauri/capabilities/default.json`:

```json
{
  "$schema": "../gen/schemas/desktop-schema.json",
  "identifier": "default",
  "description": "Main desktop window capability",
  "windows": ["main"],
  "permissions": [
    "core:default",
    {
      "identifier": "shell:allow-spawn",
      "allow": [
        {
          "name": "binaries/cutmate-api",
          "sidecar": true
        }
      ]
    }
  ]
}
```

- [ ] **Step 5: Add minimal icon asset**

Create `src-tauri/icons/icon.png` as a small generated PNG if Tauri requires an icon path later. Do not spend time on brand polish in this task.

- [ ] **Step 6: Verify web build still works**

Run:

```powershell
& "$envRoot\Library\bin\pnpm.bat" build
```

Expected: Next.js build succeeds and creates `apps/web/out`.

- [ ] **Step 7: Commit**

Commit message:

```text
feat(desktop): add Tauri shell scaffold
```

## Task 5: Manual macOS Unsigned DMG Workflow

**Files:**
- Create: `.github/workflows/build-macos.yml`
- Create: `docs/desktop-build.md`

- [ ] **Step 1: Add manual workflow**

Create `.github/workflows/build-macos.yml`:

```yaml
name: Build macOS DMG

on:
  workflow_dispatch:

permissions:
  contents: read

jobs:
  build-macos:
    name: Build unsigned macOS DMG
    runs-on: macos-latest
    timeout-minutes: 45
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup pnpm
        uses: pnpm/action-setup@v4
        with:
          version: 10.33.2

      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm

      - name: Setup uv
        uses: astral-sh/setup-uv@v5

      - name: Install JavaScript dependencies
        run: pnpm install --frozen-lockfile

      - name: Install Python dependencies
        run: uv sync --project apps/api --dev

      - name: Build API sidecar
        working-directory: apps/api
        run: |
          uv run pyinstaller --onefile --name cutmate-api app/desktop_sidecar.py
          TARGET_TRIPLE="$(rustc -Vv | awk '/host:/ {print $2}')"
          mkdir -p ../../src-tauri/binaries
          cp dist/cutmate-api "../../src-tauri/binaries/cutmate-api-${TARGET_TRIPLE}"
          chmod +x "../../src-tauri/binaries/cutmate-api-${TARGET_TRIPLE}"

      - name: Run verification
        run: |
          pnpm lint
          pnpm typecheck
          pnpm test
          pnpm build

      - name: Build unsigned DMG
        uses: tauri-apps/tauri-action@v0
        with:
          args: --bundles dmg

      - name: Upload DMG artifact
        uses: actions/upload-artifact@v4
        with:
          name: cutmate-ai-macos-dmg
          path: src-tauri/target/release/bundle/dmg/*.dmg
          if-no-files-found: error
          retention-days: 3
```

- [ ] **Step 2: Add Korean build guide**

Create `docs/desktop-build.md`:

```md
# CutMate AI macOS 빌드 가이드

## 목적

이 저장소는 Windows에서 개발하고 GitHub Actions의 macOS runner에서 unsigned `.dmg`를 만드는 흐름을 사용합니다.

## 빌드 방법

1. GitHub 저장소 `minhyeok328/cutmate-ai`로 이동합니다.
2. `Actions` 탭을 엽니다.
3. `Build macOS DMG` workflow를 선택합니다.
4. `Run workflow` 버튼을 누릅니다.
5. 완료 후 `cutmate-ai-macos-dmg` artifact를 다운로드합니다.

## unsigned 앱 주의사항

현재 Apple Developer Program 유료 멤버십을 사용하지 않으므로 앱은 서명/공증되지 않습니다. 받는 사람의 macOS에서 처음 실행할 때 보안 경고가 뜰 수 있습니다. 나중에 유료 멤버십과 Developer ID 인증서를 준비하면 같은 workflow에 signing/notarization 단계를 추가할 수 있습니다.

## 로컬 개발

Windows 개발 중에는 다음 명령으로 계속 테스트합니다.

```powershell
pnpm dev
```
```

- [ ] **Step 3: Verify workflow is manual and short-retention**

Run:

```powershell
Select-String -Path .github/workflows/build-macos.yml -Pattern "workflow_dispatch","retention-days: 3","macos-latest"
```

Expected: all three strings are present.

- [ ] **Step 4: Commit**

Commit message:

```text
ci(desktop): add manual unsigned macOS build
```

## Task 6: Security Review and Final Verification

**Files:**
- Review all changed files.

- [ ] **Step 1: Run secret and artifact checks**

Run:

```powershell
git status --short
git ls-files .env .env.local apps/web/.env apps/api/.env
git ls-files "*.db" "*.sqlite" "*.mp4" "*.mov" ".cutmate/*"
```

Expected: no real env files, databases, uploaded media, or generated artifacts are tracked.

- [ ] **Step 2: Run full verification**

Run:

```powershell
& "$envRoot\Library\bin\pnpm.bat" lint
& "$envRoot\Library\bin\pnpm.bat" typecheck
& "$envRoot\Library\bin\pnpm.bat" test
& "$envRoot\Library\bin\pnpm.bat" build
```

Expected: all pass.

- [ ] **Step 3: Manual browser smoke**

Start:

```powershell
& "$envRoot\Library\bin\pnpm.bat" dev
```

Open `http://localhost:3000` and verify:

- Korean UI appears.
- Script-first panel is the main editing surface.
- Text is readable in the black liquid-glass theme.
- Upload, analysis, thumbnail, and export controls are still visible.

- [ ] **Step 4: Commit any final docs or fixes**

Use a scoped conventional commit only if changes were needed.

---

## Self-Review

- Spec coverage: UI redesign, Korean copy, desktop scaffold, manual macOS DMG workflow, unsigned-first caveat, and security checks all map to tasks.
- Placeholder scan: no `TBD`, `TODO`, or unresolved implementation placeholders are used.
- Type consistency: `WORKSPACE_COPY`, `workflowSteps`, `startDesktopApiSidecar`, and `desktop_sidecar.main` names are consistent across tasks.
