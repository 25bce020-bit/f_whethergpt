"""Safe, lightweight voice input helpers backed by the existing Groq client."""

from __future__ import annotations

import os
from collections.abc import Mapping

from app.services.language_service import normalize_language
from app.services.llm_service import client


VOICE_MAX_AUDIO_SIZE_MB = int(os.getenv("VOICE_MAX_AUDIO_SIZE_MB", "10"))
MAX_AUDIO_BYTES = VOICE_MAX_AUDIO_SIZE_MB * 1024 * 1024

SUPPORTED_AUDIO_FORMATS = {
    ".wav": {"audio/wav", "audio/x-wav"},
    ".mp3": {"audio/mpeg", "audio/mp3"},
    ".mpeg": {"audio/mpeg"}, ".webm": {"audio/webm"},
    ".ogg": {"audio/ogg"}, ".mp4": {"audio/mp4"},
    ".m4a": {"audio/mp4", "audio/x-m4a"},
}

# Groq Whisper supports these as explicit hints. Odia remains usable through
# auto-detection and the existing text-language layer, but is not sent as an
# unsupported provider hint.
STT_HINT_LANGUAGES = {"en", "hi", "gu", "mr", "bn", "ta", "te", "kn", "ml", "pa"}

# TTS deliberately remains client-side. These BCP-47 hints are for browser
# SpeechSynthesis and require no paid service or server-side audio generation.
BROWSER_TTS_LOCALES = {
    "en": "en-IN", "hi": "hi-IN", "gu": "gu-IN", "mr": "mr-IN",
    "bn": "bn-IN", "ta": "ta-IN", "te": "te-IN", "kn": "kn-IN",
    "ml": "ml-IN", "pa": "pa-IN", "or": "or-IN",
}


class VoiceValidationError(ValueError):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _extension(filename: str | None) -> str:
    safe_name = (filename or "").rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
    return "." + safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""


def _looks_like_audio(data: bytes, extension: str) -> bool:
    if extension == ".wav":
        return data.startswith(b"RIFF") and data[8:12] == b"WAVE"
    if extension in {".mp3", ".mpeg"}:
        return data.startswith(b"ID3") or (len(data) > 1 and data[0] == 0xFF and data[1] & 0xE0 == 0xE0)
    if extension == ".ogg":
        return data.startswith(b"OggS")
    if extension == ".webm":
        return data.startswith(b"\x1aE\xdf\xa3")
    if extension in {".mp4", ".m4a"}:
        return len(data) >= 12 and data[4:8] == b"ftyp"
    return False


def validate_audio_upload(filename: str | None, content_type: str | None, data: bytes) -> str:
    """Validate metadata and a small format signature before an STT upload."""
    extension = _extension(filename)
    if extension not in SUPPORTED_AUDIO_FORMATS:
        raise VoiceValidationError("Unsupported audio format. Use WAV, MP3, WebM, OGG, MP4, or M4A.", 415)
    if content_type and content_type.lower() not in SUPPORTED_AUDIO_FORMATS[extension]:
        raise VoiceValidationError("Audio content type does not match the uploaded format.", 415)
    if not data:
        raise VoiceValidationError("Audio upload is empty.")
    if len(data) > MAX_AUDIO_BYTES:
        raise VoiceValidationError(f"Audio upload exceeds the {VOICE_MAX_AUDIO_SIZE_MB} MB limit.", 413)
    if not _looks_like_audio(data, extension):
        raise VoiceValidationError("Uploaded data is not a valid audio file for its declared format.", 415)
    return extension


def _read_transcription_field(response: object, field: str) -> str | None:
    value = response.get(field) if isinstance(response, Mapping) else getattr(response, field, None)
    return value if isinstance(value, str) and value.strip() else None


async def transcribe_audio(filename: str | None, content_type: str | None, data: bytes, language: str | None = None) -> dict:
    """Transcribe in memory; untrusted recordings are never persisted to disk."""
    validate_audio_upload(filename, content_type, data)
    requested_language = normalize_language(language)
    kwargs = {
        "model": "whisper-large-v3-turbo",
        "file": ((filename or "recording.webm").rsplit("/", 1)[-1].rsplit("\\", 1)[-1], data),
        "response_format": "verbose_json",
    }
    if requested_language in STT_HINT_LANGUAGES:
        kwargs["language"] = requested_language
    try:
        result = await client.audio.transcriptions.create(**kwargs)
    except Exception as exc:
        raise RuntimeError("Speech transcription is temporarily unavailable.") from exc
    transcript = _read_transcription_field(result, "text")
    if not transcript:
        raise RuntimeError("Speech transcription returned no text.")
    detected = normalize_language(_read_transcription_field(result, "language"))
    return {"transcript": transcript.strip(), "language": requested_language or detected or "en"}


def browser_tts_contract(language: str | None) -> dict:
    """Return a browser SpeechSynthesis contract; this generates no server audio."""
    code = normalize_language(language) or "en"
    return {"provider": "browser_speech_synthesis", "language": code, "locale": BROWSER_TTS_LOCALES[code]}
