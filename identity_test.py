# identity_test.py
from fetch_tool import ALLOWED, fetch

ALLOWED["httpbin.org"] = ["/headers"]  # an echo service, allowed for this test only
print(fetch("https://httpbin.org/headers")["text"])