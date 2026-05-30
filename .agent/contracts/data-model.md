# CutMate AI SQLite Data Model Contract

Status: Draft contract for MVP parallel implementation
Date: 2026-05-31
Owner: Integration Coordinator Agent for API/Data contracts
Applies to: Python FastAPI backend, SQLite, local-first worker

## Scope

This contract defines the SQLite data model for CutMate AI MVP. It covers user ownership, projects, media assets, async analysis jobs, subtitles, cut/highlight recommendations, thumbnail candidates, export jobs, deletion scheduling, enum values, constraints, indexes, and safe query rules.

The schema must support a single-user local-first MVP while preserving `owner_id` and `user_id` ownership boundaries for future multi-user auth. Core analysis must not require external APIs.

This contract does not create implementation code.

## Storage And Exposure Rules

- SQLite tables store opaque string IDs as primary keys. Do not expose SQLite rowids.
- Store times as integer milliseconds.
- Store timestamps as ISO 8601 UTC strings.
- Store booleans as integer `0` or `1`.
- Store JSON-like fields as validated JSON text, not ad hoc delimited strings.
- Store server-side file references as opaque `storage_key` values, not public URLs and not user-provided paths.
- Prefer storage keys relative to the configured CutMate storage root. Do not store client-supplied absolute paths.
- API responses must never return `storage_key`, absolute local paths, raw worker stderr, stack traces, or internal numeric thumbnail scores.
- Enable SQLite foreign keys for every connection.

## Parameterized Query And ORM Rule

All SQL must be executed through parameterized queries or ORM query builders. Do not build SQL by concatenating user-controlled values.

Allowed:

```sql
SELECT *
FROM video_projects
WHERE id = :project_id
  AND owner_id = :owner_id
  AND deleted_at IS NULL;
```

Forbidden:

```sql
-- Do not build queries by interpolating project_id, owner_id, sort fields, or filters.
```

Dynamic sorting, filtering, and enum filters must use allowlisted column names and enum values. User-controlled values must never become raw SQL fragments.

## Ownership Query Rule

Every project-scoped table either includes `owner_id` directly or is queried through `video_projects.owner_id`.

Project read/update/delete operations must filter by owner and active deletion state:

```sql
SELECT *
FROM video_projects
WHERE id = :project_id
  AND owner_id = :owner_id
  AND deleted_at IS NULL;
```

Nested resource operations must join through the project:

```sql
SELECT s.*
FROM subtitles s
JOIN video_projects p ON p.id = s.project_id
WHERE s.id = :subtitle_id
  AND s.project_id = :project_id
  AND p.owner_id = :owner_id
  AND p.deleted_at IS NULL;
```

When an owned project is deleted, the API may query by `owner_id` without `deleted_at IS NULL` only to return `PROJECT_DELETED`. No nested resource data or asset metadata may be returned for deleted projects.

## Enum Values

### Project Status

- `uploaded`
- `analyzing`
- `draft_ready`
- `exporting`
- `completed`
- `failed`
- `deleted`

### Analysis Job Status

- `queued`
- `processing`
- `completed`
- `completed_with_warnings`
- `failed`
- `retrying`

### Analysis Mode

- `light`
- `standard`
- `quality`

### Analysis Step

- `upload_validated`
- `metadata_extraction`
- `audio_extraction`
- `speech_recognition`
- `subtitle_generation`
- `silence_detection`
- `scene_analysis`
- `thumbnail_generation`
- `recommendation_generation`
- `draft_generation`

### Content Purpose

- `short_form`
- `vlog`
- `lecture`
- `interview`
- `promotional_video`

### Output Goal

- `source_summary`
- `highlight_extraction`
- `subtitle_generation`
- `short_form_conversion`

### Segment Type

- `cut`
- `highlight`

### Recommendation Status

- `pending`
- `accepted`
- `rejected`
- `modified`

### Thumbnail Status

- `pending`
- `selected`
- `rejected`
- `custom_selected`

### Export Job Status

- `queued`
- `rendering`
- `completed`
- `failed`

### Export Aspect Ratio

- `original`
- `ratio_9_16`
- `ratio_1_1`

