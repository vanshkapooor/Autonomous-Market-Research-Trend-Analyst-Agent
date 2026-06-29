# 📡 Autonomous Market Research & Trend Analyst

> An end-to-end AI-powered market intelligence system that autonomously crawls the web, analyses trends, monitors competitors, detects opportunities and risks, and delivers real-time alerts — all without human intervention.

---

## 📌 Project Overview

The Autonomous Market Research & Trend Analyst is a fully functional agentic AI pipeline built in Python that automates the entire process of gathering, analysing, and distributing business intelligence from across the web. The system uses Firecrawl to continuously crawl over the industry websites, passes the collected content through a series of specialised LLM modules powered by Groq, stores all results in Google Sheets, compares findings against historical data via the Memento TimeTravel API, and delivers real-time alerts to Slack — all on a fully automated schedule.

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    APScheduler (Cron)                           │
│       Every 6 h → Pipeline  |  Monday 08:00 → Weekly Report    │
└────────────────────────┬────────────────────────────────────────┘
                         │
          ┌──────────────▼──────────────┐
          │       DataCollector         │
          │      (Firecrawl API)        │
          │  Crawls blogs, news, forums │
          └──────────────┬──────────────┘
                         │ articles[]
          ┌──────────────▼──────────────┐
          │       LLM Analyzer          │  ← Groq (Llama 4 Scout)
          │  • Trend Analysis           │
          │  • Sentiment Analysis       │
          │  • Competitor Monitoring    │
          │  • Opportunity/Risk Detect  │
          │  • Strategic Recommendations│
          └──────┬───────────┬──────────┘
                 │           │
   ┌─────────────▼──┐   ┌───▼──────────────┐
   │ SheetsManager  │   │ MementoAnalyzer  │
   │ (Google Sheets)│   │ (Historical diff)│
   │  RawData       │   └──────────────────┘
   │  Trends        │
   │  Sentiment     │
   │  Competitors   │
   │  Opportunities │
   │  WeeklyReport  │
   └────────────────┘
                 │
          ┌──────▼──────────┐
          │  SlackAlerter   │
          │  • Trend alerts │
          │  • Sentiment ↑↓ │
          │  • Competitor ⚠ │
          │  • Weekly digest│
          └─────────────────┘
```

---

## 📁 Project Structure

```
market_analyst/
├── main.py                     # Orchestrator + CLI + scheduler
├── dashboard.py                # Streamlit monitoring UI
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variable template
├── config/
│   ├── config.py               # Central configuration constants
│   └── service_account.json    # Google service account key (not committed)
├── modules/
│   ├── data_collector.py       # Firecrawl web crawling integration
│   ├── llm_analyzer.py         # All 6 Groq LLM analysis modules
│   ├── sheets_manager.py       # Google Sheets read/write operations
│   ├── slack_alerter.py        # Slack webhook alert functions
│   └── memento_analyzer.py     # Memento TimeTravel historical comparison
└── logs/
    └── agent.log               # Persistent pipeline execution log
```

---

## ⚙️ Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| LLM | Groq API (Llama 4 Scout) |
| Web Scraping | Firecrawl API |
| Storage | Google Sheets (gspread) |
| Authentication | Google OAuth2 Service Account |
| Alerts | Slack Incoming Webhooks |
| Historical Data | Memento TimeTravel API |
| Scheduling | APScheduler |
| Dashboard | Streamlit |

---

## 🚀 Setup Guide

### 1. Clone and Install

```bash
git clone <your-repo-url>
cd market_analyst
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

### 2. Create the logs folder

```bash
mkdir logs
```

### 3. Configure Environment Variables

```bash
copy .env.example .env
```

Edit `.env` with your real credentials:

```env
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
FIRECRAWL_API_KEY=fc-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
GOOGLE_SERVICE_ACCOUNT_FILE=config/service_account.json
SPREADSHEET_ID=your_google_sheet_id_here
```

| Variable | Where to get it |
|---|---|
| `GROQ_API_KEY` | https://console.groq.com → API Keys |
| `FIRECRAWL_API_KEY` | https://www.firecrawl.dev → Dashboard |
| `SLACK_WEBHOOK_URL` | Slack App → Incoming Webhooks |
| `SPREADSHEET_ID` | Google Sheets URL between `/d/` and `/edit` |
| `GOOGLE_SERVICE_ACCOUNT_FILE` | Path to downloaded JSON key file |

### 4. Google Cloud Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Google Sheets API** and **Google Drive API**
3. Go to **IAM & Admin → Service Accounts → Create**
4. Download the JSON key → save as `config/service_account.json`
5. Open your Google Sheet → **Share** → paste the service account email → set role to **Editor**

### 5. Configure Target URLs

Edit `config/config.py` and update the `TARGET_URLS` list with websites relevant to your industry:

```python
TARGET_URLS = [
    "https://techcrunch.com",
    "https://venturebeat.com",
    "https://www.theverge.com",
    # Add your own sources here
]
```

---

## ▶️ Running the Agent

### Single pipeline run (test)
```bash
python main.py run
```

### Generate weekly report immediately
```bash
python main.py weekly
```

### Start continuous background scheduler
```bash
python main.py schedule
```

### Launch Streamlit dashboard
```bash
streamlit run dashboard.py
```

---

## 📊 Dashboard Features

The Streamlit dashboard at `http://localhost:8501` includes:

