from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.emotion_service import EmotionService
from app.services.tts_service import TTSService
from app.services.voice_mapper import VoiceMapper


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"

app = FastAPI(title="The Empathy Engine", version="0.1.0")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

emotion_service = EmotionService()
voice_mapper = VoiceMapper()
tts_service = TTSService(output_dir=OUTPUTS_DIR)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "text": "",
            "analysis": None,
            "voice_profile": None,
            "synthesis": None,
            "error": None,
        },
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(request: Request, text: str = Form(...)) -> HTMLResponse:
    cleaned_text = text.strip()
    if not cleaned_text:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "text": text,
                "analysis": None,
                "voice_profile": None,
                "synthesis": None,
                "error": "Please enter some text before generating audio.",
            },
            status_code=400,
        )

    try:
        analysis = emotion_service.analyze(cleaned_text)
        voice_profile = voice_mapper.map_emotion(analysis)
        synthesis = tts_service.synthesize_to_file(cleaned_text, voice_profile)
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "text": cleaned_text,
                "analysis": None,
                "voice_profile": None,
                "synthesis": None,
                "error": str(exc),
            },
            status_code=500,
        )

    audio_url = request.url_for("outputs", path=synthesis.file_name)

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "text": cleaned_text,
            "analysis": analysis,
            "voice_profile": voice_profile,
            "synthesis": synthesis,
            "audio_url": audio_url,
            "error": None,
        },
    )
