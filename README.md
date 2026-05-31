# CutMate AI

CutMate AI는 긴 영상을 로컬에서 분석하고, 대본 중심으로 컷 후보와 하이라이트 후보를 정리해 주는 영상 편집 보조 프로그램입니다. 브루(Vrew)처럼 대본을 보면서 편집 흐름을 잡는 경험을 목표로 하며, 현재 UI는 한국어 기반의 블랙 리퀴드 글래스 스타일 데스크톱 작업 공간으로 구성되어 있습니다.

이 프로젝트는 기본적으로 로컬 우선(local-first) 구조입니다. 업로드한 영상, 대본, 썸네일 후보, 내보내기 작업 정보는 외부 API로 보내지 않는 것을 기본 원칙으로 하고, MVP에서는 LLM이 없어도 분석 초안을 만들 수 있게 설계되어 있습니다.

## 주요 기능

- 영상 업로드: `mp4`, `mov`, `m4v` 파일 지원, 최대 20분/2GB 기준.
- 로컬 메타데이터 분석: `ffprobe`를 사용해 길이, 해상도, FPS, 오디오 유무를 확인.
- 대본 중심 편집: 자막 문장 수정, 타이밍 조정, 상태 변경 흐름 제공.
- 컷/하이라이트 후보: 로컬 분석 초안을 기반으로 컷 후보와 하이라이트 후보를 생성.
- 썸네일 후보: 자동 후보 생성과 직접 프레임 선택 흐름 제공.
- 내보내기 작업: 원본 비율, 세로 9:16, 정사각형 설정과 자막/썸네일 포함 옵션 제공.
- 분석 모드: 빠른 분석, 표준 분석, 품질 분석 UI 제공.
- 데스크톱 앱 구조: Tauri 셸이 Python FastAPI sidecar를 실행하는 구조를 준비.
- macOS 빌드: GitHub Actions에서 unsigned DMG를 수동으로 생성하는 workflow 제공.

## 현재 상태

MVP 1-4차 범위의 기본 틀은 구현되어 있습니다. 현재 분석 결과는 실제 고급 모델 추론을 완전히 붙인 상태라기보다, 로컬 API와 SQLite 저장소, 업로드 검증, 대본/컷/썸네일/내보내기 작업 흐름을 검증하기 위한 로컬 초안 생성 방식입니다.

품질 모드의 목표 모델은 `openai/gpt-oss-20b`이지만 OpenAI API를 호출하는 구조가 아닙니다. 로컬 self-hosted inference를 전제로 하며, 기본 분석은 LLM 없이도 동작하도록 유지합니다.

## 기술 스택

- Frontend: Next.js 16, React 19, TypeScript, Vitest
- Backend: FastAPI, Python 3.12, SQLite, uv
- Desktop: Tauri v2, Rust, PyInstaller sidecar
- Package manager: pnpm 10.33.2
- Build/CI: GitHub Actions macOS runner

## 프로젝트 구조

```text
.
├─ apps/
│  ├─ web/          # Next.js 한국어 작업 공간 UI
│  └─ api/          # FastAPI 로컬 API, SQLite 저장소, 분석 초안 생성
├─ src-tauri/       # Tauri 데스크톱 셸과 macOS DMG 번들 설정
├─ scripts/         # Tauri/GitHub Actions 설정 검증 스크립트
├─ docs/            # 데스크톱 빌드 가이드와 작업 문서
├─ .env.example     # 공유 가능한 더미 환경 변수 구조
└─ package.json     # 루트 개발/검증/빌드 명령
```

## 사전 준비

필수 도구:

- Node.js 22 이상
- pnpm 10.33.2
- Python 3.12
- uv
- FFmpeg/ffprobe
- Rust toolchain

Windows 개발 환경에서는 conda 환경을 사용해도 됩니다.

```powershell
conda activate cutmate-ai
```

## 설치

루트 디렉터리에서 JavaScript와 Python 의존성을 설치합니다.

```powershell
pnpm install
uv --cache-dir .uv-cache sync --project apps/api --dev
```

환경 변수 구조가 필요하면 `.env.example`을 참고해 로컬 `.env`를 만들 수 있습니다. 실제 `.env` 파일은 Git에 커밋하지 않습니다.

## 개발 서버 실행

프론트엔드와 API를 함께 실행합니다.

```powershell
pnpm dev
```

기본 주소:

- Web: `http://localhost:3000`
- API: `http://127.0.0.1:8000`

개별 실행이 필요하면 다음 명령을 사용할 수 있습니다.

```powershell
pnpm --filter @cutmate/web dev
pnpm --filter @cutmate/api dev
```

## 검증 명령

```powershell
pnpm test
pnpm lint
pnpm typecheck
pnpm build
cargo check --manifest-path src-tauri/Cargo.toml
```

`pnpm test`에는 다음 정적 검증도 포함됩니다.

- Tauri config와 sidecar 권한 검증
- macOS DMG workflow 수동 실행 조건 검증
- 웹/API 단위 테스트

## 데스크톱 앱 개발

Tauri 셸을 로컬에서 확인할 때는 다음 명령을 사용합니다.

```powershell
pnpm desktop:dev
```

Windows에서 이 명령은 데스크톱 셸과 프론트엔드 확인에 가깝습니다. 완전한 데스크톱 패키징은 macOS GitHub Actions 빌드를 기준으로 하며, release/DMG 빌드는 실제 PyInstaller sidecar가 있어야 통과하도록 되어 있습니다. 개발 모드의 `cargo check`는 target별 sidecar placeholder를 자동 생성해 Rust/Tauri 스캐폴드만 검증할 수 있게 합니다.

## macOS DMG 빌드

macOS용 DMG는 GitHub Actions에서 수동으로 생성합니다.

1. GitHub 저장소 `minhyeok328/cutmate-ai`로 이동합니다.
2. `Actions` 탭을 엽니다.
3. `Build macOS DMG` workflow를 선택합니다.
4. `Run workflow`를 실행합니다.
5. 완료 후 `cutmate-ai-macos-dmg` artifact를 다운로드합니다.

자세한 내용은 [docs/desktop-build.md](docs/desktop-build.md)를 참고하세요.

현재 DMG는 Apple Developer Program 서명/공증이 없는 unsigned 빌드입니다. 받는 사람이 macOS에서 처음 실행할 때 보안 경고를 볼 수 있습니다.

## 환경 변수

공유 가능한 예시는 `.env.example`에 있습니다.

주요 값:

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

실제 비밀값, API 키, 로컬 DB, 업로드 영상, 모델 가중치, export 산출물은 커밋하지 않습니다.

## 보안/로컬 데이터 원칙

- 기본 분석은 외부 API 호출 없이 로컬에서 처리합니다.
- OpenAI API 키는 MVP 로컬 분석에 필요하지 않습니다.
- 업로드 영상은 `.cutmate/storage` 아래에 저장되며 Git에서 제외됩니다.
- API는 허용된 웹/Tauri origin만 CORS에 포함합니다.
- Tauri는 sidecar 실행 권한을 `binaries/cutmate-api`로 제한하고 CSP를 사용합니다.

## 참고 문서

- [macOS 빌드 가이드](docs/desktop-build.md)
- [데스크톱 한국어 리디자인 설계](docs/superpowers/specs/2026-05-31-desktop-korean-redesign-design.md)
- [데스크톱 한국어 리디자인 구현 계획](docs/superpowers/plans/2026-05-31-desktop-korean-redesign.md)
