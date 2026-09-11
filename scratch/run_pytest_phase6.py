import sys, os
sys.path.insert(0, os.path.abspath("."))
import pytest

if __name__ == "__main__":
    ret = pytest.main(["-v", "-s", "tests/test_jarvis_global_architecture.py"])
    sys.exit(ret)
