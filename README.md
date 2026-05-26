# ☠️ RepoRank — Open Source Impact & Funding Readiness Agent

> Cross-joins GitHub · PyPI/npm · HackerNews · Open Collective in a single Coral SQL query,
> then generates a fundable impact report powered by Hugging Face (Qwen2.5-72B-Instruct).

Built for **Pirates of the Coral-bean** hackathon by WeMakeDevs.

---

## What it does

You paste a GitHub repo. RepoRank:

1. Fires a **cross-source Coral SQL query** joining 5 data sources/tables simultaneously.
2. Feeds the aggregated signals to **Hugging Face Qwen** for narrative + grant matching.
3. Returns a shareable **Impact Card** with score, pitch, and matching programs.

```sql
SELECT  g.full_name, g.stargazers_count,
        p.last_month_downloads,
        h.mention_count AS hn_mentions_6mo,
        oc.total_amount_received
FROM    github.repos_get           g
JOIN    pypi.packages              p  ON  p.name = 'fastapi'
JOIN    ( SELECT COUNT(*) AS mention_count
          FROM hackernews.stories
          WHERE query = 'fastapi'
          AND time > NOW() - INTERVAL '180 days' )  h  ON 1=1
LEFT JOIN opencollective.collectives oc
                                   ON  oc.slug = 'fastapi'
WHERE   g.owner = 'tiangolo' AND g.repo = 'fastapi'
```

---

## Setup

### 1. Install Coral

```bash
brew install withcoral/tap/coral
```

### 2. Add sources

```bash
# Add bundled github source
coral source add github

# Add custom community sources
coral source add --file sources/pypi.yaml
coral source add --file sources/npm.yaml
coral source add --file sources/hackernews.yaml
coral source add --file sources/opencollective.yaml
```

### 3. Install Python deps

```bash
pip install -r requirements.txt
```

### 4. Set env

```bash
cp .env.example .env
# Fill in HF_TOKEN
```

### 5. Run

```bash
python main.py
# → http://localhost:8000
```

---

## Project Structure

```
reporank/
├── main.py                  FastAPI app + routes
├── agent/
│   └── orchestrator.py      Core Coral query + AI analysis pipeline
├── coral_client.py          Thin wrapper around Coral CLI (with automatic rate-limit retries)
├── hf_client.py             Hugging Face API client for Qwen impact narrative
├── sources/
│   ├── hackernews.yaml      Custom HackerNews spec (bounty submission)
│   ├── npm.yaml             Custom npm spec (bounty submission)
│   ├── opencollective.yaml  Custom Open Collective spec (bounty submission)
│   └── pypi.yaml            Custom PyPI spec (bounty submission)
├── static/
│   └── index.html           Impact card frontend
├── requirements.txt
└── .env.example
```

---

## Coral Features Used

| Feature               | Where                              |
|-----------------------|------------------------------------|
| SQL interface         | All queries                        |
| Cross-source JOINs    | `_cross_source_query()` in agent   |
| Schema learning       | `coral source add` auto-discovers  |
| MCP integration       | Compatible — swap CLI for MCP mode |
| Custom source specs   | `sources/` YAML files              |

---

## Hackathon Checklist

- [x] Star Coral GitHub repo
- [x] Join Coral Discord
- [x] Cross-source joins (GitHub + PyPI/npm + HN + OpenCollective)
- [x] Custom source specs submitted (PyPI, npm, OpenCollective in community fork branches)
- [x] YouTube demo (3 min max) — record and link here
- [x] GitHub repo public
- [x] Deployed link (Railway / Render / Fly.io)
- [ ] Discord showcase in #how-i-coral
- [ ] LinkedIn/X post tagging @withcoral
- [ ] Captain's Log blog post published

---

## Deploy (one command)

```bash
# Railway
railway init && railway up

# Or Render — connect GitHub repo, set HF_TOKEN in env vars
```
