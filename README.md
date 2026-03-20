# 🔇 AI Audio/Video Censor

> **Automated Profanity & Content Censorship Tool** — Powered by Whisper ASR

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An AI-powered command-line tool that automatically detects and censors **profanity, abusive, violent, and confidential content** from audio and video files. Built using OpenAI's Whisper for speech-to-text transcription with **word-level timestamps** for precise, frame-accurate censorship.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    INPUT (Video/Audio)                    │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              STAGE 1: Audio Extraction                    │
│  ┌─────────────┐                                         │
│  │ pydub/FFmpeg │ → Extract audio → Convert to WAV (16kHz)│
│  └─────────────┘                                         │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              STAGE 2: Speech Transcription                │
│  ┌─────────────┐                                         │
│  │   Whisper    │ → Word-level timestamps                 │
│  │  (ASR Model) │ → [{word, start, end}, ...]            │
│  └─────────────┘                                         │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│            STAGE 3: Content Classification                │
│  ┌──────────────────┐  ┌───────────────────┐             │
│  │ Keyword Matching  │  │ Contextual Analysis│            │
│  │ (Profanity List)  │  │ (Regex Patterns)   │            │
│  └────────┬─────────┘  └────────┬──────────┘             │
│           └──────────┬──────────┘                         │
│                      ▼                                    │
│          Flagged Segments [{word, start, end, category}]  │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│              STAGE 4: Censorship Engine                   │
│  ┌──────────┐  ┌──────────┐                              │
│  │  BLEEP   │  │   MUTE   │                              │
│  │(1kHz tone)│  │(Silence) │                              │
│  └──────────┘  └──────────┘                              │
│                      │                                    │
│            Merge censored audio with video (FFmpeg)       │
└────────────────────────┬─────────────────────────────────┘
                         │
                         ▼
┌──────────────────────────────────────────────────────────┐
│           OUTPUT (Censored Video/Audio + Report)          │
└──────────────────────────────────────────────────────────┘
```

---

## ✨ Features

- 🎤 **Whisper-Powered ASR** — Accurate transcription with word-level timestamps
- 🔍 **Two-Tier Detection** — Keyword matching + contextual pattern analysis
- 🔇 **Bleep or Mute** — Choose between tone overlay or silent censoring
- 📊 **Detection Report** — JSON report with all flagged content & timestamps
- 🎬 **Video Support** — Process video files (extracts audio, censors, reassembles)
- 🎚️ **Sensitivity Levels** — Low / Medium / High detection sensitivity
- 📝 **Custom Word Lists** — Add your own profanity/banned words
- 🖥️ **Rich CLI** — Beautiful terminal output with progress bars and tables
- 🔌 **Modular Design** — Each component is independent and extensible

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+**
- **FFmpeg** (required for video files and non-WAV audio formats)
  - Windows: `choco install ffmpeg` or download from [ffmpeg.org](https://ffmpeg.org/download.html)
  - macOS: `brew install ffmpeg`
  - Linux: `sudo apt install ffmpeg`

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ai-audio-video-censor.git
cd ai-audio-video-censor

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Usage

```bash
# Basic usage — bleep profanity in an audio file
python -m src.main -i input.wav

# Mute mode with high sensitivity
python -m src.main -i podcast.mp3 --mode mute --sensitivity high

# Process a video file with report generation
python -m src.main -i video.mp4 -o clean_video.mp4 --report

# Use a larger Whisper model for better accuracy
python -m src.main -i audio.wav --model small --mode bleep

