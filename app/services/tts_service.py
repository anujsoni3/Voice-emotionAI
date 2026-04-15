from __future__ import annotations

import asyncio
import re
from concurrent.futures import Future
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from sys import platform
from threading import Thread
from typing import Any, Awaitable, Callable, Protocol, cast

import requests

from app.models import SynthesisResult, VoiceProfile
from app.settings import Settings

try:
    import edge_tts
except ImportError:  # pragma: no cover - handled by runtime validation
    edge_tts = None

try:
    import pyttsx3
except ImportError:  # pragma: no cover - handled by runtime validation
    pyttsx3 = None


class Pyttsx3Engine(Protocol):
    def setProperty(self, name: str, value: str | float | int) -> None: ...

    def save_to_file(self, text: str, filename: str) -> None: ...

    def runAndWait(self) -> None: ...

    def stop(self) -> None: ...


class TTSService:
    """Synthesizes audio using a local TTS backend."""

    DEFAULT_EDGE_VOICE = "en-US-AriaNeural"

    def __init__(
        self,
        output_dir: str | Path = "outputs",
        provider: str | None = None,
        engine_factory: Callable[[], Pyttsx3Engine] | None = None,
        settings: Settings | None = None,
        http_session: requests.sessions.Session | None = None,
    ) -> None:
        self.settings = settings or Settings.from_env()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.provider = provider or self.settings.tts_provider
        self.engine_factory = engine_factory or self._default_engine_factory
        self.http_session = http_session or requests.Session()
        if http_session is None:
            self.http_session.trust_env = False

    def synthesize_to_file(self, text: str, voice_profile: VoiceProfile, persona: str = "support") -> SynthesisResult:
        cleaned_text = text.strip()
        if not cleaned_text:
            raise ValueError("Text input cannot be empty.")
        prepared_text = self._enhance_text_prosody(cleaned_text, voice_profile, persona)

        selected_provider = self.provider or "auto"
        attempted_providers = self._provider_chain(selected_provider)

        last_error: RuntimeError | None = None
        provider_used = attempted_providers[0]
        pitch_applied = False

        for candidate in attempted_providers:
            output_path = self.build_output_path(cleaned_text, candidate)
            try:
                if candidate == "elevenlabs":
                    self._synthesize_with_elevenlabs(prepared_text, voice_profile, output_path)
                    pitch_applied = True
                elif candidate == "edge":
                    self._synthesize_with_edge_tts(prepared_text, voice_profile, output_path)
                    pitch_applied = True
                else:
                    self._synthesize_with_pyttsx3(prepared_text, voice_profile, output_path)
                    pitch_applied = False
            except RuntimeError as exc:
                last_error = exc
                continue

            provider_used = candidate
            break
        else:
            if last_error is not None:
                raise last_error
            raise RuntimeError("No text-to-speech provider is available.")

        if not output_path.exists() or output_path.stat().st_size == 0:
            raise RuntimeError(
                "Audio synthesis completed without producing a file. "
                "Check that your local speech engine supports file output."
            )

        return SynthesisResult(
            output_path=str(output_path.resolve()),
            file_name=output_path.name,
            provider=provider_used,
            rate=voice_profile.rate,
            volume=voice_profile.volume,
            pitch_delta=voice_profile.pitch_delta,
            pitch_applied=pitch_applied,
        )

    def build_output_path(self, text: str, provider: str | None = None) -> Path:
        slug = self._slugify(text)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        resolved_provider = provider or self._resolve_provider()
        extension = ".mp3" if resolved_provider in {"edge", "elevenlabs"} else ".wav"
        return self.output_dir / f"{timestamp}_{slug}{extension}"

    def _default_engine_factory(self) -> Pyttsx3Engine:
        if pyttsx3 is None:
            raise RuntimeError(
                "pyttsx3 is not installed. Install dependencies with `python -m pip install -r requirements.txt`."
            )
        return cast(Pyttsx3Engine, pyttsx3.init())

    def _resolve_provider(self) -> str:
        if self.provider != "auto":
            return self.provider
        if self.settings.elevenlabs_api_key:
            return "elevenlabs"
        if edge_tts is not None:
            return "edge"
        if platform.startswith("win"):
            return "pyttsx3"
        return "pyttsx3"

    def _provider_chain(self, provider: str) -> list[str]:
        if provider == "elevenlabs":
            preferred = ["elevenlabs", "edge", "pyttsx3"]
        elif provider == "edge":
            preferred = ["edge", "pyttsx3"]
        elif provider == "pyttsx3":
            preferred = ["pyttsx3"]
        elif provider == "auto":
            preferred = ["elevenlabs", "edge", "pyttsx3"]
        else:
            preferred = [provider]

        chain: list[str] = []
        for candidate in preferred:
            if candidate == "elevenlabs" and not self.settings.elevenlabs_api_key:
                continue
            if candidate == "edge" and edge_tts is None:
                continue
            chain.append(candidate)

        if "pyttsx3" not in chain:
            chain.append("pyttsx3")

        seen: set[str] = set()
        return [candidate for candidate in chain if not (candidate in seen or seen.add(candidate))]

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
            self._run_async_task(communicate.save(str(output_path)))
        except Exception as exc:  # pragma: no cover - depends on runtime/network
            raise RuntimeError(
                "Edge TTS synthesis failed. Check your internet connection or switch to the preview mode."
            ) from exc

    def _synthesize_with_elevenlabs(self, text: str, voice_profile: VoiceProfile, output_path: Path) -> None:
        if not self.settings.elevenlabs_api_key:
            raise RuntimeError(
                "ElevenLabs provider selected, but `ELEVENLABS_API_KEY` is not set."
            )

        url = (
            f"https://api.elevenlabs.io/v1/text-to-speech/"
            f"{self.settings.elevenlabs_voice_id}?output_format=mp3_44100_128"
        )
        headers = {
            "xi-api-key": self.settings.elevenlabs_api_key,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }
        payload = {
            "text": text,
            "model_id": self.settings.elevenlabs_model_id,
            "voice_settings": self._elevenlabs_voice_settings(voice_profile),
        }

        try:
            response = self.http_session.post(url, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                "ElevenLabs synthesis failed. Check the API key, voice id, model id, or network access."
            ) from exc

        output_path.write_bytes(response.content)

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
    def _elevenlabs_voice_settings(voice_profile: VoiceProfile) -> dict[str, float | bool]:
        speed = max(0.7, min(1.2, round(voice_profile.rate / 175, 2)))
        stability = {
            "happy": 0.35,
            "neutral": 0.6,
            "frustrated": 0.7,
        }.get(voice_profile.emotion, 0.6)
        similarity_boost = {
            "happy": 0.8,
            "neutral": 0.78,
            "frustrated": 0.82,
        }.get(voice_profile.emotion, 0.78)
        style = {
            "mild": 0.1,
            "moderate": 0.28,
            "strong": 0.45,
        }.get(voice_profile.intensity, 0.2)

        return {
            "stability": stability,
            "similarity_boost": similarity_boost,
            "style": style,
            "speed": speed,
            "use_speaker_boost": True,
        }

    @staticmethod
    def _slugify(text: str) -> str:
        snippet = " ".join(text.lower().split()[:6])
        slug = re.sub(r"[^a-z0-9]+", "-", snippet).strip("-")
        return slug or "speech"

    @staticmethod
    def _run_async_task(coro: Awaitable[object]) -> None:
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.run(coro)
            return

        result: Future[None] = Future()

        def runner() -> None:
            try:
                asyncio.run(coro)
            except Exception as exc:  # pragma: no cover - depends on runtime/network
                result.set_exception(exc)
            else:
                result.set_result(None)

        thread = Thread(target=runner, daemon=True)
        thread.start()
        thread.join()
        result.result()

    @staticmethod
    def as_dict(result: SynthesisResult) -> dict[str, object]:
        return asdict(result)

    @staticmethod
    def _enhance_text_prosody(text: str, voice_profile: VoiceProfile, persona: str) -> str:
        normalized = " ".join(text.split())
        if not normalized:
            return text

        # Insert pause hints after common clause boundaries for smoother pacing.
        normalized = re.sub(r",\s*", ", ", normalized)
        normalized = re.sub(r"\s+(and|but|because|however|therefore|so)\s+", r", \1 ", normalized, flags=re.IGNORECASE)

        if normalized[-1] not in ".!?":
            normalized = f"{normalized}."

        if voice_profile.emotion in {"frustrated", "concerned"}:
            normalized = re.sub(r"!+", ".", normalized)

        if voice_profile.emotion in {"happy", "surprised"} and "!" not in normalized:
            normalized = normalized[:-1] + "!"

        persona_prefix = {
            "support": "Let me walk you through this clearly.",
            "sales": "Here is the exciting part.",
            "executive": "Key update.",
        }.get(persona, "")

        if persona_prefix:
            return f"{persona_prefix} {normalized}"
        return normalized
