"""
Audio Extractor Module
Handles extraction of audio from video files and conversion to WAV format.
Uses pydub (FFmpeg wrapper) for audio processing.
"""

import os
import tempfile
from pydub import AudioSegment
from src.utils import logger, is_video_file, is_audio_file, check_ffmpeg


class AudioExtractor:
    """Extracts and prepares audio for transcription."""

    def __init__(self):
        self.temp_files = []

    def extract(self, input_path: str) -> str:
        """
        Extract audio from the input file and return path to a WAV file.
        
        For video files: extracts the audio track and saves as WAV.
        For audio files: converts to WAV if not already in WAV format.
        
        Args:
            input_path: Path to the input audio/video file
            
        Returns:
            Path to the extracted/converted WAV file
            
        Raises:
            RuntimeError: If FFmpeg is not available for video processing
        """
        ext = os.path.splitext(input_path)[1].lower()

        if is_video_file(input_path):
            return self._extract_from_video(input_path)
        elif ext == ".wav":
            logger.info("[green]✓[/green] Input is already WAV format")
            return input_path
        else:
            return self._convert_to_wav(input_path)

    def _extract_from_video(self, video_path: str) -> str:
        """Extract audio track from a video file."""
        if not check_ffmpeg():
            raise RuntimeError(
                "FFmpeg is required to extract audio from video files.\n"
                "Install FFmpeg:\n"
                "  Windows: choco install ffmpeg  OR  download from https://ffmpeg.org/download.html\n"
                "  macOS:   brew install ffmpeg\n"
                "  Linux:   sudo apt install ffmpeg"
            )

        logger.info(f"[cyan]⏳[/cyan] Extracting audio from video: {os.path.basename(video_path)}")

        try:
            audio = AudioSegment.from_file(video_path)
            wav_path = self._get_temp_path("extracted_audio.wav")
            audio = audio.set_channels(1).set_frame_rate(16000)  # Mono, 16kHz for Whisper
            audio.export(wav_path, format="wav")
            logger.info(f"[green]✓[/green] Audio extracted: {audio.duration_seconds:.1f}s duration")
            return wav_path
        except Exception as e:
            raise RuntimeError(f"Failed to extract audio from video: {e}")

    def _convert_to_wav(self, audio_path: str) -> str:
        """Convert audio file to WAV format."""
        if not check_ffmpeg():
            raise RuntimeError(
                "FFmpeg is required to convert this audio format to WAV.\n"
                "Install FFmpeg or provide a WAV file directly."
            )

        logger.info(f"[cyan]⏳[/cyan] Converting to WAV: {os.path.basename(audio_path)}")

        try:
            audio = AudioSegment.from_file(audio_path)
            wav_path = self._get_temp_path("converted_audio.wav")
            audio = audio.set_channels(1).set_frame_rate(16000)  # Mono, 16kHz for Whisper
            audio.export(wav_path, format="wav")
            logger.info(f"[green]✓[/green] Converted to WAV: {audio.duration_seconds:.1f}s duration")
            return wav_path
        except Exception as e:
            raise RuntimeError(f"Failed to convert audio: {e}")

    def _get_temp_path(self, filename: str) -> str:
        """Create a temporary file path and track it for cleanup."""
        temp_dir = tempfile.mkdtemp(prefix="avcensor_")
        temp_path = os.path.join(temp_dir, filename)
        self.temp_files.append(temp_path)
        return temp_path

    def cleanup(self):
        """Remove temporary files created during processing."""
        import shutil
        for temp_file in self.temp_files:
            try:
                temp_dir = os.path.dirname(temp_file)
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except OSError:
                pass
        self.temp_files.clear()
