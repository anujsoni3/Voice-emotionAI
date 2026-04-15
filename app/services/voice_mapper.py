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

PERSONA_PRESETS = {
    "support": {
        "rate_shift": -5,
        "volume_shift": 0.02,
        "pitch_shift": -1,
        "style_prefix": "Support Agent persona: calm, patient, and reassuring.",
    },
    "sales": {
        "rate_shift": 6,
        "volume_shift": 0.03,
        "pitch_shift": 1,
        "style_prefix": "Sales Rep persona: confident, upbeat, and persuasive.",
    },
    "executive": {
        "rate_shift": -2,
        "volume_shift": 0.0,
        "pitch_shift": -1,
        "style_prefix": "Executive Briefing persona: composed, concise, and authoritative.",
    },
}


class VoiceMapper:
    """Maps emotion analysis to speech settings for the TTS layer."""

    def map_emotion(self, analysis: EmotionAnalysis, persona: str = "support") -> VoiceProfile:
        base = BASE_PROFILES[analysis.emotion]
        adjustment = INTENSITY_ADJUSTMENTS[analysis.intensity]
        persona_config = PERSONA_PRESETS.get(persona, PERSONA_PRESETS["support"])

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

        rate = max(120, min(240, rate + persona_config["rate_shift"]))
        volume = max(0.5, min(1.0, volume + persona_config["volume_shift"]))
        pitch_delta = max(-8, min(8, pitch_delta + persona_config["pitch_shift"]))

        return VoiceProfile(
            emotion=analysis.emotion,
            intensity=analysis.intensity,
            rate=rate,
            volume=round(volume, 2),
            pitch_delta=pitch_delta,
            style_note=f"{persona_config['style_prefix']} {base['style_note']}",
        )

    def map_as_dict(self, analysis: EmotionAnalysis, persona: str = "support") -> dict[str, object]:
        return asdict(self.map_emotion(analysis, persona=persona))
