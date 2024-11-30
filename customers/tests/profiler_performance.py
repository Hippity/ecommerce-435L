import cProfile
from pstats import Stats
import pytest

def profile_all_tests():
    """
    Profiles all test functions in the test suite using cProfile.
    """
    profiler = cProfile.Profile()

    # Enable profiling
    profiler.enable()

    # Run all test functions
    pytest.main(["-v", "test_app.py"])

    # Disable profiling and save the results
    profiler.disable()
    with open("all_tests_profiling_results.txt", "w") as f:
        stats = Stats(profiler, stream=f)
        stats.strip_dirs()
        stats.sort_stats("cumulative")
        stats.print_stats()

    print("Profiling data saved to 'all_tests_profiling_results.txt'.")

if __name__ == "__main__":
    profile_all_tests()
