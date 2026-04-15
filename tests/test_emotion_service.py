import unittest

from app.services.emotion_service import EmotionService


class EmotionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = EmotionService()

    def test_detects_happy_text(self) -> None:
        analysis = self.service.analyze("This is the best news ever! Thank you so much!")
        self.assertEqual(analysis.emotion, "happy")
        self.assertIn(analysis.intensity, {"moderate", "strong"})
        self.assertGreater(analysis.sentiment_score, 0)

    def test_detects_frustrated_text(self) -> None:
        analysis = self.service.analyze("I am very frustrated. This delay is awful and the issue is still not fixed.")
        self.assertEqual(analysis.emotion, "frustrated")
        self.assertGreaterEqual(analysis.sentiment_score, -1.0)
        self.assertLess(analysis.sentiment_score, 0)

    def test_detects_neutral_text(self) -> None:
        analysis = self.service.analyze("Please confirm the meeting schedule for tomorrow afternoon.")
        self.assertEqual(analysis.emotion, "neutral")

    def test_detects_surprised_text(self) -> None:
        analysis = self.service.analyze("Wow, this is incredible news! I am amazed!")
        self.assertEqual(analysis.emotion, "surprised")

    def test_detects_concerned_text(self) -> None:
        analysis = self.service.analyze("I am concerned about this urgent issue, please help immediately.")
        self.assertEqual(analysis.emotion, "concerned")

    def test_detects_inquisitive_text(self) -> None:
        analysis = self.service.analyze("Could you clarify why the schedule changed?")
        self.assertEqual(analysis.emotion, "inquisitive")

    def test_rejects_empty_text(self) -> None:
        with self.assertRaises(ValueError):
            self.service.analyze("   ")

    def test_intensity_override_forces_output_level(self) -> None:
        analysis = self.service.analyze(
            "This is fine and informational.",
            intensity_override="strong",
        )
        self.assertEqual(analysis.intensity, "strong")

    def test_split_sentences_limits_segments(self) -> None:
        text = "One. Two! Three? Four. Five. Six. Seven."
        segments = self.service.split_sentences(text, max_sentences=4)
        self.assertEqual(len(segments), 4)
        self.assertEqual(segments[0], "One.")


if __name__ == "__main__":
    unittest.main()
