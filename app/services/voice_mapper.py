from __future__ import annotations

from dataclasses import asdict

from app.models import EmotionAnalysis, VoiceProfile


BASE_PROFILES = {
    "happy": {
        "rate": 195,
        "volume": 0.95,
        "pitch_delta": 4,
        "style_note": "Deliver with warmth, uplift, and positive momentum.",
    },
    "surprised": {
        "rate": 190,
        "volume": 0.96,
        "pitch_delta": 5,
        "style_note": "Deliver with energetic emphasis and crisp excitement.",
    },
    "neutral": {
        "rate": 175,
        "volume": 0.85,
        "pitch_delta": 0,
        "style_note": "Deliver clearly, steadily, and without strong affect.",
    },
    "inquisitive": {
        "rate": 172,
        "volume": 0.86,
        "pitch_delta": 2,
        "style_note": "Deliver with curious clarity and a lightly rising intonation.",
    },
    "concerned": {
        "rate": 162,
        "volume": 0.9,
        "pitch_delta": -2,
        "style_note": "Deliver with care, reassurance, and attentive urgency.",
    },
    "frustrated": {
        "rate": 155,
        "volume": 0.9,
        "pitch_delta": -3,
        "style_note": "Deliver calmly and patiently with grounded reassurance.",
    },
}

INTENSITY_ADJUSTMENTS = {
    "mild": {"rate": 0, "volume": 0.0, "pitch_delta": 0},
    "moderate": {"rate": 8, "volume": 0.03, "pitch_delta": 1},
    "strong": {"rate": 15, "volume": 0.06, "pitch_delta": 2},
}


class VoiceMapper:
    """Maps emotion analysis to speech settings for the TTS layer."""

    def map_emotion(self, analysis: EmotionAnalysis) -> VoiceProfile:
        base = BASE_PROFILES[analysis.emotion]
        adjustment = INTENSITY_ADJUSTMENTS[analysis.intensity]

        if analysis.emotion in {"frustrated", "concerned"}:
            rate = base["rate"] - adjustment["rate"]
            volume = min(1.0, base["volume"] + adjustment["volume"])
            pitch_delta = base["pitch_delta"] - adjustment["pitch_delta"]
        elif analysis.emotion in {"happy", "surprised"}:
            rate = base["rate"] + adjustment["rate"]
            volume = min(1.0, base["volume"] + adjustment["volume"])
            pitch_delta = base["pitch_delta"] + adjustment["pitch_delta"]
        elif analysis.emotion == "inquisitive":
            rate = base["rate"] + max(2, adjustment["rate"] // 3)
            volume = min(1.0, base["volume"] + adjustment["volume"] / 2)
            pitch_delta = base["pitch_delta"] + max(1, adjustment["pitch_delta"])
        else:
            rate = base["rate"]
            volume = min(1.0, base["volume"] + adjustment["volume"] / 2)
            pitch_delta = base["pitch_delta"]

        return VoiceProfile(
            emotion=analysis.emotion,
            intensity=analysis.intensity,
            rate=rate,
            volume=round(volume, 2),
            pitch_delta=pitch_delta,
            style_note=base["style_note"],
        )

    def map_as_dict(self, analysis: EmotionAnalysis) -> dict[str, object]:
        return asdict(self.map_emotion(analysis))
