import sys
import subprocess

test_files = [
    "tests/test_jarvis_investigation_workspace.py",
    "tests/test_jarvis_intelligence_operations.py",
    "tests/test_jarvis.py"
]

print("Starting regression tests...")
all_passed = True
for tf in test_files:
    print(f"\n--- Running {tf} ---")
    cmd = [sys.executable, "-m", "pytest", tf, "-q", "-W", "ignore"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)
    if res.returncode != 0:
        all_passed = False
        print(f"FAILED: {tf}")
    else:
        print(f"PASSED: {tf}")

print(f"\nFinal Regression Result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
sys.exit(0 if all_passed else 1)
