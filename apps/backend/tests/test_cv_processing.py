from __future__ import annotations

import asyncio
import io
import subprocess
import uuid
from pathlib import Path

import pymupdf
import pytest
from fastapi import UploadFile
from starlette.datastructures import Headers

from app.cv import CVExtractionError, CVStorage, CVValidationError, extract_pdf


ENGLISH_TEXT = """
Curriculum Vitae
Work experience and education
Responsible for product design and user research.
Skills and knowledge include Figma, prototyping, English and German.
Training and studies completed successfully.
"""

GERMAN_TEXT = """
Lebenslauf
Berufserfahrung und Ausbildung
Verantwortlich für Produktdesign und Nutzerforschung.
Kenntnisse: Figma, Prototyping, Deutsch und Englisch.
Studium, Schule und Weiterbildung erfolgreich abgeschlossen.
"""


def test_secure_storage_accepts_and_sanitizes_valid_pdf(tmp_path: Path) -> None:
    storage = CVStorage(tmp_path, maximum_bytes=26214400, maximum_pages=50)
    stored = asyncio.run(
        storage.store(
            upload(_pdf_bytes(ENGLISH_TEXT), "../../resume.pdf"),
            user_id=uuid.uuid4(),
        )
    )

    path = storage.resolve(stored.storage_key)
    assert stored.original_filename == "resume.pdf"
    assert stored.page_count == 1
    assert stored.byte_size == path.stat().st_size
    assert oct(path.stat().st_mode & 0o777) == "0o600"
    assert len(stored.sha256) == 64


@pytest.mark.parametrize(
    ("filename", "content_type", "data", "code"),
    [
        ("resume.txt", "application/pdf", b"%PDF-test", "invalid_extension"),
        ("resume.pdf", "text/plain", b"%PDF-test", "invalid_content_type"),
        ("resume.pdf", "application/pdf", b"not-a-pdf", "invalid_signature"),
        ("resume.pdf", "application/pdf", b"", "empty_file"),
    ],
)
def test_storage_rejects_invalid_uploads(
    tmp_path: Path,
    filename: str,
    content_type: str,
    data: bytes,
    code: str,
) -> None:
    storage = CVStorage(tmp_path, maximum_bytes=26214400, maximum_pages=50)
    with pytest.raises(CVValidationError) as captured:
        asyncio.run(
            storage.store(
                upload(data, filename, content_type),
                user_id=uuid.uuid4(),
            )
        )
    assert captured.value.code == code


def test_storage_rejects_size_page_and_encryption_limits(tmp_path: Path) -> None:
    too_large = CVStorage(tmp_path / "size", maximum_bytes=100, maximum_pages=50)
    with pytest.raises(CVValidationError) as size_error:
        asyncio.run(
            too_large.store(upload(_pdf_bytes(ENGLISH_TEXT), "resume.pdf"), user_id=uuid.uuid4())
        )
    assert size_error.value.code == "file_too_large"

    too_many_pages = CVStorage(tmp_path / "pages", maximum_bytes=26214400, maximum_pages=1)
    with pytest.raises(CVValidationError) as page_error:
        asyncio.run(
            too_many_pages.store(
                upload(_pdf_bytes(ENGLISH_TEXT, pages=2), "resume.pdf"),
                user_id=uuid.uuid4(),
            )
        )
    assert page_error.value.code == "too_many_pages"

    encrypted = CVStorage(tmp_path / "encrypted", maximum_bytes=26214400, maximum_pages=50)
    with pytest.raises(CVValidationError) as encrypted_error:
        asyncio.run(
            encrypted.store(
                upload(_pdf_bytes(ENGLISH_TEXT, encrypted=True), "resume.pdf"),
                user_id=uuid.uuid4(),
            )
        )
    assert encrypted_error.value.code == "encrypted_pdf"


def test_storage_size_limit_is_inclusive(tmp_path: Path) -> None:
    data = _pdf_bytes(ENGLISH_TEXT)
    accepted = CVStorage(tmp_path / "accepted", maximum_bytes=len(data), maximum_pages=50)
    stored = asyncio.run(
        accepted.store(upload(data, "resume.pdf"), user_id=uuid.uuid4())
    )
    assert stored.byte_size == len(data)

    rejected = CVStorage(tmp_path / "rejected", maximum_bytes=len(data) - 1, maximum_pages=50)
    with pytest.raises(CVValidationError) as captured:
        asyncio.run(
            rejected.store(upload(data, "resume.pdf"), user_id=uuid.uuid4())
        )
    assert captured.value.code == "file_too_large"


