# CutMate AI Requirements Specification Draft

> **Document version:** v0.1 (Draft)
> **Date:** 2026-05-29
> **Reference documents:** `planning.md`
> **Purpose:** Document functional, non-functional, data, screen, and exception-handling requirements for CutMate AI MVP in a developable and verifiable form.

---

## 1. Document Overview

### 1.1 Product Definition
- CutMate AI is an AI-based video editing assistant that analyzes source video and proposes subtitles, cut edit candidates, highlight segments, and thumbnail candidates.
- Users review AI-generated edit drafts and can accept, modify, or reject them.
- MVP targets a collaborative assistant that reduces repetitive editor work, not a fully automatic editor.
- MVP does not assume paid external API calls by default; it prioritizes open-source models and video processing tools runnable locally.

### 1.2 MVP Goals
- Generate first edit draft and thumbnail candidates for videos ≤20 minutes.
- Expect average use at 5–10 minutes and minimize analysis wait fatigue in that range.
- Allow users to review subtitles, cut candidates, highlight candidates, and thumbnail candidates in one flow.
- Allow download of final video and selected thumbnail image.

### 1.3 MVP Scope
- Included: video upload, basic metadata extraction, speech recognition, subtitle draft, cut candidate detection, highlight recommendation, thumbnail candidate recommendation, timeline review, export
- Included: local speech recognition, local scene analysis, local thumbnail candidate scoring, local recommendation rationale generation
- Excluded: fully automatic publishing, real-time live editing, professional color grading, professional sound mixing, AI-generated thumbnail images, deepfake/voice cloning/face synthesis, required external API dependency

---

## 2. Users and Permissions

### 2.1 Primary Users
- Solo creator: users who need to quickly produce vlogs, reviews, and short-form clips
- Educational content creator: users who need to organize subtitles and key segments in long lecture videos
- Marketing content owner: users who need upload-ready video and thumbnail candidates together

### 2.2 Permission Requirements
| ID | Requirement | Priority |
|---|---|---|
| AUTH-001 | Users may view, modify, and download only projects they uploaded. | Must |
| AUTH-002 | Sharing/collaboration is out of MVP scope. | Won't |
| AUTH-003 | Users may request project deletion; access to original and outputs of deleted projects must be blocked. | Must |

---

## 3. Functional Requirements

### 3.1 Video Upload
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| UP-001 | Video file upload | User can upload a video file. | Must | Project is created after upload completes. |
| UP-002 | File format restriction | MVP prioritizes `mp4`, `mov`, `m4v` files. | Must | Unsupported file upload shows reason. |
| UP-003 | Size/duration limit | MVP processes videos ≤20 minutes and a predefined max size. | Must | Over 20 minutes or over size limit shows reason before analysis starts. |
| UP-004 | Basic metadata extraction | System extracts duration, resolution, frame aspect ratio, and audio presence. | Must | Basic info displayed on project detail. |
| UP-005 | Content purpose selection | User can select purpose: short-form, vlog, lecture, interview, promotional video. | Must | Selected value included in analysis request. |

### 3.2 Analysis Job Management
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| JOB-001 | Analysis job creation | Create analysis job after upload completes. | Must | Job status saved as `queued`. |
| JOB-002 | Progress query | User can check speech recognition, scene analysis, and recommendation generation progress. | Must | Step-by-step status shown on screen. |
| JOB-003 | Failure handling | On analysis failure, show failed step and retry availability. | Must | Failure message and retry button displayed. |
| JOB-004 | Async processing | Video analysis and rendering run as async jobs. | Must | User can check job status without refresh. |

### 3.3 Automatic Subtitles
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| SUB-001 | Speech recognition | System converts audio to text. | Must | Subtitle draft with timecodes generated. |
| SUB-002 | Subtitle segment generation | Subtitles split by sentence or semantic unit. | Must | Each subtitle has start/end time. |
| SUB-003 | Subtitle editing | User can edit subtitle text. | Must | Edited text saved and reflected in preview. |
| SUB-004 | Sync adjustment | User can adjust subtitle start/end times. | Should | Adjusted times reflected on timeline. |
| SUB-005 | Source replay | User can replay source video for a subtitle segment. | Should | Video plays from selected subtitle segment. |

