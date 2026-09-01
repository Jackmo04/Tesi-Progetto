import csv
from model import TestResult

class Exporter:
    @staticmethod
    def export_to_csv(results: list[TestResult], summary_metrics: dict, filename: str = "results.csv"):
        with open(filename, mode='w', newline='') as f:
            writer = csv.writer(f)
            
            # RAW DATA
            writer.writerow([
                "Test_ID", "Name", "Category", "Type", "Test_Duration_ms", 
                "Falco_Detected", "Tetragon_Detected",
                "Falco_CPU_Avg(%)", "Falco_RAM_Max(MB)", "Falco_Drops_Delta",
                "Tetragon_CPU_Avg(%)", "Tetragon_RAM_Max(MB)", "Tetragon_Drops_Delta"
            ])
            
            for r in results:
                perf = r.performance_stats or {}
                falco_perf = perf.get("falco_monitor", {})
                tetragon_perf = perf.get("tetragon_monitor", {})
                
                falco_detected = any(e.source == "falco" for e in r.events_detected)
                tetragon_detected = any(e.source == "tetragon" for e in r.events_detected)

                writer.writerow([
                    r.test.id, r.test.name, r.test.category, r.test.test_type.value, round(r.duration_ms, 2),
                    falco_detected, tetragon_detected,
                    round(falco_perf.get("cpu_avg", 0), 2), round(falco_perf.get("ram_max", 0), 2), r.falco_drops,
                    round(tetragon_perf.get("cpu_avg", 0), 2), round(tetragon_perf.get("ram_max", 0), 2), r.tetragon_drops
                ])

            # AGGREGATE METRICS
            writer.writerow([])
            writer.writerow(["--- AGGREGATE METRICS ---"])
            writer.writerow(["Tool", "True_Positives", "False_Positives", "True_Negatives", "False_Negatives", "Recall(TPR)", "Precision", "Avg_Latency_ms"])
            
            for tool in ["falco", "tetragon"]:
                m = summary_metrics[tool]
                writer.writerow([
                    tool.capitalize(), 
                    m["TP"], m["FP"], m["TN"], m["FN"],
                    round(m["Recall"], 4), 
                    round(m["Precision"], 4), 
                    round(m["Avg_Latency_ms"], 2)
                ])