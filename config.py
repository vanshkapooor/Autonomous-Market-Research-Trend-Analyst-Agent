import os
from dotenv import load_dotenv

load_dotenv()

# ─── API Keys ────────────────────────────────────────────────────────────────
GROQ_API_KEY        = os.getenv("GROQ_API_KEY", "")
FIRECRAWL_API_KEY   = os.getenv("FIRECRAWL_API_KEY", "")
SLACK_WEBHOOK_URL   = os.getenv("SLACK_WEBHOOK_URL", "")

# ─── Google Sheets ────────────────────────────────────────────────────────────
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "config/service_account.json")
SPREADSHEET_ID              = os.getenv("SPREADSHEET_ID", "")

# Sheet tab names
SHEET_RAW_DATA      = "RawData"
SHEET_TRENDS        = "Trends"
SHEET_SENTIMENT     = "Sentiment"
SHEET_COMPETITORS   = "Competitors"
SHEET_OPPORTUNITIES = "Opportunities"
SHEET_WEEKLY_REPORT = "WeeklyReport"

# ─── LLM (Groq) ──────────────────────────────────────────────────────────────
LLM_MODEL        = "meta-llama/llama-4-scout-17b-16e-instruct"   # Groq-hosted; swap to any available model
LLM_TEMPERATURE  = 0.3
LLM_MAX_TOKENS   = 2048

# ─── Firecrawl ────────────────────────────────────────────────────────────────
# Add/remove URLs for your target industry
TARGET_URLS = [
    "https://techcrunch.com",
    "https://www.theverge.com",
    "https://venturebeat.com",
    "https://www.wired.com/category/business",
    "https://news.ycombinator.com",
]

FIRECRAWL_LIMIT         = 10   # pages per crawl job
FIRECRAWL_MAX_DEPTH     = 2

# ─── Scheduler ────────────────────────────────────────────────────────────────
CRAWL_INTERVAL_HOURS    = 6    # how often to re-crawl
WEEKLY_REPORT_DAY       = "monday"   # weekday for the weekly digest
WEEKLY_REPORT_HOUR      = 8          # 08:00 local time

# ─── Sentiment Thresholds ─────────────────────────────────────────────────────
NEGATIVE_ALERT_THRESHOLD = -0.6   # score below this → Slack alert
POSITIVE_SPIKE_THRESHOLD =  0.7   # score above this → Slack alert

# ─── Memento ─────────────────────────────────────────────────────────────────
MEMENTO_API_BASE = "http://timetravel.mementoweb.org/api/json"
HISTORICAL_DAYS_BACK = 30   # compare current vs. data from N days ago
