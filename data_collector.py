import logging
import time
from datetime import datetime
from typing import List, Dict, Any

import requests

from config.config import (
    FIRECRAWL_API_KEY,
    TARGET_URLS,
    FIRECRAWL_LIMIT,
    FIRECRAWL_MAX_DEPTH,
)

logger = logging.getLogger(__name__)

FIRECRAWL_BASE = "https://api.firecrawl.dev/v1"


class DataCollector:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
            "Content-Type": "application/json",
        }

    # ─── Public API ──────────────────────────────────────────────────────────

    def collect_all(self, urls: List[str] = None) -> List[Dict[str, Any]]:
        """Crawl every target URL and return a flat list of article dicts."""
        urls = urls or TARGET_URLS
        all_articles: List[Dict[str, Any]] = []

        for url in urls:
            logger.info(f"Crawling: {url}")
            try:
                articles = self._crawl_url(url)
                all_articles.extend(articles)
                logger.info(f"  OK {len(articles)} articles from {url}")
            except Exception as exc:
                logger.error(f"  FAILED {url}: {exc}")

        logger.info(f"Total articles collected: {len(all_articles)}")
        return all_articles

    def scrape_single(self, url: str) -> Dict[str, Any]:
        """Scrape a single page and return structured data."""
        payload = {
            "url": url,
            "formats": ["markdown", "extract"],
            "extract": {
                "schema": {
                    "type": "object",
                    "properties": {
                        "title":       {"type": "string"},
                        "summary":     {"type": "string"},
                        "published_at":{"type": "string"},
                        "author":      {"type": "string"},
                        "tags":        {"type": "array", "items": {"type": "string"}},
                    },
                }
            },
        }
        resp = requests.post(
            f"{FIRECRAWL_BASE}/scrape",
            json=payload,
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        return self._normalise(resp.json(), source_url=url)

    # ─── Internals ───────────────────────────────────────────────────────────

    def _crawl_url(self, url: str) -> List[Dict[str, Any]]:
        """Kick off an async crawl job and poll until done."""
        job_id = self._start_crawl_job(url)
        results = self._poll_crawl_job(job_id)
        return [self._normalise(r, source_url=url) for r in results]

    def _start_crawl_job(self, url: str) -> str:
        payload = {
            "url": url,
            "limit": FIRECRAWL_LIMIT,
            "maxDepth": FIRECRAWL_MAX_DEPTH,
            "scrapeOptions": {"formats": ["markdown"]},
        }
        resp = requests.post(
            f"{FIRECRAWL_BASE}/crawl",
            json=payload,
            headers=self.headers,
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def _poll_crawl_job(self, job_id: str, max_wait: int = 120) -> List[Dict]:
        """Poll /crawl/{id} until status is 'completed'."""
        deadline = time.time() + max_wait
        while time.time() < deadline:
            resp = requests.get(
                f"{FIRECRAWL_BASE}/crawl/{job_id}",
                headers=self.headers,
                timeout=15,
            )
            resp.raise_for_status()
            data = resp.json()
            status = data.get("status", "")
            if status == "completed":
                return data.get("data", [])
            if status == "failed":
                raise RuntimeError(f"Crawl job {job_id} failed: {data}")
            time.sleep(5)
        raise TimeoutError(f"Crawl job {job_id} did not complete in {max_wait}s")

    @staticmethod
    def _normalise(raw: Dict, source_url: str = "") -> Dict[str, Any]:
        """Flatten Firecrawl response into a consistent schema."""
        meta     = raw.get("metadata", {})
        extract  = raw.get("extract", {}) or {}
        markdown = raw.get("markdown", "")

        return {
            "url":          raw.get("url") or raw.get("sourceURL") or source_url,
            "title":        extract.get("title") or meta.get("title", "Untitled"),
            "summary":      extract.get("summary", ""),
            "content":      markdown[:4000],   # cap to avoid huge LLM prompts
            "author":       extract.get("author", ""),
            "tags":         extract.get("tags", []),
            "published_at": extract.get("published_at") or meta.get("publishedTime", ""),
            "source_url":   source_url,
            "collected_at": datetime.utcnow().isoformat(),
        }
