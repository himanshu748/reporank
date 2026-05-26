You are working on a project called **RepoRank** — an Open Source Impact &
Funding Readiness Agent built for the "Pirates of the Coral-bean" hackathon
by WeMakeDevs.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHAT REPORANK IS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

RepoRank answers one question for open source maintainers:
"How much real-world impact does my project actually have — and what
funding do I qualify for?"

The core idea: most maintainers see GitHub stars but miss the full picture —
npm/PyPI downloads, HackerNews buzz, Open Collective funding status.
RepoRank cross-joins all of these in a single Coral SQL query, feeds the
aggregated data to Qwen2.5-72B-Instruct via HuggingFace Inference API,
and produces:

  1. An impact score (0–100)
  2. A 2–3 sentence plain-English narrative of the project's real-world reach
  3. A one-sentence funding pitch the maintainer can paste into grant applications
  4. A list of grants and sponsor programs they qualify for
  5. Strengths and improvement gaps
  6. A verdict tag: Thriving / Growing / Promising / Hidden Gem / Needs Attention

Output is rendered as a shareable "Impact Card" — a dark-themed web UI with
an animated SVG score ring, stat grid, and a copy-to-clipboard pitch button.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AI LAYER — HUGGINGFACE + QWEN2.5-72B
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Model     : Qwen/Qwen2.5-72B-Instruct
Provider  : HuggingFace Inference API (serverless, no GPU setup needed)
Endpoint  : https://api-inference.huggingface.co/v1/chat/completions
Auth      : Bearer token via HF_TOKEN env var
Format    : OpenAI-compatible (messages array, choices[0].message.content)
Temp      : 0.2 (low — we need consistent JSON output, not creativity)
Max tokens: 1024

The request is a two-message chat:
  - system: instructs the model to return ONLY raw JSON, no markdown fences
  - user:   passes the full raw_signals dict as JSON and specifies exact keys

The model MUST return a single JSON object with these exact keys:
  narrative, funding_pitch, top_grants (list), verdict,
  impact_score (int 0-100), strengths (list), gaps (list)

The response parser in hf_client.py:
  1. Takes choices[0].message.content
  2. Strips ```json ... ``` fences if Qwen adds them despite instructions
  3. Calls json.loads() on the clean string
  4. Returns the parsed dict — no fallback, raises on malformed JSON

Why Qwen2.5-72B specifically:
  - Strong instruction following for JSON-only output
  - Excellent at synthesising structured multi-source data into coherent narrative
  - HuggingFace Inference API has a free tier suitable for demo/hackathon use
  - Consistent with the rest of Himanshu's project stack across challenges

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
WHY CORAL IS THE STAR
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Coral is a SQL-over-APIs engine. Instead of writing separate API clients for
GitHub, PyPI, HackerNews, and Open Collective and stitching results together
in Python, RepoRank fires a single cross-source SQL JOIN via the Coral CLI:

  SELECT  g.full_name,
          g.stargazers_count,
          g.forks_count,
          g.open_issues_count,
          p.last_month_downloads   AS monthly_downloads,
          h.mention_count          AS hn_mentions_6mo,
          h.top_score              AS hn_top_score,
          oc.total_amount_received,
          oc.contributors_count
  FROM    github.repos                  g
  JOIN    pypi.packages                 p   ON  p.name = '<pkg>'
  JOIN    (
            SELECT COUNT(*) AS mention_count, MAX(score) AS top_score
            FROM   hackernews.stories
            WHERE  title LIKE '%<pkg>%'
              AND  time > NOW() - INTERVAL '180 days'
          )                             h   ON  1 = 1
  LEFT JOIN opencollective.collectives  oc  ON  oc.github_url LIKE '%<owner>%'
  WHERE   g.full_name = '<owner>/<repo>'

This one query replaces 4 separate async HTTP calls and 100+ lines of
data-wrangling code. The result rows are passed directly to Qwen as JSON.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TECH STACK
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Language    : Python 3.11+
  Backend     : FastAPI + uvicorn
  Data layer  : Coral CLI — all queries via subprocess `coral query --format json`
  AI layer    : HuggingFace Inference API — Qwen/Qwen2.5-72B-Instruct
                Called via httpx.AsyncClient (OpenAI-compatible chat endpoint)
  Frontend    : Vanilla HTML/CSS/JS, single file, no build step
  Fonts       : Syne (display) + Space Mono (mono) via Google Fonts
  Env vars    : HF_TOKEN (required), GITHUB_TOKEN (optional)
                Coral reads its own auth from ~/.coral/ after `coral source add`

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FILE STRUCTURE & WHAT EACH FILE DOES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

