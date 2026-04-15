from __future__ import annotations

import asyncio
import re
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from sys import platform
from typing import Callable

from app.models import SynthesisResult, VoiceProfile

try:
    import edge_tts
except ImportError:  # pragma: no cover - handled by runtime validation
    edge_tts = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover - handled by runtime validation
    pyttsx3 = None


class TTSService:
    """Synthesizes audio using a local TTS backend."""

    DEFAULT_EDGE_VOICE = "en-US-AriaNeural"

    def __init__(
        self,
        output_dir: str | Path = "outputs",
        provider: str = "auto",
        engine_factory: Callable[[], object] | None = None,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.provider = provider
        self.engine_factory = engine_factory or self._default_engine_factory

    def synthesize_to_file(self, text: str, voice_profile: VoiceProfile) -> SynthesisResult:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Text input cannot be empty.")

        provider = self._resolve_provider()
        output_path = self.build_output_path(cleaned_text, provider)

        if provider == "edge":
            self._synthesize_with_edge_tts(cleaned_text, voice_profile, output_path)
            pitch_applied = True
        else:
            self._synthesize_with_pyttsx3(cleaned_text, voice_profile, output_path)
            pitch_applied = False

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(
                "Audio synthesis completed without producing a file. "
                "Check that your local speech engine supports file output."
            )

        return SynthesisResult(
            output_path=str(output_path.resolve()),
            file_name=output_path.name,
            provider=provider,
            rate=voice_profile.rate,
            volume=voice_profile.volume,
            pitch_delta=voice_profile.pitch_delta,
            pitch_applied=pitch_applied,
        )

    def build_output_path(self, text: str, provider: str | None = None) -> Path:
        slug = self._slugify(text)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resolved_provider = provider or self._resolve_provider()
        extension = ".mp3" if resolved_provider == "edge" else ".wav"
        return self.output_dir / f"{timestamp}_{slug}{extension}"

    def _default_engine_factory(self) -> object:
        if pyttsx3 is None:
            raise RuntimeError(
                "pyttsx3 is not installed. Install dependencies with `python -m pip install -r requirements.txt`."
            )
        return pyttsx3.init()

    def _resolve_provider(self) -> str:
        if self.provider != "auto":
            return self.provider
        if edge_tts is not None:
            return "edge"
        if platform.startswith("win"):
            return "pyttsx3"
        return "pyttsx3"

    def _synthesize_with_pyttsx3(self, text: str, voice_profile: VoiceProfile, output_path: Path) -> None:
        engine = self.engine_factory()
        try:
            engine.setProperty("rate", voice_profile.rate)
            engine.setProperty("volume", voice_profile.volume)
            engine.save_to_file(text, str(output_path))
            engine.runAndWait()
        finally:
            stop = getattr(engine, "stop", None)
            if callable(stop):
                stop()

    def _synthesize_with_edge_tts(self, text: str, voice_profile: VoiceProfile, output_path: Path) -> None:
        if edge_tts is None:
            raise RuntimeError(
                "edge-tts is not installed. Install dependencies with `python -m pip install edge-tts`."
            )

        communicate = edge_tts.Communicate(
            text=text,
            voice=self.DEFAULT_EDGE_VOICE,
            rate=self._to_edge_rate(voice_profile.rate),
            volume=self._to_edge_volume(voice_profile.volume),
            pitch=self._to_edge_pitch(voice_profile.pitch_delta),
        )

        try:
            asyncio.run(communicate.save(str(output_path)))
        except Exception as exc:  # pragma: no cover - depends on runtime/network
            raise RuntimeError(
                "Edge TTS synthesis failed. Check your internet connection or switch to the preview mode."
            ) from exc

    @staticmethod
    def _to_edge_rate(rate: int) -> str:
        percent = max(-50, min(50, round((rate - 175) / 1.75)))
        return f"{percent:+d}%"

    @staticmethod
    def _to_edge_volume(volume: float) -> str:
        percent = max(-50, min(50, round((volume - 0.85) * 100)))
        return f"{percent:+d}%"

    @staticmethod
    def _to_edge_pitch(pitch_delta: int) -> str:
        hz = max(-20, min(20, pitch_delta * 4))
        return f"{hz:+d}Hz"

    @staticmethod
    def _slugify(text: str) -> str:
        snippet = " ".join(text.lower().split()[:6])
        slug = re.sub(r"[^a-z0-9]+", "-", snippet).strip("-")
        return slug or "speech"

    @staticmethod
    def as_dict(result: SynthesisResult) -> dict[str, object]:
        return asdict(result)
