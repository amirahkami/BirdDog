from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class CVExtractionError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


@dataclass(frozen=True)
class CVExtractionResult:
    text: str
    language: str
    method: str


def extract_pdf(
    path: Path,
    *,
    timeout_seconds: int,
    ocr_dpi: int,
    maximum_characters: int = 2_000_000,
) -> CVExtractionResult:
    command = [
        sys.executable,
        "-m",
        "app.cv.extract_child",
        "--path",
        str(path),
        "--ocr-dpi",
        str(ocr_dpi),
        "--maximum-characters",
        str(maximum_characters),
    ]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as error:
        raise CVExtractionError(
            "extraction_timeout",
            "CV text extraction exceeded its time limit",
            retryable=True,
        ) from error

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as error:
        detail = completed.stderr.strip()[-500:]
        raise CVExtractionError(
            "extractor_failure",
            f"CV extractor returned an invalid response: {detail}",
            retryable=True,
        ) from error

    if completed.returncode != 0:
        raise CVExtractionError(
            str(payload.get("error_code", "extractor_failure")),
            str(payload.get("message", "CV extraction failed")),
            retryable=bool(payload.get("retryable", False)),
        )

    return CVExtractionResult(
        text=str(payload["text"]),
        language=str(payload["language"]),
        method=str(payload["method"]),
    )
