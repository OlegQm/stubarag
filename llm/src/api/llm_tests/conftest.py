import pytest

results = []

@pytest.hookimpl(tryfirst=True)
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Print the final results of the test run, showing the correct/incorrect answers and statistics.
    """
    failed_tests = len([
        result for result in results
        if "invalid" in next(iter(result.values()))
    ])
    no_data_tests = len([
        result for result in results
        if "No data was found" in next(iter(result.values()))
    ])
    total_tests = len(results)
    passed_tests = total_tests - failed_tests
    correct_percentage = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    terminalreporter.write_line("\n\nDetailed results:\n")

    for i, result in enumerate(results):
        terminalreporter.write_line(
            f"\n{i + 1}) Question: " + str(next(iter(result.keys())))
        )
        terminalreporter.write_line(f"{str(next(iter(result.values())))}\n\n")

    terminalreporter.write_line("\nTest results:")
    terminalreporter.write_line(f"  Total tests: {total_tests}")
    terminalreporter.write_line(f"  Passed: {passed_tests}")
    terminalreporter.write_line(f"  Failed: {failed_tests}")
    terminalreporter.write_line(f"  N/A: {no_data_tests}")
    terminalreporter.write_line(f"  Correct answers: {correct_percentage:.2f}%")
