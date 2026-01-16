"""
Dataset Downloader Service.

Downloads public datasets from HuggingFace and other sources
for testing the Scenario Manager.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# Base path for test datasets
# Use /tmp in container, or local tests directory on host
import tempfile
_default_path = Path(tempfile.gettempdir()) / 'llars_test_datasets'
TEST_DATASETS_PATH = _default_path


# Available datasets configuration
AVAILABLE_DATASETS = {
    'hh_rlhf': {
        'name': 'Anthropic HH-RLHF',
        'description': 'Human preference data for helpful/harmless assistant training',
        'url': 'https://huggingface.co/datasets/Anthropic/hh-rlhf',
        'hf_dataset': 'Anthropic/hh-rlhf',
        'hf_config': 'default',
        'llars_types': ['comparison', 'ranking'],
        'size': 170000,
        'format': 'jsonl',
        'default_split': 'train'
    },
    'sst2': {
        'name': 'Stanford Sentiment Treebank',
        'description': 'Sentiment classification dataset (positive/negative)',
        'url': 'https://huggingface.co/datasets/stanfordnlp/sst2',
        'hf_dataset': 'stanfordnlp/sst2',
        'hf_config': 'default',
        'llars_types': ['rating', 'labeling'],
        'size': 70000,
        'format': 'parquet'
    },
    'ag_news': {
        'name': 'AG News',
        'description': 'News article topic classification (World, Sports, Business, Sci/Tech)',
        'url': 'https://huggingface.co/datasets/fancyzhx/ag_news',
        'hf_dataset': 'fancyzhx/ag_news',
        'hf_config': 'default',
        'llars_types': ['labeling'],
        'size': 120000,
        'format': 'parquet'
    },
    'truthful_qa': {
        'name': 'TruthfulQA',
        'description': 'Questions to test truthfulness of language models',
        'url': 'https://huggingface.co/datasets/truthfulqa/truthful_qa',
        'hf_dataset': 'truthfulqa/truthful_qa',
        'hf_config': 'generation',
        'llars_types': ['authenticity'],
        'size': 800,
        'format': 'parquet',
        'default_split': 'validation'
    },
    'imdb': {
        'name': 'IMDB Reviews',
        'description': 'Movie review sentiment classification',
        'url': 'https://huggingface.co/datasets/stanfordnlp/imdb',
        'hf_dataset': 'stanfordnlp/imdb',
        'hf_config': None,
        'llars_types': ['rating'],
        'size': 50000,
        'format': 'parquet'
    }
}


class DatasetDownloader:
    """
    Downloads and manages test datasets from HuggingFace.
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the downloader.

        Args:
            base_path: Base path for storing datasets. Defaults to tests/fixtures/test_datasets
        """
        self.base_path = base_path or TEST_DATASETS_PATH
        self.base_path.mkdir(parents=True, exist_ok=True)

    def list_available_datasets(self) -> List[Dict[str, Any]]:
        """
        List all available datasets with download status.

        Returns:
            List of dataset info dicts
        """
        datasets = []
        for dataset_id, config in AVAILABLE_DATASETS.items():
            dataset_path = self.base_path / dataset_id
            sample_file = dataset_path / 'sample.json'

            local_samples = 0
            if sample_file.exists():
                try:
                    with open(sample_file, 'r') as f:
                        data = json.load(f)
                        local_samples = len(data.get('items', []))
                except Exception:
                    pass

            datasets.append({
                'id': dataset_id,
                'name': config['name'],
                'description': config['description'],
                'url': config['url'],
                'llars_types': config['llars_types'],
                'size': config['size'],
                'downloaded': sample_file.exists(),
                'local_samples': local_samples
            })

        return datasets

    def get_dataset_info(self, dataset_id: str) -> Optional[Dict[str, Any]]:
        """
        Get info about a specific dataset.

        Args:
            dataset_id: The dataset identifier

        Returns:
            Dataset info dict or None if not found
        """
        if dataset_id not in AVAILABLE_DATASETS:
            return None

        config = AVAILABLE_DATASETS[dataset_id]
        dataset_path = self.base_path / dataset_id
        sample_file = dataset_path / 'sample.json'

        return {
            'id': dataset_id,
            **config,
            'downloaded': sample_file.exists(),
            'local_path': str(dataset_path) if dataset_path.exists() else None
        }

    def download_dataset(
        self,
        dataset_id: str,
        sample_size: int = 100,
        split: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Download a dataset from HuggingFace.

        Args:
            dataset_id: The dataset identifier
            sample_size: Number of samples to download
            split: Dataset split to use (train, test, validation). Defaults to dataset's default_split or 'train'.

        Returns:
            Download result with path and sample count
        """
        if dataset_id not in AVAILABLE_DATASETS:
            raise ValueError(f"Unknown dataset: {dataset_id}")

        config = AVAILABLE_DATASETS[dataset_id]
        # Use provided split, or dataset's default_split, or fall back to 'train'
        split = split or config.get('default_split', 'train')
        dataset_path = self.base_path / dataset_id
        dataset_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Downloading {config['name']} (sample_size={sample_size})")

        try:
            # Try to use datasets library if available
            samples = self._download_via_datasets_lib(
                config['hf_dataset'],
                config.get('hf_config'),
                split,
                sample_size
            )
        except Exception as e:
            logger.warning(f"datasets library failed: {e}, trying API fallback")
            samples = self._download_via_api(
                config['hf_dataset'],
                config.get('hf_config'),
                split,
                sample_size
            )

        # Save raw samples
        raw_file = dataset_path / 'raw_samples.json'
        with open(raw_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_id': dataset_id,
                'source': config['hf_dataset'],
                'split': split,
                'downloaded_at': datetime.utcnow().isoformat(),
                'count': len(samples),
                'items': samples
            }, f, ensure_ascii=False, indent=2)

        # Save metadata
        metadata_file = dataset_path / 'metadata.json'
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump({
                'dataset_id': dataset_id,
                'name': config['name'],
                'description': config['description'],
                'source_url': config['url'],
                'hf_dataset': config['hf_dataset'],
                'llars_types': config['llars_types'],
                'downloaded_at': datetime.utcnow().isoformat(),
                'sample_count': len(samples),
                'split': split
            }, f, ensure_ascii=False, indent=2)

        logger.info(f"Downloaded {len(samples)} samples to {dataset_path}")

        return {
            'status': 'success',
            'dataset_id': dataset_id,
            'samples_downloaded': len(samples),
            'output_path': str(raw_file)
        }

    def _download_via_datasets_lib(
        self,
        dataset_name: str,
        config_name: Optional[str],
        split: str,
        limit: int
    ) -> List[Dict]:
        """
        Download using the HuggingFace datasets library.
        """
        try:
            from datasets import load_dataset
        except ImportError:
            raise RuntimeError("datasets library not installed")

        logger.info(f"Loading {dataset_name} via datasets library")

        if config_name:
            dataset = load_dataset(dataset_name, config_name, split=split)
        else:
            dataset = load_dataset(dataset_name, split=split)

        # Take sample
        if len(dataset) > limit:
            dataset = dataset.select(range(limit))

        # Convert to list of dicts
        samples = [dict(item) for item in dataset]
        return samples

    def _download_via_api(
        self,
        dataset_name: str,
        config_name: Optional[str],
        split: str,
        limit: int
    ) -> List[Dict]:
        """
        Download using HuggingFace API (fallback).
        """
        # Construct API URL
        base_url = "https://datasets-server.huggingface.co/rows"
        params = {
            'dataset': dataset_name,
            'split': split,
            'offset': 0,
            'length': min(limit, 100)  # API limit
        }
        if config_name:
            params['config'] = config_name

        logger.info(f"Fetching from HuggingFace API: {dataset_name}")

        samples = []
        while len(samples) < limit:
            params['offset'] = len(samples)
            params['length'] = min(limit - len(samples), 100)

            response = requests.get(base_url, params=params, timeout=30)
            if response.status_code != 200:
                logger.warning(f"API returned {response.status_code}: {response.text[:200]}")
                break

            data = response.json()
            rows = data.get('rows', [])
            if not rows:
                break

            for row in rows:
                samples.append(row.get('row', row))

            if len(rows) < params['length']:
                break

        return samples[:limit]

    def get_raw_samples(self, dataset_id: str) -> Optional[List[Dict]]:
        """
        Get raw samples from a downloaded dataset.

        Args:
            dataset_id: The dataset identifier

        Returns:
            List of raw sample dicts or None if not downloaded
        """
        dataset_path = self.base_path / dataset_id
        raw_file = dataset_path / 'raw_samples.json'

        if not raw_file.exists():
            return None

        with open(raw_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('items', [])

    def delete_dataset(self, dataset_id: str) -> bool:
        """
        Delete a downloaded dataset.

        Args:
            dataset_id: The dataset identifier

        Returns:
            True if deleted, False if not found
        """
        dataset_path = self.base_path / dataset_id
        if not dataset_path.exists():
            return False

        import shutil
        shutil.rmtree(dataset_path)
        logger.info(f"Deleted dataset {dataset_id}")
        return True
