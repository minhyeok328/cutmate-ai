from __future__ import annotations

import io
from pathlib import Path

import pytest

from app.media.storage import (
    InvalidMediaIdentifierError,
    LocalMediaStorage,
    UnsupportedMediaExtensionError,
    UploadTooLargeError,
)


def test_source_upload_uses_stable_layout_and_preserves_allowed_extension(
    tmp_path: Path,
) -> None:
    storage_root = tmp_path / ".cutmate" / "storage"
    storage = LocalMediaStorage(storage_root)

    saved = storage.save_source_upload(
        video_id="video_123",
        upload_filename="My Clip.MP4",
        source=io.BytesIO(b"video-bytes"),
        max_bytes=32,
    )

    assert saved.path == storage_root / "uploads" / "video_123" / "source.mp4"
    assert saved.video_id == "video_123"
    assert saved.extension == "mp4"
    assert saved.size_bytes == len(b"video-bytes")
    assert saved.path.read_bytes() == b"video-bytes"


@pytest.mark.parametrize("filename", ["clip.avi", "clip", "clip.mp4.exe"])
def test_source_upload_rejects_unsupported_extensions(
    tmp_path: Path,
    filename: str,
) -> None:
    storage = LocalMediaStorage(tmp_path / ".cutmate" / "storage")

    with pytest.raises(UnsupportedMediaExtensionError):
        storage.save_source_upload(
            video_id="video_123",
            upload_filename=filename,
            source=io.BytesIO(b"video-bytes"),
            max_bytes=32,
        )


def test_source_upload_rejects_files_over_max_bytes(tmp_path: Path) -> None:
    storage_root = tmp_path / ".cutmate" / "storage"
    storage = LocalMediaStorage(storage_root)

    with pytest.raises(UploadTooLargeError):
        storage.save_source_upload(
            video_id="video_123",
            upload_filename="clip.mov",
            source=io.BytesIO(b"123456"),
            max_bytes=5,
            chunk_size=2,
        )

    assert not (storage_root / "uploads" / "video_123" / "source.mov").exists()
    assert not (storage_root / "uploads" / "video_123" / "source.mov.uploading").exists()


class TrackingStream(io.BytesIO):
    def __init__(self, data: bytes) -> None:
        super().__init__(data)
        self.read_sizes: list[int | None] = []

    def read(self, size: int | None = -1, /) -> bytes:
        self.read_sizes.append(size)
        if size is None or size < 0:
            raise AssertionError("storage helper must not perform unbounded reads")
        return super().read(size)


def test_source_upload_streams_copy_in_bounded_chunks(tmp_path: Path) -> None:
    stream = TrackingStream(b"abcdefghi")
    storage = LocalMediaStorage(tmp_path / ".cutmate" / "storage")

    saved = storage.save_source_upload(
        video_id="video_stream",
        upload_filename="clip.m4v",
        source=stream,
        max_bytes=32,
        chunk_size=4,
    )

    assert saved.path.read_bytes() == b"abcdefghi"
    assert len(stream.read_sizes) > 1
    assert set(stream.read_sizes) == {4}


@pytest.mark.parametrize(
    "video_id",
    ["", ".", "..", "../video", "..\\video", "/video", "C:\\video", "%2e%2e", "bad id"],
)
def test_source_upload_rejects_unsafe_video_ids(tmp_path: Path, video_id: str) -> None:
    storage = LocalMediaStorage(tmp_path / ".cutmate" / "storage")

    with pytest.raises(InvalidMediaIdentifierError):
        storage.save_source_upload(
            video_id=video_id,
            upload_filename="clip.mp4",
            source=io.BytesIO(b"video-bytes"),
            max_bytes=32,
        )
