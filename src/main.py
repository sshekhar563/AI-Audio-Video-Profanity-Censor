"""
AI Audio/Video Censor - CLI Entry Point
Automated profanity and content censorship tool powered by Whisper ASR.

Usage:
    python -m src.main -i input.mp4 -o output.mp4 --mode bleep
    python -m src.main -i audio.wav --mode mute --sensitivity high --report
"""

import sys
import os
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.utils import print_banner, console, check_ffmpeg
from src.pipeline import CensorPipeline
from config.config import (
    SUPPORTED_WHISPER_MODELS,
    CENSOR_MODES,
    SENSITIVITY_LEVELS,
    DEFAULT_WORDLIST,
    DEFAULT_WHISPER_MODEL,
)


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        prog="avcensor",
        description=(
            "🔇 AI Audio/Video Censor — "
            "Automated profanity & content censorship using Whisper ASR"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Bleep profanity in a video:
    python -m src.main -i video.mp4 -o clean_video.mp4

  Mute profanity in audio with high sensitivity:
    python -m src.main -i podcast.wav --mode mute --sensitivity high

  Use a custom word list and generate a report:
    python -m src.main -i audio.wav --wordlist my_words.txt --report

  Use a larger Whisper model for better accuracy:
    python -m src.main -i video.mp4 --model small --mode bleep
        """,
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to the input audio or video file",
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Path for the output file (auto-generated if not specified)",
    )
    parser.add_argument(
        "--mode",
        choices=CENSOR_MODES,
        default="bleep",
        help="Censorship mode: 'bleep' (tone) or 'mute' (silence). Default: bleep",
    )
    parser.add_argument(
        "--model",
        choices=SUPPORTED_WHISPER_MODELS,
        default=DEFAULT_WHISPER_MODEL,
        help=f"Whisper model size. Default: {DEFAULT_WHISPER_MODEL}",
    )
    parser.add_argument(
        "--sensitivity",
        choices=list(SENSITIVITY_LEVELS.keys()),
        default="medium",
        help="Detection sensitivity level. Default: medium",
    )
    parser.add_argument(
        "--wordlist",
        default=DEFAULT_WORDLIST,
        help="Path to custom profanity word list file",
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate a JSON report of all detected content",
    )
    parser.add_argument(
        "--bleep-freq",
        type=int,
        default=1000,
        help="Bleep tone frequency in Hz. Default: 1000",
    )

    return parser.parse_args()


def main():
    """Main entry point for the AI Audio/Video Censor tool."""
    args = parse_args()

    # Display banner
    print_banner()

    # Check FFmpeg availability
    if not check_ffmpeg():
        console.print(
            "[yellow]⚠ FFmpeg not found.[/yellow] "
            "Video processing and some audio formats may not work.\n"
            "  Install: [dim]https://ffmpeg.org/download.html[/dim]\n"
        )

    # Display configuration
    console.print(f"  [dim]Mode:[/dim]        {args.mode}")
    console.print(f"  [dim]Model:[/dim]       {args.model}")
    console.print(f"  [dim]Sensitivity:[/dim] {args.sensitivity}")
    console.print(f"  [dim]Word List:[/dim]   {os.path.basename(args.wordlist)}")
    console.print()

    try:
        # Create and run the pipeline
        pipeline = CensorPipeline(
            model_size=args.model,
            censor_mode=args.mode,
            sensitivity=args.sensitivity,
            wordlist_path=args.wordlist,
            bleep_frequency=args.bleep_freq,
        )

        results = pipeline.run(
            input_path=args.input,
            output_path=args.output,
            generate_report=args.report,
        )

        # Exit code based on flagged content
        flagged_count = results["summary"]["flagged_count"]
        if flagged_count > 0:
            console.print(
                f"[bold yellow]⚠ {flagged_count} segment(s) were censored.[/bold yellow]"
            )
        else:
            console.print("[bold green]✅ No objectionable content detected![/bold green]")

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except RuntimeError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
