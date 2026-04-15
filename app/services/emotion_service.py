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

SURPRISED_CUES = {
    "wow",
    "unbelievable",
    "incredible",
    "unexpected",
    "surprised",
    "shocked",
    "amazed",
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

CONCERNED_CUES = {
    "concerned",
    "worried",
    "urgent",
    "risk",
    "immediately",
    "asap",
    "critical",
    "please",
    "help",
}

NEUTRAL_CUES = {
    "update",
    "schedule",
    "confirm",
    "noted",
    "information",
    "details",
}

INQUISITIVE_CUES = {
    "can",
    "could",
    "would",
    "when",
    "where",
    "why",
    "how",
    "what",
    "clarify",
    "explain",
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
        surprised_hits = self._count_hits(cleaned_text, SURPRISED_CUES)
        concerned_hits = self._count_hits(cleaned_text, CONCERNED_CUES)
        inquisitive_hits = self._count_hits(cleaned_text, INQUISITIVE_CUES)
        question_marks = cleaned_text.count("?")
        exclamation_count = cleaned_text.count("!")

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
        if surprised_hits:
            cues.append(f"surprised_keywords:{surprised_hits}")
        if concerned_hits:
            cues.append(f"concerned_keywords:{concerned_hits}")
        if inquisitive_hits:
            cues.append(f"inquisitive_keywords:{inquisitive_hits}")
        if question_marks:
            cues.append(f"questions:{question_marks}")

        adjusted_score = max(-1.0, min(1.0, adjusted_score))
        emotion = self._label_for_signal(
            adjusted_score,
            surprised_hits=surprised_hits,
            concerned_hits=concerned_hits,
            inquisitive_hits=inquisitive_hits,
            negative_hits=negative_hits,
            question_marks=question_marks,
            exclamation_count=exclamation_count,
        )
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
    def _label_for_signal(
        score: float,
        surprised_hits: int,
        concerned_hits: int,
        inquisitive_hits: int,
        negative_hits: int,
        question_marks: int,
        exclamation_count: int,
    ) -> str:
        if surprised_hits and score >= 0.2:
            return "surprised"
        if surprised_hits and exclamation_count >= 2 and score >= 0.45:
            return "surprised"
        if concerned_hits >= 3:
            return "concerned"
        if concerned_hits >= 2 and negative_hits:
            return "concerned"
        if concerned_hits >= 2 and score <= 0.35:
            return "concerned"
        if concerned_hits and score <= -0.15:
            return "concerned"
        if question_marks and (inquisitive_hits or abs(score) < 0.35):
            return "inquisitive"
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
