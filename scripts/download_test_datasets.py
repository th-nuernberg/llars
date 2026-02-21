#!/usr/bin/env python3
"""
Download Test Datasets CLI.

Downloads public datasets from HuggingFace for testing the Scenario Manager.

Usage:
    # Download all datasets (100 samples each)
    python scripts/download_test_datasets.py --all

    # Download specific dataset
    python scripts/download_test_datasets.py --dataset hh_rlhf --limit 500

    # List available datasets
    python scripts/download_test_datasets.py --list

    # Download and transform
    python scripts/download_test_datasets.py --dataset sst2 --transform
"""

import argparse
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from services.test_data.dataset_downloader import DatasetDownloader, AVAILABLE_DATASETS
from services.test_data.dataset_transformer import DatasetTransformer


def main():
    parser = argparse.ArgumentParser(
        description='Download test datasets for LLARS Scenario Manager'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List available datasets'
    )
    parser.add_argument(
        '--all', '-a',
        action='store_true',
        help='Download all available datasets'
    )
    parser.add_argument(
        '--dataset', '-d',
        type=str,
        help='Download specific dataset by ID'
    )
    parser.add_argument(
        '--limit', '-n',
        type=int,
        default=100,
        help='Number of samples to download (default: 100)'
    )
    parser.add_argument(
        '--transform', '-t',
        action='store_true',
        help='Transform dataset to LLARS format after download'
    )
    parser.add_argument(
        '--split', '-s',
        type=str,
        default='train',
        help='Dataset split to use (default: train)'
    )

    args = parser.parse_args()

    downloader = DatasetDownloader()
    transformer = DatasetTransformer()

    # List datasets
    if args.list:
        print("\nAvailable Datasets:")
        print("=" * 80)
        for dataset_id, config in AVAILABLE_DATASETS.items():
            print(f"\n  {dataset_id}")
            print(f"    Name: {config['name']}")
            print(f"    Description: {config['description']}")
            print(f"    LLARS Types: {', '.join(config['llars_types'])}")
            print(f"    Size: ~{config['size']:,} items")
        print("\n")
        return

    # Download all datasets
    if args.all:
        print(f"\nDownloading all datasets (limit={args.limit} per dataset)...")
        for dataset_id in AVAILABLE_DATASETS.keys():
            print(f"\n{'=' * 60}")
            print(f"Dataset: {dataset_id}")
            print('=' * 60)

            try:
                result = downloader.download_dataset(
                    dataset_id=dataset_id,
                    sample_size=args.limit,
                    split=args.split
                )
                print(f"  Downloaded: {result['samples_downloaded']} samples")

                if args.transform:
                    transform_result = transformer.transform_dataset(dataset_id)
                    print(f"  Transformed: {transform_result['items_transformed']} items")
                    print(f"  LLARS Type: {transform_result['llars_type']}")

            except Exception as e:
                print(f"  Error: {e}")

        print("\n✓ All downloads complete!")
        return

    # Download specific dataset
    if args.dataset:
        dataset_id = args.dataset

        if dataset_id not in AVAILABLE_DATASETS:
            print(f"Error: Unknown dataset '{dataset_id}'")
            print(f"Available: {', '.join(AVAILABLE_DATASETS.keys())}")
            sys.exit(1)

        print(f"\nDownloading {dataset_id}...")
        print(f"  Limit: {args.limit}")
        print(f"  Split: {args.split}")

        try:
            result = downloader.download_dataset(
                dataset_id=dataset_id,
                sample_size=args.limit,
                split=args.split
            )
            print(f"\n✓ Downloaded: {result['samples_downloaded']} samples")
            print(f"  Output: {result['output_path']}")

            if args.transform:
                print("\nTransforming to LLARS format...")
                transform_result = transformer.transform_dataset(dataset_id)
                print(f"✓ Transformed: {transform_result['items_transformed']} items")
                print(f"  LLARS Type: {transform_result['llars_type']}")
                print(f"  Output: {transform_result['output_path']}")

        except Exception as e:
            print(f"\nError: {e}")
            sys.exit(1)

        return

    # No action specified
    parser.print_help()


if __name__ == '__main__':
    main()
