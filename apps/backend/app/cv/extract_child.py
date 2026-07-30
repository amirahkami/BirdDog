from __future__ import annotations

import argparse
import json
import re

import pymupdf


MINIMUM_PAGE_CHARACTERS = 40
MINIMUM_DOCUMENT_CHARACTERS = 40
MAXIMUM_OCR_PIXELS_PER_PAGE = 25_000_000
GERMAN_WORDS = {
    "ausbildung", "berufserfahrung", "deutsch", "kenntnisse", "schule",
    "studium", "tätigkeiten", "über", "und", "verantwortlich", "weiterbildung",
}
ENGLISH_WORDS = {
    "and", "education", "english", "experience", "knowledge", "responsible",
    "school", "skills", "studies", "training", "work",
}


def extract(path: str, *, ocr_dpi: int, maximum_characters: int) -> dict[str, str]:
    try:
        document = pymupdf.open(path)
    except Exception as error:
        raise ChildExtractionError("invalid_pdf", "The stored PDF cannot be opened") from error

    with document:
        if document.needs_pass or document.is_encrypted:
            raise ChildExtractionError("encrypted_pdf", "Encrypted PDFs are not accepted")
        page_texts: list[str] = []
        ocr_pages = 0
        native_pages = 0
        for page in document:
            native_text = page.get_text("text", sort=True).strip()
            if len(re.sub(r"\s+", "", native_text)) >= MINIMUM_PAGE_CHARACTERS:
                text = native_text
                native_pages += 1
            else:
                width_pixels = page.rect.width * ocr_dpi / 72
                height_pixels = page.rect.height * ocr_dpi / 72
                if width_pixels * height_pixels > MAXIMUM_OCR_PIXELS_PER_PAGE:
                    raise ChildExtractionError(
                        "page_too_large", "A CV page is too large for safe OCR"
                    )
                try:
                    text_page = page.get_textpage_ocr(
                        language="deu+eng",
                        dpi=ocr_dpi,
                        full=True,
                    )
                    text = page.get_text("text", textpage=text_page, sort=True).strip()
                    ocr_pages += 1
                except Exception as error:
                    raise ChildExtractionError(
                        "ocr_failed", "OCR could not read the PDF", retryable=True
                    ) from error
            page_texts.append(text)
            if sum(len(item) for item in page_texts) > maximum_characters:
                raise ChildExtractionError(
                    "text_too_large", "Extracted CV text exceeds the safety limit"
                )

    text = "\n\n".join(part for part in page_texts if part).strip()
    if len(re.sub(r"\s+", "", text)) < MINIMUM_DOCUMENT_CHARACTERS:
        raise ChildExtractionError("no_readable_text", "No readable CV text was found")
    method = "mixed" if native_pages and ocr_pages else "ocr" if ocr_pages else "native"
    return {"text": text, "language": detect_language(text), "method": method}


def detect_language(text: str) -> str:
    words = set(re.findall(r"[a-zäöüß]+", text.lower()))
    german_score = len(words & GERMAN_WORDS)
    english_score = len(words & ENGLISH_WORDS)
    if german_score == english_score == 0:
        return "other"
    return "de" if german_score > english_score else "en"


class ChildExtractionError(RuntimeError):
    def __init__(self, code: str, message: str, *, retryable: bool = False) -> None:
        super().__init__(message)
        self.code = code
        self.retryable = retryable


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", required=True)
    parser.add_argument("--ocr-dpi", required=True, type=int)
    parser.add_argument("--maximum-characters", required=True, type=int)
    arguments = parser.parse_args()
    try:
        result = extract(
            arguments.path,
            ocr_dpi=arguments.ocr_dpi,
            maximum_characters=arguments.maximum_characters,
        )
    except ChildExtractionError as error:
        print(
            json.dumps(
                {
                    "error_code": error.code,
                    "message": str(error),
                    "retryable": error.retryable,
                }
            )
        )
        raise SystemExit(1) from error
    print(json.dumps(result))


if __name__ == "__main__":
    main()