reporank/
├── main.py
│     FastAPI app. Serves GET / → static/index.html.
│     POST /analyze: accepts { repo, ecosystem } → returns full analysis JSON.
│     GET /health → { "status": "sailing" }
│
├── coral_client.py
│     Wraps `coral query --format json <sql>` as a Python subprocess call.
│     query(sql) → list[dict]. query_one(sql) → dict | None.
│     Raises RuntimeError with install instructions if `coral` binary not found.
│     Timeout: 30s per query.
│
├── hf_client.py                          ← THE AI LAYER
│     Async function: generate_impact_report(data: dict) → dict
│     - Reads HF_TOKEN from env (also checks HUGGINGFACE_TOKEN as fallback)
│     - POSTs to HF_API_URL with Qwen2.5-72B-Instruct model
│     - System prompt: JSON-only, no fences, no preamble
│     - User prompt: passes raw_signals as json.dumps(data, indent=2),
│       specifies exact output schema with field descriptions and rules
│     - Parses choices[0].message.content, strips fences, json.loads()
│     - Returns dict with: narrative, funding_pitch, top_grants, verdict,
│       impact_score, strengths, gaps
│     - Uses temperature=0.2 and stream=False
│
├── agent/
│   ├── __init__.py    (empty)
│   └── orchestrator.py
│         class RepoRankAgent — async run(repo, ecosystem) → dict
│
│         Step 1: _fetch_github(full_name)
│                 → coral query on github.repos (stars, forks, issues, desc)
│         Step 2: _fetch_pypi(pkg) | _fetch_npm(pkg)
│                 → coral query on pypi.packages or npm.packages
│                   (version, monthly/weekly downloads, summary)
│         Step 3: _fetch_hn(keyword)
│                 → coral aggregate on hackernews.stories
│                   (mention_count, top_score, last_mention in last 180 days)
│         Step 4: _fetch_opencollective(owner)
│                 → coral query on opencollective.collectives (custom source)
│                   (total_amount_received, contributors_count, balance)
│         Step 5: _cross_source_query(repo, pkg, ecosystem)
│                 → the big 4-source JOIN — the Coral demo centerpiece
│         Step 6: Assembles raw dict:
│                 { repo, ecosystem, github, package_registry,
│                   community_buzz, funding, cross_source }
│         Step 7: await hf_client.generate_impact_report(raw) → analysis dict
│         Step 8: returns { repo, raw_signals, analysis }
│         (imported as: import hf_client as llm)
│
├── sources/
│   └── opencollective.yaml
│         Custom Coral source spec — bounty submission for $100 cash prize.
│         Wraps Open Collective public GraphQL API (no auth needed).
│         Tables: opencollective.collectives, opencollective.contributors
│         Fields use dot-path syntax to map GraphQL response to SQL columns.
│         Install: coral source add --spec sources/opencollective.yaml
│
├── static/
│   └── index.html
│         Dark-themed single-page Impact Card UI.
│         Colours: bg #0a0a0f, accent green #7fff6e, cyan #3de8ff, pink #ff6eab
│         Components: logo with pulsing dot, h1 gradient text, repo input +
│         ecosystem dropdown + Analyze button, CSS spinner status line,
│         Impact Card (verdict badge, SVG score ring with stroke-dashoffset
│         animation, narrative, 6-stat grid, funding pitch + copy button,
│         grant tags, strengths/gaps grid, collapsible Coral SQL panel)
│         Footer: "Powered by Qwen2.5-72B via HuggingFace"
│
├── requirements.txt
│     fastapi==0.115.0, uvicorn[standard]==0.30.6,
│     httpx==0.27.2, pydantic==2.8.2,
│     python-dotenv==1.0.1, huggingface-hub==0.23.4
│
├── .env.example
│     HF_TOKEN=hf_...        ← required, get from huggingface.co/settings/tokens
│     GITHUB_TOKEN=ghp_...   ← optional, raises Coral GitHub rate limits
│
└── README.md

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DATA FLOW (end to end)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  User types "tiangolo/fastapi" + selects "Python" → clicks Analyze
       ↓
  POST /analyze { repo: "tiangolo/fastapi", ecosystem: "python" }
       ↓
  RepoRankAgent.run("tiangolo/fastapi", "python")
       ↓
  5 Coral CLI subprocess calls (coral query --format json)
    · github.repos WHERE full_name = 'tiangolo/fastapi'
    · pypi.packages WHERE name = 'fastapi'
    · hackernews.stories aggregate for 'fastapi' last 180 days
    · opencollective.collectives WHERE github_url LIKE '%tiangolo%'
    · Cross-source JOIN of all 4 in one query
       ↓
  raw_signals dict assembled
       ↓
  hf_client.generate_impact_report(raw_signals)
    → POST to https://api-inference.huggingface.co/v1/chat/completions
    → model: Qwen/Qwen2.5-72B-Instruct
    → temperature: 0.2, max_tokens: 1024
    → parse choices[0].message.content → json.loads()
       ↓
  FastAPI returns { repo, raw_signals, analysis }
       ↓
  Frontend renders Impact Card + animates SVG ring

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
RUNNING THE PROJECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  brew install withcoral/tap/coral
  coral source add github
  coral source add pypi          # or: coral source add npm
  coral source add --spec sources/opencollective.yaml

  pip install -r requirements.txt
  cp .env.example .env
  # Add HF_TOKEN from https://huggingface.co/settings/tokens

  python main.py
  # → http://localhost:8000

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
IMPORTANT CONSTRAINTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  - AI model is ALWAYS Qwen/Qwen2.5-72B-Instruct via HuggingFace.
    Do NOT switch to Claude, GPT, or any other model.
  - Do NOT add ANTHROPIC_API_KEY anywhere — this project uses HF_TOKEN only.
  - The HF endpoint is OpenAI-compatible. Do NOT use the legacy
    api-inference.huggingface.co/models/<model> endpoint.
  - The Qwen system prompt MUST say "respond with raw JSON only, no fences".
    Qwen occasionally adds ```json despite instructions — hf_client.py
    handles this by stripping fences before json.loads().
  - temperature must stay at 0.2. Higher values cause malformed JSON output.
  - Do NOT use any ORM or database. All data comes from Coral only.
  - Do NOT add npm/node dependencies. Pure Python backend.
  - Frontend stays as a single index.html file — no React, no bundler.
  - The cross-source JOIN in orchestrator.py is the demo centrepiece.
    Never replace it with sequential individual queries — the JOIN is the point.
  - Coral SQL strings use single quotes for string literals.
    Be careful with f-strings and apostrophes in repo/package names.
