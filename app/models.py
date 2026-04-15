from dataclasses import dataclass, field


@dataclass(slots=True)
class EmotionAnalysis:
    text: str
    emotion: str
    sentiment_score: float
    intensity: str
    confidence: float
    cues: list[str] = field(default_factory=list)


@dataclass(slots=True)
class VoiceProfile:
    emotion: str
    intensity: str
    rate: int
    volume: float
    pitch_delta: int
    style_note: str


@dataclass(slots=True)
class SynthesisResult:
    output_path: str
    file_name: str
    provider: str
    rate: int
    volume: float
    pitch_delta: int
    pitch_applied: bool
