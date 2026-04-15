import unittest

from app.models import EmotionAnalysis
from app.services.voice_mapper import VoiceMapper


class VoiceMapperTests(unittest.TestCase):
    def setUp(self) -> None:
        self.mapper = VoiceMapper()

    def test_happy_voice_is_faster_than_neutral(self) -> None:
        happy = EmotionAnalysis(
            text="Great job!",
            emotion="happy",
            sentiment_score=0.7,
            intensity="strong",
            confidence=0.9,
        )
        neutral = EmotionAnalysis(
            text="Please share the report.",
            emotion="neutral",
            sentiment_score=0.0,
            intensity="mild",
            confidence=0.6,
        )

        happy_profile = self.mapper.map_emotion(happy)
        neutral_profile = self.mapper.map_emotion(neutral)

        self.assertGreater(happy_profile.rate, neutral_profile.rate)
        self.assertGreaterEqual(happy_profile.volume, neutral_profile.volume)

    def test_frustrated_voice_is_slower_than_neutral(self) -> None:
        frustrated = EmotionAnalysis(
            text="This problem is getting worse.",
            emotion="frustrated",
            sentiment_score=-0.8,
            intensity="strong",
            confidence=0.9,
        )
        neutral = EmotionAnalysis(
            text="Checking current status.",
            emotion="neutral",
            sentiment_score=0.0,
            intensity="mild",
            confidence=0.6,
        )

        frustrated_profile = self.mapper.map_emotion(frustrated)
        neutral_profile = self.mapper.map_emotion(neutral)

        self.assertLess(frustrated_profile.rate, neutral_profile.rate)
        self.assertLess(frustrated_profile.pitch_delta, neutral_profile.pitch_delta)


if __name__ == "__main__":
    unittest.main()
