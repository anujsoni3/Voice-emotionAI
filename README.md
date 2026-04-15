# The Empathy Engine

The Empathy Engine is a Python-based voice AI demo that analyzes the emotional tone of text and generates speech with adjusted vocal delivery. Instead of reading every line in a flat robotic voice, it detects whether a message feels happy, frustrated, or neutral, then changes the speech rate, pitch, and volume profile to better match that emotional context.

This project was built for the assignment "The Empathy Engine: Giving AI a Human Voice" and is designed to satisfy the required features while also adding bonus polish through intensity scaling, a web interface, and optional premium voice generation through ElevenLabs.

## Assignment Coverage
This project satisfies the core requirements:
- `Text Input`: supported through both CLI and FastAPI web form
- `Emotion Detection`: classifies text into `happy`, `frustrated`, and `neutral`
- `Vocal Parameter Modulation`: modulates `rate`, `volume`, and `pitch`
- `Emotion-to-Voice Mapping`: implemented with explicit mapping logic in the service layer
- `Audio Output`: generates playable `.mp3` or `.wav` files depending on provider

Bonus features included:
- `Intensity Scaling`: mild, moderate, and strong intensity levels affect voice modulation
- `Web Interface`: browser UI with text area, result summary, and embedded audio playback
- `Provider Flexibility`: supports `edge-tts`, `pyttsx3`, and optional `ElevenLabs`

## Project Structure
```text
app/
  services/
    emotion_service.py
    tts_service.py
    voice_mapper.py
  templates/
    index.html
  models.py
  settings.py
  web.py
main.py
requirements.txt
PLAN.md
```

## How It Works
### 1. Emotion Detection
The `EmotionService` uses VADER sentiment analysis plus simple rule-based cues to classify input text.

It looks at:
- sentiment polarity score
- positive keywords like `thanks`, `great`, `best`
- negative keywords like `issue`, `delay`, `awful`
- emphasis signals like exclamation marks and all-caps words

It returns:
- detected emotion
- sentiment score
- intensity level
- confidence score
- detected cues

### 2. Emotion-to-Voice Mapping
The `VoiceMapper` converts emotion into speech parameters.

Base mapping:
- `happy`: faster, slightly louder, higher pitch
- `neutral`: balanced rate and volume
- `frustrated`: slower, grounded delivery, lower pitch

Intensity scaling:
- `mild`: minimal modulation
- `moderate`: noticeable modulation
- `strong`: more dramatic modulation

### 3. Audio Generation
The `TTSService` generates the final audio file.

Supported providers:
- `auto`: prefers ElevenLabs if API key exists, otherwise falls back
- `elevenlabs`: best human-like voice quality
- `edge`: strong free prototype option with pitch/rate/volume support
- `pyttsx3`: offline fallback

## Setup
### 1. Clone the repository
```bash
git clone https://github.com/anujsoni3/Voice-emotionAI.git
cd Voice-emotionAI
```

### 2. Create and activate a virtual environment
```bash
python -m venv .venv
.venv\Scripts\activate
```

### 3. Install dependencies
```bash
python -m pip install -r requirements.txt
```

### 4. Configure environment variables
Copy `.env.example` to `.env` and fill values if you want ElevenLabs:

```bash
copy .env.example .env
```

Example `.env`:
```env
EMPATHY_TTS_PROVIDER=auto
ELEVENLABS_API_KEY=your_api_key_here
ELEVENLABS_VOICE_ID=EXAVITQu4vr4xnSDxMaL
ELEVENLABS_MODEL_ID=eleven_multilingual_v2
```

If no ElevenLabs key is provided, the app can still use `edge-tts`.

## Running The Project
### CLI mode
Generate audio from a text string:

```bash
python main.py "This is the best news ever! Thank you so much!"
```

Preview emotion analysis without generating audio:

```bash
python main.py --preview-only "Please confirm the meeting schedule for tomorrow."
```

Force a specific TTS provider:

```bash
python main.py --provider edge "Thanks for your patience."
python main.py --provider elevenlabs "We are thrilled to share this update with you!"
```

### Web mode
Run the FastAPI web interface:

```bash
python main.py --web
```

Then open:

```text
http://127.0.0.1:8000
```

## Deployment Notes
For assignment-level deployment, Render is the best fit because this is a Python/FastAPI project.

Suggested Render start command:

```bash
uvicorn app.web:app --host 0.0.0.0 --port $PORT
```

If you deploy with ElevenLabs, add the same environment variables from `.env` into your hosting provider’s dashboard instead of uploading the `.env` file.

## Key Design Choices
### Why VADER instead of TextBlob?
VADER performs well for short conversational text and customer-style messages. It also pairs nicely with lightweight rule-based cues for a fast prototype.

### Why intensity scaling?
The assignment specifically benefits from modulation that changes with emotional strength. This makes `This is good` sound different from `This is the best news ever!`

### Why support multiple TTS providers?
- `ElevenLabs`: best voice quality for demos
- `edge-tts`: practical and free for prototyping
- `pyttsx3`: offline fallback

This makes the project more robust across local testing, hackathon demos, and deployment.

## Testing
Run the test suite:

```bash
python -m unittest discover -s tests -v
```

## Current Status
Completed:
- project scaffold
- emotion detection
- voice mapping
- audio generation
- CLI demo
- FastAPI web demo scaffold
- optional ElevenLabs support

Final polish still recommended:
- add more web route tests
- add screenshots to the README
- deploy to Render

## Repository
GitHub URL:

```text
https://github.com/anujsoni3/Voice-emotionAI.git
```
