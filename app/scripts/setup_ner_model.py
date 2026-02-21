#!/usr/bin/env python3
"""
Download and setup the German NER model for entity detection.

This script downloads the Flair NER model (flair/ner-german-large) which is required
for detecting entities (names, locations, organizations, etc.) in the anonymization pipeline.

Usage:
    python scripts/setup_ner_model.py
"""

from pathlib import Path
import sys

# Add app to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from flair.models import SequenceTagger
    print("✓ Flair library is available")
except ImportError:
    print("✗ Flair library not found. Install with: pip install flair")
    sys.exit(1)


def download_ner_model():
    """Download the German NER model from HuggingFace."""
    print("\n" + "="*80)
    print("Downloading German NER Model (flair/ner-german-large)")
    print("="*80)
    print("\nThis is a ~500MB model and may take several minutes to download...")
    print("The model will be cached by HuggingFace and reused.\n")

    try:
        # Load the model - this will download it if not present
        print("Loading model: flair/ner-german-large")
        tagger = SequenceTagger.load("flair/ner-german-large")
        print("\n✓ Model downloaded and loaded successfully!")

        # Test the model
        print("\nTesting model with sample text...")
        from flair.data import Sentence

        sentence = Sentence("Hallo, ich bin Maria und ich wohne in Berlin.")
        tagger.predict(sentence)

        print(f"✓ Model test successful! Found {len(sentence.get_spans('ner'))} entities:")
        for entity in sentence.get_spans('ner'):
            print(f"  - {entity.tag}: {entity.text}")

        print("\n" + "="*80)
        print("Setup Complete!")
        print("="*80)
        print("\nThe NER model is now ready for use in the anonymization pipeline.")
        print("Entity detection will work automatically when importing conversations.")

    except Exception as e:
        print(f"\n✗ Error downloading model: {e}")
        sys.exit(1)


if __name__ == "__main__":
    download_ner_model()
