# CutMate AI Product Spec

> **Document version:** v0.1 (Spec Draft)
> **Date:** 2026-05-29
> **Reference documents:** `planning.md`, `requirements.md`
> **Purpose:** Consolidate CutMate AI MVP product scope, user flows, feature behavior, data, exception handling, and acceptance criteria into one executable spec.

---

## 1. Product Summary

CutMate AI is a video editing assistant where users upload source video, AI generates automatic subtitles, recommended deletion segments, highlight segments, and thumbnail candidates, and users review them to download final video and thumbnail images.

MVP is a collaborative tool that reduces repetitive editor work, not a fully automatic editor. All AI recommendations require user accept/modify/reject, not automatic application.

The product direction is local-first. It does not require paid external APIs; it provides a free analysis pipeline on the user's local machine or personal server combining FFmpeg, faster-whisper, OpenCV, PySceneDetect, OpenCLIP, and local LLMs.

---

## 2. Key Decisions

| Item | Decision |
|---|---|
| Project name | CutMate AI |
| Primary users | Solo creator, educational content creator, marketing content owner |
| Average video length | 5–10 minutes |
| Maximum video length | ≤20 minutes |
| Maximum file size | 2 GB (`2_147_483_648` bytes), centralized for future expansion |
| Videos over 20 minutes | Block upload/analysis; explain increased processing time and cost |
| Supported file formats | `mp4`, `mov`, `m4v` prioritized |
| Thumbnail approach | In-video actual frame-based candidate recommendation |
| Generative thumbnails | Out of MVP scope |
| Thumbnail score exposure | Hide numeric scores from users; show recommendation reasons only |
| 9:16 crop | Center crop default; user can adjust directly |
| Project deletion | Immediately shown as deleted to user; originals/outputs physically deleted within 24 hours |
| Default AI strategy | Local open-source models/tools first |
| API usage | Optional future high-quality analysis, not required path |
| Default speech recognition | faster-whisper |
| Default video analysis | FFmpeg, PySceneDetect, OpenCV |
| Default thumbnail analysis | OpenCV quality scoring + OpenCLIP semantic matching |
| Recommendation reason generation | Qwen3-8B, gpt-oss-20b, etc. (local LLM selection) |

---

## 3. MVP Goals

- Generate first edit draft and thumbnail candidates from uploaded videos ≤20 minutes.
- Allow users to review subtitles, cut candidates, highlight candidates, and thumbnail candidates in one workflow.
- Users can accept, modify, reject, or skip AI recommendations.
- Users can download final video and selected thumbnail image.
- Do not start analysis for videos over 20 minutes; explain block reason and alternatives.
- Provide local MVP where core analysis works without API keys.

---

## 4. MVP Scope

### 4.1 In Scope
- Video upload and basic metadata extraction
- Analysis progress display
- Speech-recognition-based automatic subtitles
- Subtitle text editing and sync adjustment
- Silence/repetition/unnecessary segment detection
- Highlight segment recommendation
- AI recommendation timeline display
- 3–5 thumbnail candidate recommendations
- Direct thumbnail frame selection
- Original aspect ratio and 9:16 short-form export
- Selected thumbnail image download
- Local model/tool-based analysis pipeline
- Light/standard/quality analysis mode design

### 4.2 Out of Scope
- Fully automatic publishing
- Real-time live editing
- Professional color grading and sound mixing
- AI-generated thumbnail images
- Deepfake, voice cloning, face synthesis
- Automatic insertion of external music with unclear copyright
- Team collaboration review/comments
- Automatic BGM recommendation
- Brand template-based thumbnail editing
- Analysis features requiring external API as mandatory

---

## 5. User Flows

### 5.1 Default Success Flow
1. User uploads a video file.
2. System checks file format, video length, size, and audio presence.
3. If video is ≤20 minutes and supported format, create project.
4. User selects content purpose and output goal.
5. System runs speech recognition, scene analysis, cut candidates, highlight candidates, and thumbnail candidates.
6. User reviews subtitles, cut candidates, and highlight candidates on edit draft screen.
7. User selects thumbnail candidate or specifies frame directly on thumbnail recommendation screen.
8. User selects aspect ratio, resolution, subtitle inclusion, and thumbnail inclusion on export settings.
9. System renders output and provides download URLs.

### 5.2 Over-20-Minute Video Flow
1. User uploads video exceeding 20 minutes.
2. System does not create analysis job.
3. User sees the following message:

