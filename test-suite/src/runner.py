import time
import docker
import logging

from model import Test

logger = logging.getLogger(__name__)

class TestRunner:
    def __init__(self):
        self.client = docker.from_env()

    def run_test(self, test: Test) -> tuple[str, float]:
        start_time = time.time()
        try:
            container = self.client.containers.create(
                image=test.container_image,
                command=test.command,
                detach=True,
            )
            short_container_id = container.id[:12]
            logger.info(f"Created container {short_container_id} for test '{test.name}'")
            container.start()
            container.wait(timeout=30)
            container.remove(force=True)
        except Exception as e:
            logger.error(f"Error occurred while running test: {e}")

        duration_ms = (time.time() - start_time) * 1000
        return short_container_id, duration_ms