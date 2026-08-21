#!/usr/bin/env python3
"""Test script to download Flair NER model with verbose logging."""

import sys
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

print("=" * 80)
print("Testing Flair NER Model Download")
print("=" * 80)

try:
    print("\n1. Importing libraries...")
    import torch
    import flair
    from flair.models import SequenceTagger
    from flair.data import Sentence
    print("✓ Libraries imported successfully")

    print("\n2. Setting device to CPU...")
    flair.device = torch.device("cpu")
    print(f"✓ Device set to: {flair.device}")

    print("\n3. Loading model from HuggingFace (this may take several minutes)...")
    print("   Model: flair/ner-german-large (~500MB)")
    tagger = SequenceTagger.load("flair/ner-german-large")
    print("✓ Model loaded successfully!")

    print("\n4. Testing model with sample sentence...")
    sentence = Sentence("Maria wohnt in Berlin und arbeitet in München.")
    tagger.predict(sentence)

    entities = sentence.get_spans('ner')
    print(f"✓ Model test successful! Found {len(entities)} entities:")
    for entity in entities:
        print(f"   - {entity.tag}: {entity.text}")

    print("\n" + "=" * 80)
    print("SUCCESS - Model is working correctly!")
    print("=" * 80)
    sys.exit(0)

except Exception as e:
    print(f"\n✗ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
