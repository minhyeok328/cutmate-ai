# CutMate AI API Contract

Status: Draft contract for MVP parallel implementation
Date: 2026-05-31
Owner: Integration Coordinator Agent for API/Data contracts
Applies to: Next.js TypeScript frontend, Python FastAPI backend, SQLite, local-first worker

## Scope

This contract defines the app-local HTTP API surface for CutMate AI MVP. It freezes endpoint names, DTO names, status enums, error codes, ownership behavior, deleted-project behavior, upload validation, async analysis jobs, export jobs, and download rules.

The API must support the MVP as a local-first app. Core analysis, subtitles, cut/highlight recommendations, thumbnail recommendations, and exports must not depend on any external API. Quality modes may use local model runtimes only unless a future contract explicitly adds opt-in external services.

This contract does not create implementation code.

## Global Rules

- Base path: `/api/v1`.
- Default request and response format: JSON over HTTP.
- Upload requests use `multipart/form-data`.
- Download responses stream binary content from authorized backend endpoints.
- IDs exposed through the API are opaque string IDs, not SQLite rowids.
- API DTOs may include `owner_id` or `user_id` as opaque string IDs so future multi-user auth can be added without reshaping contracts.
- Request bodies must not accept `owner_id` or `user_id` for project ownership. The backend derives ownership from the authenticated or local-current user context.
- MVP single-user mode must still create and use a real user identity, such as a local default user row.
- Every project-scoped endpoint must enforce server-side ownership checks.
- Project list endpoints must return only projects owned by the current user and not deleted.
- Deleted projects must block all access to source videos, generated assets, analysis jobs, subtitles, recommendations, exports, and downloads.
- API responses must never include local filesystem paths, storage keys, raw tool stderr, stack traces, environment values, model filesystem paths, SQLite rowids, or internal numeric thumbnail scores.
- Error responses must be sanitized and stable enough for frontend handling.
- Timestamps use ISO 8601 UTC strings.
- Video times use integer milliseconds in API contracts: `duration_ms`, `start_ms`, `end_ms`, and `timestamp_ms`.

## Ownership And Deleted-Project Behavior

All project-scoped endpoints first resolve the project by `project_id` and current `user_id`.

| Case | Required response |
| --- | --- |
| Project exists, same owner, not deleted | Continue request. |
| Project exists, same owner, `deleted_at` set or status `deleted` | `410 Gone` with `PROJECT_DELETED`. |
| Project missing | `404 Not Found` with `PROJECT_NOT_FOUND`. |
| Project belongs to another user | `404 Not Found` with `PROJECT_NOT_FOUND`. |
| Nested resource missing under an accessible project | `404 Not Found` with resource-specific code. |
| Nested resource belongs to another project | `404 Not Found` with resource-specific code. |

The API may return `401 UNAUTHENTICATED` when no valid local or authenticated user context exists. It must not reveal whether another user's project or asset exists.

## Upload Validation Contract

The upload endpoint must validate all of the following on the backend:

- Extension allowlist: `mp4`, `mov`, `m4v`.
- MIME/container compatibility using local media inspection, not filename alone.
- Maximum duration: 20 minutes, represented as `1_200_000` ms.
- Maximum upload size: 2 GB, represented as `2_147_483_648` bytes.
- File must be parseable by local media tooling.
- Filename is display-only and must be sanitized before storage or UI display.
- Client-provided paths must be ignored.

Unsupported format, over-size, over-duration, and corrupt media failures must not create an analysis job. Over-duration videos must not start analysis.

No-audio videos are allowed. The analysis job records a warning and skips subtitle generation while continuing scene, cut, highlight, and thumbnail processing.

## Error Envelope

All JSON error responses use `ErrorEnvelope`.

```ts
type ErrorEnvelope = {
  error: {
    code: ErrorCode;
    message: string;
    retryable: boolean;
    request_id?: string;
    details?: Record<string, string | number | boolean | null>;
  };
};
```

`message` and `details` are user-safe. They must not include raw stderr, stack traces, absolute paths, storage keys, SQL text, model paths, secrets, or internal thumbnail scores.

## Error Codes

