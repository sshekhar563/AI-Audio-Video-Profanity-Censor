"""
Content Classifier Module
Detects profanity, abusive, violent, and confidential content in transcribed text.
Supports keyword matching and contextual analysis.
"""

import os
import re
from typing import List, Dict
from src.utils import logger


class ContentClassifier:
    """Classifies transcribed words into content categories for censorship."""

    # Contextual patterns for sentence-level analysis
    VIOLENT_PATTERNS = [
        r"\b(i('ll|'m going to|will|wanna)\s+(kill|hurt|attack|shoot|stab|destroy|murder))\b",
        r"\b(gonna|going to)\s+(die|kill|murder|shoot|destroy)\b",
        r"\b(threat(en)?|threaten(ing|ed)?)\b.*\b(you|him|her|them)\b",
        r"\b(blow\s+(up|away)|shoot\s+(up|down))\b",
    ]

    ABUSIVE_PATTERNS = [
        r"\b(you('re| are)\s+(an?\s+)?(stupid|idiot|moron|pathetic|worthless|useless|dumb))\b",
        r"\b(shut\s+(up|the))\b",
        r"\b(go\s+(to\s+hell|die|away))\b",
        r"\b(hate\s+you)\b",
        r"\b(piece\s+of\s+(shit|crap|trash|garbage))\b",
    ]

    def __init__(self, wordlist_path: str = None, sensitivity: str = "medium"):
        """
        Initialize the content classifier.
        
        Args:
            wordlist_path: Path to profanity word list file
            sensitivity: Detection sensitivity (low, medium, high)
        """
        self.sensitivity = sensitivity
        self.profanity_words = set()
        self.word_categories = {}  # word -> category mapping
        
        # Load word list
        if wordlist_path:
            self._load_wordlist(wordlist_path)
        else:
            self._load_default_wordlist()

    def _load_wordlist(self, filepath: str):
        """Load profanity words from a file."""
        if not os.path.exists(filepath):
            logger.warning(f"[yellow]⚠[/yellow] Word list not found: {filepath}")
            return

        current_category = "profanity"

        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    # Check for category headers in comments
                    if "profanity" in line.lower():
                        current_category = "profanity"
                    elif "abusive" in line.lower() or "hate" in line.lower():
                        current_category = "abusive"
                    elif "violent" in line.lower() or "threat" in line.lower():
                        current_category = "violent"
                    elif "confidential" in line.lower() or "sensitive" in line.lower():
                        current_category = "confidential"
                    continue

                word = line.lower()
                self.profanity_words.add(word)
                self.word_categories[word] = current_category

        logger.info(f"[green]✓[/green] Loaded {len(self.profanity_words)} words from word list")

    def _load_default_wordlist(self):
        """Load the default word list from the config directory."""
        default_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config",
            "profanity_words.txt",
        )
        self._load_wordlist(default_path)

    def classify(self, transcript_data: dict) -> List[Dict]:
        """
        Classify transcribed content and return flagged segments.
        
        Args:
            transcript_data: Output from Transcriber.transcribe()
            
        Returns:
            List of flagged items:
            [{
                'word': str,
                'start': float,
                'end': float,
                'category': str,
                'method': str ('keyword' or 'contextual'),
                'confidence': float
            }, ...]
        """
        flagged = []

        # Method 1: Keyword matching on individual words
        keyword_flags = self._keyword_match(transcript_data["words"])
        flagged.extend(keyword_flags)

        # Method 2: Contextual analysis (if sensitivity allows)
        if self.sensitivity == "high":
            contextual_flags = self._contextual_analysis(transcript_data)
            # Avoid duplicates
            existing_ranges = {(f["start"], f["end"]) for f in flagged}
            for flag in contextual_flags:
                if (flag["start"], flag["end"]) not in existing_ranges:
                    flagged.append(flag)

        # Sort by timestamp
        flagged.sort(key=lambda x: x["start"])

        logger.info(
            f"[green]✓[/green] Content classification complete: "
            f"[bold red]{len(flagged)}[/bold red] flagged segments found"
        )

        # Log breakdown by category
        categories = {}
        for flag in flagged:
            cat = flag["category"]
            categories[cat] = categories.get(cat, 0) + 1

        for cat, count in categories.items():
            logger.info(f"  [dim]├─[/dim] {cat}: {count} instances")

        return flagged

    def _keyword_match(self, words: List[Dict]) -> List[Dict]:
        """Match individual words against the profanity word list."""
        flagged = []
        match_partial = self.sensitivity in ("medium", "high")

        for word_data in words:
            word_clean = re.sub(r"[^\w\s]", "", word_data["word"].lower()).strip()

            if not word_clean:
                continue

            # Exact match
            if word_clean in self.profanity_words:
                flagged.append({
                    "word": word_data["word"],
                    "start": word_data["start"],
                    "end": word_data["end"],
                    "category": self.word_categories.get(word_clean, "profanity"),
                    "method": "keyword",
                    "confidence": 1.0,
                })
                continue

            # Partial match (check if any profanity word is a substring)
            if match_partial:
                for profanity_word in self.profanity_words:
                    if len(profanity_word) >= 4 and profanity_word in word_clean:
                        flagged.append({
                            "word": word_data["word"],
                            "start": word_data["start"],
                            "end": word_data["end"],
                            "category": self.word_categories.get(profanity_word, "profanity"),
                            "method": "keyword_partial",
                            "confidence": 0.8,
                        })
                        break

        return flagged

    def _contextual_analysis(self, transcript_data: dict) -> List[Dict]:
        """Analyze sentence-level context for violent/abusive patterns."""
        flagged = []
        full_text = transcript_data["text"].lower()

        # Check violent patterns
        for pattern in self.VIOLENT_PATTERNS:
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                matched_text = match.group()
                # Find the corresponding word timestamps
                word_flags = self._find_words_in_range(
                    transcript_data["words"],
                    matched_text,
                )
                for wf in word_flags:
                    flagged.append({
                        "word": wf["word"],
                        "start": wf["start"],
                        "end": wf["end"],
                        "category": "violent",
                        "method": "contextual",
                        "confidence": 0.7,
                    })

        # Check abusive patterns
        for pattern in self.ABUSIVE_PATTERNS:
            for match in re.finditer(pattern, full_text, re.IGNORECASE):
                matched_text = match.group()
                word_flags = self._find_words_in_range(
                    transcript_data["words"],
                    matched_text,
                )
                for wf in word_flags:
                    flagged.append({
                        "word": wf["word"],
                        "start": wf["start"],
                        "end": wf["end"],
                        "category": "abusive",
                        "method": "contextual",
                        "confidence": 0.7,
                    })

        return flagged

    def _find_words_in_range(self, words: List[Dict], matched_text: str) -> List[Dict]:
        """
        Find word entries that correspond to a matched text pattern.
        Returns words that are part of the matched phrase.
        """
        matched_words_list = matched_text.lower().split()
        results = []

        for i, word_data in enumerate(words):
            word_clean = re.sub(r"[^\w\s]", "", word_data["word"].lower()).strip()
            if word_clean in matched_words_list:
                results.append(word_data)

        return results
