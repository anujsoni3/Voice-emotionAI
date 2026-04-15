# The Empathy Engine: Phase-Wise Execution Plan

## Goal
Build a polished Python project that takes text input, detects emotion, maps that emotion to voice settings, and generates a playable audio file with noticeably different delivery styles.

This plan is written to maximize:
- assignment completeness
- demo quality
- judge confidence
- clean GitHub delivery

## Working Style For This Repo
- For every task in this session, we will first define the plan, then implement.
- We will build the project in small reviewable phases.
- We will keep the MVP working at every phase so the repo always stays demo-ready.

## Recommended Technical Direction
- Language: Python 3.11+
- Emotion detection: `vaderSentiment`
- TTS engine: `pyttsx3`
- API/UI: `FastAPI` with a simple HTML demo page
- Audio output: `.wav` file
- Optional polish: intensity scaling and SSML-inspired text preprocessing where supported

## Why This Stack
- `vaderSentiment` is lightweight, fast, and reliable for positive / negative / neutral classification.
- `pyttsx3` works well for local prototyping and supports direct control over speech properties.
- `FastAPI` gives both a clean API story and an easy path to a web demo.
- This combination is practical for an assignment because it reduces setup risk and keeps the demo self-contained.

## Success Criteria
The final project must clearly demonstrate:
1. Text input is accepted from CLI and/or web form.
2. Emotion is classified into at least 3 categories.
3. At least 2 voice parameters are changed programmatically.
4. The emotion-to-voice mapping is explicit and easy to explain.
5. A playable audio file is generated.
6. The repository is easy to run from README instructions.

## Phase 1: Repository Foundation
### Objective
Create a clean, professional project structure before feature work starts.

### Tasks
- Initialize git repository.
- Add `.gitignore`.
- Create base folders:
  - `app/`
  - `app/services/`
  - `app/static/`
  - `app/templates/`
  - `outputs/`
  - `tests/`
- Add starter files:
  - `README.md`
  - `requirements.txt`
  - `main.py`

### Deliverable
A runnable repo skeleton ready for incremental implementation.

## Phase 2: MVP Emotion Detection
### Objective
Build a simple and dependable emotion classifier first.

### Tasks
- Create `emotion_service.py`.
- Use VADER compound score to classify:
  - `happy`
  - `frustrated`
  - `neutral`
- Add keyword boosters for better assignment-specific behavior:
  - exclamation-heavy text
  - apology / complaint language
  - praise / gratitude language
- Return:
  - label
  - sentiment score
  - intensity level

### Deliverable
A tested service that turns raw text into an emotion object.

## Phase 3: Voice Mapping Engine
### Objective
Translate emotion into expressive speech settings.

### Tasks
- Create `voice_mapper.py`.
- Define a mapping table for:
  - `rate`
  - `volume`
- If feasible on the local engine, add:
  - pitch adjustment
- Add intensity scaling:
  - mild
  - moderate
  - strong

### Example Mapping
- `happy`: slightly faster, slightly louder
- `frustrated`: slower, firmer volume, controlled delivery
- `neutral`: balanced defaults

### Deliverable
A deterministic mapping layer that is easy to demo and explain in README.

## Phase 4: Audio Generation Pipeline
### Objective
Convert analyzed text into a saved audio file.

### Tasks
- Create `tts_service.py`.
- Accept text plus mapped voice settings.
- Generate timestamped output files in `outputs/`.
- Return metadata:
  - detected emotion
  - parameter values
  - output filename

### Deliverable
The end-to-end MVP requirement is satisfied locally.

## Phase 5: CLI Demo
### Objective
Ensure there is always a simple fallback demo path.

### Tasks
- Add CLI entry flow in `main.py`.
- Ask for text input.
- Print detected emotion and chosen voice settings.
- Save and announce the audio file path.

### Deliverable
Judges can test the full assignment from terminal even without web UI.

## Phase 6: Web Demo
### Objective
Create a cleaner presentation layer to improve selection chances.

### Tasks
- Add FastAPI app with:
  - text area
  - submit button
  - result summary
  - embedded audio player
- Show:
  - detected emotion
  - intensity
  - voice parameters used

### Deliverable
A browser-based demo that feels product-like, not just script-like.

## Phase 7: Quality, Testing, and Edge Cases
### Objective
Make the project stable and presentation-ready.

### Tasks
- Add unit tests for emotion classification.
- Add tests for voice mapping outputs.
- Handle empty input and very short text.
- Sanitize filenames.
- Make failure messages human-friendly.

### Deliverable
The app behaves predictably and looks thoughtfully engineered.

## Phase 8: Documentation and Submission Polish
### Objective
Turn a working project into a convincing submission.

### Tasks
- Write a strong `README.md` covering:
  - project overview
  - features
  - setup
  - how to run CLI
  - how to run web app
  - design choices
  - emotion-to-voice logic
- Add screenshots if possible.
- Add sample demo text cases.

### Deliverable
A repository that reviewers can understand in minutes.

## Phase 9: GitHub Delivery
### Objective
Push a clean and credible final repository.

### Tasks
- Verify file structure.
- Run final checks.
- Review git diff.
- Create clear commits.
- Push to the target GitHub repository.

### Commit Strategy
- `chore: initialize empathy engine project structure`
- `feat: add emotion detection and voice mapping`
- `feat: add audio generation pipeline and cli demo`
- `feat: add web interface for empathy engine`
- `docs: add setup guide and design notes`

## Judging Strategy
To improve selection chances, we should optimize for these visible strengths:
- clear compliance with all must-have requirements
- noticeable emotional difference in audio output
- simple but polished UI
- clean documentation
- reliable local setup
- thoughtful explanation of design decisions

## Key Risks And Mitigation
### Risk: TTS engine supports limited parameters
Mitigation:
Use `rate` and `volume` as guaranteed parameters for MVP, then attempt pitch only if stable.

### Risk: Emotion detection feels too generic
Mitigation:
Combine VADER score with lightweight rule-based keyword handling and intensity scaling.

### Risk: Demo fails on another machine
Mitigation:
Keep dependencies small, document setup clearly, and maintain CLI as fallback.

## Definition Of Done
The project is ready for submission when:
- CLI flow works
- web demo works
- audio file is generated
- 3+ emotions are classified correctly enough for demo cases
- 2+ voice parameters change by emotion
- README is complete
- repository is pushed cleanly to GitHub

## Immediate Next Execution Order
1. Initialize the repository and add project scaffold.
2. Build the emotion detection service.
3. Build the voice mapping layer.
4. Generate audio output from text.
5. Add the CLI flow.
6. Add the web interface.
7. Test, document, and push.
