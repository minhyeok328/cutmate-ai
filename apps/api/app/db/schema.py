from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1


def initialize_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE,
            display_name TEXT,
            local_user INTEGER NOT NULL DEFAULT 0 CHECK (local_user IN (0, 1)),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS video_projects (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            title TEXT NOT NULL,
            purpose TEXT NOT NULL CHECK (
                purpose IN ('short_form', 'vlog', 'lecture', 'interview', 'promotional_video')
            ),
            output_goal TEXT NOT NULL CHECK (
                output_goal IN (
                    'source_summary',
                    'highlight_extraction',
                    'subtitle_generation',
                    'short_form_conversion'
                )
            ),
            status TEXT NOT NULL CHECK (
                status IN (
                    'uploaded',
                    'analyzing',
                    'draft_ready',
                    'exporting',
                    'completed',
                    'failed',
                    'deleted'
                )
            ),
            duration_ms INTEGER NOT NULL CHECK (duration_ms >= 0 AND duration_ms <= 1200000),
            width INTEGER NOT NULL CHECK (width > 0),
            height INTEGER NOT NULL CHECK (height > 0),
            fps REAL,
            aspect_ratio TEXT NOT NULL,
            has_audio INTEGER NOT NULL CHECK (has_audio IN (0, 1)),
            source_file_name TEXT NOT NULL,
            source_extension TEXT NOT NULL CHECK (source_extension IN ('mp4', 'mov', 'm4v')),
            source_mime_type TEXT,
            source_size_bytes INTEGER NOT NULL CHECK (source_size_bytes > 0),
            selected_thumbnail_candidate_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            deleted_at TEXT,
            delete_after_at TEXT
        );

        CREATE TABLE IF NOT EXISTS media_assets (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            project_id TEXT NOT NULL REFERENCES video_projects(id),
            kind TEXT NOT NULL,
            storage_key TEXT NOT NULL UNIQUE,
            content_type TEXT,
            byte_size INTEGER CHECK (byte_size IS NULL OR byte_size >= 0),
            checksum_sha256 TEXT,
            width INTEGER,
            height INTEGER,
            duration_ms INTEGER,
            is_downloadable INTEGER NOT NULL DEFAULT 0 CHECK (is_downloadable IN (0, 1)),
            created_by_job_id TEXT,
            created_at TEXT NOT NULL,
            deleted_at TEXT
        );

        CREATE TABLE IF NOT EXISTS analysis_jobs (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            project_id TEXT NOT NULL REFERENCES video_projects(id),
            status TEXT NOT NULL CHECK (
                status IN (
                    'queued',
                    'processing',
                    'completed',
                    'completed_with_warnings',
                    'failed',
                    'retrying'
                )
            ),
            mode TEXT NOT NULL CHECK (mode IN ('light', 'standard', 'quality')),
            progress_percent INTEGER NOT NULL CHECK (
                progress_percent >= 0 AND progress_percent <= 100
            ),
            current_step TEXT CHECK (
                current_step IS NULL OR current_step IN (
                    'upload_validated',
                    'metadata_extraction',
                    'audio_extraction',
                    'speech_recognition',
                    'subtitle_generation',
                    'silence_detection',
                    'scene_analysis',
                    'thumbnail_generation',
                    'recommendation_generation',
                    'draft_generation'
                )
            ),
            failed_step TEXT CHECK (
                failed_step IS NULL OR failed_step IN (
                    'upload_validated',
                    'metadata_extraction',
                    'audio_extraction',
                    'speech_recognition',
                    'subtitle_generation',
                    'silence_detection',
                    'scene_analysis',
                    'thumbnail_generation',
                    'recommendation_generation',
                    'draft_generation'
                )
            ),
            error_code TEXT,
            error_summary TEXT,
            retry_of_job_id TEXT REFERENCES analysis_jobs(id),
            local_runtime TEXT,
            model_profile_json TEXT,
            tool_versions_json TEXT,
            created_at TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS analysis_results (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            project_id TEXT NOT NULL REFERENCES video_projects(id),
            job_id TEXT NOT NULL REFERENCES analysis_jobs(id),
            status TEXT NOT NULL CHECK (status IN ('completed', 'completed_with_warnings')),
            warnings_json TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            UNIQUE(project_id)
        );

        CREATE TABLE IF NOT EXISTS subtitles (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            project_id TEXT NOT NULL REFERENCES video_projects(id),
            analysis_result_id TEXT NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
            start_ms INTEGER NOT NULL CHECK (start_ms >= 0),
            end_ms INTEGER NOT NULL CHECK (end_ms > start_ms),
            text TEXT NOT NULL,
            edited_text TEXT,
            status TEXT NOT NULL CHECK (status IN ('draft', 'edited')),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS video_segments (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            project_id TEXT NOT NULL REFERENCES video_projects(id),
            analysis_result_id TEXT NOT NULL REFERENCES analysis_results(id) ON DELETE CASCADE,
            segment_type TEXT NOT NULL CHECK (segment_type IN ('cut', 'highlight')),
            start_ms INTEGER NOT NULL CHECK (start_ms >= 0),
            end_ms INTEGER NOT NULL CHECK (end_ms > start_ms),
            transcript TEXT,
            recommendation_reason TEXT NOT NULL,
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'accepted', 'rejected', 'modified')
            ),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS thumbnail_candidates (
            id TEXT PRIMARY KEY,
            owner_id TEXT NOT NULL REFERENCES users(id),
            project_id TEXT NOT NULL REFERENCES video_projects(id),
            timestamp_ms INTEGER NOT NULL CHECK (timestamp_ms >= 0),
            image_asset_id TEXT NOT NULL,
            reason TEXT NOT NULL,
            tags_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL CHECK (
                status IN ('pending', 'selected', 'rejected', 'custom_selected')
            ),
            internal_score REAL NOT NULL CHECK (
                internal_score >= 0.0 AND internal_score <= 1.0
            ),
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_projects_owner_deleted_created
            ON video_projects(owner_id, deleted_at, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_projects_owner_status
            ON video_projects(owner_id, status);
        CREATE INDEX IF NOT EXISTS idx_assets_project_kind
            ON media_assets(project_id, kind);
        CREATE INDEX IF NOT EXISTS idx_assets_owner_project
            ON media_assets(owner_id, project_id);
        CREATE INDEX IF NOT EXISTS idx_analysis_jobs_project_created
            ON analysis_jobs(project_id, created_at DESC);
        CREATE INDEX IF NOT EXISTS idx_analysis_jobs_owner_status
            ON analysis_jobs(owner_id, status);
        CREATE INDEX IF NOT EXISTS idx_subtitles_project_time
            ON subtitles(project_id, start_ms, end_ms);
        CREATE INDEX IF NOT EXISTS idx_segments_project_type_time
            ON video_segments(project_id, segment_type, start_ms, end_ms);
        CREATE INDEX IF NOT EXISTS idx_thumbnails_project_status_time
            ON thumbnail_candidates(project_id, status, timestamp_ms);
        CREATE UNIQUE INDEX IF NOT EXISTS ux_analysis_one_active_per_project
            ON analysis_jobs(project_id)
            WHERE status IN ('queued', 'processing', 'retrying');
        """
    )
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
    connection.commit()
