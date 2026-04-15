import tempfile
import unittest
from pathlib import Path

from app.models import VoiceProfile
from app.services.tts_service import TTSService


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
    def test_build_output_path_uses_wav_and_slug_for_pyttsx3(self) -> None:
        service = TTSService(output_dir="outputs", provider="pyttsx3", engine_factory=FakeEngine)
        output_path = service.build_output_path("This is the best news ever!", provider="pyttsx3")

        self.assertEqual(output_path.suffix, ".wav")
        self.assertIn("this-is-the-best-news-ever", output_path.name)

    def test_build_output_path_uses_mp3_for_edge(self) -> None:
        service = TTSService(output_dir="outputs", provider="edge")
        output_path = service.build_output_path("This is the best news ever!", provider="edge")

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

            result = service.synthesize_to_file("Thank you for the wonderful update!", profile)

            self.assertTrue(Path(result.output_path).exists())
            self.assertEqual(fake_engine.properties["rate"], 203)
            self.assertEqual(fake_engine.properties["volume"], 0.92)
            self.assertFalse(result.pitch_applied)

    def test_edge_rate_conversion_is_clamped(self) -> None:
        service = TTSService(output_dir="outputs")
        self.assertEqual(service._to_edge_rate(175), "+0%")
        self.assertEqual(service._to_edge_rate(210), "+20%")
        self.assertEqual(service._to_edge_rate(1000), "+50%")


if __name__ == "__main__":
    unittest.main()
