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

const timelineItems = [
  { time: "00:18", kind: "Cut", title: "Long pause", status: "Pending" },
  { time: "01:42", kind: "Highlight", title: "Key explanation", status: "Pending" },
  { time: "03:06", kind: "Subtitle", title: "Manual sync", status: "Draft" }
];

const thumbnailCandidates = [
  { time: "01:44", reason: "Sharp frame" },
  { time: "02:12", reason: "Subject centered" },
  { time: "04:28", reason: "Bright scene" }
];

export default function WorkspacePage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [purpose, setPurpose] = useState<ContentPurpose>("short_form");
  const [outputGoal, setOutputGoal] = useState<OutputGoal>("highlight_extraction");
  const [analysisMode, setAnalysisMode] = useState<AnalysisMode>("standard");
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("Ready for a local upload.");
  const [createdProject, setCreatedProject] = useState<ProjectCreateResponse | null>(null);

  const pipelineSteps = useMemo(
    () => [
      {
        label: "Upload",
        state: createdProject ? "Ready" : selectedFile ? "Selected" : "Ready",
        value: createdProject ? 100 : selectedFile ? 35 : 0
      },
      {
        label: "Analysis",
        state: createdProject?.analysis_job.status ?? "Queued",
        value: createdProject?.analysis_job.progress_percent ?? 0
      },
      { label: "Draft", state: createdProject ? "Waiting" : "Idle", value: 0 },
      { label: "Export", state: "Idle", value: 0 }
    ],
    [createdProject, selectedFile]
  );

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
                <article key={`${item.kind}-${item.time}`} className="timeline-item">
                  <span>{item.time}</span>
                  <strong>{item.kind}</strong>
                  <p>{item.title}</p>
                  <button type="button">{item.status}</button>
                </article>
              ))}
            </div>
          </div>

          <div className="thumbnail-panel">
            <div className="section-heading">
              <div>
                <p className="eyebrow">Thumbnail</p>
                <h2>Candidates</h2>
              </div>
              <button type="button">Frame Pick</button>
            </div>
            <div className="thumbnail-grid">
              {thumbnailCandidates.map((candidate, index) => (
                <article key={candidate.time} className="thumbnail-card">
                  <div className="thumb-preview" data-index={index + 1} />
                  <strong>{candidate.time}</strong>
                  <p>{candidate.reason}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="export" className="export-band" aria-label="Export settings">
          <div>
            <p className="eyebrow">Output</p>
            <h2>Render Queue</h2>
          </div>
          <div className="segmented-control" aria-label="Aspect ratio">
            <button type="button">Original</button>
            <button type="button">9:16</button>
            <button type="button">1:1</button>
          </div>
          <button type="button" className="primary-action">
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