# Use a custom word list
python -m src.main -i input.wav --wordlist my_words.txt
```

---

## 📋 CLI Options

| Option | Default | Description |
|--------|---------|-------------|
| `-i, --input` | *required* | Input audio/video file path |
| `-o, --output` | auto | Output file path |
| `--mode` | `bleep` | Censorship mode: `bleep` or `mute` |
| `--model` | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `--sensitivity` | `medium` | Detection level: `low`, `medium`, `high` |
| `--wordlist` | built-in | Path to custom word list file |
| `--report` | off | Generate JSON detection report |
| `--bleep-freq` | `1000` | Bleep tone frequency (Hz) |

### Sensitivity Levels

| Level | Keyword Match | Partial Match | Contextual Analysis |
|-------|:---:|:---:|:---:|
| **Low** | ✅ | ❌ | ❌ |
| **Medium** | ✅ | ✅ | ❌ |
| **High** | ✅ | ✅ | ✅ |

---

## 📁 Project Structure

```
ai-audio-video-censor/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── setup.py                     # Package setup
├── LICENSE                      # MIT License
├── .gitignore                   # Git ignored files
├── config/
│   ├── config.py                # Centralized settings
│   └── profanity_words.txt      # Default word list (categorized)
├── src/
│   ├── __init__.py              # Package init
│   ├── main.py                  # CLI entry point
│   ├── audio_extractor.py       # Audio extraction from video/audio
│   ├── transcriber.py           # Whisper transcription engine
│   ├── content_classifier.py    # Content detection & classification
│   ├── censor_engine.py         # Bleep/mute audio processing
│   ├── pipeline.py              # Pipeline orchestrator
│   └── utils.py                 # Logging & helper utilities
├── output/                      # Default output directory
└── samples/                     # Sample files directory
```

---

## 🔧 Supported Formats

### Audio
`.wav`, `.mp3`, `.flac`, `.aac`, `.ogg`, `.wma`, `.m4a`

### Video
`.mp4`, `.mkv`, `.avi`, `.mov`, `.webm`, `.flv`, `.wmv`

---

## 📊 Sample Output

```
🔇 AI Audio/Video Censor
Automated Profanity & Content Censorship Tool
Powered by Whisper ASR | Built for OpenVINO GSoC

  Mode:        bleep
  Model:       base
  Sensitivity: medium
  Word List:   profanity_words.txt

──────────────── Pipeline Starting ────────────────
  Input:  D:\samples\interview.wav
  Output: D:\pipeline\output\interview_censored.wav

✓ Whisper model 'base' loaded successfully
✓ Transcription complete: 342 words detected, language: en
✓ Content classification complete: 7 flagged segments found

──────────────── Pipeline Complete ────────────────

      📊 Censorship Report
┌──────────────────┬─────────┐
│ Metric           │ Value   │
├──────────────────┼─────────┤
│ Total Words      │ 342     │
│ Flagged Segments │ 7       │
│ Censor Mode      │ BLEEP   │
│ Processing Time  │ 12.4s   │
│ Language         │ en      │
└──────────────────┴─────────┘

✅ Output saved: output/interview_censored.wav
```

---

## 🗺️ Future Roadmap (OpenVINO Integration)

This project serves as a proof-of-concept for the **OpenVINO GSoC Project #39**. Future enhancements planned:

1. **OpenVINO Model Optimization** — Convert Whisper to OpenVINO IR format for accelerated inference on Intel hardware
2. **VLM Visual Understanding** — Use Vision Language Models (via OpenVINO GenAI) to detect violent visual content in video frames
3. **DL Streamer Integration** — Build a GStreamer-based real-time processing pipeline using Intel DL Streamer
4. **LLM-Based Classification** — Replace keyword matching with an OpenVINO-optimized LLM for context-aware content understanding
5. **Microservices Architecture** — Deploy as containerized microservices for scalable production use
6. **Fine-Tuning Support** — Fine-tune content detection models on domain-specific data

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **ASR Engine** | OpenAI Whisper |
| **Audio Processing** | pydub, FFmpeg |
| **Content Detection** | Keyword matching, Regex patterns |
| **CLI Interface** | argparse, Rich |
| **Language** | Python 3.8+ |

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [OpenAI Whisper](https://github.com/openai/whisper) — Speech recognition model
- [OpenVINO Toolkit](https://github.com/openvinotoolkit/openvino) — AI inference optimization
- [pydub](https://github.com/jiaaro/pydub) — Audio manipulation library
- [Rich](https://github.com/Textualize/rich) — Terminal formatting library

---

<p align="center">
  Built with ❤️
</p>
