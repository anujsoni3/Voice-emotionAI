from __future__ import annotations

import argparse
import os

import uvicorn

from app.services.emotion_service import EmotionService
from app.services.tts_service import TTSService
from app.services.voice_mapper import VoiceMapper


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze text emotion and preview the voice settings for The Empathy Engine."
    )
    parser.add_argument("text", nargs="*", help="Text to analyze. If omitted, interactive mode is used.")
    parser.add_argument(
        "--web",
        action="store_true",
        help="Launch the FastAPI web demo instead of the CLI flow.",
    )
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
    parser.add_argument(
        "--intensity",
        choices=["auto", "mild", "moderate", "strong"],
        default="auto",
        help="Force intensity level instead of auto detection.",
    )
    parser.add_argument(
        "--persona",
        choices=["support", "sales", "executive"],
        default="support",
        help="Select speaking persona preset.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.web:
        port = int(os.getenv("PORT", "8000"))
        uvicorn.run("app.web:app", host="0.0.0.0", port=port, reload=False)
        return

    text = " ".join(args.text).strip()
    if not text:
        text = input("Enter text for the Empathy Engine: ").strip()

    emotion_service = EmotionService()
    voice_mapper = VoiceMapper()
    cli_provider = args.provider or "edge"
    tts_service = TTSService(provider=cli_provider)

    intensity_override = None if args.intensity == "auto" else args.intensity
    analysis = emotion_service.analyze(text, intensity_override=intensity_override)
    voice_profile = voice_mapper.map_emotion(analysis, persona=args.persona)

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
    print(f"Persona: {args.persona}")

    if analysis.cues:
        print(f"Detected cues: {', '.join(analysis.cues)}")

    if args.preview_only:
        print("\nPreview mode enabled. Audio generation skipped.")
        return

    print(f"\nGenerating audio with provider: {cli_provider}")
    synthesis = tts_service.synthesize_to_file(analysis.text, voice_profile, persona=args.persona)
    print(f"\nAudio file generated: {synthesis.output_path}")
    print(f"TTS provider: {synthesis.provider}")
    print(f"Pitch applied directly: {synthesis.pitch_applied}")


if __name__ == "__main__":
    main()