```text
Only videos up to 20 minutes can be analyzed at this time.
CutMate AI MVP is optimized for 5–10 minute videos; longer videos may greatly increase processing time and cost.
Please split the video to 20 minutes or less, or trim to key segments and upload again.
```

4. User can remove file and upload a different video.

### 5.3 No-Audio Video Flow
1. User uploads video without audio.
2. System skips subtitle generation and proceeds with scene/frame analysis.
3. User reviews cut candidates, highlight candidates, and thumbnail candidates without subtitles.

---

## 6. Screen Spec

### 6.1 Upload Screen
- Provide file upload area.
- Supported formats: `mp4`, `mov`, `m4v`.
- Recommended average length 5–10 minutes; maximum 20 minutes.
- Block videos over 20 minutes before analysis.
- Content purpose options: short-form, vlog, lecture, interview, promotional video.
- Output goal options: source summary, highlight extraction, subtitle generation, short-form conversion.

### 6.2 Analysis Progress Screen
- Show upload complete, speech recognition, scene analysis, recommendation generation, and rendering steps.
- Show step progress and current status.
- Clearly mark estimated completion time as estimate.
- On failure, provide failed step, cause, and retry button.

### 6.3 Edit Draft Screen
- Provide video preview.
- Show recommended cuts, highlights, and subtitles on timeline.
- Recommended segments have pending, accepted, rejected, modified status.
- User can accept or reject cut candidates.
- User can edit subtitle text and sync.
- Recommendation rationale visible when segment selected.
- User can send specific segment to thumbnail candidate review.

### 6.4 Thumbnail Recommendation Screen
- Display 3–5 thumbnail candidates as cards.
- Each candidate includes image, timestamp, recommendation reason, and select button.
- Do not expose internal numeric scores to users.
- Example recommendation reasons:
  - Linked to key scene
  - Product centered on screen
  - Natural speaker expression
  - Stable and sharp composition
- User can replace candidate via direct frame selection timeline scrubber.
- Platform previews prioritize 16:9, 9:16, 1:1.

### 6.5 Export Screen
- Aspect ratio options: original, 9:16, 1:1.
- Resolution selectable.
- Subtitle inclusion selectable.
- Thumbnail image inclusion selectable.
- Render status: queued, in progress, complete, failed.
- On complete, provide video download URL and thumbnail download URL.

---

## 7. Feature Spec

### 7.1 Video Upload
| ID | Spec | Acceptance Criteria |
|---|---|---|
| UP-001 | User can upload a video file. | Project created if file supported. |
| UP-002 | System checks file format. | Non-`mp4`/`mov`/`m4v` files blocked with reason. |
| UP-003 | System checks video length. | Videos over 20 minutes do not create analysis job. |
| UP-004 | System extracts basic video info. | Duration, resolution, aspect ratio, audio presence saved. |

### 7.2 Analysis Jobs
| ID | Spec | Acceptance Criteria |
|---|---|---|
| JOB-001 | Create analysis job after upload completes. | Job status saved as `queued`. |
| JOB-002 | Process analysis asynchronously. | User can check progress on screen. |
| JOB-003 | On failure, save failed step and cause. | User can check retry availability. |

### 7.3 Automatic Subtitles
| ID | Spec | Acceptance Criteria |
|---|---|---|
| SUB-001 | Convert audio to text. | Subtitle segments with timecodes generated. |
| SUB-002 | Split subtitles by sentence or semantic unit. | Each segment has start/end time. |
| SUB-003 | User can edit subtitle text. | Edits saved and reflected in preview. |
| SUB-004 | User can adjust subtitle sync. | Adjusted times reflected on timeline. |

### 7.4 Cut Candidate Detection
| ID | Spec | Acceptance Criteria |
|---|---|---|
| CUT-001 | Mark long silence segments as deletion candidates. | Candidate includes start/end time and reason. |
| CUT-002 | Mark repeated speech, stutters, wait segments as candidates. | Recommendation rationale shown per candidate. |
| CUT-003 | Cut candidates are not auto-deleted. | User approval required to apply to edit draft. |
| CUT-004 | User can revert accepted cuts. | Timeline and preview updated after revert. |

### 7.5 Highlight Recommendation
| ID | Spec | Acceptance Criteria |
|---|---|---|
| HIL-001 | Recommend key segments aligned with content purpose. | One or more candidate segments generated. |
| HIL-002 | Provide recommendation reason. | User can see why recommended. |
| HIL-003 | Selected highlight used for short-form output. | Selected segment enables 9:16 export. |

