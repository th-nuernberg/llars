"""
Dataset Transformer Service.

Transforms raw datasets into LLARS-compatible format for import.
"""

import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

# Base path for test datasets
# Use /tmp in container, or local tests directory on host
import tempfile
_default_path = Path(tempfile.gettempdir()) / 'llars_test_datasets'
TEST_DATASETS_PATH = _default_path


class BaseTransformer(ABC):
    """Base class for dataset transformers."""

    @abstractmethod
    def transform(self, raw_items: List[Dict]) -> List[Dict]:
        """Transform raw items to LLARS format."""
        pass

    @property
    @abstractmethod
    def llars_type(self) -> str:
        """Return the LLARS evaluation type this transformer produces."""
        pass


class HHRLHFTransformer(BaseTransformer):
    """
    Transformer for Anthropic HH-RLHF dataset.

    Converts preference data (chosen/rejected) to comparison format.
    """

    @property
    def llars_type(self) -> str:
        return 'comparison'

    def transform(self, raw_items: List[Dict]) -> List[Dict]:
        """Transform HH-RLHF items to LLARS comparison format."""
        threads = []

        for idx, item in enumerate(raw_items):
            chosen = item.get('chosen', '')
            rejected = item.get('rejected', '')

            # Parse the conversation format: "Human: ...\n\nAssistant: ..."
            chosen_messages = self._parse_conversation(chosen)
            rejected_messages = self._parse_conversation(rejected)

            if not chosen_messages or not rejected_messages:
                continue

            # Extract the human prompt (should be same for both)
            human_prompt = chosen_messages[0]['content'] if chosen_messages else 'Unknown prompt'

            # Create thread with both responses
            thread = {
                'thread_id': f'hh_rlhf_{idx:05d}',
                'subject': self._truncate(human_prompt, 100),
                'messages': [
                    {
                        'message_id': 1,
                        'sender': 'user',
                        'content': human_prompt,
                        'role': 'human',
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    {
                        'message_id': 2,
                        'sender': 'assistant_a',
                        'content': chosen_messages[-1]['content'] if len(chosen_messages) > 1 else chosen,
                        'role': 'assistant',
                        'is_chosen': True,
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    {
                        'message_id': 3,
                        'sender': 'assistant_b',
                        'content': rejected_messages[-1]['content'] if len(rejected_messages) > 1 else rejected,
                        'role': 'assistant',
                        'is_chosen': False,
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ],
                'metadata': {
                    'source': 'hh_rlhf',
                    'ground_truth': 'assistant_a',
                    'evaluation_type': 'comparison'
                }
            }
            threads.append(thread)

        return threads

    def _parse_conversation(self, text: str) -> List[Dict]:
        """Parse HH-RLHF conversation format."""
        messages = []
        # Split by "Human:" and "Assistant:" markers
        parts = re.split(r'\n\n(?=Human:|Assistant:)', text)

        for part in parts:
            part = part.strip()
            if part.startswith('Human:'):
                messages.append({
                    'role': 'human',
                    'content': part[6:].strip()
                })
            elif part.startswith('Assistant:'):
                messages.append({
                    'role': 'assistant',
                    'content': part[10:].strip()
                })

        return messages

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


class SST2Transformer(BaseTransformer):
    """
    Transformer for Stanford Sentiment Treebank.

    Converts sentiment labels to rating format.
    """

    @property
    def llars_type(self) -> str:
        return 'rating'

    def transform(self, raw_items: List[Dict]) -> List[Dict]:
        """Transform SST-2 items to LLARS rating format."""
        threads = []

        for idx, item in enumerate(raw_items):
            sentence = item.get('sentence', item.get('text', ''))
            label = item.get('label', 0)

            # SST-2: 0=negative, 1=positive
            # Map to 1-5 rating: negative=1-2, positive=4-5
            rating_value = 5 if label == 1 else 1

            thread = {
                'thread_id': f'sst2_{idx:05d}',
                'subject': f'Sentiment: {self._truncate(sentence, 80)}',
                'messages': [
                    {
                        'message_id': 1,
                        'sender': 'text',
                        'content': sentence,
                        'role': 'content',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ],
                'features': [
                    {
                        'feature_id': 1,
                        'feature_type': 'sentiment',
                        'feature_content': sentence
                    }
                ],
                'metadata': {
                    'source': 'sst2',
                    'ground_truth_label': 'positive' if label == 1 else 'negative',
                    'ground_truth_rating': rating_value,
                    'evaluation_type': 'rating'
                }
            }
            threads.append(thread)

        return threads

    def _truncate(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


class AGNewsTransformer(BaseTransformer):
    """
    Transformer for AG News dataset.

    Converts topic labels to labeling format.
    """

    LABELS = ['World', 'Sports', 'Business', 'Sci/Tech']

    @property
    def llars_type(self) -> str:
        return 'labeling'

    def transform(self, raw_items: List[Dict]) -> List[Dict]:
        """Transform AG News items to LLARS labeling format."""
        threads = []

        for idx, item in enumerate(raw_items):
            text = item.get('text', '')
            label = item.get('label', 0)

            thread = {
                'thread_id': f'agnews_{idx:05d}',
                'subject': f'News: {self._truncate(text, 80)}',
                'messages': [
                    {
                        'message_id': 1,
                        'sender': 'article',
                        'content': text,
                        'role': 'content',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ],
                'metadata': {
                    'source': 'ag_news',
                    'ground_truth_label': self.LABELS[label] if label < len(self.LABELS) else 'Unknown',
                    'available_labels': self.LABELS,
                    'evaluation_type': 'labeling'
                }
            }
            threads.append(thread)

        return threads

    def _truncate(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


class TruthfulQATransformer(BaseTransformer):
    """
    Transformer for TruthfulQA dataset.

    Converts to authenticity (truthful vs untruthful) format.
    """

    @property
    def llars_type(self) -> str:
        return 'authenticity'

    def transform(self, raw_items: List[Dict]) -> List[Dict]:
        """Transform TruthfulQA items to LLARS authenticity format."""
        threads = []

        for idx, item in enumerate(raw_items):
            question = item.get('question', '')
            best_answer = item.get('best_answer', '')
            correct_answers = item.get('correct_answers', [])
            incorrect_answers = item.get('incorrect_answers', [])

            # Create thread with question and best answer
            thread = {
                'thread_id': f'truthfulqa_{idx:05d}',
                'subject': f'Q: {self._truncate(question, 80)}',
                'messages': [
                    {
                        'message_id': 1,
                        'sender': 'questioner',
                        'content': question,
                        'role': 'human',
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    {
                        'message_id': 2,
                        'sender': 'responder',
                        'content': best_answer,
                        'role': 'assistant',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ],
                'metadata': {
                    'source': 'truthful_qa',
                    'is_truthful': True,
                    'correct_answers': correct_answers,
                    'incorrect_answers': incorrect_answers,
                    'evaluation_type': 'authenticity'
                }
            }
            threads.append(thread)

        return threads

    def _truncate(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


class IMDBTransformer(BaseTransformer):
    """
    Transformer for IMDB Reviews dataset.

    Converts review sentiment to rating format.
    """

    @property
    def llars_type(self) -> str:
        return 'rating'

    def transform(self, raw_items: List[Dict]) -> List[Dict]:
        """Transform IMDB items to LLARS rating format."""
        threads = []

        for idx, item in enumerate(raw_items):
            text = item.get('text', '')
            label = item.get('label', 0)

            # IMDB: 0=negative, 1=positive
            rating_value = 5 if label == 1 else 1

            thread = {
                'thread_id': f'imdb_{idx:05d}',
                'subject': f'Review: {self._truncate(text, 80)}',
                'messages': [
                    {
                        'message_id': 1,
                        'sender': 'reviewer',
                        'content': text,
                        'role': 'content',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                ],
                'features': [
                    {
                        'feature_id': 1,
                        'feature_type': 'review',
                        'feature_content': text
                    }
                ],
                'metadata': {
                    'source': 'imdb',
                    'ground_truth_label': 'positive' if label == 1 else 'negative',
                    'ground_truth_rating': rating_value,
                    'evaluation_type': 'rating'
                }
            }
            threads.append(thread)

        return threads

    def _truncate(self, text: str, max_length: int) -> str:
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + '...'


# Transformer registry
TRANSFORMERS = {
    'hh_rlhf': HHRLHFTransformer,
    'sst2': SST2Transformer,
    'ag_news': AGNewsTransformer,
    'truthful_qa': TruthfulQATransformer,
    'imdb': IMDBTransformer
}


class DatasetTransformer:
    """
    Main service for transforming datasets to LLARS format.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the transformer.

        Args:
            base_path: Base path for dataset storage
        """
        self.base_path = base_path or TEST_DATASETS_PATH

    def get_transformer(self, dataset_id: str) -> Optional[BaseTransformer]:
        """
        Get the appropriate transformer for a dataset.

        Args:
            dataset_id: The dataset identifier

        Returns:
            Transformer instance or None if not found
        """
        transformer_class = TRANSFORMERS.get(dataset_id)
        if transformer_class:
            return transformer_class()
        return None

    def transform_dataset(
        self,
        dataset_id: str,
        raw_items: Optional[List[Dict]] = None,
        limit: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Transform a dataset to LLARS format.

        Args:
            dataset_id: The dataset identifier
            raw_items: Optional raw items (if not provided, loads from file)
            limit: Optional limit on number of items to transform

        Returns:
            Transformation result with items and metadata
        """
        transformer = self.get_transformer(dataset_id)
        if not transformer:
            raise ValueError(f"No transformer available for dataset: {dataset_id}")

        # Load raw items if not provided
        if raw_items is None:
            raw_file = self.base_path / dataset_id / 'raw_samples.json'
            if not raw_file.exists():
                raise FileNotFoundError(f"Raw samples not found for {dataset_id}. Download first.")

            with open(raw_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                raw_items = data.get('items', [])

        # Apply limit
        if limit and len(raw_items) > limit:
            raw_items = raw_items[:limit]

        # Transform
        logger.info(f"Transforming {len(raw_items)} items from {dataset_id}")
        transformed_items = transformer.transform(raw_items)

        # Save transformed data
        sample_file = self.base_path / dataset_id / 'sample.json'
        with open(sample_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_id': dataset_id,
                'llars_type': transformer.llars_type,
                'transformed_at': datetime.utcnow().isoformat(),
                'count': len(transformed_items),
                'items': transformed_items
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"Transformed {len(transformed_items)} items to LLARS format")

        return {
            'status': 'success',
            'dataset_id': dataset_id,
            'llars_type': transformer.llars_type,
            'items_transformed': len(transformed_items),
            'output_path': str(sample_file)
        }

    def get_transformed_items(
        self,
        dataset_id: str,
        limit: Optional[int] = None
    ) -> Optional[List[Dict]]:
        """
        Get transformed items from a dataset.

        Args:
            dataset_id: The dataset identifier
            limit: Optional limit on number of items

        Returns:
            List of transformed items or None if not available
        """
        sample_file = self.base_path / dataset_id / 'sample.json'
        if not sample_file.exists():
            return None

        with open(sample_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            items = data.get('items', [])

        if limit:
            items = items[:limit]

        return items

    def preview_transformation(
        self,
        dataset_id: str,
        raw_items: List[Dict],
        count: int = 3
    ) -> List[Dict]:
        """
        Preview transformation without saving.

        Args:
            dataset_id: The dataset identifier
            raw_items: Raw items to transform
            count: Number of items to preview

        Returns:
            List of transformed items
        """
        transformer = self.get_transformer(dataset_id)
        if not transformer:
            raise ValueError(f"No transformer available for dataset: {dataset_id}")

        return transformer.transform(raw_items[:count])