| Code | HTTP status | Meaning |
| --- | --- | --- |
| `UNAUTHENTICATED` | 401 | No valid user context exists. |
| `ACCESS_DENIED` | 403 | Authenticated user cannot use a non-project global capability. Do not use for object ownership mismatches. |
| `PROJECT_NOT_FOUND` | 404 | Project is missing or hidden because it belongs to another user. |
| `PROJECT_DELETED` | 410 | Current user's project is deleted and access is blocked. |
| `RESOURCE_NOT_FOUND` | 404 | Nested resource is missing under an accessible project. |
| `VALIDATION_FAILED` | 400 | Request fields failed type, enum, length, range, or state validation. |
| `FILE_REQUIRED` | 400 | Upload request did not include a file. |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | Uploaded file is not `mp4`, `mov`, or `m4v`, or container/MIME validation failed. |
| `UPLOAD_TOO_LARGE` | 413 | Uploaded file exceeds the configured max upload size. |
| `VIDEO_DURATION_EXCEEDED` | 422 | Video duration is greater than 20 minutes. |
| `MEDIA_METADATA_FAILED` | 422 | Local media metadata extraction failed or media appears corrupt. |
| `ANALYSIS_JOB_NOT_FOUND` | 404 | Analysis job is missing under an accessible project. |
| `ANALYSIS_ALREADY_RUNNING` | 409 | Project already has an active analysis job. |
| `ANALYSIS_RETRY_NOT_ALLOWED` | 409 | Failed job cannot be retried in its current state. |
| `ANALYSIS_STEP_FAILED` | 500 | Analysis failed with a sanitized step-level cause. |
| `LOCAL_TOOL_UNAVAILABLE` | 503 | Required local tool is unavailable for the selected mode. |
| `LOCAL_MODEL_MISSING` | 503 | Required local model is unavailable for the selected mode. |
| `EXPORT_JOB_NOT_FOUND` | 404 | Export job is missing under an accessible project. |
| `EXPORT_NOT_READY` | 409 | Export output is not ready for download. |
| `DOWNLOAD_NOT_READY` | 409 | Requested asset is not ready or not downloadable. |
| `ASSET_NOT_FOUND` | 404 | Asset is missing under an accessible project. |
| `INVALID_STATE` | 409 | Request is invalid for the current project, job, segment, thumbnail, or export status. |
| `PROCESSING_UNAVAILABLE` | 503 | Local worker is not available to accept new work. |
| `INTERNAL_ERROR` | 500 | Unexpected sanitized server failure. |

## Enums

```ts
type ProjectStatus =
  | "uploaded"
  | "analyzing"
  | "draft_ready"
  | "exporting"
  | "completed"
  | "failed"
  | "deleted";

type AnalysisJobStatus =
  | "queued"
  | "processing"
  | "completed"
  | "completed_with_warnings"
  | "failed"
  | "retrying";

type AnalysisStep =
  | "upload_validated"
  | "metadata_extraction"
  | "audio_extraction"
  | "speech_recognition"
  | "subtitle_generation"
  | "silence_detection"
  | "scene_analysis"
  | "thumbnail_generation"
  | "recommendation_generation"
  | "draft_generation";

type AnalysisMode = "light" | "standard" | "quality";

type ContentPurpose =
  | "short_form"
  | "vlog"
  | "lecture"
  | "interview"
  | "promotional_video";

type OutputGoal =
  | "source_summary"
  | "highlight_extraction"
  | "subtitle_generation"
  | "short_form_conversion";

type SegmentType = "cut" | "highlight";

type RecommendationStatus =
  | "pending"
  | "accepted"
  | "rejected"
  | "modified";

type ThumbnailStatus =
  | "pending"
  | "selected"
  | "rejected"
  | "custom_selected";

type ExportJobStatus = "queued" | "rendering" | "completed" | "failed";

type ExportAspectRatio = "original" | "ratio_9_16" | "ratio_1_1";

type CropMode = "center" | "manual";

type AssetKind =
  | "original_video"
  | "proxy_video"
  | "analysis_audio"
  | "thumbnail_candidate"
  | "selected_thumbnail"
  | "export_video"
  | "export_thumbnail";
```

## DTOs

### `HealthDTO`

```ts
type HealthDTO = {
  status: "ok";
  local_worker: "available" | "unavailable";
  external_api_mode: "disabled";
};
```

### `UserDTO`

```ts
type UserDTO = {
  user_id: string;
  email?: string | null;
  local_user: boolean;
  created_at: string;
};
```

### `VideoMetadataDTO`

