import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app import main as api
from app.services import voice_service
from app.services.voice_service import (
    VoiceValidationError,
    browser_tts_contract,
    transcribe_audio,
    validate_audio_upload,
)


# Minimal valid WAV header used for unit tests.
WAV = b"RIFF\x24\x00\x00\x00WAVEfmt " + b"\x00" * 32


class VoiceValidationTests(unittest.TestCase):

    def test_voice_service_and_supported_wav(self):
        result = validate_audio_upload(
            "voice.wav",
            "audio/wav",
            WAV,
        )

        self.assertEqual(result, ".wav")

    def test_invalid_empty_and_oversized_audio_are_rejected(self):

        # Unsupported file type
        with self.assertRaises(VoiceValidationError) as unsupported:
            validate_audio_upload(
                "payload.exe",
                "application/octet-stream",
                b"MZ",
            )

        self.assertEqual(
            unsupported.exception.status_code,
            415,
        )

        # Empty file
        with self.assertRaises(VoiceValidationError):
            validate_audio_upload(
                "voice.wav",
                "audio/wav",
                b"",
            )

        # Oversized file
        with patch.object(
            voice_service,
            "MAX_AUDIO_BYTES",
            10,
        ):
            with self.assertRaises(VoiceValidationError) as oversized:
                validate_audio_upload(
                    "voice.wav",
                    "audio/wav",
                    WAV,
                )

        self.assertEqual(
            oversized.exception.status_code,
            413,
        )

    def test_browser_tts_contract_is_free_and_language_normalized(self):

        gujarati = browser_tts_contract("Gujarati")

        self.assertEqual(
            gujarati["locale"],
            "gu-IN",
        )

        unsupported = browser_tts_contract("not-supported")

        self.assertEqual(
            unsupported["language"],
            "en",
        )


class SttTests(unittest.IsolatedAsyncioTestCase):

    async def test_mocked_hindi_stt_and_provider_hint(self):

        mock_create = AsyncMock(
            return_value={
                "text": "Ahmedabad mein kal baarish hogi?",
                "language": "hi",
            }
        )

        with patch.object(
            voice_service.client.audio.transcriptions,
            "create",
            mock_create,
        ):
            result = await transcribe_audio(
                "voice.webm",
                "audio/webm",
                b"\x1a\x45\xdf\xa3data",
                "hi",
            )

        self.assertEqual(
            result["language"],
            "hi",
        )

        self.assertIn(
            "Ahmedabad",
            result["transcript"],
        )

        self.assertEqual(
            mock_create.await_args.kwargs["language"],
            "hi",
        )

    async def test_mocked_gujarati_stt_response(self):

        mock_create = AsyncMock(
            return_value={
                "text": "અમદાવાદમાં કાલે વરસાદ પડશે?",
                "language": "gu",
            }
        )

        with patch.object(
            voice_service.client.audio.transcriptions,
            "create",
            mock_create,
        ):
            result = await transcribe_audio(
                "voice.ogg",
                "audio/ogg",
                b"OggSdata",
            )

        self.assertEqual(
            result["language"],
            "gu",
        )

        self.assertTrue(
            result["transcript"]
        )

    async def test_empty_provider_response_is_safe_failure(self):

        with patch.object(
            voice_service.client.audio.transcriptions,
            "create",
            AsyncMock(
                return_value={
                    "text": "",
                }
            ),
        ):
            with self.assertRaises(RuntimeError):
                await transcribe_audio(
                    "voice.wav",
                    "audio/wav",
                    WAV,
                )


class VoiceChatTests(unittest.IsolatedAsyncioTestCase):

    async def test_voice_chat_reuses_common_chat_pipeline_and_session(self):

        transcript = {
            "transcript": "Ahmedabad mein kal baarish hogi?",
            "language": "hi",
        }

        chat_response = {
            "response": "कल बारिश की संभावना है।",
            "understanding": {
                "location": "Ahmedabad",
            },
        }

        with (
            patch.object(
                api,
                "_voice_transcription",
                AsyncMock(return_value=transcript),
            ),
            patch.object(
                api,
                "process_chat_message",
                AsyncMock(return_value=chat_response),
            ) as process,
        ):
            response = await api.voice_chat(
                object(),
                session_id="voice-session",
                language="hi",
            )

        # Verify that the existing chat pipeline received the
        # transcribed message rather than a separate voice pipeline.
        request = process.await_args.args[0]

        self.assertEqual(
            request.message,
            transcript["transcript"],
        )

        self.assertEqual(
            request.session_id,
            "voice-session",
        )

        self.assertEqual(
            request.language,
            "hi",
        )

        # Verify voice-chat response
        self.assertEqual(
            response["language"],
            "hi",
        )

        self.assertEqual(
            response["session_id"],
            "voice-session",
        )

        self.assertEqual(
            response["tts"]["provider"],
            "browser_speech_synthesis",
        )

    async def test_voice_transcribe_response_preserves_session(self):

        transcript = {
            "transcript": "What is the weather tomorrow?",
            "language": "en",
        }

        with patch.object(
            api,
            "_voice_transcription",
            AsyncMock(return_value=transcript),
        ):
            response = await api.voice_transcribe(
                object(),
                session_id="voice-session",
                language="en",
            )

        self.assertEqual(
            response["session_id"],
            "voice-session",
        )

        self.assertTrue(
            response["success"]
        )

        self.assertEqual(
            response["transcript"],
            "What is the weather tomorrow?",
        )

        self.assertEqual(
            response["language"],
            "en",
        )

    def test_transcribe_endpoint_accepts_multipart_upload(self):

        transcript = {
            "transcript": "Ahmedabad mein kal baarish hogi?",
            "language": "hi",
        }

        with patch.object(
            api,
            "transcribe_audio",
            AsyncMock(return_value=transcript),
        ) as transcribe:

            response = TestClient(api.app).post(
                "/voice/transcribe",
                files={
                    "audio": (
                        "voice.wav",
                        WAV,
                        "audio/wav",
                    )
                },
                data={
                    "session_id": "multipart-session",
                    "language": "hi",
                },
            )

        self.assertEqual(
            response.status_code,
            200,
        )

        self.assertEqual(
            response.json()["session_id"],
            "multipart-session",
        )

        self.assertEqual(
            response.json()["language"],
            "hi",
        )

        self.assertEqual(
            response.json()["transcript"],
            "Ahmedabad mein kal baarish hogi?",
        )

        transcribe.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()