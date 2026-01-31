#!/usr/bin/env python3
"""
LLARS Heavy Load Test Script

Tests the production server under heavy load:
- Concurrent HTTP API requests
- Multiple simultaneous WebSocket connections
- Sustained load over configurable duration
- Measures response times, throughput, and error rates

Usage:
    python scripts/load_test.py --host localhost --port 8081 --duration 60

For production server:
    ssh llars "cd /var/llars && docker exec llars_flask_service python3 /app/scripts/load_test.py"
"""

import argparse
import concurrent.futures
import json
import random
import statistics
import sys
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

try:
    import socketio
except ImportError:
    print("Installing python-socketio...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "python-socketio[client]", "-q"])
    import socketio


@dataclass
class LoadTestConfig:
    """Configuration for load test"""
    host: str = "localhost"
    port: int = 8081
    duration_seconds: int = 60
    http_concurrent_users: int = 50
    http_requests_per_user: int = 10
    websocket_connections: int = 20
    websocket_messages_per_conn: int = 5
    ramp_up_seconds: int = 5


@dataclass
class TestResults:
    """Results from load test"""
    http_response_times: list = field(default_factory=list)
    http_errors: int = 0
    http_success: int = 0
    http_status_codes: dict = field(default_factory=lambda: defaultdict(int))
    ws_connect_times: list = field(default_factory=list)
    ws_connect_errors: int = 0
    ws_connect_success: int = 0
    ws_message_times: list = field(default_factory=list)
    start_time: float = 0
    end_time: float = 0

    def get_summary(self) -> dict:
        """Generate summary statistics"""
        duration = self.end_time - self.start_time

        http_stats = {}
        if self.http_response_times:
            http_stats = {
                "total_requests": self.http_success + self.http_errors,
                "successful": self.http_success,
                "errors": self.http_errors,
                "error_rate": f"{(self.http_errors / max(1, self.http_success + self.http_errors)) * 100:.2f}%",
                "requests_per_second": f"{self.http_success / max(1, duration):.2f}",
                "response_times_ms": {
                    "min": f"{min(self.http_response_times):.2f}",
                    "max": f"{max(self.http_response_times):.2f}",
                    "avg": f"{statistics.mean(self.http_response_times):.2f}",
                    "median": f"{statistics.median(self.http_response_times):.2f}",
                    "p95": f"{sorted(self.http_response_times)[int(len(self.http_response_times) * 0.95)]:.2f}" if len(self.http_response_times) > 20 else "N/A",
                    "p99": f"{sorted(self.http_response_times)[int(len(self.http_response_times) * 0.99)]:.2f}" if len(self.http_response_times) > 100 else "N/A",
                },
                "status_codes": dict(self.http_status_codes),
            }

        ws_stats = {}
        if self.ws_connect_times:
            ws_stats = {
                "total_connections": self.ws_connect_success + self.ws_connect_errors,
                "successful": self.ws_connect_success,
                "errors": self.ws_connect_errors,
                "connect_times_ms": {
                    "min": f"{min(self.ws_connect_times):.2f}",
                    "max": f"{max(self.ws_connect_times):.2f}",
                    "avg": f"{statistics.mean(self.ws_connect_times):.2f}",
                }
            }

        return {
            "duration_seconds": f"{duration:.2f}",
            "http": http_stats,
            "websocket": ws_stats,
        }


class LoadTester:
    """Heavy load tester for LLARS"""

    # API endpoints to test (mix of light and heavy operations)
    API_ENDPOINTS = [
        ("/api/llm/models/available", "GET"),
        ("/api/scenarios", "GET"),
        ("/api/chatbots", "GET"),
        ("/api/rag/collections", "GET"),
        ("/api/prompts", "GET"),
    ]

    def __init__(self, config: LoadTestConfig):
        self.config = config
        self.base_url = f"http://{config.host}:{config.port}"
        self.results = TestResults()
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def _make_http_request(self, endpoint: str, method: str) -> Optional[float]:
        """Make a single HTTP request and return response time in ms"""
        url = f"{self.base_url}{endpoint}"
        try:
            start = time.perf_counter()
            if method == "GET":
                response = requests.get(url, timeout=30)
            else:
                response = requests.post(url, json={}, timeout=30)
            elapsed_ms = (time.perf_counter() - start) * 1000

            with self._lock:
                self.results.http_response_times.append(elapsed_ms)
                self.results.http_status_codes[response.status_code] += 1
                # 401 is expected (no auth), count as success for load testing
                if response.status_code in (200, 401, 403):
                    self.results.http_success += 1
                else:
                    self.results.http_errors += 1

            return elapsed_ms
        except Exception as e:
            with self._lock:
                self.results.http_errors += 1
            return None

    def _http_user_simulation(self, user_id: int):
        """Simulate a single user making multiple requests"""
        # Ramp up delay
        time.sleep(random.uniform(0, self.config.ramp_up_seconds))

        for _ in range(self.config.http_requests_per_user):
            if self._stop_event.is_set():
                break
            endpoint, method = random.choice(self.API_ENDPOINTS)
            self._make_http_request(endpoint, method)
            # Small delay between requests
            time.sleep(random.uniform(0.1, 0.5))

    def _websocket_test(self, conn_id: int):
        """Test a single WebSocket connection"""
        sio = socketio.Client()
        connected = threading.Event()

        @sio.event
        def connect():
            connected.set()

        try:
            start = time.perf_counter()
            sio.connect(self.base_url, transports=['websocket'], wait_timeout=10)
            elapsed_ms = (time.perf_counter() - start) * 1000

            if connected.wait(timeout=5):
                with self._lock:
                    self.results.ws_connect_times.append(elapsed_ms)
                    self.results.ws_connect_success += 1

                # Keep connection alive for a bit
                time.sleep(random.uniform(1, 3))

                # Send some ping messages
                for _ in range(self.config.websocket_messages_per_conn):
                    if self._stop_event.is_set():
                        break
                    try:
                        start = time.perf_counter()
                        sio.emit('ping', {})
                        elapsed = (time.perf_counter() - start) * 1000
                        with self._lock:
                            self.results.ws_message_times.append(elapsed)
                    except Exception:
                        pass
                    time.sleep(0.5)
            else:
                with self._lock:
                    self.results.ws_connect_errors += 1

        except Exception as e:
            with self._lock:
                self.results.ws_connect_errors += 1
        finally:
            try:
                sio.disconnect()
            except Exception:
                pass

    def run_http_load_test(self):
        """Run HTTP load test with concurrent users"""
        print(f"\n{'='*60}")
        print("HTTP Load Test")
        print(f"{'='*60}")
        print(f"Concurrent users: {self.config.http_concurrent_users}")
        print(f"Requests per user: {self.config.http_requests_per_user}")
        print(f"Endpoints: {len(self.API_ENDPOINTS)}")
        print(f"Ramp-up: {self.config.ramp_up_seconds}s")
        print()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.http_concurrent_users) as executor:
            futures = [
                executor.submit(self._http_user_simulation, i)
                for i in range(self.config.http_concurrent_users)
            ]

            # Progress indicator
            start = time.time()
            while not all(f.done() for f in futures):
                completed = sum(1 for f in futures if f.done())
                elapsed = time.time() - start
                print(f"\r  Progress: {completed}/{len(futures)} users completed, "
                      f"{self.results.http_success + self.results.http_errors} requests, "
                      f"{elapsed:.1f}s elapsed", end="")
                time.sleep(0.5)
            print()

    def run_websocket_load_test(self):
        """Run WebSocket load test with concurrent connections"""
        print(f"\n{'='*60}")
        print("WebSocket Load Test")
        print(f"{'='*60}")
        print(f"Concurrent connections: {self.config.websocket_connections}")
        print(f"Messages per connection: {self.config.websocket_messages_per_conn}")
        print()

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.websocket_connections) as executor:
            futures = [
                executor.submit(self._websocket_test, i)
                for i in range(self.config.websocket_connections)
            ]

            # Progress indicator
            start = time.time()
            while not all(f.done() for f in futures):
                completed = sum(1 for f in futures if f.done())
                elapsed = time.time() - start
                print(f"\r  Progress: {completed}/{len(futures)} connections, "
                      f"{self.results.ws_connect_success} successful, "
                      f"{elapsed:.1f}s elapsed", end="")
                time.sleep(0.5)
            print()

    def run_sustained_load_test(self):
        """Run sustained load over a period of time"""
        print(f"\n{'='*60}")
        print("Sustained Load Test")
        print(f"{'='*60}")
        print(f"Duration: {self.config.duration_seconds}s")
        print(f"Target RPS: ~{self.config.http_concurrent_users * 2}")
        print()

        end_time = time.time() + self.config.duration_seconds
        request_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.config.http_concurrent_users) as executor:
            while time.time() < end_time and not self._stop_event.is_set():
                # Submit batch of requests
                futures = []
                for _ in range(self.config.http_concurrent_users):
                    endpoint, method = random.choice(self.API_ENDPOINTS)
                    futures.append(executor.submit(self._make_http_request, endpoint, method))

                # Wait for batch completion
                concurrent.futures.wait(futures)
                request_count += len(futures)

                remaining = end_time - time.time()
                print(f"\r  Time remaining: {remaining:.0f}s, "
                      f"Requests: {self.results.http_success + self.results.http_errors}, "
                      f"Errors: {self.results.http_errors}", end="")

                # Small delay between batches
                time.sleep(0.1)
        print()

    def run(self, test_type: str = "all"):
        """Run the load test"""
        print(f"\n{'#'*60}")
        print(f"# LLARS Heavy Load Test")
        print(f"# Target: {self.base_url}")
        print(f"{'#'*60}")

        self.results.start_time = time.time()

        try:
            if test_type in ("all", "http"):
                self.run_http_load_test()

            if test_type in ("all", "websocket"):
                self.run_websocket_load_test()

            if test_type in ("all", "sustained"):
                self.run_sustained_load_test()

        except KeyboardInterrupt:
            print("\n\nTest interrupted by user!")
            self._stop_event.set()

        self.results.end_time = time.time()

        # Print results
        print(f"\n{'='*60}")
        print("RESULTS")
        print(f"{'='*60}")

        summary = self.results.get_summary()
        print(json.dumps(summary, indent=2))

        return summary


