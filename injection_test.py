# injection_test.py
import os

import fetch_tool
from agent import ask
from fetch_tool import fetch

url = f"{os.environ['STAGING_BASE']}/injection.html"
print("review flags:", fetch(url)["flags"])  # what the guard sees in the page

out = ask(f"What does the Trail Stove cost? Use {url}.")
print("answer:", out["answer"])
print("output check problems:", out["problems"] or "none")
print("urls fetched this run:", sorted(fetch_tool.run.fetched))