"""
Utility functions for the AI Audio/Video Censor tool.
Provides logging setup, file validation, and helper functions.
"""

import os
import sys
import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.text import Text

# Global console instance
console = Console()


def setup_logger(name: str = "avcensor", level: int = logging.INFO) -> logging.Logger:
    """Set up a Rich-formatted logger."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = RichHandler(
            console=console,
            show_path=False,
            markup=True,
            rich_tracebacks=True,
        )
        handler.setLevel(level)
        formatter = logging.Formatter("%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# Default logger
logger = setup_logger()


def validate_input_file(filepath: str) -> str:
    """
    Validate that the input file exists and is a supported format.
    Returns the absolute path to the file.
    
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If format is not supported
    """
    # Add parent directory to path for config imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.config import ALL_SUPPORTED_FORMATS

    filepath = os.path.abspath(filepath)

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")

    ext = os.path.splitext(filepath)[1].lower()
    if ext not in ALL_SUPPORTED_FORMATS:
        raise ValueError(
            f"Unsupported format '{ext}'. Supported formats: {', '.join(ALL_SUPPORTED_FORMATS)}"
        )

    return filepath


def get_output_path(input_path: str, output_path: str = None, suffix: str = "_censored") -> str:
    """
    Generate the output file path.
    If output_path is not specified, creates one based on the input filename.
    """
    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        return os.path.abspath(output_path)

    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.config import OUTPUT_DIR

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    base, ext = os.path.splitext(os.path.basename(input_path))
    output_file = os.path.join(OUTPUT_DIR, f"{base}{suffix}{ext}")
    return output_file


def is_video_file(filepath: str) -> bool:
    """Check if a file is a video format."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.config import SUPPORTED_VIDEO_FORMATS

    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_VIDEO_FORMATS


def is_audio_file(filepath: str) -> bool:
    """Check if a file is an audio format."""
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.config import SUPPORTED_AUDIO_FORMATS

    ext = os.path.splitext(filepath)[1].lower()
    return ext in SUPPORTED_AUDIO_FORMATS


def format_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def print_banner():
    """Display the application banner."""
    banner_text = Text()
    banner_text.append("🔇 AI Audio/Video Censor", style="bold cyan")
    banner_text.append("\n")
    banner_text.append("Automated Profanity & Content Censorship Tool", style="dim")
    banner_text.append("\n")
    banner_text.append("Powered by Whisper ASR | Built for OpenVINO GSoC", style="dim italic")

    console.print(
        Panel(
            banner_text,
            border_style="cyan",
            padding=(1, 2),
        )
    )


def check_ffmpeg() -> bool:
    """Check if FFmpeg is available on the system."""
    import shutil
    return shutil.which("ffmpeg") is not None