### 7.6 Thumbnail Candidate Recommendation
| ID | Spec | Acceptance Criteria |
|---|---|---|
| THM-001 | Generate 3–5 candidates from actual video frames. | Candidate images and timestamps displayed. |
| THM-002 | Select candidates by highlight relevance, sharpness, composition, subject visibility, safety. | Recommendation reason saved per candidate. |
| THM-003 | Exclude blur, closed eyes, excessive crop, sensitive info exposure. | Unsuitable candidates not in default list. |
| THM-004 | User can select one candidate. | Selected candidate saved as project output. |
| THM-005 | User can specify frame directly. | Directly specified frame saved as thumbnail image. |
| THM-006 | Do not expose numeric scores to users. | UI shows recommendation reasons only. |

### 7.7 Export
| ID | Spec | Acceptance Criteria |
|---|---|---|
| EXP-001 | User can download original aspect ratio video. | Download URL provided after render completes. |
| EXP-002 | User can download 9:16 short-form video. | Center crop default and user adjustment applied. |
| EXP-003 | User can choose subtitle inclusion. | Render result differs by selection. |
| EXP-004 | User can download selected thumbnail image. | Thumbnail download URL provided. |

### 7.8 Local Processing and Model Management
| ID | Spec | Acceptance Criteria |
|---|---|---|
| LOC-001 | Default analysis pipeline runs without external API key. | Sample video analysis completes with local models/tools only. |
| LOC-002 | Extract analysis audio, frames, proxy video with FFmpeg. | Intermediate outputs generated when analysis starts. |
| LOC-003 | Generate local subtitles with faster-whisper. | Subtitle draft with timecodes generated. |
| LOC-004 | Detect speech/silence with Silero VAD or audio level analysis. | Silence candidates linked to cut candidates. |
| LOC-005 | Extract scene transitions and candidate frames with PySceneDetect/OpenCV. | Scene transition points and thumbnail candidate frames generated. |
| LOC-006 | Score thumbnail candidate quality with OpenCV. | Blur, darkness, unstable crop candidates excluded. |
| LOC-007 | Compute highlight keyword and frame semantic similarity with OpenCLIP. | Semantically relevant candidates ranked higher. |
| LOC-008 | Generate recommendation reasons with local LLM. | Basic recommendation candidates generated when LLM disabled. |
| LOC-009 | External API is optional high-quality analysis only. | Must features work without API configuration. |

---

## 8. Local AI Processing Spec

### 8.0 Processing Principles
- Connect task-specific tools rather than one large API model for all processing.
- Handle candidate detection and scoring with deterministic rules and signal-based analysis where possible.
- Local LLM is auxiliary for natural-language rationale and subtitle cleanup, not core decision-maker for candidates.
- Subtitles, cut candidates, and basic thumbnail candidates must generate even without local LLM/VLM installed.
- External API integration is opt-in, not default.

### 8.0.1 Default Local Model/Tool Configuration

| Processing Area | Default Configuration | Role | Phase |
|---|---|---|---|
| Video/audio extraction | FFmpeg | Generate audio, frames, low-res proxy | MVP required |
| Speech recognition | faster-whisper | Subtitle generation, timecode extraction | MVP required |
| Silence/speech detection | Silero VAD or audio level analysis | Separate silence/speech segments | MVP required |
| Scene transitions | PySceneDetect, OpenCV | Cut points, scene changes, candidate frame extraction | MVP required |
| Thumbnail quality analysis | OpenCV | Score blur, brightness, composition, crop stability | MVP required |
| Thumbnail semantic matching | OpenCLIP | Compute semantic similarity between keywords/highlights and frames | MVP recommended |
| Recommendation reason generation | Qwen3-8B, gpt-oss-20b, etc. (local LLM) | Natural-language highlight/thumbnail recommendation reasons | Phase 2 |
| Image description enrichment | Qwen3-VL-8B, etc. (local VLM) | Enrich thumbnail candidate scene descriptions | Later |
| Speaker diarization | pyannote.audio or WhisperX | Speaker separation for interviews/lectures | Later |

### 8.1 Inputs
- Video file
- Audio track
- Frame samples
- Content purpose
- Output goal
- Title or primary keywords (optional)
- Brand tone or prohibited expressions (optional)