### 3.4 Cut Candidate Detection
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| CUT-001 | Silence detection | System marks long silence segments as deletion candidates. | Must | Candidate includes start/end time and reason. |
| CUT-002 | Repeated speech detection | Mark stutters, repeated speech, and meaningless wait segments as candidates. | Must | Recommendation rationale shown per candidate. |
| CUT-003 | No auto-delete | Cut candidates are not auto-deleted by default. | Must | User approval required to apply to edit draft. |
| CUT-004 | Accept/reject | User can accept or reject cut candidates. | Must | Selection state saved. |
| CUT-005 | Undo | User can revert accepted cut candidates. | Should | Timeline updated after revert. |

### 3.5 Highlight Recommendation
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| HIL-001 | Highlight candidate generation | System recommends key segments aligned with content purpose. | Must | One or more candidate segments generated. |
| HIL-002 | Recommendation rationale display | Highlight candidates include recommendation reason. | Must | User can see why segment was selected. |
| HIL-003 | Purpose-specific criteria | Apply different criteria for vlog, product review, lecture, interview, promotional video. | Should | Recommendations or rationale change when purpose changes. |
| HIL-004 | Short-form candidate link | Highlight candidates usable for short-form output generation. | Must | Selected candidate enables 9:16 export. |

### 3.6 Thumbnail Candidate Recommendation
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| THM-001 | Candidate frame generation | System generates 3–5 thumbnail candidates from video frames. | Must | Candidate images and timestamps displayed. |
| THM-002 | Recommendation criteria | Candidates scored by highlight relevance, sharpness, composition, subject visibility, safety. | Must | Internal score and rationale saved per candidate. |
| THM-003 | Unsuitable frame exclusion | Exclude blur, closed eyes, excessive crop, sensitive info exposure by default. | Must | Unsuitable candidates not shown in default list. |
| THM-004 | Recommendation rationale display | Each candidate includes descriptions such as "product visible," "natural expression." | Must | User can see candidate selection reason. |
| THM-005 | Candidate selection | User can select one recommended candidate. | Must | Selected candidate saved as project output. |
| THM-006 | Direct frame selection | User can specify thumbnail frame via timeline scrubber. | Must | Directly specified frame saved as thumbnail. |
| THM-007 | Platform preview | User can preview 16:9, 9:16, 1:1 crops. | Should | Per-candidate crop preview displayed. |
| THM-008 | Generated image exclusion | MVP does not generate scenes not in video. | Won't | Thumbnail candidates from in-video frames only. |

### 3.7 Edit Timeline
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| TIM-001 | Unified timeline display | Show subtitles, cut candidates, and highlight candidates on one timeline. | Must | User can distinguish recommendation types per segment. |
| TIM-002 | Preview playback | User can play selected segment in video preview. | Must | Video plays from clicked segment. |
| TIM-003 | Recommendation status display | Recommended segments have pending, accepted, rejected status. | Must | Status changes reflected immediately on screen. |
| TIM-004 | Thumbnail candidate link | User can send specific segment to thumbnail candidate review. | Should | Candidates refreshed based on selected segment. |

### 3.8 Export
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| EXP-001 | Original aspect ratio export | User can download video at original aspect ratio. | Must | Download URL provided after render completes. |
| EXP-002 | Short-form aspect ratio export | User can download 9:16 video. | Must | Short-form file generated from selected highlight. |
| EXP-003 | Subtitle inclusion option | User can choose subtitle included/excluded. | Must | Render result differs by selection. |
| EXP-004 | Thumbnail download | User can download selected thumbnail image. | Must | Thumbnail image URL provided. |
| EXP-005 | Render status display | Show render queued, in progress, complete, failed. | Must | On failure, show retry availability. |

### 3.9 Local Processing and Model Management
| ID | Requirement | Detail | Priority | Acceptance Criteria |
|---|---|---|---|---|
| LOC-001 | Local-first processing | Default MVP analysis pipeline must run locally without paid external API. | Must | Sample video analysis possible without network API key. |
| LOC-002 | Video processing tools | System extracts audio, frames, and low-res proxy with FFmpeg. | Must | Analysis audio and frame samples generated from uploaded video. |
| LOC-003 | Local speech recognition | System supports faster-whisper-based local speech recognition. | Must | Subtitle draft with timecodes from audio file. |
| LOC-004 | Silence/speech detection | System detects speech/silence with Silero VAD or audio level analysis. | Must | Silence candidates linked to cut candidates. |
| LOC-005 | Scene analysis | System supports PySceneDetect or OpenCV-based scene transition detection. | Must | Scene transition points and candidate frames generated. |
| LOC-006 | Thumbnail quality scoring | System scores blur, brightness, composition, crop stability with OpenCV. | Must | Unsuitable frames excluded from default thumbnail candidates. |
| LOC-007 | Thumbnail semantic matching | System can compute semantic similarity between keywords/highlights and frames with OpenCLIP. | Should | Frames highly related to highlight keywords ranked higher. |
| LOC-008 | Local recommendation rationale | System can generate recommendation reasons with Qwen3-8B, gpt-oss-20b, etc. (local LLM). | Should | Natural-language rationale generated for recommended segments. |
| LOC-009 | Local VLM extension | System can enrich thumbnail candidate descriptions with Qwen3-VL-8B, etc. (local VLM). | Could | Basic candidate recommendation works when VLM disabled. |
| LOC-010 | API optional mode | External API is high-quality analysis option only, not required path. | Could | MVP core features work without API configuration. |

