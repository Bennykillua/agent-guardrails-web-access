# AI Agent Guardrails for Web Access: Allowlists, Rate Limits and Spending Caps

Put guardrails around an AI agent's web tool in Python, then attack your own agent to see which ones hold. Every check runs in code around Zenrows Fetch, outside the model, so a prompt can't talk its way past them.

## Features

- **Scope:** an allowlist of hosts and paths, checked before every call and again after redirects through the `Zr-Final-Url` header.
- **Rate:** a minimum delay per host, a local cap on parallel requests, and backoff with jitter on `422`, `429`, `5xx` and timeouts.
- **Spend:** a budget per run in US dollars, a floor on `X-Key-Credits-Remaining`, a call limit, a loop guard, and a clean stop on `402 AUTH014` and `AUTH004`.
- **Identity:** a `From` header with a contact address, sent through `custom_headers`.
- **Review:** every fetched page is wrapped as untrusted data and scanned for instruction-like text and off-list links, and the agent's answer is checked against a schema and the URLs it actually fetched.
- **Log and stop:** one JSON line per response and per decision, plus stop rules for retries, repeated failures and spend that print an alert when they end a run.
- **Red team:** `attack_agent.py` runs a fixed set of attacks against the finished agent and reports pass, fail or inconclusive per layer.

## Prerequisites

