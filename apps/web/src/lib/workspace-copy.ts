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
    light: "빠른 분석",
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
