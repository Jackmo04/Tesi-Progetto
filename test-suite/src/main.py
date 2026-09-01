import asyncio
import argparse
import logging
import signal

from collector import TelemetryCollector
from evaluator import Evaluator
from loader import TestLoader
from runner import TestRunner
from model import TestResult
from metrics import PerformanceMonitor
from exporter import Exporter

parser = argparse.ArgumentParser(description="Run security tests")
parser.add_argument("-i", "--test-file", required=True, help="JSON file containing the test cases", type=str)
parser.add_argument("-f", "--falco-logs", required=True, help="path to the Falco log file (has to be in JSON format)", type=str)
parser.add_argument("-t", "--tetragon-logs", required=True, help="path to the Tetragon log file (has to be in JSON format)", type=str)
parser.add_argument("-o", "--output-csv", required=False, help="path to the output CSV file", type=str, default="results.csv")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

async def main():
    try:
        args = parser.parse_args()
    except Exception as e:
        logger.error(f"Error parsing arguments: {e}")
        exit(1)
    tests = TestLoader.load_tests(test_file=args.test_file)

    if not tests:
        print("No tests found in the specified file.")
        exit(1)

    try:
        collector = TelemetryCollector(falco_log_path=args.falco_logs, tetragon_log_path=args.tetragon_logs)
    except Exception as e:
        logger.error(f"Error initializing TelemetryCollector: {e}")
        exit(1)
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

            test_id, executed_at, duration_ms = runner.run_test(test)
            try:
                await asyncio.wait_for(shutdown_event.wait(), timeout=2.0) # Allow some time for the production of events to be collected. TODO: tune timing
            except asyncio.TimeoutError:
                pass

            perf_stats = perf_monitor.stop()
            drops_end = PerformanceMonitor.get_drop_metrics()

            matching_events = [event for event in collector.events if event.test_id == test_id]
            results.append(TestResult(
                test=test,
                executed_at=executed_at,
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

    # Temporary printout of results.
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

    evaluator = Evaluator()
    metrics = evaluator.evaluate(results)
    print("\nEvaluation Metrics:")
    for tool, data in metrics.items():
        print(f"  - {tool.capitalize()}: Recall: {data['Recall']:.2f}, Precision: {data['Precision']:.2f}, Avg Latency: {data['Avg_Latency_ms']:.2f} ms")

    try:
        Exporter.export_to_csv(results, metrics, filename=args.output_csv)
        logger.info(f"Results exported to {args.output_csv}")
    except Exception as e:
        logger.error(f"Error exporting results to CSV: {e}")
        exit(1)

if __name__ == "__main__":
    asyncio.run(main())