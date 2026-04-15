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

    def test_surprised_voice_has_higher_pitch_than_happy_mild(self) -> None:
        surprised = EmotionAnalysis(
            text="Wow this is unbelievable!",
            emotion="surprised",
            sentiment_score=0.8,
            intensity="strong",
            confidence=0.9,
        )
        happy = EmotionAnalysis(
            text="Great update",
            emotion="happy",
            sentiment_score=0.6,
            intensity="mild",
            confidence=0.8,
        )

        surprised_profile = self.mapper.map_emotion(surprised)
        happy_profile = self.mapper.map_emotion(happy)

        self.assertGreaterEqual(surprised_profile.pitch_delta, happy_profile.pitch_delta)

    def test_concerned_voice_is_slower_than_neutral(self) -> None:
        concerned = EmotionAnalysis(
            text="I am concerned about this urgent issue.",
            emotion="concerned",
            sentiment_score=-0.3,
            intensity="moderate",
            confidence=0.82,
        )
        neutral = EmotionAnalysis(
            text="Please share the status update.",
            emotion="neutral",
            sentiment_score=0.0,
            intensity="mild",
            confidence=0.6,
        )

        concerned_profile = self.mapper.map_emotion(concerned)
        neutral_profile = self.mapper.map_emotion(neutral)

        self.assertLess(concerned_profile.rate, neutral_profile.rate)

    def test_inquisitive_voice_has_positive_pitch(self) -> None:
        inquisitive = EmotionAnalysis(
            text="Could you explain why this happened?",
            emotion="inquisitive",
            sentiment_score=0.05,
            intensity="moderate",
            confidence=0.78,
        )

        profile = self.mapper.map_emotion(inquisitive)

        self.assertGreater(profile.pitch_delta, 0)


if __name__ == "__main__":
    unittest.main()