### Crop Mode

- `center`
- `manual`

### Asset Kind

- `original_video`
- `proxy_video`
- `analysis_audio`
- `thumbnail_candidate`
- `selected_thumbnail`
- `export_video`
- `export_thumbnail`

### Deletion Task Status

- `queued`
- `processing`
- `completed`
- `failed`

## Tables

### `users`

Stores local and future authenticated users.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque public user ID. Primary key. |
| `email` | TEXT | no | Unique when present. Nullable for local-only MVP user. |
| `display_name` | TEXT | no | User-facing label. |
| `local_user` | INTEGER | yes | `1` for default local user, `0` for future auth user. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `UNIQUE (email)` where supported and email is not null
- `CHECK (local_user IN (0, 1))`

### `video_projects`

Stores one uploaded source video project and its current workflow state.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque project ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `title` | TEXT | yes | User-facing title. Sanitize on output. |
| `purpose` | TEXT | yes | `Content Purpose` enum. |
| `output_goal` | TEXT | yes | `Output Goal` enum. |
| `status` | TEXT | yes | `Project Status` enum. |
| `duration_ms` | INTEGER | yes | Must be `0 <= duration_ms <= 1_200_000`. |
| `width` | INTEGER | yes | Source video width. |
| `height` | INTEGER | yes | Source video height. |
| `fps` | REAL | no | Source frame rate when available. |
| `aspect_ratio` | TEXT | yes | Display ratio such as `16:9`. |
| `has_audio` | INTEGER | yes | `1` if audio track exists, else `0`. |
| `source_file_name` | TEXT | yes | Sanitized display filename only. |
| `source_extension` | TEXT | yes | `mp4`, `mov`, or `m4v`. |
| `source_mime_type` | TEXT | no | Detected MIME/container type. |
| `source_size_bytes` | INTEGER | yes | Must be positive and under max upload limit. |
| `selected_thumbnail_candidate_id` | TEXT | no | References `thumbnail_candidates.id` when selected. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |
| `deleted_at` | TEXT | no | Set immediately when user deletes project. |
| `delete_after_at` | TEXT | no | Must be no later than 24 hours after `deleted_at`. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (selected_thumbnail_candidate_id) REFERENCES thumbnail_candidates(id)`
- enum `CHECK` constraints for `purpose`, `output_goal`, and `status`
- `CHECK (duration_ms >= 0 AND duration_ms <= 1200000)`
- `CHECK (width > 0 AND height > 0)`
- `CHECK (has_audio IN (0, 1))`
- `CHECK (source_extension IN ('mp4', 'mov', 'm4v'))`
- `CHECK (source_size_bytes > 0)`

The app-level max upload size is 2 GB. Keep the limit in application configuration and validation code so future expansion does not require broad schema churn.

### `media_assets`

Stores server-owned references to uploaded, generated, and downloadable files. Asset rows are not public file paths.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque asset ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `kind` | TEXT | yes | `Asset Kind` enum. |
| `storage_key` | TEXT | yes | Server-only storage reference. Never returned by API. |
| `content_type` | TEXT | no | Detected content type. |
| `byte_size` | INTEGER | no | Asset size if known. |
| `checksum_sha256` | TEXT | no | Optional integrity check. |
| `width` | INTEGER | no | Image/video width when applicable. |
| `height` | INTEGER | no | Image/video height when applicable. |
| `duration_ms` | INTEGER | no | Video/audio duration when applicable. |
| `is_downloadable` | INTEGER | yes | `1` when user download may be allowed after auth checks. |
| `created_by_job_id` | TEXT | no | Analysis or export job that created asset. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `deleted_at` | TEXT | no | Set when asset is no longer accessible. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- `UNIQUE (storage_key)`
- enum `CHECK` constraint for `kind`
- `CHECK (is_downloadable IN (0, 1))`
- `CHECK (byte_size IS NULL OR byte_size >= 0)`

Application-level validation must reject absolute paths, traversal segments, encoded traversal, and symlink escapes when resolving `storage_key`.

### `analysis_jobs`

Stores async local analysis job state.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque job ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `status` | TEXT | yes | `Analysis Job Status` enum. |
| `mode` | TEXT | yes | `Analysis Mode` enum. |
| `progress_percent` | INTEGER | yes | `0` through `100`. |
| `current_step` | TEXT | no | `Analysis Step` enum. |
| `failed_step` | TEXT | no | `Analysis Step` enum. |
| `error_code` | TEXT | no | API `ErrorCode` value. |
| `error_summary` | TEXT | no | Sanitized summary only. |
| `retry_of_job_id` | TEXT | no | Previous failed job if retrying. |
| `local_runtime` | TEXT | no | Local runtime label, not a path. |
| `model_profile_json` | TEXT | no | Validated JSON text with local model labels only. |
| `tool_versions_json` | TEXT | no | Validated JSON text with tool names and versions only. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `started_at` | TEXT | no | ISO 8601 UTC. |
| `completed_at` | TEXT | no | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- `FOREIGN KEY (retry_of_job_id) REFERENCES analysis_jobs(id)`
- enum `CHECK` constraints for `status`, `mode`, `current_step`, and `failed_step`
- `CHECK (progress_percent >= 0 AND progress_percent <= 100)`

Raw stderr, stack traces, local command lines, and absolute paths must not be stored in `error_summary`, `model_profile_json`, or `tool_versions_json`.

### `job_events`

Stores sanitized progress events for analysis and export jobs.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque event ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `job_id` | TEXT | yes | References `analysis_jobs.id` or `export_jobs.id` by application convention. |
| `job_type` | TEXT | yes | `analysis` or `export`. |
| `event_type` | TEXT | yes | `step_started`, `progress`, `warning`, `failed`, or `completed`. |
| `step` | TEXT | no | Analysis step or export step label. |
| `message` | TEXT | no | User-safe sanitized message. |
| `progress_percent` | INTEGER | no | `0` through `100`. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- `CHECK (job_type IN ('analysis', 'export'))`
- `CHECK (event_type IN ('step_started', 'progress', 'warning', 'failed', 'completed'))`
- `CHECK (progress_percent IS NULL OR (progress_percent >= 0 AND progress_percent <= 100))`

`message` must be sanitized and must not store raw tool output.

### `subtitles`

Stores generated and user-edited subtitle segments.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque subtitle ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `source_job_id` | TEXT | no | Analysis job that generated this subtitle. |
| `start_ms` | INTEGER | yes | Segment start within project duration. |
| `end_ms` | INTEGER | yes | Segment end within project duration. |
| `text` | TEXT | yes | Generated subtitle text. |
| `edited_text` | TEXT | no | User-edited text. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- `FOREIGN KEY (source_job_id) REFERENCES analysis_jobs(id)`
- `CHECK (start_ms >= 0)`
- `CHECK (end_ms > start_ms)`

Application validation must keep subtitle times within the owning project's `duration_ms`.

### `video_segments`

Stores cut and highlight recommendations.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque segment ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `source_job_id` | TEXT | no | Analysis job that generated this segment. |
| `segment_type` | TEXT | yes | `cut` or `highlight`. |
| `start_ms` | INTEGER | yes | Segment start within project duration. |
| `end_ms` | INTEGER | yes | Segment end within project duration. |
| `transcript` | TEXT | no | Transcript excerpt when available. |
| `recommendation_reason` | TEXT | yes | User-facing reason. |
| `status` | TEXT | yes | `Recommendation Status` enum. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- `FOREIGN KEY (source_job_id) REFERENCES analysis_jobs(id)`
- enum `CHECK` constraints for `segment_type` and `status`
- `CHECK (start_ms >= 0)`
- `CHECK (end_ms > start_ms)`

Cut recommendations must not be treated as applied unless status is `accepted`.

### `thumbnail_candidates`

Stores candidate thumbnails generated from actual video frames and direct user frame selections.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque thumbnail candidate ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `source_job_id` | TEXT | no | Analysis job that generated this candidate. |
| `asset_id` | TEXT | yes | References `media_assets.id`. |
| `timestamp_ms` | INTEGER | yes | Source video frame timestamp. |
| `reason` | TEXT | yes | User-facing recommendation reason. |
| `tags_json` | TEXT | yes | Validated JSON array of string tags. |
| `internal_score` | REAL | no | Internal ranking score. Never returned by API. |
| `rank_index` | INTEGER | no | Display order among generated candidates. |
| `safety_flags_json` | TEXT | no | Validated JSON array/object for internal filtering notes. |
| `status` | TEXT | yes | `Thumbnail Status` enum. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- `FOREIGN KEY (source_job_id) REFERENCES analysis_jobs(id)`
- `FOREIGN KEY (asset_id) REFERENCES media_assets(id)`
- enum `CHECK` constraint for `status`
- `CHECK (timestamp_ms >= 0)`
- `CHECK (internal_score IS NULL OR (internal_score >= 0 AND internal_score <= 1))`
- `CHECK (rank_index IS NULL OR rank_index >= 0)`

Only `reason`, `tags_json`, `timestamp_ms`, API asset ID, and status may flow to frontend DTOs. `internal_score`, ranking weights, and safety internals are backend-only.

### `export_jobs`

Stores async render/export job state.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque export job ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `status` | TEXT | yes | `Export Job Status` enum. |
| `format` | TEXT | yes | MVP value: `mp4`. |
| `aspect_ratio` | TEXT | yes | `Export Aspect Ratio` enum. |
| `resolution` | TEXT | yes | User-selected resolution label. |
| `include_subtitles` | INTEGER | yes | `0` or `1`. |
| `include_thumbnail` | INTEGER | yes | `0` or `1`. |
| `crop_mode` | TEXT | yes | `Crop Mode` enum. |
| `crop_settings_json` | TEXT | no | Validated JSON crop box/settings. |
| `highlight_segment_id` | TEXT | no | Selected highlight for short-form output. |
| `output_asset_id` | TEXT | no | References export video asset when complete. |
| `thumbnail_asset_id` | TEXT | no | References export thumbnail asset when complete. |
| `error_code` | TEXT | no | API `ErrorCode` value. |
| `error_summary` | TEXT | no | Sanitized summary only. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `started_at` | TEXT | no | ISO 8601 UTC. |
| `completed_at` | TEXT | no | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- `FOREIGN KEY (highlight_segment_id) REFERENCES video_segments(id)`
- `FOREIGN KEY (output_asset_id) REFERENCES media_assets(id)`
- `FOREIGN KEY (thumbnail_asset_id) REFERENCES media_assets(id)`
- enum `CHECK` constraints for `status`, `aspect_ratio`, and `crop_mode`
- `CHECK (format IN ('mp4'))`
- `CHECK (include_subtitles IN (0, 1))`
- `CHECK (include_thumbnail IN (0, 1))`

Raw render logs, stderr, stack traces, and command strings must not be stored in `error_summary`.

### `deletion_tasks`

Tracks physical cleanup for deleted project assets.

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `id` | TEXT | yes | Opaque deletion task ID. Primary key. |
| `owner_id` | TEXT | yes | References `users.id`. |
| `project_id` | TEXT | yes | References `video_projects.id`. |
| `status` | TEXT | yes | `Deletion Task Status` enum. |
| `due_at` | TEXT | yes | Must be within 24 hours of project `deleted_at`. |
| `attempts` | INTEGER | yes | Number of cleanup attempts. |
| `last_error_code` | TEXT | no | Sanitized code only. |
| `last_error_summary` | TEXT | no | Sanitized summary only. |
| `created_at` | TEXT | yes | ISO 8601 UTC. |
| `completed_at` | TEXT | no | ISO 8601 UTC. |
| `updated_at` | TEXT | yes | ISO 8601 UTC. |

Constraints:

- `PRIMARY KEY (id)`
- `FOREIGN KEY (owner_id) REFERENCES users(id)`
- `FOREIGN KEY (project_id) REFERENCES video_projects(id)`
- enum `CHECK` constraint for `status`
- `CHECK (attempts >= 0)`

Deletion task errors must not store absolute paths or raw filesystem exceptions.

## Required Indexes

Create indexes equivalent to the following names and purposes:

- `idx_projects_owner_deleted_created` on `video_projects(owner_id, deleted_at, created_at DESC)`
- `idx_projects_owner_status` on `video_projects(owner_id, status)`
- `idx_assets_project_kind` on `media_assets(project_id, kind)`
- `idx_assets_owner_project` on `media_assets(owner_id, project_id)`
- `idx_analysis_jobs_project_created` on `analysis_jobs(project_id, created_at DESC)`
- `idx_analysis_jobs_owner_status` on `analysis_jobs(owner_id, status)`
- `idx_job_events_project_job_created` on `job_events(project_id, job_id, created_at)`
- `idx_subtitles_project_start` on `subtitles(project_id, start_ms)`
- `idx_segments_project_type_start` on `video_segments(project_id, segment_type, start_ms)`
- `idx_segments_project_status` on `video_segments(project_id, status)`
- `idx_thumbnails_project_status_rank` on `thumbnail_candidates(project_id, status, rank_index)`
- `idx_exports_project_created` on `export_jobs(project_id, created_at DESC)`
- `idx_exports_owner_status` on `export_jobs(owner_id, status)`
- `idx_deletion_tasks_due_status` on `deletion_tasks(status, due_at)`

Required partial unique indexes where supported by SQLite:

- `ux_analysis_one_active_per_project` on `analysis_jobs(project_id)` where `status IN ('queued', 'processing', 'retrying')`
- `ux_thumbnail_one_selected_per_project` on `thumbnail_candidates(project_id)` where `status IN ('selected', 'custom_selected')`

## Deletion Behavior

Project deletion is a two-stage process.

1. Immediate logical deletion:
   - Set `video_projects.status = 'deleted'`.
   - Set `video_projects.deleted_at`.
   - Set `video_projects.delete_after_at` to no later than 24 hours after `deleted_at`.
   - Create a `deletion_tasks` row with status `queued`.
   - Mark related `media_assets.deleted_at` or otherwise make them non-downloadable.
   - API access to project, nested resources, and assets stops immediately.

2. Physical cleanup:
   - The local worker resolves `media_assets.storage_key` server-side.
   - It deletes original videos, proxies, analysis audio, thumbnails, exported videos, and exported thumbnails for the project.
   - It must not follow symlinks outside the configured storage root.
   - On success, mark `deletion_tasks.status = 'completed'`.
   - On failure, store sanitized `last_error_code` and `last_error_summary` only.

Deleted project database rows may remain as tombstones so the owner can receive `PROJECT_DELETED`. They must not expose asset details or permit downloads.

## Validation Rules

- Supported upload extensions: `mp4`, `mov`, `m4v`.
- Maximum video duration: 20 minutes (`1_200_000` ms).
- Maximum upload size: 2 GB (`2_147_483_648` bytes).
- Videos over 20 minutes must not create an analysis job.
- Videos with no audio may create an analysis job; subtitle generation is skipped and other analysis continues.
- Subtitle, segment, thumbnail, and crop times must stay within `video_projects.duration_ms`.
- Only one active analysis job may exist per project.
- Only one selected thumbnail may exist per project.
- Export downloads require completed `export_jobs` and ready downloadable `media_assets`.

## Security Requirements

- Ownership checks must be enforced in all queries that read or mutate project data.
- Deleted projects must be excluded from normal reads and blocked from all nested reads, mutations, and downloads.
- Object ID changes must not allow access to another user's projects, assets, jobs, subtitles, segments, thumbnails, or exports.
- Upload metadata must be verified by local media inspection; do not trust filename, extension, MIME, or client-provided metadata alone.
- File storage resolution must reject path traversal, absolute paths, symlink escapes, and encoded traversal variants.
- Store internal thumbnail scores only in `thumbnail_candidates.internal_score`; never return them in API DTOs.
- Store only sanitized error summaries for local tools, model runtimes, render failures, filesystem failures, and SQL failures.
- Do not store real API tokens, passwords, local environment values, or generated secrets in SQLite.
- Do not require external API configuration for MVP core analysis.

## Expansion Notes

- MVP max upload size is fixed at 2 GB (`2_147_483_648` bytes).
- Future expansion should update app configuration, API validation, media-storage expectations, frontend display copy, and tests together.