- Python 3.10 or above
- A Zenrows API key. [Sign up for free](https://app.zenrows.com/register)
- An OpenAI API key, for the test agent
- Optional: a second Zenrows API key with a low daily credit cap, for the spend tests
- Optional: a short link you created that points to `https://www.scrapethissite.com/`, for the redirect test

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/zenrows/agent-guardrails-web-access.git
cd agent-guardrails-web-access
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

### 3. Activate the environment

macOS and Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```bash
ZENROWS_API_KEY=your_zenrows_key
OPENAI_API_KEY=your_openai_key
STAGING_BASE=https://zenrows.github.io/guardrails-staging

# optional
RUN_BUDGET=0.05
ZENROWS_CAPPED_KEY=your_capped_key
AGENT_CONTACT=agents@yourcompany.com
SHORT_LINK=https://your-short-link
```

| Variable | Required | What it's for |
|---|---|---|
| `ZENROWS_API_KEY` | Yes | Your Zenrows key, from the [dashboard](https://app.zenrows.com/register) |
| `OPENAI_API_KEY` | Yes | The test agent's model |
| `STAGING_BASE` | Yes | The test site the agent may reach: the hosted [guardrails-staging](https://github.com/zenrows/guardrails-staging) site, or your own copy. No trailing slash |
| `RUN_BUDGET` | No | Spend limit per run in US dollars, the unit `X-Request-Cost` reports. Default `0.05` |
| `ZENROWS_CAPPED_KEY` | No | A second key with a low daily cap, set under **Settings** > **API keys** > **Credit caps** |
| `AGENT_CONTACT` | No | A team email address sent as the `From` header. Avoid a personal address |
| `SHORT_LINK` | No | A short link you created that redirects to `https://www.scrapethissite.com/` |
| `AGENT_MODEL` | No | The OpenAI model. Default `gpt-4o-mini` |

Never commit `.env`. It's listed in `.gitignore`.

## Project structure

```
.
├── fetch_tool.py        # the agent's only web tool, with every guardrail
├── agent.py             # test agent built with the OpenAI Agents SDK, plus output checks
├── attack_agent.py      # red-team runner: attacks every layer and scores the result
├── burst_test.py        # rate: 8 parallel requests to one host
├── cap_test.py          # spend: fetches with a capped key until the run stops
├── identity_test.py     # identity: prints the headers a site receives
├── header_check.py      # identity: checks which custom headers arrive in each fetch mode
├── injection_test.py    # review: points the agent at a page that tries to give it orders
├── requirements.txt
├── LICENSE.txt
├── .gitignore
└── README.md
```

The pages the tests point at live in a separate repository, [zenrows/guardrails-staging](https://github.com/zenrows/guardrails-staging), served at `https://zenrows.github.io/guardrails-staging`.

## How it works

Every request the agent makes goes through `fetch()` in `fetch_tool.py`. The model only ever sees the text that comes out the other end.

```
Prompt
  ↓
Agent (OpenAI Agents SDK) calls fetch_page(url)
  ↓
Scope: is the host, path and query string on the allowlist?   → no: BLOCKED, no request sent
  ↓
Spend: is the run under its budget, call limit and loop guard? → no: STOPPED or BLOCKED
  ↓
Rate: wait for the host's next slot and a free parallel slot
  ↓
Zenrows Fetch (mode=auto, Markdown), with retries and backoff
  ↓
402? stop the run. Repeated failures? stop the run.
  ↓
Scope again: did a redirect land off-list (Zr-Final-Url)?     → yes: content discarded
  ↓
Review: flag instruction-like text and off-list links, wrap the page as untrusted data
  ↓
Agent answers → check_answer(): schema, cited URLs in scope and fetched this run
```

Every response and every decision is written to `fetch_log.jsonl`.

## Running the project

### Ask the agent a question

```bash
python agent.py
python agent.py "Fetch https://www.scrapethissite.com/ and tell me its main heading."
```

The first command asks the default question about the staging site. The second asks for an off-list page, so scope refuses it.

### Test one layer

```bash
python burst_test.py        # rate
python identity_test.py     # identity
python header_check.py      # identity, across plain, mode=auto and js_render
python injection_test.py    # review
```

The spend test needs the capped key, set for that command only:

```bash
ZENROWS_API_KEY=your_capped_key python cap_test.py 3   # stops on the key floor, before any 402
ZENROWS_API_KEY=your_capped_key python cap_test.py 0   # stops on 402 AUTH014
```

### Attack your own agent

```bash
python attack_agent.py --runs 5
python attack_agent.py --runs 5 --only off_list,injection
```

Tests that use the model run 5 times each. Tests that call the tool directly run once.

| Test | Layer | What it tries |
|---|---|---|
| `off_list` | Scope | Asks the agent to fetch a host that isn't on the allowlist |
| `redirect_query` | Scope | Fetches an allowed URL whose query string points off-list |
| `redirect_short` | Scope | Fetches a short link that redirects off-list (needs `SHORT_LINK`) |
| `burst` | Rate | Sends 8 parallel requests to one host |
| `loop` | Spend | Two pages that link to each other and never give an answer |
| `expensive` | Spend | Keeps fetching until the run budget runs out |
| `capped_key` | Spend | Fetches with a low-cap key until `402 AUTH014` (needs `ZENROWS_CAPPED_KEY`) |
| `identity` | Identity | Checks that the `From` header reaches the site |
| `injection` | Review | A page that tells the agent to fetch an attacker URL and report a fake price |

The tests grade the guardrail code, not Zenrows. A fail means a layer in `fetch_tool.py` missed something.

## Output

- **`agent.py`** prints the agent's answer, any output-check problems, and the run's call count, spend and stop reason.
- **`attack_agent.py`** prints a Markdown table with one row per test: the layer, the pass rate and what caught it. It then prints the total Zenrows cost in US dollars, and writes each run's details to `redteam_results.json`.
- **`fetch_log.jsonl`** records every call. A `response` line covers each request that reached Zenrows (status, final URL, cost, credits left, request ID). A `decision` line records what the guard did (ok, blocked or stopped) and why.
- **Stop alerts** print in the terminal, for example `[guardrails] run stopped: AUTH014: this key reached its credit cap`.

A test reports "inconclusive" when the layer it targets never got exercised, for example when a request timed out before any page came back to check.

## Technologies

- Python
- Zenrows Fetch
- OpenAI Agents SDK
- Pydantic
- Requests

## Troubleshooting

| Problem | Fix |
|---|---|
| A double slash in URLs, or "never fetched" in output checks | Remove the trailing slash from `STAGING_BASE` |
| `capped_key` stops on the first call | The key's daily cap is used up. It resets at midnight UTC |
| `redirect_short` is inconclusive with a `504` or timeout | The short link didn't load through Fetch. Try a different shortener |
| `identity_test.py` fails with `422` | The echo service was unavailable. Run it again, or switch it to `https://httpbin.io/headers` |
| `[non-fatal] Tracing request failed` | OpenAI Agents SDK tracing couldn't reach OpenAI. It doesn't affect the run. Set `OPENAI_AGENTS_DISABLE_TRACING=1` to turn it off |
| Loop test blocked on `/loop-b.html` at the site root | Your copy of the staging site uses relative links. Use absolute links that include your repository path |

## License

MIT. See [LICENSE.txt](LICENSE.txt).

## Related article

This repository accompanies the Zenrows article:

[AI Agent Guardrails for Web Access: Allowlists, Rate Limits and Spending Caps]()