import os
import time
from concurrent.futures import ThreadPoolExecutor

from fetch_tool import fetch

base = os.environ["STAGING_BASE"]
urls = [f"{base}/index.html?burst={i}" for i in range(8)]

t0 = time.monotonic()
with ThreadPoolExecutor(max_workers=8) as pool:
    pages = list(pool.map(fetch, urls))

sent = sorted(p["sent_at"] - t0 for p in pages)
gaps = [round(b - a, 2) for a, b in zip(sent, sent[1:])]
print("sent at (s):", [round(s, 2) for s in sent])
print("smallest gap (s):", min(gaps))