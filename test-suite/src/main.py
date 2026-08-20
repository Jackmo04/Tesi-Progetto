if __name__ == "__main__":
    from model import Test, TestType
    from runner import TestRunner

    # Prove
    tests = [
        Test(
            name="Example Test 1",
            test_type=TestType.MALICIOUS,
            command="cat /etc/shadow"
        ),
        Test(
            name="Example Test 2",
            test_type=TestType.BENIGN,
            command="echo 'Hello, World!'"
        )
    ]

    runner = TestRunner()
    for test in tests:
        print(f"Running test: {test}")
        test_id, duration_ms = runner.run_test(test)
        print(f"Test executed in {duration_ms:.2f} ms, Test ID: {test_id}")