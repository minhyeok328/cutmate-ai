from app.analysis.draft import DraftMedia, build_draft_analysis


def test_draft_analysis_generates_reviewable_candidates_without_llm() -> None:
    result = build_draft_analysis(
        DraftMedia(
            duration_ms=60_000,
            has_audio=True,
            purpose="promotional_video",
            output_goal="highlight_extraction",
        )
    )

    assert len(result.subtitles) == 2
    assert result.subtitles[0].start_ms == 0
    assert result.subtitles[0].end_ms > result.subtitles[0].start_ms
    assert len(result.cut_candidates) == 1
    assert result.cut_candidates[0].segment_type == "cut"
    assert result.cut_candidates[0].start_ms < result.cut_candidates[0].end_ms
    assert "pause" in result.cut_candidates[0].reason.lower()
    assert len(result.highlight_candidates) == 1
    assert result.highlight_candidates[0].segment_type == "highlight"
    assert "promotional" in result.highlight_candidates[0].reason
    assert result.warnings == ()


def test_draft_analysis_skips_subtitles_but_keeps_candidates_without_audio() -> None:
    result = build_draft_analysis(
        DraftMedia(
            duration_ms=45_000,
            has_audio=False,
            purpose="lecture",
            output_goal="source_summary",
        )
    )

    assert result.subtitles == ()
    assert len(result.cut_candidates) == 1
    assert "without audio" in result.cut_candidates[0].reason
    assert len(result.highlight_candidates) == 1
    assert result.warnings == ("speech_recognition_skipped_no_audio",)
