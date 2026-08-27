import asyncio
import json
import logging
from datetime import datetime

from model import SecurityEvent

logger = logging.getLogger(__name__)

class TelemetryCollector:
    def __init__(self, falco_log_path: str, tetragon_log_path: str):
        self.falco_log_path = falco_log_path
        self.tetragon_log_path = tetragon_log_path
        self.events: list[SecurityEvent] = []
        self._running = False

    async def start(self):
        self._running = True
        await asyncio.gather(
            self._collect_falco_events(),
            self._collect_tetragon_events()
        )

    def stop(self):
        self._running = False

    async def _collect_falco_events(self):
        try:
            with open(self.falco_log_path, "r") as f:
                f.seek(0, 2)
                while self._running:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.05)
                        continue
                    event_data = json.loads(line)
                    output_fields = event_data.get("output_fields", {})
                    container_id = output_fields.get("container.id", "")

                    if container_id and container_id != "host":
                        event = SecurityEvent(
                            source="falco",
                            timestamp=datetime.fromisoformat(event_data["time"]),
                            test_id=container_id[:12].lower(), # Normalize the container ID
                            rule_name=event_data.get("rule", "Unknown"),
                            raw_event=event_data
                        )
                        self.events.append(event)
        except Exception as e:
            logger.error(f"Error while collecting Falco events: {e}")

    async def _collect_tetragon_events(self):
        try:
            with open(self.tetragon_log_path, "r") as f:
                f.seek(0, 2)
                while self._running:
                    line = f.readline()
                    if not line:
                        await asyncio.sleep(0.05)
                        continue
                    event_data = json.loads(line)
                    process = (
                        event_data.get("process_kprobe", {}).get("process", {}) or
                        event_data.get("process_exec", {}).get("process", {}) or
                        event_data.get("process_tracepoint", {}).get("process", {})
                    )
                    container_id = process.get("docker", "")

                    if container_id and container_id != "host":
                        rule = (event_data.get("process_kprobe", {}).get("function_name") or process.get("binary", "Unknown"))
                        timestamp_str = event_data.get("start_time")
                        event = SecurityEvent(
                            source="tetragon",
                            timestamp=datetime.fromisoformat(timestamp_str) if timestamp_str else None,
                            test_id=container_id[:12].lower(), # Normalize the container ID
                            rule_name=rule,
                            raw_event=event_data
                        )
                        self.events.append(event)
        except Exception as e:
            logger.error(f"Error while collecting Tetragon events: {e}")