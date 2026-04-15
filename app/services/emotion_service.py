from __future__ import annotations

import re
from dataclasses import asdict
from typing import Iterable

from app.models import EmotionAnalysis

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
except ImportError:  # pragma: no cover - fallback is for missing local dependency
    SentimentIntensityAnalyzer = None


POSITIVE_CUES = {
    "thank",
    "thanks",
    "great",
    "awesome",
    "amazing",
    "love",
    "wonderful",
    "fantastic",
    "glad",
    "happy",
    "perfect",
    "excellent",
    "best",
}

NEGATIVE_CUES = {
    "bad",
    "terrible",
    "awful",
    "upset",
    "frustrated",
    "angry",
    "issue",
    "problem",
    "broken",
    "worst",
    "disappointed",
    "sorry",
    "delay",
    "complaint",
}

NEUTRAL_CUES = {
    "update",
    "schedule",
    "confirm",
    "noted",
    "information",
    "details",
}


class EmotionService:
    """Detects coarse emotional tone for the empathy engine."""

    def __init__(self) -> None:
        self._analyzer = SentimentIntensityAnalyzer() if SentimentIntensityAnalyzer else None

    def analyze(self, text: str) -> EmotionAnalysis:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Text input cannot be empty.")

        compound = self._compound_score(cleaned_text)
        emphasis = self._emphasis_multiplier(cleaned_text)
        positive_hits = self._count_hits(cleaned_text, POSITIVE_CUES)
        negative_hits = self._count_hits(cleaned_text, NEGATIVE_CUES)
        neutral_hits = self._count_hits(cleaned_text, NEUTRAL_CUES)

        adjusted_score = compound
        cues: list[str] = []

        if positive_hits:
            adjusted_score += 0.08 * positive_hits
            cues.append(f"positive_keywords:{positive_hits}")
        if negative_hits:
            adjusted_score -= 0.1 * negative_hits
            cues.append(f"negative_keywords:{negative_hits}")
        if emphasis > 1.0:
            adjusted_score *= emphasis
            cues.append(f"emphasis:{emphasis:.2f}")
        if neutral_hits and not positive_hits and not negative_hits:
            adjusted_score *= 0.75
            cues.append(f"neutral_keywords:{neutral_hits}")

        adjusted_score = max(-1.0, min(1.0, adjusted_score))
        emotion = self._label_for_score(adjusted_score)
        intensity = self._intensity_for_score(adjusted_score, cleaned_text, positive_hits, negative_hits)
        confidence = min(0.99, 0.45 + abs(adjusted_score) * 0.45 + min(0.1, 0.03 * (positive_hits + negative_hits)))

        return EmotionAnalysis(
            text=cleaned_text,
            emotion=emotion,
            sentiment_score=round(adjusted_score, 3),
            intensity=intensity,
            confidence=round(confidence, 3),
            cues=cues,
        )

    def analyze_as_dict(self, text: str) -> dict[str, object]:
        return asdict(self.analyze(text))

    def _compound_score(self, text: str) -> float:
        if self._analyzer is not None:
            return float(self._analyzer.polarity_scores(text)["compound"])

        positive_hits = self._count_hits(text, POSITIVE_CUES)
        negative_hits = self._count_hits(text, NEGATIVE_CUES)
        if positive_hits == negative_hits == 0:
            return 0.0
        return max(-1.0, min(1.0, (positive_hits - negative_hits) / 4))

    @staticmethod
    def _count_hits(text: str, keywords: Iterable[str]) -> int:
        tokens = re.findall(r"[A-Za-z']+", text.lower())
        return sum(token in keywords for token in tokens)

    @staticmethod
    def _emphasis_multiplier(text: str) -> float:
        exclamation_count = text.count("!")
        uppercase_words = sum(word.isupper() and len(word) > 2 for word in text.split())
        return 1.0 + min(0.35, exclamation_count * 0.07 + uppercase_words * 0.08)

    @staticmethod
    def _label_for_score(score: float) -> str:
        if score >= 0.25:
            return "happy"
        if score <= -0.25:
            return "frustrated"
        return "neutral"

    @staticmethod
    def _intensity_for_score(score: float, text: str, positive_hits: int, negative_hits: int) -> str:
        signal = abs(score) + min(0.35, text.count("!") * 0.06) + min(0.2, (positive_hits + negative_hits) * 0.04)
        if signal >= 0.8:
            return "strong"
        if signal >= 0.4:
            return "moderate"
        return "mild"
