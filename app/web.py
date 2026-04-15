from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.services.emotion_service import EmotionService
from app.services.tts_service import TTSService
from app.services.voice_mapper import VoiceMapper
from app.models import EmotionAnalysis, VoiceProfile


BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUTS_DIR = BASE_DIR / "outputs"
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
PERSONA_LABELS = {
    "support": "Support Agent",
    "sales": "Sales Rep",
    "executive": "Executive Briefing",
}

app = FastAPI(title="The Empathy Engine", version="0.1.0")
app.mount("/outputs", StaticFiles(directory=str(OUTPUTS_DIR)), name="outputs")
app.mount("/static", StaticFiles(directory=str(Path(__file__).resolve().parent / "static")), name="static")

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))

emotion_service = EmotionService()
voice_mapper = VoiceMapper()
tts_service = TTSService(output_dir=OUTPUTS_DIR)


def _flatten_neutral_baseline(profile: VoiceProfile) -> VoiceProfile:
    """Make neutral baseline intentionally flatter for clearer A/B comparison."""
    return VoiceProfile(
        emotion=profile.emotion,
        intensity=profile.intensity,
        rate=max(145, min(180, profile.rate - 18)),
        volume=round(max(0.72, min(0.88, profile.volume - 0.08)), 2),
        pitch_delta=0,
        style_note=f"{profile.style_note} Neutral baseline: flattened cadence and affect for A/B clarity.",
    )


def _resolve_tts_service() -> TTSService:
    """Return a request-scoped TTS service so .env changes are reflected without stale settings."""
    global tts_service
    if isinstance(tts_service, TTSService):
        return TTSService(output_dir=OUTPUTS_DIR)
    return tts_service


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "text": "",
            "persona": "support",
            "persona_label": PERSONA_LABELS["support"],
            "intensity_mode": "auto",
            "compare_mode": True,
            "sentence_mode": True,
            "analysis": None,
            "voice_profile": None,
            "synthesis": None,
            "neutral_synthesis": None,
            "neutral_profile": None,
            "sentence_results": [],
            "report_url": None,
            "error": None,
        },
    )