```ts
type VideoMetadataDTO = {
  duration_ms: number;
  width: number;
  height: number;
  fps?: number | null;
  aspect_ratio: string;
  has_audio: boolean;
  source_file_name: string;
  source_extension: "mp4" | "mov" | "m4v";
  source_mime_type?: string | null;
  source_size_bytes: number;
};
```

### `ProjectDTO`

```ts
type ProjectDTO = {
  project_id: string;
  owner_id: string;
  title: string;
  purpose: ContentPurpose;
  output_goal: OutputGoal;
  status: ProjectStatus;
  metadata: VideoMetadataDTO;
  selected_thumbnail_id?: string | null;
  created_at: string;
  updated_at: string;
  deleted_at?: string | null;
};
```

### `UploadProjectRequest`

Multipart fields:

```ts
type UploadProjectRequest = {
  file: File;
  title?: string;
  purpose: ContentPurpose;
  output_goal: OutputGoal;
  analysis_mode?: AnalysisMode;
};
```

`owner_id`, `user_id`, local paths, and storage keys are not accepted.

### `ProjectCreateResponse`

```ts
type ProjectCreateResponse = {
  project: ProjectDTO;
  analysis_job: AnalysisJobDTO;
};
```

### `AnalysisJobDTO`

```ts
type AnalysisJobDTO = {
  job_id: string;
  project_id: string;
  owner_id: string;
  status: AnalysisJobStatus;
  mode: AnalysisMode;
  progress_percent: number;
  current_step?: AnalysisStep | null;
  failed_step?: AnalysisStep | null;
  warnings: string[];
  error?: {
    code: ErrorCode;
    message: string;
    retryable: boolean;
  } | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  updated_at: string;
};
```

Warnings and errors are sanitized. They must not expose raw worker output.

### `SubtitleDTO`

```ts
type SubtitleDTO = {
  subtitle_id: string;
  project_id: string;
  start_ms: number;
  end_ms: number;
  text: string;
  edited_text?: string | null;
  created_at: string;
  updated_at: string;
};
```

### `SubtitleUpdateRequest`

```ts
type SubtitleUpdateRequest = {
  start_ms?: number;
  end_ms?: number;
  edited_text?: string | null;
};
```

`start_ms` must be less than `end_ms`, and both must remain within project duration.

### `VideoSegmentDTO`

```ts
type VideoSegmentDTO = {
  segment_id: string;
  project_id: string;
  segment_type: SegmentType;
  start_ms: number;
  end_ms: number;
  transcript?: string | null;
  recommendation_reason: string;
  status: RecommendationStatus;
  created_at: string;
  updated_at: string;
};
```

### `SegmentUpdateRequest`

```ts
type SegmentUpdateRequest = {
  status?: RecommendationStatus;
  start_ms?: number;
  end_ms?: number;
  recommendation_reason?: string;
};
```

Only `pending`, `accepted`, `rejected`, and `modified` are valid status values. User edits that change times must set status to `modified` unless they are only reverting to generated values.

### `ThumbnailCandidateDTO`

```ts
type ThumbnailCandidateDTO = {
  thumbnail_id: string;
  project_id: string;
  timestamp_ms: number;
  image_asset_id: string;
  preview_url: string;
  reason: string;
  tags: string[];
  status: ThumbnailStatus;
  created_at: string;
  updated_at: string;
};
```

`ThumbnailCandidateDTO` must not include `internal_score`, raw ranking weights, local image paths, or storage keys.

### `CustomThumbnailRequest`

```ts
type CustomThumbnailRequest = {
  timestamp_ms: number;
  crop?: {
    aspect_ratio: ExportAspectRatio;
    crop_mode: CropMode;
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
};
```

`timestamp_ms` must be within project duration.

### `ExportCreateRequest`

```ts
type ExportCreateRequest = {
  aspect_ratio: ExportAspectRatio;
  resolution: string;
  include_subtitles: boolean;
  include_thumbnail: boolean;
  crop_mode: CropMode;
  crop?: {
    x?: number;
    y?: number;
    width?: number;
    height?: number;
  };
  highlight_segment_id?: string | null;
};
```

`highlight_segment_id` is required for `ratio_9_16` export unless the backend can derive a selected highlight. The referenced segment must belong to the same owned, non-deleted project.

### `ExportJobDTO`

