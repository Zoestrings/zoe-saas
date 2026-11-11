"""Audio transcription package for Zoe using Groq Whisper API."""

from zoe.transcription.whisper import transcribe_audio_file, transcribe_audio_file_async

__all__ = ["transcribe_audio_file", "transcribe_audio_file_async"]

