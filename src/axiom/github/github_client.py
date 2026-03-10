from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from axiom.models import PullRequestMergeEvent
from axiom.utils.logger import log


class GithubClient:
    def __init__(self, owner: str, repo: str, token: str = "", contributor_wallets_path: str = "data/contributor_wallets.json") -> None:
        self.owner = owner
        self.repo = repo
        self.token = token
        self._seen_urls: set[str] = set()
        self.contributor_wallets = self._load_contributor_wallets(contributor_wallets_path)

    def _load_contributor_wallets(self, path: str) -> dict[str, str]:
        target = Path(path)
        if not target.exists():
            log(f"Contributor wallet mapping not found at '{path}'. PR payouts will be skipped.")
            return {}
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
            return {str(k).strip().lower(): str(v).strip() for k, v in raw.items() if str(v).strip()}
        except json.JSONDecodeError:
            log(f"Invalid contributor wallet mapping JSON at '{path}'. PR payouts will be skipped.")
            return {}

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "axiom-afc-agent",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def recent_merged_prs(self, limit: int = 25) -> list[PullRequestMergeEvent]:
        if not self.owner or not self.repo:
            return self._mock_events()

        query = urlencode({"state": "closed", "sort": "updated", "direction": "desc", "per_page": str(limit)})
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls?{query}"
        req = Request(url, headers=self._headers())
        with urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        events: list[PullRequestMergeEvent] = []
        for pr in data:
            merged_at = pr.get("merged_at")
            if not merged_at:
                continue
            url_key = pr.get("html_url", "")
            if not url_key or url_key in self._seen_urls:
                continue
            self._seen_urls.add(url_key)
            author = pr.get("user", {}).get("login", "unknown")
            payout_address = self.contributor_wallets.get(author.lower(), "")
            if not payout_address:
                log(f"Skipping PR payout for '{author}': no wallet mapping configured.")
                continue
            events.append(
                PullRequestMergeEvent(
                    merged_at=datetime.fromisoformat(merged_at.replace("Z", "+00:00")),
                    author=author,
                    title=pr.get("title", ""),
                    url=url_key,
                    payout_address=payout_address,
                )
            )
        return events

    def _mock_events(self) -> list[PullRequestMergeEvent]:
        # Out-of-the-box demo behavior for local judges.
        now = datetime.now(timezone.utc)
        if getattr(self, "_mock_emitted", False):
            return []
        payout_address = self.contributor_wallets.get("demo-dev", "")
        if not payout_address:
            log("Skipping mock PR payout: add 'demo-dev' in contributor wallet mapping.")
            self._mock_emitted = True
            return []
        self._mock_emitted = True
        return [
            PullRequestMergeEvent(
                merged_at=now,
                author="demo-dev",
                title="Add treasury rebalance logic",
                url="https://example.local/pr/1",
                payout_address=payout_address,
            )
        ]
