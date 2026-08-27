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
            logger.info(f"[{test.id}] Created container with ID: {short_container_id}")
            container.start()
            logger.info(f"[{test.id}] Started container. Running test...")
            container.wait(timeout=30)
            container.remove(force=True)
            logger.info(f"[{test.id}] Test completed and container removed")
        except Exception as e:
            logger.error(f"[{test.id}] Error occurred while running test: {e}")

        duration_ms = (time.time() - start_time) * 1000
        return short_container_id, duration_ms