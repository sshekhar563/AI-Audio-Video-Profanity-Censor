"""
Configuration settings for the AI Audio/Video Censor tool.
"""

import os

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_DIR = os.path.join(PROJECT_ROOT, "config")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
SAMPLES_DIR = os.path.join(PROJECT_ROOT, "samples")

# Default profanity word list path
DEFAULT_WORDLIST = os.path.join(CONFIG_DIR, "profanity_words.txt")

# Whisper settings
DEFAULT_WHISPER_MODEL = "base"  # Options: tiny, base, small, medium, large
SUPPORTED_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]

# Audio settings
SUPPORTED_AUDIO_FORMATS = [".wav", ".mp3", ".flac", ".aac", ".ogg", ".wma", ".m4a"]
SUPPORTED_VIDEO_FORMATS = [".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv"]
ALL_SUPPORTED_FORMATS = SUPPORTED_AUDIO_FORMATS + SUPPORTED_VIDEO_FORMATS

# Censor settings
BLEEP_FREQUENCY = 1000  # Hz - frequency of the bleep tone
BLEEP_VOLUME_DB = -10   # dB - volume of bleep relative to original
CENSOR_MODES = ["bleep", "mute"]

# Sensitivity levels
SENSITIVITY_LEVELS = {
    "low": {
        "description": "Only exact keyword matches",
        "use_contextual": False,
        "match_partial": False,
    },
    "medium": {
        "description": "Keyword matches + partial word matching",
        "use_contextual": False,
        "match_partial": True,
    },
    "high": {
        "description": "Keywords + partial matching + contextual analysis",
        "use_contextual": True,
        "match_partial": True,
    },
}

# Content categories
CONTENT_CATEGORIES = {
    "profanity": "Profane or vulgar language",
    "abusive": "Abusive, hateful, or demeaning language",
    "violent": "Violent or threatening language",
    "confidential": "Potentially confidential or sensitive information",
}