def test_storage_rejects_damaged_pdf_with_valid_signature(tmp_path: Path) -> None:
    storage = CVStorage(tmp_path, maximum_bytes=26214400, maximum_pages=50)
    with pytest.raises(CVValidationError) as captured:
        asyncio.run(
            storage.store(upload(b"%PDF-damaged", "resume.pdf"), user_id=uuid.uuid4())
        )
    assert captured.value.code == "invalid_pdf"


def test_storage_rejects_symlink_entries(tmp_path: Path) -> None:
    outside = tmp_path / "outside.pdf"
    outside.write_bytes(_pdf_bytes(ENGLISH_TEXT))
    link = tmp_path / "link.pdf"
    link.symlink_to(outside)
    storage = CVStorage(tmp_path, maximum_bytes=26214400, maximum_pages=50)
    with pytest.raises(CVValidationError) as captured:
        storage.resolve("link.pdf")
    assert captured.value.code == "unsafe_storage_entry"


@pytest.mark.parametrize(
    ("text", "language"),
    [(ENGLISH_TEXT, "en"), (GERMAN_TEXT, "de")],
)
def test_native_text_extraction(tmp_path: Path, text: str, language: str) -> None:
    path = tmp_path / f"{language}.pdf"
    path.write_bytes(_pdf_bytes(text))
    result = extract_pdf(path, timeout_seconds=20, ocr_dpi=150)
    assert result.method == "native"
    assert result.language == language
    assert "experience" in result.text.lower() or "berufserfahrung" in result.text.lower()


def test_scanned_pdf_uses_ocr(tmp_path: Path) -> None:
    path = tmp_path / "scan.pdf"
    path.write_bytes(_scanned_pdf_bytes())
    result = extract_pdf(path, timeout_seconds=60, ocr_dpi=200)
    assert result.method == "ocr"
    assert result.language == "en"
    assert "experience" in result.text.lower()


def test_ocr_rejects_unsafe_page_dimensions(tmp_path: Path) -> None:
    path = tmp_path / "oversized-page.pdf"
    document = pymupdf.open()
    document.new_page(width=14400, height=14400)
    path.write_bytes(document.tobytes())
    document.close()

    with pytest.raises(CVExtractionError) as captured:
        extract_pdf(path, timeout_seconds=20, ocr_dpi=200)
    assert captured.value.code == "page_too_large"


def test_extraction_timeout_is_retryable(monkeypatch, tmp_path: Path) -> None:
    def timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="extract", timeout=1)

    monkeypatch.setattr("app.cv.extraction.subprocess.run", timeout)
    with pytest.raises(CVExtractionError) as captured:
        extract_pdf(tmp_path / "unused.pdf", timeout_seconds=5, ocr_dpi=150)
    assert captured.value.code == "extraction_timeout"
    assert captured.value.retryable is True


def upload(
    data: bytes,
    filename: str,
    content_type: str = "application/pdf",
) -> UploadFile:
    return UploadFile(
        file=io.BytesIO(data),
        filename=filename,
        headers=Headers({"content-type": content_type}),
    )


def _pdf_bytes(text: str, *, pages: int = 1, encrypted: bool = False) -> bytes:
    document = pymupdf.open()
    for _ in range(pages):
        page = document.new_page()
        page.insert_textbox(page.rect + (50, 50, -50, -50), text, fontsize=12)
    options = {}
    if encrypted:
        options = {
            "encryption": pymupdf.PDF_ENCRYPT_AES_256,
            "owner_pw": "owner-secret",
            "user_pw": "user-secret",
        }
    data = document.tobytes(**options)
    document.close()
    return data


def _scanned_pdf_bytes() -> bytes:
    source = pymupdf.open()
    page = source.new_page(width=1000, height=700)
    page.insert_text(
        (60, 100),
        "WORK EXPERIENCE AND SKILLS EDUCATION TRAINING RESPONSIBLE WORK ENGLISH",
        fontsize=25,
    )
    image = page.get_pixmap(dpi=200).tobytes("png")
    source.close()

    scanned = pymupdf.open()
    page = scanned.new_page(width=1000, height=700)
    page.insert_image(page.rect, stream=image)
    data = scanned.tobytes()
    scanned.close()
    return data