```ts
type ExportJobDTO = {
  export_id: string;
  project_id: string;
  owner_id: string;
  status: ExportJobStatus;
  aspect_ratio: ExportAspectRatio;
  resolution: string;
  include_subtitles: boolean;
  include_thumbnail: boolean;
  crop_mode: CropMode;
  output_video_asset_id?: string | null;
  thumbnail_asset_id?: string | null;
  download_urls?: {
    video?: string;
    thumbnail?: string;
  };
  error?: {
    code: ErrorCode;
    message: string;
    retryable: boolean;
  } | null;
  created_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  updated_at: string;
};
```

Download URLs are API URLs only. They must not contain local paths or storage keys.

### `TimelineDTO`

```ts
type TimelineDTO = {
  project: ProjectDTO;
  analysis_job?: AnalysisJobDTO | null;
  subtitles: SubtitleDTO[];
  segments: VideoSegmentDTO[];
  thumbnail_candidates: ThumbnailCandidateDTO[];
};
```

## Endpoint List

### Health And Current User

| Method | Path | Request | Success response | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/health` | none | `HealthDTO` | Must not check or call external APIs. |
| `GET` | `/me` | none | `UserDTO` | Returns current local/authenticated user. |

### Projects And Uploads

| Method | Path | Request | Success response | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/projects` | query: pagination optional | `{ "projects": ProjectDTO[] }` | Returns only current user's non-deleted projects. |
| `POST` | `/projects` | `UploadProjectRequest` multipart | `201 ProjectCreateResponse` | Validates upload, creates project, creates queued analysis job. |
| `GET` | `/projects/{project_id}` | none | `ProjectDTO` | Enforces ownership and deleted-project behavior. |
| `PATCH` | `/projects/{project_id}` | title, purpose, output_goal | `ProjectDTO` | No ownership fields accepted. Block if deleted. |
| `DELETE` | `/projects/{project_id}` | none | `{ "project_id": string, "status": "deleted", "deleted_at": string }` | Soft deletes immediately and schedules physical asset deletion within 24 hours. |

### Analysis Jobs

| Method | Path | Request | Success response | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/projects/{project_id}/analysis-jobs` | none | `{ "analysis_jobs": AnalysisJobDTO[] }` | Ordered newest first. |
| `GET` | `/projects/{project_id}/analysis-jobs/{job_id}` | none | `AnalysisJobDTO` | Polling endpoint for progress UI. |
| `POST` | `/projects/{project_id}/analysis-jobs/{job_id}/retry` | optional `{ "mode": AnalysisMode }` | `202 AnalysisJobDTO` | Allowed only for failed jobs with retryable sanitized errors. |

Analysis processing is asynchronous. Worker failures update `AnalysisJobDTO.error` with sanitized code/message only.

### Timeline, Subtitles, And Recommendations

| Method | Path | Request | Success response | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/projects/{project_id}/timeline` | none | `TimelineDTO` | Main edit draft payload. |
| `GET` | `/projects/{project_id}/subtitles` | none | `{ "subtitles": SubtitleDTO[] }` | Ordered by `start_ms`. |
| `PATCH` | `/projects/{project_id}/subtitles/{subtitle_id}` | `SubtitleUpdateRequest` | `SubtitleDTO` | Validates time range and ownership through project. |
| `PATCH` | `/projects/{project_id}/segments/{segment_id}` | `SegmentUpdateRequest` | `VideoSegmentDTO` | Used for accept, reject, modify, and revert behavior. |

Cut and highlight recommendations must never be applied automatically. The frontend applies only user-approved statuses.

### Thumbnail Candidates

| Method | Path | Request | Success response | Notes |
| --- | --- | --- | --- | --- |
| `GET` | `/projects/{project_id}/thumbnail-candidates` | none | `{ "thumbnail_candidates": ThumbnailCandidateDTO[] }` | Returns recommendation reasons, not internal scores. |
| `POST` | `/projects/{project_id}/thumbnail-candidates/{thumbnail_id}/select` | none | `ThumbnailCandidateDTO` | Marks this candidate selected and clears prior selected/custom-selected candidates. |
| `POST` | `/projects/{project_id}/thumbnail-candidates/custom` | `CustomThumbnailRequest` | `ThumbnailCandidateDTO` | Creates a `custom_selected` thumbnail from an in-video frame. |
| `POST` | `/projects/{project_id}/thumbnail-candidates/{thumbnail_id}/reject` | none | `ThumbnailCandidateDTO` | Marks candidate rejected. |

