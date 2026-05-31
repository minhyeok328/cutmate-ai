"use client";

import type { ChangeEvent, FormEvent } from "react";
import { useMemo, useState } from "react";

import { runtimeConfig, type AnalysisMode } from "@/lib/config";

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

export default function WorkspacePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [purpose, setPurpose] = useState<ContentPurpose>("short_form");
  const [outputGoal, setOutputGoal] = useState<OutputGoal>("highlight_extraction");
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("standard");
  const [uploading, setUploading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Ready for a local upload.");
  const [createdProject, setCreatedProject] = useState<ProjectCreateResponse | null>(null);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse["analysis"] | null>(null);
  const [thumbnailCandidates, setThumbnailCandidates] = useState<ThumbnailCandidate[]>([]);
  const [exportAspectRatio, setExportAspectRatio] = useState<ExportJob["aspect_ratio"]>("original");
  const [includeSubtitles, setIncludeSubtitles] = useState(true);
  const [includeThumbnail, setIncludeThumbnail] = useState(true);
  const [exportJob, setExportJob] = useState<ExportJob | null>(null);

  const pipelineSteps = useMemo(
    () => [
      {
        label: "Upload",
        state: createdProject ? "Ready" : selectedFile ? "Selected" : "Ready",
        value: createdProject ? 100 : selectedFile ? 35 : 0
      },
      {
        label: "Analysis",
        state: analysisResult?.status ?? createdProject?.analysis_job.status ?? "Queued",
        value: analysisResult ? 100 : (createdProject?.analysis_job.progress_percent ?? 0)
      },
      { label: "Draft", state: analysisResult ? "Ready" : createdProject ? "Waiting" : "Idle", value: analysisResult ? 100 : 0 },
      { label: "Export", state: "Idle", value: 0 }
    ],
    [analysisResult, createdProject, selectedFile]
  );

  const timelineItems = [
    ...(analysisResult?.cut_candidates ?? []),
    ...(analysisResult?.highlight_candidates ?? [])
  ].sort((first, second) => first.start_ms - second.start_ms);

  async function handleUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!selectedFile) {
      setStatusMessage("Select a video before uploading.");
      return;
    }

    setUploading(true);
    setStatusMessage("Uploading to the local API...");
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
        setStatusMessage(readErrorMessage(payload));
        return;
      }
      const projectResponse = payload as ProjectCreateResponse;
      setCreatedProject(projectResponse);
      setAnalysisResult(null);
      setThumbnailCandidates([]);
      setExportJob(null);
      setStatusMessage(`Queued ${projectResponse.analysis_job.mode} analysis locally.`);
    } catch {
      setStatusMessage("Local API is unavailable.");
    } finally {
      setUploading(false);
    }
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    setSelectedFile(nextFile);
    setStatusMessage(nextFile ? `${nextFile.name} selected.` : "Ready for a local upload.");
  }

  async function handleRunAnalysis() {
    if (!createdProject) {
      setStatusMessage("Create a project before analysis.");
      return;
    }

    setAnalyzing(true);
    setStatusMessage("Running local deterministic analysis...");
    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/analysis/run`,
        { method: "POST" }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload));
        return;
      }
      const analysisPayload = payload as AnalysisResponse;
      setAnalysisResult(analysisPayload.analysis);
      setStatusMessage("Draft analysis is ready for review.");
    } catch {
      setStatusMessage("Local analysis API is unavailable.");
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
      setStatusMessage("Subtitle text cannot be empty.");
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
        setStatusMessage(readErrorMessage(payload));
        return;
      }
      const updated = (payload as { subtitle: SubtitleDraft }).subtitle;
      setAnalysisResult({
        ...analysisResult,
        subtitles: analysisResult.subtitles.map((item) =>
          item.subtitle_id === updated.subtitle_id ? updated : item
        )
      });
      setStatusMessage("Subtitle edit saved.");
    } catch {
      setStatusMessage("Could not save subtitle edit.");
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
        setStatusMessage(readErrorMessage(payload));
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
      setStatusMessage(`${updated.type} candidate marked ${updated.status}.`);
    } catch {
      setStatusMessage("Could not update candidate status.");
    }
  }

  async function generateThumbnails() {
    if (!createdProject) {
      setStatusMessage("Create a project before generating thumbnails.");
      return;
    }

    try {
      const response = await fetch(
        `${runtimeConfig.apiUrl}/api/v1/projects/${createdProject.project.project_id}/thumbnails/generate`,
        { method: "POST" }
      );
      const payload = (await response.json()) as unknown;
      if (!response.ok) {
        setStatusMessage(readErrorMessage(payload));
        return;
      }
      const nextCandidates = (payload as { thumbnail_candidates: ThumbnailCandidate[] })
        .thumbnail_candidates;
      setThumbnailCandidates(nextCandidates);
      setStatusMessage("Thumbnail candidates generated.");
    } catch {
      setStatusMessage("Could not generate thumbnail candidates.");
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
        setStatusMessage(readErrorMessage(payload));
        return;
      }
      const updated = (payload as { thumbnail: ThumbnailCandidate }).thumbnail;
      setThumbnailCandidates((items) =>
        items.map((item) => (item.thumbnail_id === updated.thumbnail_id ? updated : item))
      );
      setStatusMessage(`Thumbnail marked ${updated.status}.`);
    } catch {
      setStatusMessage("Could not update thumbnail status.");
    }
  }

  async function createDirectFrameThumbnail(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!createdProject) {
      setStatusMessage("Create a project before selecting a frame.");
      return;
    }

    const formData = new FormData(event.currentTarget);
    const seconds = Number(formData.get("seconds") ?? 0);
    if (!Number.isFinite(seconds) || seconds < 0) {
      setStatusMessage("Frame timestamp must be zero or greater.");
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
        setStatusMessage(readErrorMessage(payload));
        return;
      }
      const created = (payload as { thumbnail: ThumbnailCandidate }).thumbnail;
      setThumbnailCandidates((items) => [...items, created]);
      setStatusMessage("Direct frame thumbnail selected.");
    } catch {
      setStatusMessage("Could not select direct frame thumbnail.");
    }
  }

  async function createExport() {
    if (!createdProject) {
      setStatusMessage("Create a project before rendering.");
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
        setStatusMessage(readErrorMessage(payload));
        return;
      }
      const created = (payload as { export_job: ExportJob }).export_job;
      setExportJob(created);
      setStatusMessage("Export render completed locally.");
    } catch {
      setStatusMessage("Could not create export job.");
    }
  }

  return (
    <main className="workspace-shell">
      <aside className="sidebar" aria-label="CutMate AI navigation">
        <div>
          <p className="eyebrow">CutMate AI</p>
          <h1>Review Workspace</h1>
        </div>
        <nav className="nav-list" aria-label="Workflow">
          <a href="#upload">Upload</a>
          <a href="#analysis">Analysis</a>
          <a href="#draft">Draft</a>
          <a href="#export">Export</a>
        </nav>
        <div className="runtime-panel">
          <span>Mode</span>
          <strong>{analysisMode[0].toUpperCase() + analysisMode.slice(1)}</strong>
          <small>{runtimeConfig.qualityLocalLlm} local quality option</small>
        </div>
      </aside>

      <section className="workspace-main">
        <header className="topbar">
          <div>
            <p className="eyebrow">Local-first</p>
            <h2>{createdProject?.project.title ?? "Untitled project"}</h2>
          </div>
          <div className="topbar-actions">
            <button type="button" className="icon-button" aria-label="Open settings">
              Settings
            </button>
            <button type="button" onClick={handleRunAnalysis} disabled={!createdProject || analyzing}>
              {analyzing ? "Analyzing" : "Run Analysis"}
            </button>
            <button type="button">Export</button>
          </div>
        </header>

        <section id="upload" className="upload-band" aria-labelledby="upload-title">
          <div>
            <p className="eyebrow">Source</p>
            <h2 id="upload-title">Upload Queue</h2>
            <p className="compact-copy">MP4, MOV, M4V | 20 min max | 2 GB upload limit</p>
          </div>
          <form className="upload-form" onSubmit={handleUpload}>
            <div className="field-grid">
              <label>
                <span>Title</span>
                <input value={title} onChange={(event) => setTitle(event.target.value)} />
              </label>
              <label>
                <span>Purpose</span>
                <select
                  value={purpose}
                  onChange={(event) => setPurpose(event.target.value as ContentPurpose)}
                >
                  <option value="short_form">Short form</option>
                  <option value="vlog">Vlog</option>
                  <option value="lecture">Lecture</option>
                  <option value="interview">Interview</option>
                  <option value="promotional_video">Promotional</option>
                </select>
              </label>
              <label>
                <span>Goal</span>
                <select
                  value={outputGoal}
                  onChange={(event) => setOutputGoal(event.target.value as OutputGoal)}
                >
                  <option value="highlight_extraction">Highlights</option>
                  <option value="source_summary">Summary</option>
                  <option value="subtitle_generation">Subtitles</option>
                  <option value="short_form_conversion">Short form cut</option>
                </select>
              </label>
              <label>
                <span>Mode</span>
                <select
                  value={analysisMode}
                  onChange={(event) => setAnalysisMode(event.target.value as AnalysisMode)}
                >
                  {runtimeConfig.modes.map((mode) => (
                    <option key={mode} value={mode}>
                      {mode[0].toUpperCase() + mode.slice(1)}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <label className="drop-zone">
              <input
                type="file"
                accept=".mp4,.mov,.m4v,video/mp4,video/quicktime"
                onChange={handleFileChange}
              />
              <span>{selectedFile?.name ?? "Select Video"}</span>
            </label>
            <div className="upload-actions">
              <p className="status-line">{statusMessage}</p>
              <button type="submit" disabled={uploading || !selectedFile}>
                {uploading ? "Uploading" : "Create Project"}
              </button>
            </div>
          </form>
        </section>

        <section className="split-layout">
          <div className="video-workbench" aria-label="Video preview">
            <div className="video-frame">
              <div className="frame-subject" />
              <div className="frame-caption">
                {createdProject?.project.metadata.source_file_name ?? "Preview"}
              </div>
            </div>
            <div className="scrubber" aria-hidden="true">
              <span style={{ width: "18%" }} />
              <span style={{ width: "24%" }} />
              <span style={{ width: "13%" }} />
              <span style={{ width: "31%" }} />
            </div>
          </div>

          <div id="analysis" className="analysis-panel" aria-labelledby="analysis-title">
            <p className="eyebrow">Analysis</p>
            <h2 id="analysis-title">Pipeline</h2>
            <div className="step-list">
              {pipelineSteps.map((step) => (
                <div key={step.label} className="step-row">
                  <span>{step.label}</span>
                  <strong>{step.state}</strong>
                  <div className="meter" aria-hidden="true">
                    <span style={{ width: `${step.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="draft" className="draft-grid" aria-label="Edit draft">
          <div className="timeline-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Draft</p>
                <h2>Timeline</h2>
              </div>
              <button type="button">Apply Selected</button>
            </div>
            <div className="timeline-list">
              {timelineItems.map((item) => (
                <article key={item.segment_id} className="timeline-item">
                  <span>{formatMs(item.start_ms)}</span>
                  <strong>{item.type === "cut" ? "Cut" : "Highlight"}</strong>
                  <p>{item.reason}</p>
                  <button
                    type="button"
                    onClick={() =>
                      updateSegmentStatus(item, item.status === "accepted" ? "pending" : "accepted")
                    }
                  >
                    {item.status}
                  </button>
                </article>
              ))}
              {timelineItems.length === 0 ? <p className="empty-state">No draft candidates yet.</p> : null}
            </div>
            <div className="subtitle-list">
              {(analysisResult?.subtitles ?? []).map((subtitle) => (
                <form
                  key={subtitle.subtitle_id}
                  className="subtitle-row"
                  onSubmit={(event) => handleSubtitleSave(event, subtitle)}
                >
                  <span>{formatMs(subtitle.start_ms)}</span>
                  <input
                    name="text"
                    defaultValue={subtitle.edited_text ?? subtitle.text}
                    aria-label={`Subtitle at ${formatMs(subtitle.start_ms)}`}
                  />
                  <button type="submit">Save</button>
                </form>
              ))}
            </div>
          </div>

          <div className="thumbnail-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Thumbnail</p>
                <h2>Candidates</h2>
              </div>
              <button type="button" onClick={generateThumbnails} disabled={!createdProject}>
                Generate
              </button>
            </div>
            <div className="thumbnail-grid">
              {thumbnailCandidates.map((candidate, index) => (
                <article key={candidate.thumbnail_id} className="thumbnail-card">
                  <div className="thumb-preview" data-index={index + 1} />
                  <strong>{formatMs(candidate.timestamp_ms)}</strong>
                  <p>{candidate.reason}</p>
                  <button
                    type="button"
                    onClick={() =>
                      updateThumbnailStatus(
                        candidate,
                        candidate.status === "selected" ? "pending" : "selected"
                      )
                    }
                  >
                    {candidate.status}
                  </button>
                </article>
              ))}
            </div>
            <form className="direct-frame-form" onSubmit={createDirectFrameThumbnail}>
              <input name="seconds" type="number" min="0" step="0.1" placeholder="12.0" />
              <button type="submit" disabled={!createdProject}>
                Frame Pick
              </button>
            </form>
          </div>
        </section>

        <section id="export" className="export-band" aria-label="Export settings">
          <div>
            <p className="eyebrow">Output</p>
            <h2>Render Queue</h2>
            {exportJob ? (
              <p className="compact-copy">
                {exportJob.status} | {exportJob.resolution} | {exportJob.download_url}
              </p>
            ) : null}
          </div>
          <div className="segmented-control" aria-label="Aspect ratio">
            {(["original", "9:16", "1:1"] as const).map((aspectRatio) => (
              <button
                key={aspectRatio}
                type="button"
                data-active={exportAspectRatio === aspectRatio}
                onClick={() => setExportAspectRatio(aspectRatio)}
              >
                {aspectRatio === "original" ? "Original" : aspectRatio}
              </button>
            ))}
          </div>
          <label className="export-toggle">
            <input
              type="checkbox"
              checked={includeSubtitles}
              onChange={(event) => setIncludeSubtitles(event.target.checked)}
            />
            Subtitles
          </label>
          <label className="export-toggle">
            <input
              type="checkbox"
              checked={includeThumbnail}
              onChange={(event) => setIncludeThumbnail(event.target.checked)}
            />
            Thumbnail
          </label>
          <button type="button" className="primary-action" onClick={createExport}>
            Render
          </button>
        </section>
      </section>
    </main>
  );
}

function readErrorMessage(payload: unknown): string {
  if (!isObject(payload)) {
    return "Upload failed.";
  }
  const detail = payload.detail;
  if (!isObject(detail) || !isObject(detail.error)) {
    return "Upload failed.";
  }
  return typeof detail.error.message === "string" ? detail.error.message : "Upload failed.";
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