| Tab | What it shows |
|---|---|
| 📈 Trends | Detected trend cards with confidence scores, keyword badges, and bar chart |
| 💬 Sentiment | Score over time chart, sentiment distribution, per-article sentiment cards |
| 🕵️ Competitors | Most active competitors chart, filterable activity log with source links |
| 🔍 Opps & Risks | Side-by-side opportunities and risks with impact and likelihood badges |
| 📰 Raw Articles | Searchable table of all crawled articles with timestamps and URLs |
| 📋 Weekly Reports | Full executive report viewer with date selector and markdown download |

**Sidebar controls:**
- Time window filter (Last 7 / 14 / 30 days / All time)
- Manual refresh button
- Run pipeline directly from dashboard

---

## 🔔 Slack Alert Types

| Alert | Trigger Condition |
|---|---|
| 📈 New Trends Detected | Trends not seen in historical Sheets data |
| 🚀 Positive Sentiment Spike | Sentiment score > +0.7 |
| ⚠️ Negative Sentiment Alert | Sentiment score < -0.6 |
| 🕵️ Competitor Activity | Competitor signal with `impact_level == "high"` |
| 🔍 Strategic Alert | Opportunity or risk with high impact/severity |
| 📊 Weekly Digest | Every Monday at 08:00 IST |

---

## 🗂️ Google Sheets Structure

The agent auto-creates all six tabs on first run:

| Tab | Contents |
|---|---|
| `RawData` | Every crawled article with URL, title, author, tags, summary |
| `Trends` | LLM-detected trends with confidence scores and keywords |
| `Sentiment` | Per-article sentiment scores, themes, and summaries |
| `Competitors` | Competitor activities with impact level and source URL |
| `Opportunities` | Business opportunities and risks with severity ratings |
| `WeeklyReport` | Full markdown executive report saved by week |

---

## 🔁 Scheduler Jobs

| Job | Schedule | Function |
|---|---|---|
| Research Pipeline | Every 6 hours | Crawl → Analyse → Store → Alert |
| Weekly Report | Monday 08:00 IST | Generate → Save → Slack |

Change intervals in `config/config.py`:
```python
CRAWL_INTERVAL_HOURS = 6
WEEKLY_REPORT_DAY    = "monday"
WEEKLY_REPORT_HOUR   = 8
```

---

## 📦 Dependencies

```
python-dotenv    # Load .env variables
requests         # HTTP client for API calls
groq             # Groq LLM SDK
firecrawl-py     # Firecrawl web scraping client
gspread          # Google Sheets interface
google-auth      # Google OAuth2 service account auth
APScheduler      # Background job scheduling
pandas           # Data processing for dashboard
numpy            # Numerical operations
streamlit        # Dashboard UI framework
```

---

## 🧠 LLM Modules (Groq)

| Module | Role | Output |
|---|---|---|
| `analyze_trends` | Identifies emerging market trends | `{trends: [...]}` |
| `batch_sentiment` | Scores sentiment per article | Sentiment list |
| `batch_competitor_monitor` | Extracts competitor signals | Competitor list |
| `detect_opportunities_risks` | Finds strategic opps and risks | `{opportunities, risks}` |
| `generate_recommendations` | Produces strategic recommendations | `{recommendations, summary}` |
| `generate_weekly_report` | Writes executive markdown report | Markdown string |

---

## 📈 Results

From a live pipeline run on 29 June 2026:

- **90** articles crawled from 5 industry sources
- **11** market trends detected (e.g. AI Model Advances, Autonomous Vehicles, Digital Wellness)
- **70** articles sentiment analysed — avg score +0.04 (neutral)
- **42** competitor signals tracked (Anthropic, OpenAI, Google, Meta, Waymo)
- **18** opportunities and risks identified
- **1** weekly executive report generated and delivered to Slack

---

## ⚠️ Limitations

- LLM responses can occasionally return malformed JSON causing empty analysis results
- Firecrawl free tier limits crawl volume per pipeline run
- Memento trend comparison uses name matching rather than semantic similarity
- No deduplication — the same article may be stored across multiple pipeline runs
- Weekly report is truncated to 2800 characters in Slack preview

---

## 🔮 Future Improvements

- Integrate a vector database (Pinecone / ChromaDB) for semantic trend deduplication
- Add Twitter and Reddit APIs for real-time social sentiment coverage
- Implement email delivery of weekly reports via SMTP
- Add dashboard authentication for safe multi-user team deployment
- Build a confidence-weighted trend scoring system for the weekly report
- Add support for custom alert thresholds configurable from the dashboard UI

---

## 📚 Key Learning Outcomes

- Building a complete end-to-end agentic AI pipeline from data ingestion to output delivery
- Prompt engineering LLMs to return consistent structured JSON for programmatic use
- Managing asynchronous API workflows using polling patterns
- Integrating multiple third-party services into a single cohesive system
- Handling Windows-specific environment issues including encoding errors and .env loading
- Defensive programming with type guards and graceful error recovery

---

## ✅ Deliverables Checklist

- [x] `main.py` — Orchestrator, CLI, and scheduler
- [x] `modules/data_collector.py` — Firecrawl integration
- [x] `modules/llm_analyzer.py` — 6 LLM analysis modules
- [x] `modules/sheets_manager.py` — Google Sheets storage
- [x] `modules/slack_alerter.py` — Real-time Slack alerts
- [x] `modules/memento_analyzer.py` — Historical trend comparison
- [x] `config/config.py` — Central configuration
- [x] `dashboard.py` — Streamlit monitoring dashboard
- [x] `requirements.txt` — Python dependencies
- [x] `.env.example` — Environment variable template
- [x] `README.md` — Full project documentation

---

## 👤 Author

**Vansh Kapoor**

---

*Powered by Groq · Firecrawl · Google Sheets · Slack · Memento TimeTravel · Streamlit*