Thumbnail images are served through asset endpoints. The response may include `preview_url` as an API URL, but not a local path.

### Exports And Downloads

| Method | Path | Request | Success response | Notes |
| --- | --- | --- | --- | --- |
| `POST` | `/projects/{project_id}/exports` | `ExportCreateRequest` | `202 ExportJobDTO` | Creates queued render job. |
| `GET` | `/projects/{project_id}/exports` | none | `{ "exports": ExportJobDTO[] }` | Ordered newest first. |
| `GET` | `/projects/{project_id}/exports/{export_id}` | none | `ExportJobDTO` | Polling endpoint for render progress. |
| `POST` | `/projects/{project_id}/exports/{export_id}/retry` | none | `202 ExportJobDTO` | Allowed only for failed retryable render jobs. |
| `GET` | `/projects/{project_id}/assets/{asset_id}/download` | optional query: `disposition` as `inline` or `attachment` | binary stream | Enforces ownership, non-deleted project, asset belongs to project, asset is ready. |

Download endpoints must return `404 ASSET_NOT_FOUND`, `409 DOWNLOAD_NOT_READY`, `409 EXPORT_NOT_READY`, or `410 PROJECT_DELETED` as appropriate. They must never redirect to or expose local filesystem paths.

## State Transitions

### Project

Allowed project transitions:

- `uploaded` -> `analyzing`
- `analyzing` -> `draft_ready`
- `analyzing` -> `failed`
- `draft_ready` -> `exporting`
- `exporting` -> `completed`
- `exporting` -> `failed`
- any non-deleted status -> `deleted`

Deleted is terminal for API access.

### Analysis Job

Allowed analysis job transitions:

- `queued` -> `processing`
- `processing` -> `completed`
- `processing` -> `completed_with_warnings`
- `processing` -> `failed`
- `failed` -> `retrying`
- `retrying` -> `processing`
- `retrying` -> `completed`
- `retrying` -> `completed_with_warnings`
- `retrying` -> `failed`

Only one active analysis job per project may be `queued`, `processing`, or `retrying` at a time.

### Segment Recommendation

Allowed segment statuses:

- Generated recommendations start as `pending`.
- User acceptance sets `accepted`.
- User rejection sets `rejected`.
- User time or rationale edit sets `modified`.
- Reverting a user change may return to `pending` or `accepted`, based on the UI action.

### Thumbnail Candidate

Allowed thumbnail statuses:

- Generated recommendations start as `pending`.
- Selecting a generated candidate sets it to `selected`.
- Direct frame selection creates or updates one `custom_selected` candidate.
- Rejecting a candidate sets `rejected`.
- Only one candidate per project may be `selected` or `custom_selected`.

### Export Job

Allowed export job transitions:

- `queued` -> `rendering`
- `rendering` -> `completed`
- `rendering` -> `failed`

Completed export jobs expose API download URLs for ready assets only.

## Security Requirements

- Enforce ownership server-side for every project, nested resource, asset, analysis job, and export job.
- Treat object ID tampering as `404 PROJECT_NOT_FOUND` or resource-specific `404`, not `403`, to avoid cross-user enumeration.
- Block all access to deleted projects and all associated files immediately after deletion.
- Resolve files from server-owned storage keys only. Never accept a path from the client.
- Reject path traversal, absolute paths, symlinks that escape storage roots, and encoded traversal variants in any storage-facing logic.
- Validate upload extension, content type, media container, size, duration, and parseability before creating an analysis job.
- Escape user-controlled strings such as filenames, titles, transcripts, subtitles, and recommendation edits in frontend rendering.
- Sanitize worker errors before storing or returning them.
- Do not return raw FFmpeg, model runtime, Python, SQL, or OS errors to the client.
- Do not expose internal numeric thumbnail scores in API DTOs.
- Do not require external API keys or send user video, audio, subtitles, thumbnails, or project metadata to external APIs for MVP core flows.
- State-changing routes must use the app's auth/session protection once multi-user auth is added.

## Expansion Notes

- MVP max upload size is fixed at 2 GB (`2_147_483_648` bytes).
- Future expansion must update the workspace profile, API contract, data model contract, media-storage contract, frontend config, backend config, and validation tests in one coordinated change.