---

## 4. Screen Requirements

### 4.1 Upload Screen
- Provide file upload area.
- Show supported formats, max length, and max size before upload.
- Allow content purpose and output goal selection.
- Block unsupported or over-limit files before analysis.

### 4.2 Analysis Progress Screen
- Show upload complete, speech recognition, scene analysis, recommendation generation, and rendering steps.
- Show estimated completion time; clearly mark as estimate when inaccurate.
- On failure, provide failed step, cause, and retry action.

### 4.3 Edit Draft Screen
- Provide video preview, AI recommendation timeline, and subtitle panel together.
- Cut/highlight/subtitle recommendations have distinguishable visual labels.
- Recommendation rationale visible immediately when segment selected.
- User can accept, modify, delete, or undo recommendations.

### 4.4 Thumbnail Recommendation Screen
- Display 3–5 thumbnail candidates as cards.
- Each card provides image, timestamp, recommendation reason, and select button.
- Provide video scrubber for direct frame selection.
- Platform crop previews confirmable before candidate selection.

### 4.5 Export Screen
- Allow selection of aspect ratio, resolution, subtitle inclusion, thumbnail inclusion.
- Provide render status and download button.
- Failed render jobs must be retryable.

---

## 5. Data Requirements

### 5.1 Core Entities
| Entity | Description | Key Fields |
|---|---|---|
| User | User information | `id`, `email`, `created_at` |
| VideoProject | Uploaded video project | `id`, `user_id`, `title`, `original_file_url`, `duration`, `resolution`, `purpose`, `status` |
| AnalysisJob | Analysis job state | `id`, `project_id`, `status`, `progress`, `current_step`, `error_message` |
| VideoSegment | Cut/highlight candidate segment | `id`, `project_id`, `start_time`, `end_time`, `segment_type`, `transcript`, `reason`, `is_selected` |
| Subtitle | Subtitle segment | `id`, `project_id`, `start_time`, `end_time`, `text`, `edited_text` |
| ThumbnailCandidate | Thumbnail candidate | `id`, `project_id`, `timestamp`, `image_url`, `internal_score`, `reason`, `tags`, `is_selected` |
| ExportJob | Render job | `id`, `project_id`, `format`, `aspect_ratio`, `include_subtitle`, `include_thumbnail`, `status`, `output_file_url`, `thumbnail_file_url` |

### 5.2 Status Values
| Category | Values |
|---|---|
| Project | `uploaded`, `analyzing`, `draft_ready`, `exporting`, `completed`, `failed`, `deleted` |
| Analysis job | `queued`, `processing`, `completed`, `failed`, `retrying` |
| Recommended segment | `pending`, `accepted`, `rejected`, `modified` |
| Render job | `queued`, `rendering`, `completed`, `failed` |

---

## 6. Local AI Analysis Requirements

### 6.0 Local Processing Principles
- Default MVP analysis runs locally.
- Default configuration does not send source video, audio, or frames to external APIs for cost savings and privacy.
- Local models are separated by task: speech recognition, scene analysis, thumbnail scoring, and recommendation rationale use different tools/models.
- Must be extensible for light and quality modes based on user hardware.

### 6.0.1 Default Model/Tool Configuration

| Area | Default Tool/Model | Priority |
|---|---|---|
| Video/audio extraction | FFmpeg | Must |
| Speech recognition | faster-whisper | Must |
| Silence/speech detection | Silero VAD or audio level analysis | Must |
| Scene transitions | PySceneDetect, OpenCV | Must |
| Thumbnail quality analysis | OpenCV | Must |
| Thumbnail semantic matching | OpenCLIP | Should |
| Recommendation reason generation | Qwen3-8B, gpt-oss-20b, etc. (local LLM) | Should |
| Image description enrichment | Qwen3-VL-8B, etc. (local VLM) | Could |
| Speaker diarization | pyannote.audio or WhisperX | Could |

