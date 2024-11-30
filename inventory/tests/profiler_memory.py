from memory_profiler import profile
import pytest

@profile
def run_memory_profiling():
    """
    Runs pytest while profiling memory usage for the tests.
    """
    pytest.main(["-v", "test_app.py"])

if __name__ == "__main__":
    run_memory_profiling()
