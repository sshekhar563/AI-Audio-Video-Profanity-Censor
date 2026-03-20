"""
Pipeline Module
Orchestrates the full audio/video censorship pipeline:
Extract → Transcribe → Classify → Censor → Output
"""

import os
import json
import time
from typing import Dict, Optional
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from src.audio_extractor import AudioExtractor
from src.transcriber import Transcriber
from src.content_classifier import ContentClassifier
from src.censor_engine import CensorEngine
from src.utils import (
    logger,
    console,
    validate_input_file,
    get_output_path,
    format_timestamp,
)


class CensorPipeline:
    """
    Main pipeline that orchestrates the full censorship workflow.
    
    Pipeline stages:
    1. Extract audio from input file
    2. Transcribe audio using Whisper
    3. Classify content for profanity/violence/abuse
    4. Apply censorship (bleep/mute) to flagged segments
    5. Output the censored file and optional report
    """

    def __init__(
        self,
        model_size: str = "base",
        censor_mode: str = "bleep",
        sensitivity: str = "medium",
        wordlist_path: str = None,
        bleep_frequency: int = 1000,
    ):
        """
        Initialize the censorship pipeline.
        
        Args:
            model_size: Whisper model size (tiny/base/small/medium/large)
            censor_mode: 'bleep' or 'mute'
            sensitivity: Detection sensitivity (low/medium/high)
            wordlist_path: Path to custom profanity word list
            bleep_frequency: Bleep tone frequency in Hz
        """
        self.extractor = AudioExtractor()
        self.transcriber = Transcriber(model_size=model_size)
        self.classifier = ContentClassifier(
            wordlist_path=wordlist_path,
            sensitivity=sensitivity,
        )
        self.censor_engine = CensorEngine(
            mode=censor_mode,
            bleep_frequency=bleep_frequency,
        )

        self.results = {}

    def run(
        self,
        input_path: str,
        output_path: str = None,
        generate_report: bool = False,
    ) -> Dict:
        """
        Run the full censorship pipeline.
        
        Args:
            input_path: Path to the input audio/video file
            output_path: Path for the output file (auto-generated if None)
            generate_report: Whether to save a JSON detection report
            
        Returns:
            Dictionary with pipeline results
        """
        start_time = time.time()

        # Validate input
        input_path = validate_input_file(input_path)
        output_path = get_output_path(input_path, output_path)

        console.print()
        console.rule("[bold cyan]Pipeline Starting[/bold cyan]")
        console.print(f"  [dim]Input:[/dim]  {input_path}")
        console.print(f"  [dim]Output:[/dim] {output_path}")
        console.print()

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
            ) as progress:

                # Stage 1: Extract Audio
                task1 = progress.add_task("[cyan]Stage 1/4: Extracting audio...", total=1)
                wav_path = self.extractor.extract(input_path)
                progress.update(task1, completed=1)

                # Stage 2: Transcribe
                task2 = progress.add_task("[cyan]Stage 2/4: Transcribing audio...", total=1)
                transcript = self.transcriber.transcribe(wav_path)
                progress.update(task2, completed=1)

                # Stage 3: Classify Content
                task3 = progress.add_task("[cyan]Stage 3/4: Classifying content...", total=1)
                flagged = self.classifier.classify(transcript)
                progress.update(task3, completed=1)

                # Stage 4: Apply Censorship
                task4 = progress.add_task("[cyan]Stage 4/4: Applying censorship...", total=1)
                result_path = self.censor_engine.censor(
                    input_path, wav_path, flagged, output_path
                )
                progress.update(task4, completed=1)

            elapsed = time.time() - start_time

            # Compile results
            self.results = {
                "input_file": input_path,
                "output_file": result_path,
                "processing_time_seconds": round(elapsed, 2),
                "transcript": {
                    "text": transcript["text"],
                    "language": transcript["language"],
                    "word_count": transcript["word_count"],
                },
                "flagged_content": [
                    {
                        "word": f["word"],
                        "start": f["start"],
                        "end": f["end"],
                        "start_formatted": format_timestamp(f["start"]),
                        "end_formatted": format_timestamp(f["end"]),
                        "category": f["category"],
                        "method": f["method"],
                        "confidence": f["confidence"],
                    }
                    for f in flagged
                ],
                "summary": {
                    "total_words": transcript["word_count"],
                    "flagged_count": len(flagged),
                    "categories": self._count_categories(flagged),
                    "censor_mode": self.censor_engine.mode,
                },
            }

            # Display results
            self._print_results(self.results)

            # Generate report if requested
            if generate_report:
                report_path = self._save_report(result_path)
                self.results["report_file"] = report_path

            return self.results

        finally:
            # Cleanup temporary files
            self.extractor.cleanup()

    def _count_categories(self, flagged: list) -> Dict[str, int]:
        """Count flagged items by category."""
        counts = {}
        for item in flagged:
            cat = item["category"]
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _print_results(self, results: Dict):
        """Print a beautiful results summary using Rich."""
        console.print()
        console.rule("[bold green]Pipeline Complete[/bold green]")
        console.print()

        # Summary table
        summary = results["summary"]
        table = Table(
            title="📊 Censorship Report",
            show_header=True,
            header_style="bold cyan",
        )
        table.add_column("Metric", style="dim")
        table.add_column("Value", style="bold")

        table.add_row("Total Words", str(summary["total_words"]))
        table.add_row("Flagged Segments", f"[red]{summary['flagged_count']}[/red]")
        table.add_row("Censor Mode", summary["censor_mode"].upper())
        table.add_row("Processing Time", f"{results['processing_time_seconds']}s")
        table.add_row("Language", results["transcript"]["language"])

        console.print(table)

        # Category breakdown
        if summary["categories"]:
            console.print()
            cat_table = Table(
                title="🏷️ Categories",
                show_header=True,
                header_style="bold yellow",
            )
            cat_table.add_column("Category", style="dim")
            cat_table.add_column("Count", style="bold red")

            for cat, count in sorted(summary["categories"].items()):
                cat_table.add_row(cat.title(), str(count))

            console.print(cat_table)

        # Flagged words detail (show first 20)
        flagged = results["flagged_content"]
        if flagged:
            console.print()
            detail_table = Table(
                title="🔍 Flagged Content (Detail)",
                show_header=True,
                header_style="bold magenta",
            )
            detail_table.add_column("#", style="dim", width=4)
            detail_table.add_column("Word", style="bold red")
            detail_table.add_column("Time", style="cyan")
            detail_table.add_column("Category", style="yellow")
            detail_table.add_column("Method", style="dim")

            for i, item in enumerate(flagged[:20], 1):
                detail_table.add_row(
                    str(i),
                    item["word"],
                    f"{item['start_formatted']} → {item['end_formatted']}",
                    item["category"],
                    item["method"],
                )

            if len(flagged) > 20:
                detail_table.add_row("...", f"+{len(flagged) - 20} more", "", "", "")

            console.print(detail_table)

        console.print()
        console.print(f"[green]✅ Output saved:[/green] [bold]{results['output_file']}[/bold]")
        console.print()

    def _save_report(self, output_path: str) -> str:
        """Save the detection report as JSON."""
        report_path = os.path.splitext(output_path)[0] + "_report.json"

        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        logger.info(f"[green]✓[/green] Report saved: {report_path}")
        return report_path
