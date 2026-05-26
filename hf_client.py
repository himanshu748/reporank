import httpx
import json
import os
from typing import Any

# We use the router endpoint since it is fully OpenAI-compatible and resolves reliably
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "Qwen/Qwen2.5-72B-Instruct"


async def generate_impact_report(data: dict[str, Any]) -> dict[str, Any]:
    """
    Feed aggregated repo data to Hugging Face Qwen model and get back:
    - narrative: 2-3 sentence impact summary
    - funding_pitch: 1-sentence pitch for sponsors/grants
    - top_grants: list of matching opportunities
    - verdict: one word tag (e.g. "Thriving", "Growing", "At Risk", "Hidden Gem")
    """

    hf_token = (
        os.environ.get("HF_TOKEN")
        or os.environ.get("HUGGINGFACE_API_KEY")
        or os.environ.get("HUGGINGFACE_TOKEN")
    )
    if not hf_token:
        raise ValueError(
            "Hugging Face API token is missing. Please set HF_TOKEN or HUGGINGFACE_TOKEN in your environment or .env file."
        )

    prompt = f"""
You are an open source impact analyst. Given the following aggregated data about a GitHub repository,
produce a JSON response (no markdown, no preamble) with these exact keys:

{{
  "narrative": "2-3 sentence plain-English summary of the project's real-world impact",
  "funding_pitch": "One punchy sentence a maintainer can paste into a grant or sponsor application",
  "top_grants": ["list", "of", "3-5", "specific", "grant/sponsor programs they likely qualify for"],
  "verdict": "One word: Thriving | Growing | Promising | Hidden Gem | Needs Attention",
  "impact_score": integer 0-100,
  "strengths": ["up to 3 bullet strings"],
  "gaps": ["up to 2 improvement areas"]
}}

Repo data:
{json.dumps(data, indent=2)}
"""

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {hf_token}",
    }

    body = {
        "model": MODEL,
        "max_tokens": 1024,
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant. You must respond with raw JSON only, no markdown fences (like ```json), no preamble, and no explanation.",
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }

    async with httpx.AsyncClient(timeout=45) as client:
        resp = await client.post(HF_API_URL, headers=headers, json=body)
        resp.raise_for_status()

    content = resp.json()["choices"][0]["message"]["content"].strip()

    # Strip possible ```json fences
    if content.startswith("```"):
        lines = content.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    return json.loads(content)
