import json
import os

from model import Test, TestType

class TestLoader:
    @staticmethod
    def load_tests(test_file: str) -> list[Test]:
        tests = []
        with open(test_file, "r") as f:
            data = json.load(f)

        for item in data:
            test = Test(
                id=item["id"],
                name=item["name"],
                category=item["category"],
                test_type=TestType(item["test_type"]),
                container_image=item["container_image"],
                command=item["command"]
            )
            tests.append(test)

        return tests