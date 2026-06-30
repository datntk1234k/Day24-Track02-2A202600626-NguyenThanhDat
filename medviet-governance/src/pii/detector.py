# src/pii/detector.py
import re

from presidio_analyzer import AnalyzerEngine, RecognizerResult


CCCD_REGEX = r"\b\d{12}\b"
PHONE_REGEX = r"\b0[35789]\d{8}\b"
EMAIL_REGEX = r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}\b"
NAME_REGEX = (
    r"\b[A-ZÀ-Ỹ][a-zà-ỹ]*(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]*){1,5}\b"
)


class VietnameseAnalyzer:
    """Lightweight analyzer compatible with Presidio's analyze() contract."""

    def __init__(self):
        self._patterns = {
            "VN_CCCD": (re.compile(CCCD_REGEX), 0.9),
            "VN_PHONE": (re.compile(PHONE_REGEX), 0.85),
            "EMAIL_ADDRESS": (re.compile(EMAIL_REGEX), 0.9),
            "PERSON": (re.compile(NAME_REGEX), 0.7),
        }

    def analyze(
        self,
        text: str,
        language: str = "vi",
        entities: list[str] | None = None,
    ) -> list[RecognizerResult]:
        if not text:
            return []

        del language  # Regex recognizers are language-agnostic for this lab.

        requested_entities = entities or list(self._patterns)
        results: list[RecognizerResult] = []

        for entity in requested_entities:
            pattern_config = self._patterns.get(entity)
            if not pattern_config:
                continue

            pattern, score = pattern_config
            for match in pattern.finditer(str(text)):
                results.append(
                    RecognizerResult(
                        entity_type=entity,
                        start=match.start(),
                        end=match.end(),
                        score=score,
                    )
                )

        return _remove_overlaps(results)


def _remove_overlaps(results: list[RecognizerResult]) -> list[RecognizerResult]:
    ordered_results = sorted(
        results,
        key=lambda item: (item.start, -(item.end - item.start), -item.score),
    )
    filtered: list[RecognizerResult] = []

    for result in ordered_results:
        if filtered and result.start < filtered[-1].end:
            continue
        filtered.append(result)

    return filtered


def build_vietnamese_analyzer() -> AnalyzerEngine:
    return VietnameseAnalyzer()


def detect_pii(text: str, analyzer: AnalyzerEngine) -> list:
    """Detect PII trong text tiếng Việt."""
    return analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"],
    )
