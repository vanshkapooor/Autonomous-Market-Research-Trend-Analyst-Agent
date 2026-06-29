import logging
from datetime import datetime
from typing import Any, Dict, List

import gspread
from google.oauth2.service_account import Credentials

from config.config import (
    GOOGLE_SERVICE_ACCOUNT_FILE,
    SPREADSHEET_ID,
    SHEET_RAW_DATA,
    SHEET_TRENDS,
    SHEET_SENTIMENT,
    SHEET_COMPETITORS,
    SHEET_OPPORTUNITIES,
    SHEET_WEEKLY_REPORT,
)

logger = logging.getLogger(__name__)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SHEET_HEADERS = {
    SHEET_RAW_DATA: [
        "Collected At", "URL", "Title", "Author", "Tags", "Summary", "Source URL",
    ],
    SHEET_TRENDS: [
        "Date", "Trend Name", "Description", "Confidence", "Keywords", "Relevant URLs",
    ],
    SHEET_SENTIMENT: [
        "Date", "URL", "Title", "Sentiment", "Score", "Confidence",
        "Key Themes", "Summary",
    ],
    SHEET_COMPETITORS: [
        "Date", "Competitor", "Activity Type", "Description",
        "Impact Level", "Source URL",
    ],
    SHEET_OPPORTUNITIES: [
        "Date", "Type", "Title", "Description", "Impact/Severity",
        "Likelihood", "Timeframe",
    ],
    SHEET_WEEKLY_REPORT: [
        "Week Of", "Report",
    ],
}


class SheetsManager:
    def __init__(self):
        creds = Credentials.from_service_account_file(
            GOOGLE_SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        self.client = gspread.authorize(creds)
        self.spreadsheet = self.client.open_by_key(SPREADSHEET_ID)
        self._ensure_sheets()

    # ─── Sheet setup ─────────────────────────────────────────────────────────

    def _ensure_sheets(self):
        existing = {ws.title for ws in self.spreadsheet.worksheets()}
        for name, headers in SHEET_HEADERS.items():
            if name not in existing:
                ws = self.spreadsheet.add_worksheet(title=name, rows=1000, cols=len(headers))
                ws.append_row(headers)
                logger.info(f"Created sheet: {name}")

    def _get_ws(self, name: str):
        return self.spreadsheet.worksheet(name)

    def _append(self, sheet_name: str, rows: List[List[Any]]):
        ws = self._get_ws(sheet_name)
        ws.append_rows(rows, value_input_option="USER_ENTERED")

    # ─── Public write methods ─────────────────────────────────────────────────

    def save_raw_articles(self, articles: List[Dict]):
        rows = [
            [
                a.get("collected_at", ""),
                a.get("url", ""),
                a.get("title", ""),
                a.get("author", ""),
                ", ".join(a.get("tags", [])),
                a.get("summary", ""),
                a.get("source_url", ""),
            ]
            for a in articles
        ]
        self._append(SHEET_RAW_DATA, rows)
        logger.info(f"Saved {len(rows)} raw articles to Sheets")

    def save_trends(self, trends_data: Dict):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        # Guard against non-dict input
        if not isinstance(trends_data, dict):
            logger.warning("save_trends received non-dict; skipping")
            return
        rows = [
            [
                now,
                t.get("name", ""),
                t.get("description", ""),
                t.get("confidence", ""),
                ", ".join(t.get("keywords", [])),
                ", ".join(t.get("relevant_urls", [])),
            ]
            for t in trends_data.get("trends", [])
        ]
        self._append(SHEET_TRENDS, rows)
        logger.info(f"Saved {len(rows)} trends")

    def save_sentiments(self, sentiments: List[Dict]):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        rows = [
            [
                now,
                s.get("url", ""),
                s.get("title", ""),
                s.get("overall_sentiment", ""),
                s.get("score", ""),
                s.get("confidence", ""),
                ", ".join(s.get("key_themes", [])),
                s.get("summary", ""),
            ]
            for s in sentiments
        ]
        self._append(SHEET_SENTIMENT, rows)
        logger.info(f"Saved {len(rows)} sentiment records")

    def save_competitors(self, competitor_batches: List[Dict]):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        rows = []
        for batch in competitor_batches:
            src = batch.get("source_url", "")
            for c in batch.get("competitors_mentioned", []):
                rows.append([
                    now,
                    c.get("name", ""),
                    c.get("activity_type", ""),
                    c.get("description", ""),
                    c.get("impact_level", ""),
                    src,
                ])
        self._append(SHEET_COMPETITORS, rows)
        logger.info(f"Saved {len(rows)} competitor records")

    def save_opportunities_risks(self, opp_risks: Dict):
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M")
        rows = []
        for o in opp_risks.get("opportunities", []):
            rows.append([
                now, "Opportunity",
                o.get("title", ""), o.get("description", ""),
                o.get("potential_impact", ""), "", o.get("timeframe", ""),
            ])
        for r in opp_risks.get("risks", []):
            rows.append([
                now, "Risk",
                r.get("title", ""), r.get("description", ""),
                r.get("severity", ""), r.get("likelihood", ""), "",
            ])
        self._append(SHEET_OPPORTUNITIES, rows)
        logger.info(f"Saved {len(rows)} opportunity/risk records")

    def save_weekly_report(self, report_markdown: str):
        week_of = datetime.utcnow().strftime("%Y-%m-%d")
        ws = self._get_ws(SHEET_WEEKLY_REPORT)
        ws.append_row([week_of, report_markdown])
        logger.info("Weekly report saved to Sheets")

    # ─── Read helpers (for Memento historical comparison) ─────────────────────

    def get_recent_trends(self, limit: int = 50) -> List[Dict]:
        ws = self._get_ws(SHEET_TRENDS)
        records = ws.get_all_records()
        return records[-limit:] if len(records) > limit else records

    def get_recent_sentiments(self, limit: int = 50) -> List[Dict]:
        ws = self._get_ws(SHEET_SENTIMENT)
        records = ws.get_all_records()
        return records[-limit:] if len(records) > limit else records
