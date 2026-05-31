import type { AnalysisMode } from "./config";

export const WORKSPACE_COPY = {
  appName: "컷메이트 AI",
  productMark: "CutMate AI",
  tagline: "대본을 고치듯 영상 초안을 다듬는 로컬 편집 도우미",
  workspace: {
    titleFallback: "새 영상 프로젝트",
    topEyebrow: "로컬 작업공간",
    statusLabel: "현재 상태",
    modeTitle: "로컬 분석 모드",
    modeHelp: "브라우저에서 조작하고 로컬 API로 처리해요.",
    sourceMetaFallback: "영상을 올리면 정보가 표시돼요."
  },
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
  },
  upload: {
    title: "영상 가져오기",
    help: "MP4, MOV, M4V | 최대 20분 | 2GB까지 업로드",
    titleLabel: "프로젝트 제목",
    purposeLabel: "콘텐츠 유형",
    goalLabel: "작업 목표",
    modeLabel: "분석 모드",
    dropCta: "영상 파일 선택",
    emptyFile: "영상을 선택해 주세요",
    selectedSuffix: "선택됨"
  },
  preview: {
    title: "영상 프리뷰",
    empty: "업로드 후 프리뷰 준비",
    sourceInfo: "원본 정보",
    duration: "길이",
    resolution: "해상도",
    fileSize: "파일 크기"
  },
  aiPanel: {
    title: "AI 제안",
    progressTitle: "작업 흐름",
    thumbnailTitle: "썸네일 후보",
    directFrameTitle: "프레임 직접 선택",
    exportTitle: "내보내기 설정"
  },
  actions: {
    createProject: "프로젝트 만들기",
    runAnalysis: "AI 분석 시작",
    analyzing: "분석 중",
    save: "저장",
    generate: "후보 만들기",
    chooseFrame: "프레임 선택",
    render: "내보내기 생성",
    applySelected: "선택 적용",
    accept: "승인",
    undoAccept: "승인 취소",
    reject: "제외",
    settings: "설정"
  },
  status: {
    ready: "로컬 영상 업로드를 기다리고 있어요.",
    selectVideo: "분석할 영상을 먼저 선택해 주세요.",
    uploading: "로컬 작업공간으로 영상을 가져오는 중...",
    apiUnavailable: "로컬 API에 연결할 수 없어요.",
    analysisReady: "검토할 초안이 준비됐어요.",
    noDraft: "아직 생성된 대본/컷 후보가 없어요.",
    noSubtitles: "아직 자막 문장이 없어요.",
    noThumbnails: "아직 썸네일 후보가 없어요.",
    renderDone: "로컬 내보내기 작업이 생성됐어요.",
    createProjectFirst: "먼저 프로젝트를 만들어 주세요.",
    subtitleEmpty: "자막 문장을 입력해 주세요.",
    subtitleSaved: "자막 수정이 저장됐어요.",
    subtitleSaveFailed: "자막 저장에 실패했어요.",
    segmentUpdated: "컷 후보 상태가 바뀌었어요.",
    segmentUpdateFailed: "컷 후보 상태를 바꾸지 못했어요.",
    thumbnailGenerated: "썸네일 후보가 생성됐어요.",
    thumbnailGenerateFailed: "썸네일 후보를 만들지 못했어요.",
    thumbnailUpdated: "썸네일 상태가 바뀌었어요.",
    thumbnailUpdateFailed: "썸네일 상태를 바꾸지 못했어요.",
    directFrameInvalid: "프레임 시간은 0초 이상이어야 해요.",
    directFrameSelected: "직접 선택한 프레임이 추가됐어요.",
    directFrameFailed: "프레임을 선택하지 못했어요.",
    exportFailed: "내보내기 작업을 만들지 못했어요.",
    uploadFailed: "업로드에 실패했어요.",
    fileSelectedSuffix: "선택됐어요.",
    readyUpload: "로컬 업로드를 준비하고 있어요."
  },
  options: {
    purposes: {
      short_form: "쇼츠/릴스",
      vlog: "브이로그",
      lecture: "강의",
      interview: "인터뷰",
      promotional_video: "홍보 영상"
    },
    goals: {
      source_summary: "핵심 요약",
      highlight_extraction: "하이라이트 추출",
      subtitle_generation: "자막 생성",
      short_form_conversion: "쇼츠 컷 변환"
    }
  },
  stateLabels: {
    ready: "대기",
    selected: "선택됨",
    created: "생성됨",
    queued: "대기 중",
    running: "진행 중",
    completed: "완료",
    completed_with_warnings: "주의 필요",
    waiting: "대기",
    idle: "대기",
    draft: "초안",
    edited: "수정됨",
    pending: "검토 전",
    accepted: "승인됨",
    rejected: "제외됨",
    modified: "수정됨",
    selectedThumbnail: "선택됨",
    custom_selected: "직접 선택",
    rendering: "렌더링",
    failed: "실패",
    retrying: "재시도"
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
