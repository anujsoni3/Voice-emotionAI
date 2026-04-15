# The Empathy Engine

An AI voice assistant prototype that detects emotion from input text and adjusts speech delivery so the generated voice sounds more expressive and human.

## Project Status
This repository is being built phase by phase using the roadmap in [PLAN.md](/c:/Users/ANUJ/OneDrive/Desktop/Voice-emotion-ai/PLAN.md).

Current progress:
- Phase 1 complete: project scaffold and repository setup
- Phase 2 complete: emotion detection with intensity scoring
- Phase 3 complete: emotion-to-voice parameter mapping
- Phase 4 complete: audio generation using `edge-tts` with parameter modulation
- Phase 5 complete: CLI now generates playable audio

## Planned Features
- Emotion detection from user text
- Emotion-to-voice mapping
- Audio file generation
- CLI demo
- Web demo with embedded player

## Current CLI Demo
Run the full text-to-audio flow:

```bash
python main.py "This is the best news ever! Thank you so much!"
```

The current CLI now:
- detected emotion
- sentiment score
- intensity
- mapped voice parameters
- saves a playable audio file in `outputs/`

Preview without generating audio:

```bash
python main.py --preview-only "Please confirm the meeting schedule."
```

## Next Step
Implement the FastAPI web demo.
