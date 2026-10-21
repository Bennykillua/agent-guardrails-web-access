# cap_test.py
import os
import sys

from fetch_tool import StopRun, fetch, run

run.budget = float("inf")  # let the key cap end this test, not the run budget
run.max_calls = 200
run.key_floor = float(sys.argv[1]) if len(sys.argv) > 1 else 0

base = os.environ["STAGING_BASE"]
for i in range(200):
    try:
        page = fetch(f"{base}/index.html?cap={i}")
        print(f"{i:>3} ok    cost={page['cost']}  key_left={page['key_left']}")
    except StopRun as e:
        print(f"{i:>3} STOP  {e}")
        break