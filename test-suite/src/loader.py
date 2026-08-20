import json
import os

from model import Test, TestType

class TestLoader:
    def __init__(self, test_directory: str):
        self.test_directory = test_directory

    def load_tests(self) -> list[Test]:
        tests = []
        for filename in os.listdir(self.test_directory):
            if filename.endswith(".json"):
                file_path = os.path.join(self.test_directory, filename)
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