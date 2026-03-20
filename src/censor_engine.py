"""
Censor Engine Module
Applies censorship (bleep or mute) to flagged audio segments.
Handles both audio-only and video file output.
"""

import os
import subprocess
import tempfile
import math
import numpy as np
from typing import List, Dict
from pydub import AudioSegment
from pydub.generators import Sine
from src.utils import logger, is_video_file, check_ffmpeg


class CensorEngine:
    """Applies censorship to audio/video files based on flagged segments."""

    def __init__(self, mode: str = "bleep", bleep_frequency: int = 1000):
        """
        Initialize the censor engine.
        
        Args:
            mode: Censorship mode - 'bleep' (tone overlay) or 'mute' (silence)
            bleep_frequency: Frequency of the bleep tone in Hz (default: 1000)
        """
        self.mode = mode
        self.bleep_frequency = bleep_frequency

    def censor(
        self,
        input_path: str,
        wav_path: str,
        flagged_segments: List[Dict],
        output_path: str,
    ) -> str:
        """
        Apply censorship to the audio and produce the output file.
        
        Args:
            input_path: Original input file path
            wav_path: Path to the extracted WAV audio
            flagged_segments: List of flagged content with timestamps
            output_path: Path for the output file
            
        Returns:
            Path to the censored output file
        """
        if not flagged_segments:
            logger.info("[green]✓[/green] No content to censor — file is clean!")
            # Just copy the original
            import shutil
            shutil.copy2(input_path, output_path)
            return output_path

        logger.info(
            f"[cyan]⏳[/cyan] Applying censorship ({self.mode} mode) "
            f"to {len(flagged_segments)} segments..."
        )

        # Load the audio
        audio = AudioSegment.from_wav(wav_path)

        # Apply censorship to each flagged segment
        censored_audio = self._apply_censorship(audio, flagged_segments)

        # Output the result
        if is_video_file(input_path):
            result_path = self._output_video(input_path, censored_audio, output_path)
        else:
            result_path = self._output_audio(censored_audio, output_path)

        logger.info(f"[green]✓[/green] Censored file saved: [bold]{result_path}[/bold]")
        return result_path

    def _apply_censorship(
        self, audio: AudioSegment, flagged_segments: List[Dict]
    ) -> AudioSegment:
        """
        Apply bleep or mute to flagged segments in the audio.
        
        Merges overlapping segments and adds a small padding around each segment.
        """
        # Merge overlapping/adjacent segments
        merged = self._merge_segments(flagged_segments)

        # Work with the audio
        result = audio

        # Process segments in reverse order to maintain correct positions
        for segment in reversed(merged):
            start_ms = max(0, int(segment["start"] * 1000) - 50)  # 50ms padding before
            end_ms = min(len(audio), int(segment["end"] * 1000) + 50)  # 50ms padding after
            duration_ms = end_ms - start_ms

            if duration_ms <= 0:
                continue

            if self.mode == "bleep":
                # Generate a bleep tone
                bleep = Sine(self.bleep_frequency).to_audio_segment(
                    duration=duration_ms
                )
                # Match the volume of the original audio (slightly quieter)
                original_segment = audio[start_ms:end_ms]
                if original_segment.dBFS != float('-inf'):
                    bleep = bleep - max(0, bleep.dBFS - original_segment.dBFS) - 5
                else:
                    bleep = bleep - 20

                # Replace the segment
                result = result[:start_ms] + bleep + result[end_ms:]

            elif self.mode == "mute":
                # Replace with silence
                silence = AudioSegment.silent(duration=duration_ms)
                result = result[:start_ms] + silence + result[end_ms:]

        return result

    def _merge_segments(self, segments: List[Dict]) -> List[Dict]:
        """Merge overlapping or adjacent flagged segments."""
        if not segments:
            return []

        # Sort by start time
        sorted_segments = sorted(segments, key=lambda x: x["start"])

        merged = [{"start": sorted_segments[0]["start"], "end": sorted_segments[0]["end"]}]

        for segment in sorted_segments[1:]:
            last = merged[-1]
            # Merge if overlapping or within 100ms of each other
            if segment["start"] <= last["end"] + 0.1:
                last["end"] = max(last["end"], segment["end"])
            else:
                merged.append({"start": segment["start"], "end": segment["end"]})

        return merged

    def _output_audio(self, audio: AudioSegment, output_path: str) -> str:
        """Export censored audio to file."""
        ext = os.path.splitext(output_path)[1].lower()

        format_map = {
            ".wav": "wav",
            ".mp3": "mp3",
            ".flac": "flac",
            ".ogg": "ogg",
            ".m4a": "mp4",
        }

        output_format = format_map.get(ext, "wav")

        try:
            audio.export(output_path, format=output_format)
        except Exception:
            # Fallback to WAV if format not supported
            output_path = os.path.splitext(output_path)[0] + ".wav"
            audio.export(output_path, format="wav")

        return output_path

    def _output_video(
        self, original_video: str, censored_audio: AudioSegment, output_path: str
    ) -> str:
        """Replace audio in video with censored audio using FFmpeg."""
        if not check_ffmpeg():
            # Fallback: just save the audio
            audio_output = os.path.splitext(output_path)[0] + "_censored_audio.wav"
            censored_audio.export(audio_output, format="wav")
            logger.warning(
                f"[yellow]⚠[/yellow] FFmpeg not available. "
                f"Censored audio saved separately: {audio_output}"
            )
            return audio_output

        # Save censored audio to temp file
        temp_dir = tempfile.mkdtemp(prefix="avcensor_")
        temp_audio = os.path.join(temp_dir, "censored_audio.wav")
        censored_audio.export(temp_audio, format="wav")

        try:
            # Use FFmpeg to replace audio in video
            cmd = [
                "ffmpeg", "-y",
                "-i", original_video,
                "-i", temp_audio,
                "-c:v", "copy",       # Copy video stream (no re-encoding)
                "-map", "0:v:0",       # Use video from first input
                "-map", "1:a:0",       # Use audio from second input (censored)
                "-shortest",
                output_path,
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )

            if result.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {result.stderr}")

            return output_path

        except Exception as e:
            # Fallback: save audio separately
            audio_output = os.path.splitext(output_path)[0] + "_censored_audio.wav"
            censored_audio.export(audio_output, format="wav")
            logger.warning(
                f"[yellow]⚠[/yellow] Video processing failed: {e}. "
                f"Censored audio saved: {audio_output}"
            )
            return audio_output

        finally:
            # Cleanup temp
            import shutil
            shutil.rmtree(temp_dir, ignore_errors=True)
