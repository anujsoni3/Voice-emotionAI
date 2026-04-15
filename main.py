from __future__ import annotations

import argparse

from app.services.emotion_service import EmotionService
from app.services.tts_service import TTSService
from app.services.voice_mapper import VoiceMapper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze text emotion and preview the voice settings for The Empathy Engine."
    )
    parser.add_argument("text", nargs="*", help="Text to analyze. If omitted, interactive mode is used.")
    parser.add_argument(
        "--provider",
        choices=["auto", "elevenlabs", "edge", "pyttsx3"],
        help="Choose the speech provider. Defaults to environment configuration or automatic selection.",
    )
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help="Skip audio generation and only print the detected emotion and voice settings.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text = " ".join(args.text).strip()
    if not text:
        text = input("Enter text for the Empathy Engine: ").strip()

    emotion_service = EmotionService()
    voice_mapper = VoiceMapper()
    tts_service = TTSService(provider=args.provider)

    analysis = emotion_service.analyze(text)
    voice_profile = voice_mapper.map_emotion(analysis)

    print("\nThe Empathy Engine analysis")
    print(f"Text: {analysis.text}")
    print(f"Detected emotion: {analysis.emotion}")
    print(f"Sentiment score: {analysis.sentiment_score}")
    print(f"Intensity: {analysis.intensity}")
    print(f"Confidence: {analysis.confidence}")
    print(f"Voice rate: {voice_profile.rate}")
    print(f"Voice volume: {voice_profile.volume}")
    print(f"Pitch delta: {voice_profile.pitch_delta}")
    print(f"Style note: {voice_profile.style_note}")

    if analysis.cues:
        print(f"Detected cues: {', '.join(analysis.cues)}")

    if args.preview_only:
        print("\nPreview mode enabled. Audio generation skipped.")
        return

    synthesis = tts_service.synthesize_to_file(analysis.text, voice_profile)
    print(f"\nAudio file generated: {synthesis.output_path}")
    print(f"TTS provider: {synthesis.provider}")
    print(f"Pitch applied directly: {synthesis.pitch_applied}")


if __name__ == "__main__":
    main()
