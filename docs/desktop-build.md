# CutMate AI macOS 빌드 가이드

## 목적

이 저장소는 Windows에서 개발하더라도 GitHub Actions의 macOS runner에서 서명되지 않은 DMG를 만들 수 있도록 구성되어 있습니다. 현재 목표는 선물용으로 전달할 수 있는 수동 빌드 산출물을 만드는 것이며, App Store 배포나 공증 배포는 나중 단계로 남겨둡니다.

## 빌드 방법

1. GitHub 저장소 `minhyeok328/cutmate-ai`로 이동합니다.
2. `Actions` 탭을 엽니다.
3. 왼쪽 목록에서 `Build macOS DMG` workflow를 선택합니다.
4. `Run workflow` 버튼을 눌러 빌드를 시작합니다.
5. 빌드가 끝나면 실행 결과 페이지의 `Artifacts`에서 `cutmate-ai-macos-dmg`를 다운로드합니다.

## 서명되지 않은 DMG 주의사항

현재 workflow는 Apple Developer Program 인증서 없이 unsigned DMG를 만듭니다. 그래서 받는 사람이 macOS에서 처음 실행할 때 보안 경고를 볼 수 있습니다. 나중에 유료 멤버십과 Developer ID 인증서를 연결하면 같은 workflow에 signing/notarization 단계를 추가할 수 있습니다.

## 로컬 개발

Windows 개발 중에는 일반 웹 개발 서버로 계속 테스트할 수 있습니다.

```powershell
pnpm dev
```

Tauri 데스크톱 셸을 로컬에서 확인할 때는 Rust/Tauri 의존성이 설치된 환경에서 다음 명령을 사용합니다.

```powershell
pnpm desktop:dev
```

macOS 배포용 DMG는 GitHub Actions의 `Build macOS DMG` workflow에서 만드는 것을 기준으로 합니다.
