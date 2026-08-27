import json
import os

from model import Test, TestType

class TestLoader:
    @staticmethod
    def load_tests(test_directory: str) -> list[Test]:
        tests = []
        for filename in os.listdir(test_directory):
            if filename.endswith(".json"):
                file_path = os.path.join(test_directory, filename)
                with open(file_path, "r") as f:
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