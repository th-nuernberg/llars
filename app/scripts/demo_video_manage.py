#!/usr/bin/env python3
"""
Demo Video Data Manager for IJCAI 2026 (CLI wrapper)

Usage (inside Flask container):
    python3 /app/scripts/demo_video_manage.py seed
    python3 /app/scripts/demo_video_manage.py cleanup
    python3 /app/scripts/demo_video_manage.py reset
    python3 /app/scripts/demo_video_manage.py status
"""

import sys
import os
import json

sys.path.insert(0, '/app')
os.chdir('/app')

import argparse
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')


def cmd_status():
    from main import app
    from services.demo_video_service import get_status
    with app.app_context():
        result = get_status()
        print(json.dumps(result, indent=2, default=str))


def cmd_seed():
    from main import app
    from services.demo_video_service import seed
    with app.app_context():
        result = seed()
        print(json.dumps(result, indent=2, default=str))


def cmd_cleanup():
    from main import app
    from services.demo_video_service import cleanup
    with app.app_context():
        result = cleanup()
        print(json.dumps(result, indent=2, default=str))


def cmd_reset():
    from main import app
    from services.demo_video_service import reset
    with app.app_context():
        result = reset()
        print(json.dumps(result, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Demo Video Data Manager")
    parser.add_argument('command', choices=['seed', 'cleanup', 'reset', 'status'])
    args = parser.parse_args()
    {'seed': cmd_seed, 'cleanup': cmd_cleanup, 'reset': cmd_reset, 'status': cmd_status}[args.command]()


if __name__ == '__main__':
    main()