### 8.2 Processing Steps
1. Extract video metadata
2. Validate file format, length, size
3. Extract audio and analysis frames/proxy with FFmpeg
4. Speech recognition and timecode generation with faster-whisper
5. Generate subtitle segments
6. Detect silence/speech segments with Silero VAD or audio level analysis
7. Detect repeated speech, stutters, wait segment candidates
8. Extract scene transitions and candidate frames with PySceneDetect/OpenCV
9. Score highlight candidates by keywords, speech density, scene changes
10. Score thumbnail candidates for sharpness, brightness, composition, crop stability with OpenCV
11. Compute semantic similarity between highlight keywords and candidate frames with OpenCLIP
12. Generate cut/highlight/thumbnail recommendation rationale with local LLM
13. Generate edit timeline draft

### 8.3 Output
```json
{
  "project_id": "project_123",
  "duration_seconds": 612,
  "subtitles": [
    {
      "id": "sub_001",
      "start": "00:01:12.300",
      "end": "00:01:28.900",
      "text": "This feature reduces repetitive task time."
    }
  ],
  "cut_candidates": [
    {
      "id": "cut_001",
      "start": "00:03:05.100",
      "end": "00:03:12.400",
      "reason": "Long silence segment",
      "status": "pending"
    }
  ],
  "highlight_candidates": [
    {
      "id": "hil_001",
      "start": "00:01:12.300",
      "end": "00:01:28.900",
      "reason": "Segment explaining the product's core benefits",
      "status": "pending"
    }
  ],
  "thumbnail_candidates": [
    {
      "id": "thm_001",
      "timestamp": "00:01:18.200",
      "image_url": "https://cdn.example.com/projects/123/thumb_01.jpg",
      "internal_score": 0.87,
      "reason": "Sharp frame with product centered and linked to the key explanation segment",
      "tags": ["product_visible", "highlight_related", "sharp_frame"],
      "status": "pending"
    }
  ]
}
```

`internal_score` is used for recommendation ranking and internal quality judgment only; not exposed in user UI.

---

## 9. Data Model

### 9.1 `User`
- `id`
- `email`
- `created_at`

### 9.2 `VideoProject`
- `id`
- `user_id`
- `title`
- `original_file_url`
- `duration_seconds`
- `resolution`
- `aspect_ratio`
- `has_audio`
- `purpose`
- `output_goal`
- `status`
- `created_at`
- `deleted_at`

### 9.3 `AnalysisJob`
- `id`
- `project_id`
- `status`
- `progress`
- `current_step`
- `mode`
- `local_runtime`
- `model_profile`
- `tool_versions`
- `error_code`
- `error_message`
- `created_at`
- `completed_at`

### 9.4 `VideoSegment`
- `id`
- `project_id`
- `start_time`
- `end_time`
- `segment_type`
- `transcript`
- `recommendation_reason`
- `status`
- `created_at`

### 9.5 `Subtitle`
- `id`
- `project_id`
- `start_time`
- `end_time`
- `text`
- `edited_text`
- `created_at`
- `updated_at`

### 9.6 `ThumbnailCandidate`
- `id`
- `project_id`
- `timestamp`
- `image_url`
- `internal_score`
- `reason`
- `tags`
- `status`
- `created_at`

### 9.7 `ExportJob`
- `id`
- `project_id`
- `format`
- `aspect_ratio`
- `resolution`
- `include_subtitle`
- `include_thumbnail`
- `crop_mode`
- `crop_settings`
- `status`
- `output_file_url`
- `thumbnail_file_url`
- `created_at`
- `completed_at`

---

## 10. Status Definitions

| Target | Status |
|---|---|
| Project | `uploaded`, `analyzing`, `draft_ready`, `exporting`, `completed`, `failed`, `deleted` |
| Analysis job | `queued`, `processing`, `completed`, `failed`, `retrying` |
| Recommended segment | `pending`, `accepted`, `rejected`, `modified` |
| Thumbnail candidate | `pending`, `selected`, `rejected`, `custom_selected` |
| Render job | `queued`, `rendering`, `completed`, `failed` |
| Analysis mode | `light`, `standard`, `quality` |

---

## 11. Exception Handling

