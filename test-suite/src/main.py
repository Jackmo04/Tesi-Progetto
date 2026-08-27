import asyncio
import argparse
import logging
from datetime import datetime

from collector import TelemetryCollector
from loader import TestLoader
from runner import TestRunner
from model import TestResult

parser = argparse.ArgumentParser(description="Run security tests")
parser.add_argument("-d", "--test-dir", default=".", help="directory in which to look for test files. (default: .)", type=str)
parser.add_argument("-f", "--falco-log", required=True, help="path to the Falco log file (has to be in JSON format)", type=str)
parser.add_argument("-t", "--tetragon-log", required=True, help="path to the Tetragon log file (has to be in JSON format)", type=str)

logger = logging.getLogger(__name__)

async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    args = parser.parse_args()
    tests = TestLoader.load_tests(test_directory=args.test_dir)

    if not tests:
        print("No tests found in the specified directory.")
        exit(1)

    collector = TelemetryCollector(falco_log_path=args.falco_log, tetragon_log_path=args.tetragon_log)
    collector_task = asyncio.create_task(collector.start())

    runner = TestRunner()
    results = []

    logger.info("Starting test execution...")
    for test in tests:
        logger.info(f"Running test: {test.name} (Category: {test.category}, Type: {test.test_type.value})")

        test_id, duration_ms = runner.run_test(test)
        await asyncio.sleep(2.0)  # Allow some time for the production of events to be collected. TODO: tune timing

        matching_events = [event for event in collector.events if event.test_id == test_id]
        results.append(TestResult(
            test=test,
            executed_at=datetime.now(),
            duration_ms=duration_ms,
            events_detected=matching_events
        ))

    collector.stop()
    logger.info("All tests executed.")

if __name__ == "__main__":
    asyncio.run(main())