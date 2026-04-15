import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from fastapi.testclient import TestClient

from app.models import EmotionAnalysis, SynthesisResult, VoiceProfile
from app.web import app
import app.web as web_module


class FakeEmotionService:
    def analyze(self, text: str, intensity_override: str | None = None) -> EmotionAnalysis:
        return EmotionAnalysis(
            text=text,
            emotion="happy",
            sentiment_score=0.91,
            intensity=intensity_override or "strong",
            confidence=0.94,
            cues=["positive_keywords:2"],
        )

    def split_sentences(self, text: str, max_sentences: int = 6) -> list[str]:
        return ["Thank you for the wonderful update!", "This means a lot."]


class FakeVoiceMapper:
    def map_emotion(self, analysis: EmotionAnalysis, persona: str = "support") -> VoiceProfile:
        return VoiceProfile(
            emotion=analysis.emotion,
            intensity=analysis.intensity,
            rate=210 if persona != "executive" else 190,
            volume=1.0,
            pitch_delta=6,
            style_note=f"{persona} persona style.",
        )


class FakeTTSService:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.provider = "auto"
        self.settings = type("FakeSettings", (), {"elevenlabs_api_key": "test-key"})()
        self.counter = 0

    def synthesize_to_file(self, text: str, voice_profile: VoiceProfile, persona: str = "support") -> SynthesisResult:
        self.counter += 1
        target = self.output_dir / f"web-test-{self.counter}.mp3"
        target.write_bytes(b"fake-audio")
        return SynthesisResult(
            output_path=str(target),
            file_name=target.name,
            provider="edge",
            rate=voice_profile.rate,
            volume=voice_profile.volume,
            pitch_delta=voice_profile.pitch_delta,
            pitch_applied=True,
        )


class WebAppTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = TemporaryDirectory()
        self.original_emotion_service = web_module.emotion_service
        self.original_voice_mapper = web_module.voice_mapper
        self.original_tts_service = web_module.tts_service
        web_module.emotion_service = FakeEmotionService()
        web_module.voice_mapper = FakeVoiceMapper()
        web_module.tts_service = FakeTTSService(Path(self.temp_dir.name))
        self.client = TestClient(app)

    def tearDown(self) -> None:
        web_module.emotion_service = self.original_emotion_service
        web_module.voice_mapper = self.original_voice_mapper
        web_module.tts_service = self.original_tts_service
        self.temp_dir.cleanup()

    def test_home_page_loads(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("The Empathy Engine", response.text)

    def test_healthz_get_and_head(self) -> None:
        get_response = self.client.get("/healthz")
        head_response = self.client.head("/healthz")

        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), {"status": "ok"})
        self.assertEqual(head_response.status_code, 200)

    def test_generate_page_returns_audio_result(self) -> None:
        response = self.client.post(
            "/generate",
            data={
                "text": "Thank you for the wonderful update! This means a lot.",
                "compare_mode": "on",
                "sentence_mode": "on",
                "intensity_mode": "moderate",
                "persona": "executive",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("Empathetic Output", response.text)
        self.assertIn("Neutral Baseline", response.text)
        self.assertIn("Sentence-level modulation", response.text)
        self.assertIn("Download JSON", response.text)
        self.assertIn("happy", response.text)
        self.assertIn("executive", response.text)
        self.assertIn("web-test-1.mp3", response.text)

    def test_generate_requires_non_empty_text(self) -> None:
        response = self.client.post("/generate", data={"text": "   "})

        self.assertEqual(response.status_code, 400)
        self.assertIn("Please enter some text", response.text)


if __name__ == "__main__":
    unittest.main()
