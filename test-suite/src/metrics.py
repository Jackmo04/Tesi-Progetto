import docker
import requests
import threading
import time
import logging

logger = logging.getLogger(__name__)

PROMETHEUS_URL = "http://localhost:9090/api/v1/query"

class PerformanceMonitor:
    def __init__(self, containers: list[str] = None):
        self.containers = containers or ["falco_monitor", "tetragon_monitor"]
        self.client = docker.from_env()
        self.metrics_data = {}
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        self._stop_event.clear()
        self.metrics_data = {c: {"cpu": [], "ram": []} for c in self.containers}
        self._thread = threading.Thread(target=self._monitor)
        self._thread.start()

    def stop(self) -> dict:
        self._stop_event.set()
        if self._thread:
            self._thread.join()
        return self._calculate_averages()

    def _monitor(self):
        while not self._stop_event.is_set():
            for container_name in self.containers:
                try:
                    container = self.client.containers.get(container_name)
                    stats = container.stats(stream=False)
                    mem_usage = stats['memory_stats']['usage'] / (1024 * 1024)
                    cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - stats['precpu_stats']['cpu_usage']['total_usage']
                    system_delta = stats['cpu_stats']['system_cpu_usage'] - stats['precpu_stats'].get('system_cpu_usage', 0)
                    cpu_percent = (cpu_delta / system_delta) * 100.0 * stats['cpu_stats']['online_cpus'] if system_delta > 0 else 0.0
                    
                    self.metrics_data[container_name]["cpu"].append(cpu_percent)
                    self.metrics_data[container_name]["ram"].append(mem_usage)
                except Exception:
                    logger.warning(f"Failed to get stats for container '{container_name}'. It may not be running.")
            time.sleep(0.5)

    def _calculate_averages(self) -> dict:
        results = {}
        for c in self.containers:
            cpu_list = self.metrics_data.get(c, {}).get("cpu", [])
            ram_list = self.metrics_data.get(c, {}).get("ram", [])
            results[c] = {
                "cpu_avg": sum(cpu_list) / len(cpu_list) if cpu_list else 0.0,
                "ram_max": max(ram_list) if ram_list else 0.0
            }
        return results

    @staticmethod
    def get_drop_metrics() -> dict:
        def query(q: str) -> float:
            try:
                res = requests.get(PROMETHEUS_URL, params={'query': q}).json()
                data = res.get('data', {}).get('result', [])
                return int(data[0]['value'][1]) if data else 0
            except Exception:
                return 0.0
        return {
            "tetragon": query('sum(tetragon_observer_ringbuf_events_lost_total)'),
            "falco": query('sum(falcosecurity_scap_n_drops_total)')
        }