### 6.1 Inputs
- Video file
- Audio track
- Frame samples
- Content purpose
- Output goal
- Title/primary keywords (optional)
- Brand tone or prohibited expressions (optional)

### 6.2 Outputs
- Timecode-based subtitle draft
- Recommended deletion segment list
- Highlight recommendation segment list
- Thumbnail candidate list
- Recommendation rationale and internal scores
- Local processing log and model/tool versions used

### 6.3 Quality Criteria
- Recommendation results must include rationale users can accept.
- Cut and highlight candidates must not conflict.
- Thumbnail candidates must come from actual video frames only.
- Exclude frames with sensitive info, inappropriate content, or distortion risk from thumbnail candidates.
- Rule-based candidate detection and basic scoring must work when local LLM or VLM disabled.

---

## 7. Non-Functional Requirements

| ID | Requirement | Detail | Priority |
|---|---|---|---|
| NFR-001 | Processing time guidance | Provide progress and status since analysis and rendering may take long. | Must |
| NFR-002 | Stability | User must be able to retry on upload, analysis, or render failure. | Must |
| NFR-003 | Scalability | Video analysis and rendering must scale via queue-based async processing. | Should |
| NFR-004 | Security | Source video, voice, and thumbnail image URLs must not be exposed to unauthorized users. | Must |
| NFR-005 | Privacy | Apply clear deletion policy for originals and outputs on project deletion. | Must |
| NFR-006 | Cost control | Control processing cost via duration, size, and resolution limits in MVP. | Must |
| NFR-007 | Explainability | AI recommendations must include rationale labels or explanatory text. | Must |
| NFR-008 | Local executability | Default MVP must provide local analysis path runnable without external API key. | Must |
| NFR-009 | Performance modes | User should select light/standard/quality analysis modes by hardware. | Should |
| NFR-010 | Model replaceability | Speech recognition, LLM, VLM, and thumbnail scoring must be swappable modules. | Should |

---

## 8. Exceptions and Error Handling

| Situation | User Message | System Action |
|---|---|---|
| Unsupported file upload | "Unsupported file format." | Block upload |
| Video duration exceeded | "Only videos up to 20 minutes can be analyzed. CutMate AI MVP is optimized for 5–10 minute videos; longer videos may greatly increase processing time and cost." | Block analysis job creation |
| No audio | "Skipping speech subtitle generation; proceeding with scene analysis only." | Exclude subtitle step, continue analysis |
| Speech recognition failure | "Speech recognition failed. You can review edit candidates without subtitles." | Record failed step, provide partial results |
| Insufficient thumbnail candidates | "Not enough thumbnail candidates to recommend. Please select a frame directly." | Provide direct selection UI |
| Render failure | "Rendering failed. Please try again." | Save failure log, provide retry button |

---

## 9. Success Metrics

| Metric | Description |
|---|---|
| First edit draft completion rate | Rate completing edit draft generation after upload |
| AI recommendation acceptance rate | Rate user accepts cut/highlight recommendations |
| Subtitle edit-and-use rate | Rate user includes subtitles after editing |
| Thumbnail candidate selection rate | Rate user selects one of recommended candidates |
| Thumbnail direct frame reselection rate | Rate user selects direct frame instead of recommended candidate |
| Time to first download | Time from upload to final output download |
| Reuse rate | Rate same user creates new project again |

---

## 10. Release Phases

### 10.1 Phase 1 MVP
- Video upload
- Basic metadata extraction
- Speech recognition and subtitle draft
- Silence/repetition detection

### 10.2 Phase 2 MVP
- Highlight recommendation
- Recommendation rationale labels
- Unified timeline review
- Accept/reject/modify UX

### 10.3 Phase 3 MVP
- Thumbnail candidate recommendation
- Per-candidate recommendation rationale
- Direct frame selection
- Thumbnail image download

### 10.4 Phase 4 MVP
- Original/short-form aspect ratio export
- Render stabilization
- Success metrics collection
- Failure case log cleanup

---

## 11. Open Issues

- MVP max file size is 2 GB (`2_147_483_648` bytes); future expansion should update configuration, validation, UI copy, and tests together.
- Provide compress/split upload guidance for videos over 20 minutes?
- How far should auto-crop criteria go for 9:16 short-form rendering?
- How to communicate 24-hour physical deletion policy after project deletion?
- What default local model download size is acceptable?
- Officially support CPU-only, or recommend GPU/Apple Silicon?