@app.post("/generate", response_class=HTMLResponse)
async def generate(
    request: Request,
    text: str = Form(...),
    intensity_mode: str = Form("auto"),
    persona: str = Form("support"),
    compare_mode: bool = Form(False),
    sentence_mode: bool = Form(False),
) -> HTMLResponse:
    current_tts_service = _resolve_tts_service()
    cleaned_text = text.strip()
    selected_intensity = intensity_mode if intensity_mode in {"auto", "mild", "moderate", "strong"} else "auto"
    selected_persona = persona if persona in {"support", "sales", "executive"} else "support"
    selected_persona_label = PERSONA_LABELS[selected_persona]
    intensity_override = None if selected_intensity == "auto" else selected_intensity

    if not cleaned_text:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "text": text,
                "persona": selected_persona,
                "persona_label": selected_persona_label,
                "intensity_mode": selected_intensity,
                "compare_mode": compare_mode,
                "sentence_mode": sentence_mode,
                "analysis": None,
                "voice_profile": None,
                "synthesis": None,
                "neutral_synthesis": None,
                "neutral_profile": None,
                "sentence_results": [],
                "report_url": None,
                "error": "Please enter some text before generating audio.",
            },
            status_code=400,
        )

    try:
        analysis = emotion_service.analyze(cleaned_text, intensity_override=intensity_override)
        voice_profile = voice_mapper.map_emotion(analysis, persona=selected_persona)
        synthesis = current_tts_service.synthesize_to_file(cleaned_text, voice_profile, persona=selected_persona)

        neutral_analysis = EmotionAnalysis(
            text=cleaned_text,
            emotion="neutral",
            sentiment_score=0.0,
            intensity="mild",
            confidence=1.0,
            cues=["baseline_neutral"],
        )
        neutral_profile = voice_mapper.map_emotion(neutral_analysis, persona=selected_persona)
        neutral_profile = _flatten_neutral_baseline(neutral_profile)
        neutral_synthesis = (
            current_tts_service.synthesize_to_file(cleaned_text, neutral_profile, persona=selected_persona)
            if compare_mode
            else None
        )

        sentence_results: list[dict[str, object]] = []
        if sentence_mode:
            for idx, sentence_text in enumerate(emotion_service.split_sentences(cleaned_text), start=1):
                sentence_analysis = emotion_service.analyze(sentence_text, intensity_override=intensity_override)
                sentence_profile = voice_mapper.map_emotion(sentence_analysis, persona=selected_persona)
                sentence_synthesis = current_tts_service.synthesize_to_file(
                    sentence_text,
                    sentence_profile,
                    persona=selected_persona,
                )
                sentence_results.append(
                    {
                        "index": idx,
                        "text": sentence_text,
                        "analysis": sentence_analysis,
                        "voice_profile": sentence_profile,
                        "synthesis": sentence_synthesis,
                        "audio_url": request.url_for("outputs", path=sentence_synthesis.file_name),
                    }
                )

        report_payload = {
            "input_text": cleaned_text,
            "options": {
                "intensity_mode": selected_intensity,
                "persona": selected_persona,
                "persona_label": selected_persona_label,
                "compare_mode": compare_mode,
                "sentence_mode": sentence_mode,
            },
            "overall_analysis": asdict(analysis),
            "empathetic_voice_profile": asdict(voice_profile),
            "empathetic_audio": {
                "file_name": synthesis.file_name,
                "provider": synthesis.provider,
                "pitch_applied": synthesis.pitch_applied,
            },
            "neutral_audio": (
                {
                    "file_name": neutral_synthesis.file_name,
                    "provider": neutral_synthesis.provider,
                    "pitch_applied": neutral_synthesis.pitch_applied,
                    "voice_profile": asdict(neutral_profile),
                }
                if neutral_synthesis
                else None
            ),
            "sentence_segments": [
                {
                    "index": item["index"],
                    "text": item["text"],
                    "analysis": asdict(item["analysis"]),
                    "voice_profile": asdict(item["voice_profile"]),
                    "audio": {
                        "file_name": item["synthesis"].file_name,
                        "provider": item["synthesis"].provider,
                        "pitch_applied": item["synthesis"].pitch_applied,
                    },
                }
                for item in sentence_results
            ],
        }
        report_file_name = f"{Path(synthesis.file_name).stem}_report.json"
        report_path = OUTPUTS_DIR / report_file_name
        report_path.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")
    except Exception as exc:
        return templates.TemplateResponse(
            request,
            "index.html",
            {
                "text": cleaned_text,
                "persona": selected_persona,
                "persona_label": selected_persona_label,
                "intensity_mode": selected_intensity,
                "compare_mode": compare_mode,
                "sentence_mode": sentence_mode,
                "analysis": None,
                "voice_profile": None,
                "synthesis": None,
                "neutral_synthesis": None,
                "neutral_profile": None,
                "sentence_results": [],
                "report_url": None,
                "error": str(exc),
            },
            status_code=500,
        )

    audio_url = request.url_for("outputs", path=synthesis.file_name)
    neutral_audio_url = request.url_for("outputs", path=neutral_synthesis.file_name) if neutral_synthesis else None
    report_url = request.url_for("outputs", path=report_file_name)
    requested_provider = current_tts_service.provider or "auto"
    fallback_note = None
    if requested_provider == "auto":
        auto_primary = "elevenlabs" if current_tts_service.settings.elevenlabs_api_key else "edge"
        if synthesis.provider != auto_primary:
            fallback_note = (
                f"{auto_primary} was unavailable, so the app automatically generated audio with {synthesis.provider}."
            )
    elif synthesis.provider != requested_provider:
        fallback_note = (
            f"{requested_provider} was unavailable, so the app automatically generated audio with {synthesis.provider}."
        )

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "text": cleaned_text,
            "persona": selected_persona,
            "persona_label": selected_persona_label,
            "intensity_mode": selected_intensity,
            "compare_mode": compare_mode,
            "sentence_mode": sentence_mode,
            "analysis": analysis,
            "voice_profile": voice_profile,
            "synthesis": synthesis,
            "audio_url": audio_url,
            "neutral_profile": neutral_profile,
            "neutral_synthesis": neutral_synthesis,
            "neutral_audio_url": neutral_audio_url,
            "sentence_results": sentence_results,
            "report_url": report_url,
            "fallback_note": fallback_note,
            "error": None,
        },
    )