def main():
    parser = argparse.ArgumentParser(description="LLARS Heavy Load Test")
    parser.add_argument("--host", default="localhost", help="Target host")
    parser.add_argument("--port", type=int, default=8081, help="Target port")
    parser.add_argument("--duration", type=int, default=60, help="Test duration in seconds")
    parser.add_argument("--users", type=int, default=50, help="Concurrent HTTP users")
    parser.add_argument("--requests", type=int, default=10, help="Requests per user")
    parser.add_argument("--ws-connections", type=int, default=20, help="WebSocket connections")
    parser.add_argument("--test", choices=["all", "http", "websocket", "sustained"], default="all",
                        help="Test type to run")
    parser.add_argument("--quick", action="store_true", help="Quick test (reduced load)")

    args = parser.parse_args()

    config = LoadTestConfig(
        host=args.host,
        port=args.port,
        duration_seconds=args.duration,
        http_concurrent_users=args.users if not args.quick else 10,
        http_requests_per_user=args.requests if not args.quick else 5,
        websocket_connections=args.ws_connections if not args.quick else 5,
    )

    tester = LoadTester(config)
    results = tester.run(args.test)

    # Exit with error if too many failures
    if results.get("http", {}).get("errors", 0) > 0.1 * results.get("http", {}).get("total_requests", 1):
        print("\n⚠️  Warning: High error rate detected!")
        sys.exit(1)

    print("\n✅ Load test completed successfully!")


if __name__ == "__main__":
    main()
