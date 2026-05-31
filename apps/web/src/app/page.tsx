"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useMemo, useState } from "react";

import { runtimeConfig, type AnalysisMode } from "@/lib/config";
import { WORKSPACE_COPY } from "@/lib/workspace-copy";

type ContentPurpose = "short_form" | "vlog" | "lecture" | "interview" | "promotional_video";
type OutputGoal =
  | "source_summary"
  | "highlight_extraction"
  | "subtitle_generation"
  | "short_form_conversion";

type ProjectCreateResponse = {
  project: {
    project_id: string;
    title: string;
    status: string;
    metadata: {
      duration_ms: number;
      width: number;
      height: number;
      source_file_name: string;
      source_size_bytes: number;
    };
  };
  analysis_job: {
    job_id: string;
    status: string;
    mode: AnalysisMode;
    progress_percent: number;
  };
};

type SubtitleDraft = {
  subtitle_id: string;
  start_ms: number;
  end_ms: number;
  text: string;
  edited_text: string | null;
  status: "draft" | "edited";
};

type SegmentDraft = {
  segment_id: string;
  type: "cut" | "highlight";
  start_ms: number;
  end_ms: number;
  transcript: string | null;
  reason: string;
  status: "pending" | "accepted" | "rejected" | "modified";
};

type AnalysisResponse = {
  analysis_job?: ProjectCreateResponse["analysis_job"];
  analysis: {
    project_id: string;
    job_id: string;
    status: "completed" | "completed_with_warnings";
    warnings: string[];
    subtitles: SubtitleDraft[];
    cut_candidates: SegmentDraft[];
    highlight_candidates: SegmentDraft[];
  };
};

type ThumbnailCandidate = {
  thumbnail_id: string;
  timestamp_ms: number;
  image_url: string;
  reason: string;
  tags: string[];
  status: "pending" | "selected" | "rejected" | "custom_selected";
};

type ExportJob = {
  export_id: string;
  project_id: string;
  status: "queued" | "rendering" | "completed" | "failed" | "retrying";
  aspect_ratio: "original" | "9:16" | "1:1";
  resolution: string;
  include_subtitles: boolean;
  include_thumbnail: boolean;
  crop_mode: "center" | "manual";
  download_url: string;
  thumbnail_download_url: string | null;
};

const purposeOptions: Array<{ value: ContentPurpose; label: string }> = [
  { value: "short_form", label: WORKSPACE_COPY.options.purposes.short_form },
  { value: "vlog", label: WORKSPACE_COPY.options.purposes.vlog },
  { value: "lecture", label: WORKSPACE_COPY.options.purposes.lecture },
  { value: "interview", label: WORKSPACE_COPY.options.purposes.interview },
  { value: "promotional_video", label: WORKSPACE_COPY.options.purposes.promotional_video }
];

const outputGoalOptions: Array<{ value: OutputGoal; label: string }> = [
  { value: "highlight_extraction", label: WORKSPACE_COPY.options.goals.highlight_extraction },
  { value: "source_summary", label: WORKSPACE_COPY.options.goals.source_summary },
  { value: "subtitle_generation", label: WORKSPACE_COPY.options.goals.subtitle_generation },
  { value: "short_form_conversion", label: WORKSPACE_COPY.options.goals.short_form_conversion }
];

const aspectRatioOptions: Array<{ value: ExportJob["aspect_ratio"]; label: string }> = [
  { value: "original", label: WORKSPACE_COPY.export.original },
  { value: "9:16", label: WORKSPACE_COPY.export.vertical },
  { value: "1:1", label: WORKSPACE_COPY.export.square }
];

