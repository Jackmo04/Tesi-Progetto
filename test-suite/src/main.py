import asyncio
import argparse
import logging
import signal
from datetime import datetime

from collector import TelemetryCollector
from loader import TestLoader
from runner import TestRunner
from model import TestResult
from metrics import PerformanceMonitor

parser = argparse.ArgumentParser(description="Run security tests")
parser.add_argument("-d", "--test-dir", default=".", help="directory in which to look for test files. (default: .)", type=str)
parser.add_argument("-f", "--falco-log", required=True, help="path to the Falco log file (has to be in JSON format)", type=str)
parser.add_argument("-t", "--tetragon-log", required=True, help="path to the Tetragon log file (has to be in JSON format)", type=str)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def main():
    args = parser.parse_args()
    tests = TestLoader.load_tests(test_directory=args.test_dir)

    if not tests:
        print("No tests found in the specified directory.")
        exit(1)

    collector = TelemetryCollector(falco_log_path=args.falco_log, tetragon_log_path=args.tetragon_log)
    collector_task = asyncio.create_task(collector.start())
    shutdown_event = asyncio.Event()

    def handle_sigint():
        logger.info("SIGINT received, stopping test execution...")
        collector.stop()
        shutdown_event.set()

    loop = asyncio.get_running_loop()
    loop.add_signal_handler(signal.SIGINT, handle_sigint)

    runner = TestRunner()
    perf_monitor = PerformanceMonitor()
    results = []

    logger.info("Starting test execution...")
    try:
        for test in tests:
            logger.info(f"[{test.id}] Preparing test: {test.name} (Category: {test.category}, Type: {test.test_type.value})")

            drops_start = PerformanceMonitor.get_drop_metrics()
            perf_monitor.start()

            test_id, duration_ms = runner.run_test(test)
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=2.0) # Allow some time for the production of events to be collected. TODO: tune timing
            except asyncio.TimeoutError:
                pass

            perf_stats = perf_monitor.stop()
            drops_end = PerformanceMonitor.get_drop_metrics()

            matching_events = [event for event in collector.events if event.test_id == test_id]
            results.append(TestResult(
                test=test,
                executed_at=datetime.now(),
                duration_ms=duration_ms,
                events_detected=matching_events,
                performance_stats=perf_stats,
                falco_drops=drops_end["falco"] - drops_start["falco"],
                tetragon_drops=drops_end["tetragon"] - drops_start["tetragon"]
            ))

            if shutdown_event.is_set():
                break
    finally:
        collector.stop()
        await collector_task
    logger.info("Finished test execution.")

    # Temporary printout of results. TODO: implement Evaluator and CSV output.
    print("\nTest Results:")
    for result in results:
        print(f"Test: {result.test.name} (Category: {result.test.category}, Type: {result.test.test_type.value})")
        print(f"Executed at: {result.executed_at}, Duration: {result.duration_ms:.2f} ms")
        print(f"Events Detected: {len(result.events_detected)}")
        for event in result.events_detected:
            print(f"  - Source: {event.source}, Rule: {event.rule_name}, Timestamp: {event.timestamp}")
        print(f"Performance and Dropped Events: ")
        falco_perf = result.performance_stats.get('falco_monitor', {})
        tetragon_perf = result.performance_stats.get('tetragon_monitor', {})
        print(f"  - Falco: CPU Avg: {falco_perf.get('cpu_avg', 0.0):.2f}%, RAM Max: {falco_perf.get('ram_max', 0.0):.2f} MB, Drops: {result.falco_drops}")
        print(f"  - Tetragon: CPU Avg: {tetragon_perf.get('cpu_avg', 0.0):.2f}%, RAM Max: {tetragon_perf.get('ram_max', 0.0):.2f} MB, Drops: {result.tetragon_drops}")
        print("-" * 40)

if __name__ == "__main__":
    asyncio.run(main())