# header_check.py
"""which custom headers reach the site, in each fetch mode?"""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()

SENT = {"From": "agents@example.com", "X-Agent-Contact": "agents@example.com"}
MODES = {"plain": {}, "mode=auto": {"mode": "auto"}, "js_render": {"js_render": "true"}}

for name, extra in MODES.items():
    r = requests.get(
        "https://api.zenrows.com/v1/",
        params={"apikey": os.environ["ZENROWS_API_KEY"], "url": "https://httpbin.org/headers",
                "custom_headers": "true", **extra},
        headers=SENT,
        timeout=180,
    )
    text = r.text
    seen = json.loads(text[text.find("{"): text.rfind("}") + 1]).get("headers", {})
    arrived = {h: seen.get(h) for h in SENT}
    print(f"{name:<10} status={r.status_code} cost={r.headers.get('X-Request-Cost')} arrived={arrived}")