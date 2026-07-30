from __future__ import annotations

import hashlib
import os
import stat
import uuid
from dataclasses import dataclass
from pathlib import Path

import pymupdf
from fastapi import UploadFile


CHUNK_SIZE = 1024 * 1024


class CVValidationError(ValueError):
    def __init__(self, code: str, message: str, status_code: int = 422) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code


@dataclass(frozen=True)
class StoredPDF:
    original_filename: str
    storage_key: str
    byte_size: int
    page_count: int
    sha256: str


class CVStorage:
    def __init__(self, root: str | Path, *, maximum_bytes: int, maximum_pages: int) -> None:
        self.root = Path(root)
        self.maximum_bytes = maximum_bytes
        self.maximum_pages = maximum_pages

    async def store(self, upload: UploadFile, *, user_id: uuid.UUID) -> StoredPDF:
        original_filename = _safe_original_filename(upload.filename)
        if not original_filename.lower().endswith(".pdf"):
            raise CVValidationError("invalid_extension", "Only PDF files are accepted")
        if upload.content_type != "application/pdf":
            raise CVValidationError("invalid_content_type", "The file must use application/pdf")

        user_directory = self.root / str(user_id)
        user_directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        os.chmod(user_directory, 0o700)
        identifier = uuid.uuid4()
        final_path = user_directory / f"{identifier}.pdf"
        temporary_path = user_directory / f".{identifier}.upload"

        digest = hashlib.sha256()
        total = 0
        signature = bytearray()
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW

        try:
            descriptor = os.open(temporary_path, flags, 0o600)
            with os.fdopen(descriptor, "wb") as target:
                while chunk := await upload.read(CHUNK_SIZE):
                    total += len(chunk)
                    if total > self.maximum_bytes:
                        raise CVValidationError(
                            "file_too_large",
                            f"PDF files may not exceed {self.maximum_bytes} bytes",
                            status_code=413,
                        )
                    if len(signature) < 5:
                        signature.extend(chunk[: 5 - len(signature)])
                    digest.update(chunk)
                    target.write(chunk)
                target.flush()
                os.fsync(target.fileno())

            if total == 0:
                raise CVValidationError("empty_file", "The uploaded PDF is empty")
            if bytes(signature) != b"%PDF-":
                raise CVValidationError("invalid_signature", "The file is not a valid PDF")

            os.replace(temporary_path, final_path)
            os.chmod(final_path, 0o600)
            page_count = self._inspect(final_path)
            storage_key = final_path.relative_to(self.root).as_posix()
            return StoredPDF(
                original_filename=original_filename,
                storage_key=storage_key,
                byte_size=total,
                page_count=page_count,
                sha256=digest.hexdigest(),
            )
        except Exception:
            temporary_path.unlink(missing_ok=True)
            final_path.unlink(missing_ok=True)
            raise
        finally:
            await upload.close()

    def resolve(self, storage_key: str) -> Path:
        root = self.root.resolve()
        candidate = self.root / storage_key
        try:
            metadata = candidate.lstat()
        except FileNotFoundError as error:
            raise CVValidationError("file_missing", "Stored CV file is missing") from error
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise CVValidationError("unsafe_storage_entry", "Stored CV path is not a regular file")
        resolved = candidate.resolve()
        if resolved == root or root not in resolved.parents:
            raise CVValidationError("unsafe_storage_path", "Stored CV path is outside its volume")
        return resolved

    def delete(self, storage_key: str) -> None:
        try:
            path = self.resolve(storage_key)
        except CVValidationError as error:
            if error.code == "file_missing":
                return
            raise
        path.unlink(missing_ok=True)

    def _inspect(self, path: Path) -> int:
        try:
            with pymupdf.open(path) as document:
                if document.needs_pass or document.is_encrypted:
                    raise CVValidationError(
                        "encrypted_pdf", "Encrypted PDFs are not accepted"
                    )
                page_count = document.page_count
        except CVValidationError:
            raise
        except Exception as error:
            raise CVValidationError("invalid_pdf", "The PDF is damaged or unreadable") from error

        if page_count < 1:
            raise CVValidationError("empty_pdf", "The PDF contains no pages")
        if page_count > self.maximum_pages:
            raise CVValidationError(
                "too_many_pages",
                f"PDF files may not exceed {self.maximum_pages} pages",
            )
        return page_count


def _safe_original_filename(filename: str | None) -> str:
    cleaned = (filename or "").replace("\x00", "").replace("\\", "/")
    cleaned = cleaned.rsplit("/", maxsplit=1)[-1].strip()
    if not cleaned:
        raise CVValidationError("missing_filename", "A filename is required")
    return cleaned[:255]
