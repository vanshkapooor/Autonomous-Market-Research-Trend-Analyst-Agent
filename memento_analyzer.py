import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from urllib.parse import quote

import requests

from config.config import MEMENTO_API_BASE, HISTORICAL_DAYS_BACK

logger = logging.getLogger(__name__)


class MementoAnalyzer:
    """
    Uses the Memento TimeTravel API (http://timetravel.mementoweb.org)
    to retrieve archived snapshots of URLs and compare historical
    vs. current content.
    """

    def __init__(self):
        self.base = MEMENTO_API_BASE

    # ─── Public API ──────────────────────────────────────────────────────────

    def get_historical_snapshot(self, url: str, days_back: int = HISTORICAL_DAYS_BACK) -> Optional[Dict]:
        """Fetch the closest archived snapshot for `url` from N days ago."""
        target_dt = datetime.utcnow() - timedelta(days=days_back)
        timestamp = target_dt.strftime("%Y%m%d%H%M%S")
        api_url = f"{self.base}/{timestamp}/{quote(url, safe='')}"

        try:
            resp = requests.get(api_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            return self._parse_memento_response(data, url)
        except requests.HTTPError as e:
            logger.warning(f"Memento returned {e.response.status_code} for {url}")
            return None
        except Exception as exc:
            logger.error(f"Memento fetch error for {url}: {exc}")
            return None

    def compare_trends(
        self,
        current_trends: List[Dict],
        historical_sheets_data: List[Dict],
    ) -> Dict:
        """
        Compare current LLM-detected trends against historically stored trends
        in Google Sheets to surface new, declining, and recurring patterns.
        """
        current_names   = {t.get("name", "").lower() for t in current_trends}
        historical_names= {r.get("Trend Name", "").lower() for r in historical_sheets_data}

        new_trends       = [t for t in current_trends if t.get("name", "").lower() not in historical_names]
        recurring_trends = [t for t in current_trends if t.get("name", "").lower() in historical_names]
        declining_trends = [
            {"name": r.get("Trend Name"), "last_seen": r.get("Date")}
            for r in historical_sheets_data
            if r.get("Trend Name", "").lower() not in current_names
        ]

        return {
            "new_trends":       new_trends,
            "recurring_trends": recurring_trends,
            "declining_trends": declining_trends[:10],
            "analysis_date":    datetime.utcnow().isoformat(),
            "history_window_days": HISTORICAL_DAYS_BACK,
        }

    def fetch_snapshots_for_urls(self, urls: List[str], days_back: int = HISTORICAL_DAYS_BACK) -> List[Dict]:
        """Batch-fetch historical snapshots for a list of URLs."""
        results = []
        for url in urls:
            snapshot = self.get_historical_snapshot(url, days_back=days_back)
            if snapshot:
                results.append(snapshot)
        logger.info(f"Fetched {len(results)}/{len(urls)} Memento snapshots")
        return results

    # ─── Internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _parse_memento_response(data: Dict, original_url: str) -> Dict:
        """Extract the most useful fields from a Memento API JSON response."""
        mementos = data.get("mementos", {})
        closest  = mementos.get("closest", {})
        uri_list = closest.get("uri", [])
        archive_url = uri_list[0] if isinstance(uri_list, list) and uri_list else ""
        dt_str      = closest.get("datetime", [""])[0] if isinstance(closest.get("datetime"), list) else closest.get("datetime", "")

        return {
            "original_url": original_url,
            "archive_url":  archive_url,
            "archived_at":  dt_str,
            "total_mementos": data.get("timemap", {}).get("total", 0),
        }
