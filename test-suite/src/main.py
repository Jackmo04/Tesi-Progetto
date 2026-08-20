from loader import TestLoader
from runner import TestRunner
import argparse

parser = argparse.ArgumentParser(description="Run security tests")
parser.add_argument("-d", "--test-dir", default=".", help="directory in which to look for test files", type=str)

if __name__ == "__main__":
    args = parser.parse_args()
    loader = TestLoader(test_directory=args.test_dir)
    tests = loader.load_tests()

    if not tests:
        print("No tests found in the specified directory.")
        exit(1)

    runner = TestRunner()
    for test in tests:
        print(f"[*] Running test: {test.name} (Category: {test.category}, Type: {test.test_type.value})")
        test_id, duration_ms = runner.run_test(test)
        print(f"[+] Test executed in {duration_ms:.2f} ms, Test ID: {test_id}", end="\n\n")

    print("[+] All tests executed.") # TODO: print results to file