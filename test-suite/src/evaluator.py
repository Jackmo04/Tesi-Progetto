import statistics
import logging
from model import TestResult, TestType

logger = logging.getLogger(__name__)

class Evaluator:
    @staticmethod
    def evaluate(results: list[TestResult]) -> dict:
        metrics = {
            "falco": {"TP": 0, "FP": 0, "TN": 0, "FN": 0, "latencies": []},
            "tetragon": {"TP": 0, "FP": 0, "TN": 0, "FN": 0, "latencies": []}
        }

        for result in results:
            falco_events = [e for e in result.events_detected if e.source == "falco"]
            tetragon_events = [e for e in result.events_detected if e.source == "tetragon"]

            Evaluator._update_matrix(metrics["falco"], result, falco_events)
            Evaluator._update_matrix(metrics["tetragon"], result, tetragon_events)

        Evaluator._calculate_derived(metrics["falco"])
        Evaluator._calculate_derived(metrics["tetragon"])

        return metrics

    @staticmethod
    def _update_matrix(tool_metrics: dict, result: TestResult, events: list):
        is_malicious = result.test.test_type == TestType.MALICIOUS
        detected = len(events) > 0

        if is_malicious and detected:
            tool_metrics["TP"] += 1
            # Detection Latency
            first_event = min(events, key=lambda e: e.timestamp)
            if first_event.timestamp and result.executed_at:
                try:
                    latency = (first_event.timestamp - result.executed_at).total_seconds() * 1000
                    if latency > 0:
                        tool_metrics["latencies"].append(latency)
                except TypeError as e:
                    logger.warning(f"Error calculating detection latency: {e}")
        elif is_malicious and not detected:
            tool_metrics["FN"] += 1
        elif not is_malicious and detected:
            tool_metrics["FP"] += 1
        elif not is_malicious and not detected:
            tool_metrics["TN"] += 1

    @staticmethod
    def _calculate_derived(tool_metrics: dict):
        tp = tool_metrics["TP"]
        fp = tool_metrics["FP"]
        fn = tool_metrics["FN"]

        tool_metrics["Recall"] = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        tool_metrics["Precision"] = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        tool_metrics["Avg_Latency_ms"] = statistics.mean(tool_metrics["latencies"]) if tool_metrics["latencies"] else 0.0