import time
from datetime import datetime, timezone
import docker
import logging

from model import Test

logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.client = docker.from_env()

    def run_test(self, test: Test) -> tuple[str, float]:
        cmd = test.command
        if test.shell_wrap:
            cmd = f"/bin/sh -c '{cmd}'"

        start_time = time.time()
        try:
            container = self.client.containers.create(
                image=test.container_image,
                command=cmd,
                detach=True,
            )
            short_container_id = container.id[:12]
            logger.info(f"[{test.id}] Created container with ID: {short_container_id}")
            container.start()
            container.reload()
            executed_at = self._docker_time_to_datetime(container.attrs['State']['StartedAt'])
            logger.info(f"[{test.id}] Started container. Running test...")
            container.wait(timeout=60)
            container.remove(force=True)
            logger.info(f"[{test.id}] Test completed and container removed")
        except Exception as e:
            logger.error(f"[{test.id}] Error occurred while running test: {e}")

        duration_ms = (time.time() - start_time) * 1000
        return short_container_id, executed_at, duration_ms

    def _docker_time_to_datetime(self, docker_time_str: str) -> datetime:
        try:
            cut_nanoseconds = docker_time_str[:-4]
            dt = datetime.strptime(cut_nanoseconds, "%Y-%m-%dT%H:%M:%S.%f")
            return dt.replace(tzinfo=timezone.utc)
        except ValueError as e:
            logger.error(f"Error parsing Docker time string '{docker_time_str}': {e}")
            return None