| Situation | User Message | System Action |
|---|---|---|
| Unsupported file upload | Unsupported file format. Please upload `mp4`, `mov`, or `m4v` files. | Block upload |
| Video over 20 minutes | Only videos up to 20 minutes can be analyzed. CutMate AI MVP is optimized for 5–10 minute videos; longer videos may greatly increase processing time and cost. | Block analysis job creation |
| Size exceeded | File size is too large. Please compress the file or upload a shorter video. | Block analysis job creation |
| No audio | Skipping speech subtitle generation; proceeding with scene analysis only. | Exclude subtitle step, continue scene analysis |
| Speech recognition failure | Speech recognition failed. You can review edit candidates without subtitles. | Provide partial results |
| Insufficient thumbnail candidates | Not enough thumbnail candidates to recommend. Please select a frame directly. | Provide direct selection UI |
| Render failure | Rendering failed. Please try again. | Save failure log, provide retry button |
| Project deletion | Project has been deleted. | Block user access, schedule physical deletion within 24 hours |
| Local model missing | Required local models are not installed. Please download models or run in light mode. | Check model status, guide download/mode change |
| Insufficient local performance | High-quality analysis may take long on current hardware. You can switch to light mode. | Provide analysis mode change option |

---

## 12. Non-Functional Spec

| ID | Spec | Criteria |
|---|---|---|
| NFR-001 | Progress status | Show current step and status during analysis/rendering. |
| NFR-002 | Retry capability | Provide retry action for analysis/render failures after upload. |
| NFR-003 | Security | Do not expose source video, outputs, or thumbnail URLs to unauthorized users. |
| NFR-004 | Privacy | On project deletion, user loses access immediately; files physically deleted within 24 hours. |
| NFR-005 | Cost control | Do not start analysis for videos over 20 minutes. |
| NFR-006 | Explainability | All AI recommendations include understandable rationale. |
| NFR-007 | Local executability | Must features work with local models/tools only, without API key. |
| NFR-008 | Model replaceability | Speech recognition, LLM, VLM, thumbnail scoring modules separated for replacement. |
| NFR-009 | Performance modes | User can select `light`, `standard`, `quality` analysis modes. |

---

## 13. Success Metrics

| Metric | Description |
|---|---|
| First edit draft completion rate | Rate completing edit draft generation after upload |
| AI recommendation acceptance rate | Rate user accepts cut/highlight recommendations |
| Subtitle edit-and-use rate | Rate user includes subtitles after editing |
| Thumbnail candidate selection rate | Rate user selects one of recommended candidates |
| Thumbnail direct frame reselection rate | Rate user selects direct frame instead of recommended candidate |
| Time to first download | Time from upload to final output download |
| Over-20-minute block drop-off rate | Rate user leaves without re-upload after over-20-minute message |
| Reuse rate | Rate same user creates new project again |

---

## 14. Release Phases

### 14.1 Phase 1 MVP
- Video upload
- File format/length/size validation
- Basic metadata extraction
- Speech recognition and subtitle draft
- Silence/repetition detection

### 14.2 Phase 2 MVP
- Highlight recommendation
- Recommendation rationale labels
- Unified timeline review
- Accept/reject/modify UX

### 14.3 Phase 3 MVP
- Thumbnail candidate recommendation
- Per-candidate recommendation rationale
- Direct frame selection
- Platform-specific thumbnail preview
- Thumbnail image download

### 14.4 Phase 4 MVP
- Original/short-form aspect ratio export
- Center crop and user crop adjustment
- Render stabilization
- Success metrics collection
- Failure case log cleanup

---

## 15. Acceptance Checklist

- Analysis job created after upload for videos ≤20 minutes.
- Analysis job not created for videos over 20 minutes; reason shown.
- Subtitle draft generated for videos with audio.
- Scene analysis proceeds without subtitles for videos without audio.
- Local analysis pipeline works without API key.
- Basic subtitles, cut candidates, and thumbnail candidates generated without local LLM.
- Cut candidates are not auto-deleted.
- Highlight candidates show recommendation rationale.
- 3–5 thumbnail candidates displayed.
- Thumbnail internal scores not shown in UI.
- User can specify thumbnail frame directly.
- User can download original aspect ratio or 9:16 output.
- User cannot access originals/outputs after project deletion.

---

## 16. Remaining Decisions

- MVP max file size is 2 GB (`2_147_483_648` bytes); future expansion should update configuration, validation, UI copy, and tests together.
- Decide how detailed video split guidance on over-20-minute screen.
- Decide 9:16 crop adjustment UI: simple position only vs. person/product tracking assist.
- When fewer than 3 thumbnail candidates, direct selection only vs. lower quality threshold for more candidates.
- Decide default model download size and installation automation extent.
- Decide official CPU-only support vs. GPU/Apple Silicon recommendation.
