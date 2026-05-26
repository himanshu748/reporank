import coral_client as coral
import hf_client as llm
from typing import Any


class RepoRankAgent:
    """
    Orchestrates Coral SQL queries across GitHub + npm/PyPI + HackerNews
    then passes aggregated data to Hugging Face for narrative + grant matching.
    """

    async def run(self, repo: str, ecosystem: str) -> dict[str, Any]:
        owner, name = repo.split("/", 1)

        # ── 1. GitHub signal ──────────────────────────────────────────────
        github_data = self._fetch_github(repo)

        # ── 2. Package download signal ────────────────────────────────────
        pkg_data = {}
        if ecosystem == "python":
            pkg_data = self._fetch_pypi(name)
        elif ecosystem == "npm":
            pkg_data = self._fetch_npm(name)

        # ── 3. HackerNews / community buzz ───────────────────────────────
        hn_data = self._fetch_hn(name)

        # ── 4. Open Collective / funding eligibility ──────────────────────
        # Try collective with repository name first, fallback to owner name
        funding_data = self._fetch_opencollective(name)
        if not funding_data or not funding_data.get("name"):
            funding_data = self._fetch_opencollective(owner)

        # ── 5. Cross-source summary query ────────────────────────────────
        # This is the "one map for all seas" query Coral shines at.
        cross_data = self._cross_source_query(repo, name, ecosystem)

        # ── 6. Assemble raw signal dict ───────────────────────────────────
        raw = {
            "repo": repo,
            "ecosystem": ecosystem,
            "github": github_data,
            "package_registry": pkg_data,
            "community_buzz": hn_data,
            "funding": funding_data,
            "cross_source": cross_data,
        }

        # ── 7. Hugging Face narrative + grant matching ────────────────────
        analysis = await llm.generate_impact_report(raw)

        return {
            "repo": repo,
            "raw_signals": raw,
            "analysis": analysis,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Coral query helpers
    # ──────────────────────────────────────────────────────────────────────

    def _fetch_github(self, full_name: str) -> dict:
        owner, repo = full_name.split("/", 1)
        sql = f"""
            SELECT full_name, description, language, stargazers_count,
                   forks_count, open_issues_count, pushed_at,
                   watchers_count, topics
            FROM   github.repos_get
            WHERE  owner = '{owner}' AND repo = '{repo}'
            LIMIT  1
        """
        return coral.query_one(sql) or {}

    def _fetch_pypi(self, package: str) -> dict:
        sql = f"""
            SELECT name, version, last_month_downloads,
                   last_week_downloads, summary
            FROM   pypi.packages
            WHERE  name = '{package}'
            LIMIT  1
        """
        return coral.query_one(sql) or {}

    def _fetch_npm(self, package: str) -> dict:
        sql = f"""
            SELECT name, version, weekly_downloads,
                   monthly_downloads, description
            FROM   npm.packages
            WHERE  name = '{package}'
            LIMIT  1
        """
        return coral.query_one(sql) or {}

    def _fetch_hn(self, keyword: str) -> dict:
        # HackerNews source - search stories using query filter
        sql = f"""
            SELECT COUNT(*) AS mention_count,
                   MAX(score)  AS top_score,
                   MAX(time)   AS last_mention
            FROM   hackernews.stories
            WHERE  query = '{keyword}'
              AND  time  >  NOW() - INTERVAL '180 days'
        """
        return coral.query_one(sql) or {"mention_count": 0}

    def _fetch_opencollective(self, slug: str) -> dict:
        # Custom source spec — see sources/opencollective.yaml
        sql = f"""
            SELECT slug, name, currency,
                   total_amount_received, contributors_count,
                   github_url
            FROM   opencollective.collectives
            WHERE  slug = '{slug}'
            LIMIT  1
        """
        return coral.query_one(sql) or {}

    def _cross_source_query(self, full_name: str, pkg_name: str, ecosystem: str) -> list:
        """
        The star of the show — cross-source JOIN that powers the impact score.
        Joins GitHub stats with package registry downloads and HN buzz.
        """
        owner, repo = full_name.split("/", 1)
        pkg_table = "pypi.packages" if ecosystem == "python" else "npm.packages"
        dl_col    = "last_month_downloads" if ecosystem == "python" else "monthly_downloads"

        sql = f"""
            SELECT  g.full_name,
                    g.stargazers_count,
                    g.forks_count,
                    g.open_issues_count,
                    p.{dl_col}         AS monthly_downloads,
                    h.mention_count    AS hn_mentions_6mo,
                    h.top_score        AS hn_top_score
            FROM    github.repos_get    g
            JOIN    {pkg_table}         p  ON  p.name = '{pkg_name}'
            JOIN    (
                        SELECT COUNT(*) AS mention_count, MAX(score) AS top_score
                        FROM   hackernews.stories
                        WHERE  query = '{pkg_name}'
                          AND  time  > NOW() - INTERVAL '180 days'
                    )                   h  ON  1 = 1
            WHERE   g.owner = '{owner}' AND g.repo = '{repo}'
        """
        return coral.query(sql)
