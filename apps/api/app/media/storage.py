from __future__ import annotations

import os
import re
import stat
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

SUPPORTED_VIDEO_EXTENSIONS = frozenset({"mp4", "mov", "m4v"})
DEFAULT_COPY_CHUNK_SIZE = 1024 * 1024

_SAFE_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


class MediaStorageError(ValueError):
    """Base error for rejected media storage operations."""


class InvalidMediaIdentifierError(MediaStorageError):
    """Raised when a generated storage identifier is not safe for path use."""


class UnsupportedMediaExtensionError(MediaStorageError):
    """Raised when an upload filename does not end in an allowed video extension."""


class UploadTooLargeError(MediaStorageError):
    """Raised when streaming an upload exceeds the caller-supplied byte limit."""

    def __init__(self, *, max_bytes: int, bytes_read: int) -> None:
        super().__init__("Upload exceeds the configured maximum size.")
        self.max_bytes = max_bytes
        self.bytes_read = bytes_read


class UnsafeStoragePathError(MediaStorageError):
    """Raised when a storage path would escape or use filesystem indirection."""


class BinarySource(Protocol):
    def read(self, size: int = -1, /) -> object:
        """Read at most size bytes from the source."""


@dataclass(frozen=True)
class StoredSourceUpload:
    video_id: str
    extension: str
    path: Path
    size_bytes: int


class LocalMediaStorage:
    """Deterministic local media storage rooted at the configured storage directory."""

    def __init__(self, storage_root: str | Path) -> None:
        self.storage_root = Path(storage_root)

    def source_upload_dir(self, video_id: str) -> Path:
        safe_video_id = _validate_video_id(video_id)
        return self.storage_root / "uploads" / safe_video_id

    def source_upload_path(self, video_id: str, extension: str) -> Path:
        normalized_extension = _validate_upload_extension(extension)
        return self.source_upload_dir(video_id) / f"source.{normalized_extension}"

    def save_source_upload(
        self,
        *,
        video_id: str,
        upload_filename: str,
        source: BinarySource,
        max_bytes: int,
        chunk_size: int = DEFAULT_COPY_CHUNK_SIZE,
    ) -> StoredSourceUpload:
        if max_bytes < 0:
            raise ValueError("max_bytes must be greater than or equal to zero")
        if chunk_size <= 0:
            raise ValueError("chunk_size must be greater than zero")

        extension = sanitize_upload_extension(upload_filename)
        upload_dir = self.source_upload_dir(video_id)
        final_path = upload_dir / f"source.{extension}"
        temp_path = upload_dir / f"source.{extension}.uploading"

        self._prepare_upload_directory(upload_dir)
        self._reject_indirection_if_present(final_path)
        self._remove_stale_temp_file(temp_path)

        bytes_read = 0
        try:
            with temp_path.open("xb") as target:
                while True:
                    chunk = source.read(chunk_size)
                    if chunk == b"":
                        break
                    if not isinstance(chunk, bytes):
                        raise TypeError("source.read() must return bytes")

                    bytes_read += len(chunk)
                    if bytes_read > max_bytes:
                        raise UploadTooLargeError(max_bytes=max_bytes, bytes_read=bytes_read)

                    target.write(chunk)

            self._assert_inside_storage_root(temp_path)
            os.replace(temp_path, final_path)
            self._assert_inside_storage_root(final_path)
        except Exception:
            with suppress(FileNotFoundError):
                temp_path.unlink()
            raise

        return StoredSourceUpload(
            video_id=video_id,
            extension=extension,
            path=final_path,
            size_bytes=bytes_read,
        )

    def _prepare_upload_directory(self, upload_dir: Path) -> None:
        self.storage_root.mkdir(parents=True, mode=0o700, exist_ok=True)
        uploads_root = self.storage_root / "uploads"
        uploads_root.mkdir(mode=0o700, exist_ok=True)
        upload_dir.mkdir(mode=0o700, exist_ok=True)

        for path in (self.storage_root, uploads_root, upload_dir):
            self._reject_indirection_if_present(path)
            self._assert_inside_storage_root(path)

    def _remove_stale_temp_file(self, temp_path: Path) -> None:
        self._reject_indirection_if_present(temp_path)
        with suppress(FileNotFoundError):
            temp_path.unlink()

    def _assert_inside_storage_root(self, path: Path) -> None:
        root = self.storage_root.resolve(strict=False)
        resolved = path.resolve(strict=False)
        try:
            resolved.relative_to(root)
        except ValueError as exc:
            raise UnsafeStoragePathError("Resolved media path escapes the storage root.") from exc

    def _reject_indirection_if_present(self, path: Path) -> None:
        if not path.exists() and not path.is_symlink():
            return

        try:
            path_stat = path.lstat()
        except FileNotFoundError:
            return

        has_reparse_point = bool(
            getattr(path_stat, "st_file_attributes", 0)
            & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
        )
        if path.is_symlink() or has_reparse_point:
            raise UnsafeStoragePathError("Storage path uses filesystem indirection.")


def sanitize_upload_extension(upload_filename: str) -> str:
    if _has_control_character(upload_filename):
        raise UnsupportedMediaExtensionError("Upload filename contains unsafe characters.")

    filename = upload_filename.strip()
    if "." not in filename:
        raise UnsupportedMediaExtensionError("Upload filename has no extension.")

    extension = filename.rsplit(".", maxsplit=1)[1].lower()
    return _validate_upload_extension(extension)


def _validate_upload_extension(extension: str) -> str:
    normalized_extension = extension.strip().lower().removeprefix(".")
    if normalized_extension not in SUPPORTED_VIDEO_EXTENSIONS:
        raise UnsupportedMediaExtensionError("Unsupported media extension.")
    return normalized_extension


def _validate_video_id(video_id: str) -> str:
    if not _SAFE_ID_RE.fullmatch(video_id):
        raise InvalidMediaIdentifierError("Media storage IDs must be generated safe tokens.")
    return video_id


def _has_control_character(value: str) -> bool:
    return any(ord(character) < 32 or ord(character) == 127 for character in value)
