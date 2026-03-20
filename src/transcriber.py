"""
Transcriber Module
Handles speech-to-text transcription using OpenAI Whisper.
Provides word-level timestamps for precise censorship.
"""

import os
import whisper
from src.utils import logger


class Transcriber:
    """Transcribes audio using Whisper with word-level timestamps."""

    def __init__(self, model_size: str = "base"):
        """
        Initialize the Whisper transcriber.
        
        Args:
            model_size: Whisper model to use (tiny, base, small, medium, large)
        """
        self.model_size = model_size
        self.model = None

    def load_model(self):
        """Load the Whisper model."""
        logger.info(f"[cyan]⏳[/cyan] Loading Whisper model: [bold]{self.model_size}[/bold]")
        
        try:
            self.model = whisper.load_model(self.model_size)
            logger.info(f"[green]✓[/green] Whisper model '{self.model_size}' loaded successfully")
        except Exception as e:
            raise RuntimeError(f"Failed to load Whisper model '{self.model_size}': {e}")

    def transcribe(self, audio_path: str) -> dict:
        """
        Transcribe audio file and return results with word-level timestamps.
        
        Args:
            audio_path: Path to the WAV audio file
            
        Returns:
            Dictionary containing:
            - 'text': Full transcript text
            - 'segments': List of segments with timestamps
            - 'words': List of words with precise timestamps
                [{word: str, start: float, end: float}, ...]
            - 'language': Detected language
        """
        if self.model is None:
            self.load_model()

        logger.info(f"[cyan]⏳[/cyan] Transcribing audio: {os.path.basename(audio_path)}")

        try:
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False,
            )
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}")

        # Extract word-level timestamps from segments
        words = []
        for segment in result.get("segments", []):
            for word_info in segment.get("words", []):
                words.append({
                    "word": word_info["word"].strip(),
                    "start": round(word_info["start"], 3),
                    "end": round(word_info["end"], 3),
                })

        transcript_data = {
            "text": result.get("text", "").strip(),
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", []),
            "words": words,
            "word_count": len(words),
        }

        logger.info(
            f"[green]✓[/green] Transcription complete: "
            f"{len(words)} words detected, language: {transcript_data['language']}"
        )

        return transcript_data