export default function WorkspacePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [purpose, setPurpose] = useState<ContentPurpose>("short_form");
  const [outputGoal, setOutputGoal] = useState<OutputGoal>("highlight_extraction");
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("standard");
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string>(WORKSPACE_COPY.status.ready);
  const [createdProject, setCreatedProject] = useState<ProjectCreateResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse["analysis"] | null>(null);
  const [thumbnailCandidates, setThumbnailCandidates] = useState<ThumbnailCandidate[]>([]);
  const [exportAspectRatio, setExportAspectRatio] = useState<ExportJob["aspect_ratio"]>("original");
  const [includeSubtitles, setIncludeSubtitles] = useState(true);
  const [includeThumbnail, setIncludeThumbnail] = useState(true);
  const [exportJob, setExportJob] = useState<ExportJob | null>(null);

  const timelineItems = useMemo(
    () =>
      [
        ...(analysisResult?.cut_candidates ?? []),
        ...(analysisResult?.highlight_candidates ?? [])
      ].sort((first, second) => first.start_ms - second.start_ms),
    [analysisResult]
  );

  const pipelineSteps = useMemo(
    () => [
      {
        label: "업로드",
        state: createdProject
          ? WORKSPACE_COPY.stateLabels.created
          : selectedFile
            ? WORKSPACE_COPY.stateLabels.selected
            : WORKSPACE_COPY.stateLabels.ready,
        value: createdProject ? 100 : selectedFile ? 35 : 0
      },
      {
        label: "분석",
        state: analysisResult
          ? formatAnalysisStatus(analysisResult.status)
          : createdProject
            ? formatJobStatus(createdProject.analysis_job.status)
            : WORKSPACE_COPY.stateLabels.queued,
        value: analysisResult ? 100 : (createdProject?.analysis_job.progress_percent ?? 0)
      },
      {
        label: "대본",
        state: analysisResult ? "검토 가능" : WORKSPACE_COPY.stateLabels.waiting,
        value: analysisResult ? 100 : 0
      },
      {
        label: WORKSPACE_COPY.export.title,
        state: exportJob ? formatExportStatus(exportJob.status) : WORKSPACE_COPY.stateLabels.idle,
        value: exportJob ? 100 : 0
      }
    ],
    [analysisResult, createdProject, exportJob, selectedFile]
  );

  const activeProjectTitle =
    createdProject?.project.title || title || WORKSPACE_COPY.workspace.titleFallback;
  const sourceFileName =
    createdProject?.project.metadata.source_file_name ?? selectedFile?.name ?? WORKSPACE_COPY.preview.empty;
  const sourceDuration = createdProject
    ? formatDuration(createdProject.project.metadata.duration_ms)
    : "00:00";
  const sourceResolution = createdProject
    ? `${createdProject.project.metadata.width} x ${createdProject.project.metadata.height}`
    : "미정";
  const sourceSize = createdProject
    ? formatBytes(createdProject.project.metadata.source_size_bytes)
    : selectedFile
      ? formatBytes(selectedFile.size)
      : WORKSPACE_COPY.workspace.sourceMetaFallback;
  const acceptedSegments = timelineItems.filter((item) => item.status === "accepted").length;
  const selectedThumbnails = thumbnailCandidates.filter(
    (candidate) => candidate.status === "selected" || candidate.status === "custom_selected"
  ).length;

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setStatusMessage(WORKSPACE_COPY.status.selectVideo);
      return;
    }

    setUploading(true);
    setStatusMessage(WORKSPACE_COPY.status.uploading);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("title", title);
    formData.append("purpose", purpose);
    formData.append("output_goal", outputGoal);
    formData.append("analysis_mode", analysisMode);

    try {
      const response = await fetch(`${runtimeConfig.apiUrl}/api/v1/projects`, {
        method: "POST",
        body: formData
      });
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.uploadFailed));
        return;
      }
      const projectResponse = payload as ProjectCreateResponse;
      setCreatedProject(projectResponse);
      setAnalysisResult(null);
      setThumbnailCandidates([]);
      setExportJob(null);
      setStatusMessage(`${WORKSPACE_COPY.modeLabels[projectResponse.analysis_job.mode]} 작업이 대기열에 들어갔어요.`);
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.apiUnavailable);
    } finally {
      setUploading(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    setSelectedFile(nextFile);
    setStatusMessage(
      nextFile
        ? `${nextFile.name} ${WORKSPACE_COPY.status.fileSelectedSuffix}`
        : WORKSPACE_COPY.status.readyUpload
    );
  }

  async function handleRunAnalysis() {
    if (!createdProject) {
      setStatusMessage(WORKSPACE_COPY.status.createProjectFirst);
      return;
    }

    setAnalyzing(true);
    setStatusMessage("로컬 분석을 실행하고 있어요...");
    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/analysis/run`,
        { method: "POST" }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.apiUnavailable));
        return;
      }
      const analysisPayload = payload as AnalysisResponse;
      setAnalysisResult(analysisPayload.analysis);
      setStatusMessage(WORKSPACE_COPY.status.analysisReady);
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.apiUnavailable);
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleSubtitleSave(event: FormEvent<HTMLFormElement>, subtitle: SubtitleDraft) {
    event.preventDefault();
    if (!createdProject || !analysisResult) {
      return;
    }

    const formData = new FormData(event.currentTarget);
    const text = String(formData.get("text") ?? "").trim();
    if (!text) {
      setStatusMessage(WORKSPACE_COPY.status.subtitleEmpty);
      return;
    }

    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/subtitles/${subtitle.subtitle_id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            text,
            start_ms: subtitle.start_ms,
            end_ms: subtitle.end_ms
          })
        }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.subtitleSaveFailed));
        return;
      }
      const updated = (payload as { subtitle: SubtitleDraft }).subtitle;
      setAnalysisResult({
        ...analysisResult,
        subtitles: analysisResult.subtitles.map((item) =>
          item.subtitle_id === updated.subtitle_id ? updated : item
        )
      });
      setStatusMessage(WORKSPACE_COPY.status.subtitleSaved);
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.subtitleSaveFailed);
    }
  }

  async function updateSegmentStatus(segment: SegmentDraft, nextStatus: SegmentDraft["status"]) {
    if (!createdProject || !analysisResult) {
      return;
    }

    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/segments/${segment.segment_id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: nextStatus })
        }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.segmentUpdateFailed));
        return;
      }
      const updated = (payload as { segment: SegmentDraft }).segment;
      const replaceSegment = (item: SegmentDraft) =>
        item.segment_id === updated.segment_id ? updated : item;
      setAnalysisResult({
        ...analysisResult,
        cut_candidates: analysisResult.cut_candidates.map(replaceSegment),
        highlight_candidates: analysisResult.highlight_candidates.map(replaceSegment)
      });
      setStatusMessage(
        `${formatSegmentType(updated.type)}이 ${formatSegmentStatus(updated.status)} 상태가 됐어요.`
      );
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.segmentUpdateFailed);
    }
  }

  async function generateThumbnails() {
    if (!createdProject) {
      setStatusMessage(WORKSPACE_COPY.status.createProjectFirst);
      return;
    }

    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/thumbnails/generate`,
        { method: "POST" }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.thumbnailGenerateFailed));
        return;
      }
      const nextCandidates = (payload as { thumbnail_candidates: ThumbnailCandidate[] })
        .thumbnail_candidates;
      setThumbnailCandidates(nextCandidates);
      setStatusMessage(WORKSPACE_COPY.status.thumbnailGenerated);
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.thumbnailGenerateFailed);
    }
  }

  async function updateThumbnailStatus(
    thumbnail: ThumbnailCandidate,
    nextStatus: ThumbnailCandidate["status"]
  ) {
    if (!createdProject || nextStatus === "custom_selected") {
      return;
    }

    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/thumbnails/${thumbnail.thumbnail_id}`,
        {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ status: nextStatus })
        }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.thumbnailUpdateFailed));
        return;
      }
      const updated = (payload as { thumbnail: ThumbnailCandidate }).thumbnail;
      setThumbnailCandidates((items) =>
        items.map((item) => (item.thumbnail_id === updated.thumbnail_id ? updated : item))
      );
      setStatusMessage(`${formatThumbnailStatus(updated.status)} 썸네일로 표시했어요.`);
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.thumbnailUpdateFailed);
    }
  }

  async function createDirectFrameThumbnail(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!createdProject) {
      setStatusMessage(WORKSPACE_COPY.status.createProjectFirst);
      return;
    }

    const formData = new FormData(event.currentTarget);
    const seconds = Number(formData.get("seconds") ?? 0);
    if (!Number.isFinite(seconds) || seconds < 0) {
      setStatusMessage(WORKSPACE_COPY.status.directFrameInvalid);
      return;
    }

    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/thumbnails/direct-frame`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ timestamp_ms: Math.round(seconds * 1000) })
        }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.directFrameFailed));
        return;
      }
      const created = (payload as { thumbnail: ThumbnailCandidate }).thumbnail;
      setThumbnailCandidates((items) => [...items, created]);
      setStatusMessage(WORKSPACE_COPY.status.directFrameSelected);
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.directFrameFailed);
    }
  }

  async function createExport() {
    if (!createdProject) {
      setStatusMessage(WORKSPACE_COPY.status.createProjectFirst);
      return;
    }

    const resolution =
      exportAspectRatio === "9:16"
        ? "1080x1920"
        : exportAspectRatio === "1:1"
          ? "1080x1080"
          : `${createdProject.project.metadata.width}x${createdProject.project.metadata.height}`;
    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/exports`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            aspect_ratio: exportAspectRatio,
            resolution,
            include_subtitles: includeSubtitles,
            include_thumbnail: includeThumbnail,
            crop_mode: "center"
          })
        }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload, WORKSPACE_COPY.status.exportFailed));
        return;
      }
      const created = (payload as { export_job: ExportJob }).export_job;
      setExportJob(created);
      setStatusMessage(WORKSPACE_COPY.status.renderDone);
    } catch {
      setStatusMessage(WORKSPACE_COPY.status.exportFailed);
    }
  }

  return (
    <main className="workspace-shell">
      <aside className="left-rail glass-shell" aria-label="컷메이트 작업공간 탐색">
        <div className="brand-lockup">
          <span className="app-mark" aria-hidden="true">
            CM
          </span>
          <div>
            <p className="eyebrow">{WORKSPACE_COPY.productMark}</p>
            <h1>{WORKSPACE_COPY.appName}</h1>
          </div>
        </div>

        <nav className="nav-list" aria-label="작업 단계">
          <a href="#source">{WORKSPACE_COPY.nav.source}</a>
          <a href="#script">{WORKSPACE_COPY.nav.script}</a>
          <a href="#ai-suggestions">{WORKSPACE_COPY.sections.suggestions}</a>
          <a href="#export-settings">{WORKSPACE_COPY.nav.export}</a>
        </nav>

        <section className="mode-card" aria-label={WORKSPACE_COPY.workspace.modeTitle}>
          <span>{WORKSPACE_COPY.workspace.modeTitle}</span>
          <strong>{WORKSPACE_COPY.modeLabels[analysisMode]}</strong>
          <p>{WORKSPACE_COPY.workspace.modeHelp}</p>
          <small>{runtimeConfig.qualityLocalLlm}</small>
        </section>
      </aside>

      <section className="workspace-main">
        <header className="topbar glass-shell">
          <div className="topbar-title">
            <p className="eyebrow">{WORKSPACE_COPY.workspace.topEyebrow}</p>
            <h2>{activeProjectTitle}</h2>
            <p className="status-line" role="status">
              <span>{WORKSPACE_COPY.workspace.statusLabel}</span>
              {statusMessage}
            </p>
          </div>
          <div className="topbar-actions">
            <button type="button" className="ghost-button" onClick={() => setStatusMessage("기본 설정을 사용 중이에요.")}>
              {WORKSPACE_COPY.actions.settings}
            </button>
            <button type="button" onClick={handleRunAnalysis} disabled={!createdProject || analyzing}>
              {analyzing ? WORKSPACE_COPY.actions.analyzing : WORKSPACE_COPY.actions.runAnalysis}
            </button>
            <button type="button" className="primary-action" onClick={createExport} disabled={!createdProject}>
              {WORKSPACE_COPY.export.title}
            </button>
          </div>
        </header>

        <section className="editor-grid" aria-label="대본 중심 편집 작업공간">
          <section id="source" className="video-workbench glass-shell" aria-labelledby="preview-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">{WORKSPACE_COPY.sections.source}</p>
                <h2 id="preview-title">{WORKSPACE_COPY.preview.title}</h2>
              </div>
              <span className="soft-badge">{WORKSPACE_COPY.modeLabels[analysisMode]}</span>
            </div>

            <div className="video-stage" aria-label={WORKSPACE_COPY.sections.preview}>
              <div className="video-screen">
                <div className="preview-grid" aria-hidden="true">
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
                <div className="playback-mark" aria-hidden="true" />
                <p>{sourceFileName}</p>
              </div>
              <div className="scrubber" aria-hidden="true">
                <span style={{ width: "18%" }} />
                <span style={{ width: "24%" }} />
                <span style={{ width: "13%" }} />
                <span style={{ width: "31%" }} />
              </div>
            </div>

            <dl className="source-stats" aria-label={WORKSPACE_COPY.preview.sourceInfo}>
              <div>
                <dt>{WORKSPACE_COPY.preview.duration}</dt>
                <dd>{sourceDuration}</dd>
              </div>
              <div>
                <dt>{WORKSPACE_COPY.preview.resolution}</dt>
                <dd>{sourceResolution}</dd>
              </div>
              <div>
                <dt>{WORKSPACE_COPY.preview.fileSize}</dt>
                <dd>{sourceSize}</dd>
              </div>
            </dl>

            <form className="source-form" onSubmit={handleUpload}>
              <div className="field-grid">
                <label>
                  <span>{WORKSPACE_COPY.upload.titleLabel}</span>
                  <input
                    value={title}
                    onChange={(event) => setTitle(event.target.value)}
                    placeholder={WORKSPACE_COPY.workspace.titleFallback}
                  />
                </label>
                <label>
                  <span>{WORKSPACE_COPY.upload.purposeLabel}</span>
                  <select
                    value={purpose}
                    onChange={(event) => setPurpose(event.target.value as ContentPurpose)}
                  >
                    {purposeOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>{WORKSPACE_COPY.upload.goalLabel}</span>
                  <select
                    value={outputGoal}
                    onChange={(event) => setOutputGoal(event.target.value as OutputGoal)}
                  >
                    {outputGoalOptions.map((option) => (
                      <option key={option.value} value={option.value}>
                        {option.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  <span>{WORKSPACE_COPY.upload.modeLabel}</span>
                  <select
                    value={analysisMode}
                    onChange={(event) => setAnalysisMode(event.target.value as AnalysisMode)}
                  >
                    {runtimeConfig.modes.map((mode) => (
                      <option key={mode} value={mode}>
                        {WORKSPACE_COPY.modeLabels[mode]}
                      </option>
                    ))}
                  </select>
                </label>
              </div>

              <div className="upload-row">
                <label className="drop-zone">
                  <input
                    type="file"
                    accept=".mp4,.mov,.m4v,video/mp4,video/quicktime"
                    onChange={handleFileChange}
                  />
                  <span>{selectedFile?.name ?? WORKSPACE_COPY.upload.dropCta}</span>
                  <small>{WORKSPACE_COPY.upload.help}</small>
                </label>
                <button type="submit" className="primary-action" disabled={uploading || !selectedFile}>
                  {uploading ? "가져오는 중" : WORKSPACE_COPY.actions.createProject}
                </button>
              </div>
            </form>
          </section>

          <section id="script" className="script-panel glass-shell" aria-labelledby="script-title">
            <div className="panel-heading">
              <div>
                <p className="eyebrow">{WORKSPACE_COPY.sections.script}</p>
                <h2 id="script-title">{WORKSPACE_COPY.script.title}</h2>
                <p>{WORKSPACE_COPY.script.subtitle}</p>
              </div>
              <span className="soft-badge">{acceptedSegments}개 승인</span>
            </div>

            <div className="timeline-list" aria-label="컷 후보 목록">
              {timelineItems.map((item) => {
                const isAccepted = item.status === "accepted";
                const isRejected = item.status === "rejected";

                return (
                  <article key={item.segment_id} className="timeline-item">
                    <div className="item-meta">
                      <span>{formatTimeRange(item.start_ms, item.end_ms)}</span>
                      <strong>{formatSegmentType(item.type)}</strong>
                    </div>
                    <div>
                      <p>{item.transcript ?? item.reason}</p>
                      {item.transcript ? <small>{item.reason}</small> : null}
                    </div>
                    <div className="item-actions">
                      <span className="status-chip">{formatSegmentStatus(item.status)}</span>
                      <button
                        type="button"
                        onClick={() => updateSegmentStatus(item, isAccepted ? "pending" : "accepted")}
                      >
                        {isAccepted ? WORKSPACE_COPY.actions.undoAccept : WORKSPACE_COPY.actions.accept}
                      </button>
                      <button
                        type="button"
                        className="ghost-button"
                        onClick={() => updateSegmentStatus(item, isRejected ? "pending" : "rejected")}
                      >
                        {isRejected ? "제외 취소" : WORKSPACE_COPY.actions.reject}
                      </button>
                    </div>
                  </article>
                );
              })}
              {timelineItems.length === 0 ? (
                <p className="empty-state">{WORKSPACE_COPY.status.noDraft}</p>
              ) : null}
            </div>

            <div className="subtitle-list" aria-label="자막 편집 목록">
              <div className="subsection-heading">
                <h3>{WORKSPACE_COPY.script.subtitlePlaceholder}</h3>
                <span>{analysisResult?.subtitles.length ?? 0}개</span>
              </div>
              {(analysisResult?.subtitles ?? []).map((subtitle) => (
                <form
                  key={subtitle.subtitle_id}
                  className="subtitle-row"
                  onSubmit={(event) => handleSubtitleSave(event, subtitle)}
                >
                  <span>{formatTimeRange(subtitle.start_ms, subtitle.end_ms)}</span>
                  <textarea
                    name="text"
                    defaultValue={subtitle.edited_text ?? subtitle.text}
                    aria-label={`자막 ${formatMs(subtitle.start_ms)}`}
                    placeholder={WORKSPACE_COPY.script.subtitlePlaceholder}
                  />
                  <button type="submit">{WORKSPACE_COPY.actions.save}</button>
                </form>
              ))}
              {(analysisResult?.subtitles.length ?? 0) === 0 ? (
                <p className="empty-state">{WORKSPACE_COPY.status.noSubtitles}</p>
              ) : null}
            </div>
          </section>

          <aside
            id="ai-suggestions"
            className="ai-panel glass-shell"
            aria-labelledby="ai-panel-title"
          >
            <div className="panel-heading">
              <div>
                <p className="eyebrow">{WORKSPACE_COPY.sections.suggestions}</p>
                <h2 id="ai-panel-title">{WORKSPACE_COPY.aiPanel.title}</h2>
              </div>
              <span className="soft-badge">{timelineItems.length}개 후보</span>
            </div>

            <section className="progress-panel" aria-labelledby="progress-title">
              <h3 id="progress-title">{WORKSPACE_COPY.aiPanel.progressTitle}</h3>
              <div className="step-list">
                {pipelineSteps.map((step) => (
                  <div key={step.label} className="step-row">
                    <div>
                      <span>{step.label}</span>
                      <strong>{step.state}</strong>
                    </div>
                    <div className="meter" aria-hidden="true">
                      <span style={{ width: `${step.value}%` }} />
                    </div>
                  </div>
                ))}
              </div>
            </section>

            <section className="thumbnail-panel" aria-labelledby="thumbnail-title">
              <div className="subsection-heading">
                <h3 id="thumbnail-title">{WORKSPACE_COPY.aiPanel.thumbnailTitle}</h3>
                <button type="button" onClick={generateThumbnails} disabled={!createdProject}>
                  {WORKSPACE_COPY.actions.generate}
                </button>
              </div>
              <div className="thumbnail-list">
                {thumbnailCandidates.map((candidate, index) => (
                  <article key={candidate.thumbnail_id} className="thumbnail-card">
                    <div className="thumb-preview" data-index={index + 1} />
                    <div>
                      <strong>{formatMs(candidate.timestamp_ms)}</strong>
                      <p>{candidate.reason}</p>
                      <small>{formatThumbnailStatus(candidate.status)}</small>
                    </div>
                    <button
                      type="button"
                      onClick={() =>
                        updateThumbnailStatus(
                          candidate,
                          candidate.status === "selected" ? "pending" : "selected"
                        )
                      }
                    >
                      {candidate.status === "selected" ? "선택 취소" : "선택"}
                    </button>
                  </article>
                ))}
                {thumbnailCandidates.length === 0 ? (
                  <p className="empty-state">{WORKSPACE_COPY.status.noThumbnails}</p>
                ) : null}
              </div>

              <form className="direct-frame-form" onSubmit={createDirectFrameThumbnail}>
                <label>
                  <span>{WORKSPACE_COPY.aiPanel.directFrameTitle}</span>
                  <input
                    name="seconds"
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="12.0"
                    aria-label="프레임 시간(초)"
                  />
                </label>
                <button type="submit" disabled={!createdProject}>
                  {WORKSPACE_COPY.actions.chooseFrame}
                </button>
              </form>
            </section>

            <section
              id="export-settings"
              className="export-panel"
              aria-labelledby="export-title"
            >
              <div className="subsection-heading">
                <h3 id="export-title">{WORKSPACE_COPY.aiPanel.exportTitle}</h3>
                <span>{selectedThumbnails}개 선택</span>
              </div>
              <div className="segmented-control" aria-label="화면 비율">
                {aspectRatioOptions.map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    aria-pressed={exportAspectRatio === option.value}
                    data-active={exportAspectRatio === option.value}
                    onClick={() => setExportAspectRatio(option.value)}
                  >
                    {option.label}
                  </button>
                ))}
              </div>
              <label className="export-toggle">
                <input
                  type="checkbox"
                  checked={includeSubtitles}
                  onChange={(event) => setIncludeSubtitles(event.target.checked)}
                />
                <span>{WORKSPACE_COPY.export.includeSubtitles}</span>
              </label>
              <label className="export-toggle">
                <input
                  type="checkbox"
                  checked={includeThumbnail}
                  onChange={(event) => setIncludeThumbnail(event.target.checked)}
                />
                <span>{WORKSPACE_COPY.export.includeThumbnail}</span>
              </label>
              {exportJob ? (
                <p className="export-result">
                  {formatExportStatus(exportJob.status)} | {exportJob.resolution} |{" "}
                  {exportJob.download_url}
                </p>
              ) : null}
              <button
                type="button"
                className="primary-action full-width"
                onClick={createExport}
                disabled={!createdProject}
              >
                {WORKSPACE_COPY.actions.render}
              </button>
            </section>
          </aside>
        </section>
      </section>
    </main>
  );
}

function readErrorMessage(payload: unknown, fallback: string): string {
  if (!isObject(payload)) {
    return fallback;
  }
  const detail = payload.detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (!isObject(detail) || !isObject(detail.error)) {
    return fallback;
  }
  return typeof detail.error.message === "string" ? detail.error.message : fallback;
}

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null;
}

function formatMs(value: number): string {
  const totalSeconds = Math.max(0, Math.floor(value / 1000));
  const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function formatTimeRange(startMs: number, endMs: number): string {
  return `${formatMs(startMs)}-${formatMs(endMs)}`;
}

function formatDuration(value: number): string {
  const totalSeconds = Math.max(0, Math.floor(value / 1000));
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = String(totalSeconds % 60).padStart(2, "0");
  return `${minutes}:${seconds}`;
}

function formatBytes(value: number): string {
  if (value >= 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024 * 1024)).toFixed(1)}GB`;
  }
  if (value >= 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)}MB`;
  }
  return `${Math.max(1, Math.round(value / 1024))}KB`;
}

function formatSegmentType(type: SegmentDraft["type"]): string {
  return type === "cut" ? WORKSPACE_COPY.script.cutBadge : WORKSPACE_COPY.script.highlightBadge;
}

function formatSegmentStatus(status: SegmentDraft["status"]): string {
  return WORKSPACE_COPY.stateLabels[status];
}

function formatThumbnailStatus(status: ThumbnailCandidate["status"]): string {
  return status === "custom_selected"
    ? WORKSPACE_COPY.stateLabels.custom_selected
    : WORKSPACE_COPY.stateLabels[status];
}

function formatExportStatus(status: ExportJob["status"]): string {
  return WORKSPACE_COPY.stateLabels[status];
}

function formatAnalysisStatus(status: AnalysisResponse["analysis"]["status"]): string {
  return WORKSPACE_COPY.stateLabels[status];
}

function formatJobStatus(status: string): string {
  switch (status.toLowerCase()) {
    case "queued":
      return WORKSPACE_COPY.stateLabels.queued;
    case "running":
    case "processing":
    case "analyzing":
      return WORKSPACE_COPY.stateLabels.running;
    case "completed":
      return WORKSPACE_COPY.stateLabels.completed;
    case "failed":
      return WORKSPACE_COPY.stateLabels.failed;
    default:
      return status;
  }
}
