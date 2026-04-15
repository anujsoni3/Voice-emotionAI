import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
import requests

from app.models import VoiceProfile
from app.services.tts_service import TTSService
from app.settings import Settings


class FakeEngine:
    def __init__(self) -> None:
        self.properties: dict[str, object] = {}
        self.saved_path: Path | None = None

    def setProperty(self, key: str, value: object) -> None:
        self.properties[key] = value

    def save_to_file(self, text: str, filename: str) -> None:
        self.saved_path = Path(filename)
        self.saved_path.write_bytes(b"RIFFfake")

    def runAndWait(self) -> None:
        return

    def stop(self) -> None:
        return


class TTSServiceTests(unittest.TestCase):
    def test_default_http_session_ignores_proxy_env(self) -> None:
        service = TTSService(output_dir="outputs")

        self.assertFalse(service.http_session.trust_env)

    def test_auto_provider_prefers_explicit_setting(self) -> None:
        settings = Settings(tts_provider="pyttsx3")
        service = TTSService(output_dir="outputs", settings=settings, engine_factory=FakeEngine)

        self.assertEqual(service._resolve_provider(), "pyttsx3")

    def test_build_output_path_uses_wav_and_slug_for_pyttsx3(self) -> None:
        service = TTSService(output_dir="outputs", provider="pyttsx3", engine_factory=FakeEngine)
        output_path = service.build_output_path("This is the best news ever!", provider="pyttsx3")

        self.assertEqual(output_path.suffix, ".wav")
        self.assertIn("this-is-the-best-news-ever", output_path.name)

    def test_build_output_path_uses_mp3_for_edge(self) -> None:
        service = TTSService(output_dir="outputs", provider="edge")
        output_path = service.build_output_path("This is the best news ever!", provider="edge")

        self.assertEqual(output_path.suffix, ".mp3")

    def test_build_output_path_uses_mp3_for_elevenlabs(self) -> None:
        service = TTSService(output_dir="outputs", provider="elevenlabs")
        output_path = service.build_output_path("This is the best news ever!", provider="elevenlabs")

        self.assertEqual(output_path.suffix, ".mp3")

    def test_synthesize_to_file_applies_rate_and_volume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            fake_engine = FakeEngine()
            service = TTSService(output_dir=tmp_dir, provider="pyttsx3", engine_factory=lambda: fake_engine)
            profile = VoiceProfile(
                emotion="happy",
                intensity="moderate",
                rate=203,
                volume=0.92,
                pitch_delta=5,
                style_note="Warm and excited.",
            )

            result = service.synthesize_to_file("Thank you for the wonderful update!", profile, persona="sales")

            self.assertTrue(Path(result.output_path).exists())
            self.assertEqual(fake_engine.properties["rate"], 203)
            self.assertEqual(fake_engine.properties["volume"], 0.92)
            self.assertFalse(result.pitch_applied)

    def test_prosody_enhancer_adds_persona_prefix(self) -> None:
        profile = VoiceProfile(
            emotion="happy",
            intensity="moderate",
            rate=203,
            volume=0.92,
            pitch_delta=5,
            style_note="Warm and excited.",
        )

        text = TTSService._enhance_text_prosody("this is a great update", profile, persona="sales")

        self.assertTrue(text.startswith("Here is the exciting part."))
        self.assertTrue(text.endswith("!"))

    def test_prosody_enhancer_softens_concerned_exclamation(self) -> None:
        profile = VoiceProfile(
            emotion="concerned",
            intensity="strong",
            rate=150,
            volume=0.9,
            pitch_delta=-3,
            style_note="Calm and reassuring.",
        )

        text = TTSService._enhance_text_prosody("Please help immediately!", profile, persona="support")

        self.assertIn("Let me walk you through this clearly.", text)
        self.assertNotIn("!", text)

    def test_edge_rate_conversion_is_clamped(self) -> None:
        service = TTSService(output_dir="outputs")
        self.assertEqual(service._to_edge_rate(175), "+0%")
        self.assertEqual(service._to_edge_rate(210), "+20%")
        self.assertEqual(service._to_edge_rate(1000), "+50%")

    def test_auto_provider_prefers_elevenlabs_when_key_exists(self) -> None:
        settings = Settings(tts_provider="auto", elevenlabs_api_key="test-key")
        service = TTSService(output_dir="outputs", settings=settings)

        self.assertEqual(service._resolve_provider(), "elevenlabs")

    def test_elevenlabs_provider_chain_falls_back_to_edge_and_pyttsx3(self) -> None:
        settings = Settings(tts_provider="elevenlabs", elevenlabs_api_key="test-key")
        service = TTSService(output_dir="outputs", settings=settings)

        chain = service._provider_chain("elevenlabs")

        self.assertIn("elevenlabs", chain)
        self.assertIn("pyttsx3", chain)

    def test_edge_provider_chain_includes_pyttsx3_fallback(self) -> None:
        service = TTSService(output_dir="outputs", provider="edge")

        chain = service._provider_chain("edge")

        self.assertIn("edge", chain)
        self.assertIn("pyttsx3", chain)

    def test_elevenlabs_request_writes_mp3_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            response = Mock()
            response.content = b"fake-mp3-audio"
            response.raise_for_status.return_value = None

            session = Mock()
            session.post.return_value = response

            settings = Settings(
                tts_provider="elevenlabs",
                elevenlabs_api_key="test-key",
                elevenlabs_voice_id="voice-123",
                elevenlabs_model_id="eleven_multilingual_v2",
            )
            service = TTSService(output_dir=tmp_dir, settings=settings, http_session=session)
            profile = VoiceProfile(
                emotion="happy",
                intensity="strong",
                rate=210,
                volume=1.0,
                pitch_delta=6,
                style_note="Warm and excited.",
            )

            result = service.synthesize_to_file("Thank you for the wonderful update!", profile, persona="sales")

            self.assertTrue(Path(result.output_path).exists())
            self.assertEqual(Path(result.output_path).suffix, ".mp3")
            self.assertEqual(result.provider, "elevenlabs")
            self.assertTrue(result.pitch_applied)
            session.post.assert_called_once()

    def test_auto_mode_falls_back_when_elevenlabs_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            response = Mock()
            response.raise_for_status.side_effect = requests.RequestException("proxy failure")

            session = Mock()
            session.post.return_value = response

            settings = Settings(tts_provider="auto", elevenlabs_api_key="test-key")
            service = TTSService(
                output_dir=tmp_dir,
                settings=settings,
                http_session=session,
            )
            service._synthesize_with_edge_tts = lambda text, voice_profile, output_path: output_path.write_bytes(b"edge")
            profile = VoiceProfile(
                emotion="happy",
                intensity="strong",
                rate=210,
                volume=1.0,
                pitch_delta=6,
                style_note="Warm and excited.",
            )

            result = service.synthesize_to_file("Thank you for the wonderful update!", profile, persona="sales")

            self.assertEqual(result.provider, "edge")
            self.assertTrue(Path(result.output_path).exists())


if __name__ == "__main__":
    unittest.main()
