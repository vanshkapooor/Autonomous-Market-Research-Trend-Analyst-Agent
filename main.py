import json
import logging
import sys
from datetime import datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from config.config import (
    CRAWL_INTERVAL_HOURS,
    WEEKLY_REPORT_DAY,
    WEEKLY_REPORT_HOUR,
    TARGET_URLS,
)
from modules.data_collector   import DataCollector
from modules.llm_analyzer     import (
    analyze_trends,
    batch_sentiment,
    batch_competitor_monitor,
    detect_opportunities_risks,
    generate_recommendations,
    generate_weekly_report,
)
from modules.memento_analyzer import MementoAnalyzer
from modules.sheets_manager   import SheetsManager
from modules.slack_alerter    import (
    alert_new_trends,
    alert_sentiment_spike,
    alert_competitor_activity,
    alert_opportunity_or_risk,
    send_weekly_digest,
)

# ─── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("logs/agent.log"),
    ],
)
logger = logging.getLogger("main")


# ─── Singletons ───────────────────────────────────────────────────────────────
collector = DataCollector()
memento   = MementoAnalyzer()
sheets    = SheetsManager()


# ─── Core pipeline ────────────────────────────────────────────────────────────

def run_research_pipeline():
    """
    Full market research cycle:
    1. Collect → 2. Analyse → 3. Compare → 4. Store → 5. Alert
    """
    run_id = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    logger.info(f"=== Pipeline run {run_id} started ===")

    # 1. Data collection
    articles = collector.collect_all()
    if not articles:
        logger.warning("No articles collected — aborting run")
        return
    sheets.save_raw_articles(articles)

    # 2. LLM analysis
    trends_data     = analyze_trends(articles)
    sentiments      = batch_sentiment(articles)
    competitor_data = batch_competitor_monitor(articles)
    opp_risks       = detect_opportunities_risks(articles)

    # 3. Save to Google Sheets
    sheets.save_trends(trends_data)
    sheets.save_sentiments(sentiments)
    sheets.save_competitors(competitor_data)
    sheets.save_opportunities_risks(opp_risks)

    # 4. Historical comparison via Memento
    historical_trends = sheets.get_recent_trends(limit=100)
    evolution = memento.compare_trends(
        current_trends=trends_data.get("trends", []),
        historical_sheets_data=historical_trends,
    )
    logger.info(
        f"Trend evolution — new: {len(evolution['new_trends'])}, "
        f"recurring: {len(evolution['recurring_trends'])}, "
        f"declining: {len(evolution['declining_trends'])}"
    )

    # 5. Slack alerts
    alert_new_trends(evolution["new_trends"])
    for s in sentiments:
        alert_sentiment_spike(s)
    alert_competitor_activity(competitor_data)
    alert_opportunity_or_risk(opp_risks)

    logger.info(f"=== Pipeline run {run_id} completed ===")
    return {
        "run_id": run_id,
        "articles": len(articles),
        "trends":   len(trends_data.get("trends", [])),
        "new_trends": len(evolution["new_trends"]),
    }


def run_weekly_report():
    logger.info("=== Weekly report job started ===")

    historical_trends    = sheets.get_recent_trends(limit=50)
    historical_sentiment = sheets.get_recent_sentiments(limit=50)

    if not historical_trends:
        logger.warning("No trend data found — skipping weekly report")
        return

    scores = [float(s.get("Score", 0)) for s in historical_sentiment if s.get("Score") != ""]
    avg_score = sum(scores) / len(scores) if scores else 0

    context = {
        "week_ending": datetime.utcnow().strftime("%Y-%m-%d"),
        "total_trends_tracked": len(historical_trends),
        "top_trends": historical_trends[-10:],
        "avg_sentiment_score": round(avg_score, 3),
        "sentiment_records": len(historical_sentiment),
    }

    recommendations = generate_recommendations(
        trends={"trends": historical_trends[-10:]},
        sentiment_summary=f"Average sentiment score over past week: {avg_score:.2f}",
        opp_risks={},
    )
    context["recommendations"] = recommendations

    report_md = generate_weekly_report(context)
    sheets.save_weekly_report(report_md)
    send_weekly_digest(report_md)

    logger.info("=== Weekly report distributed ===")


# ─── Scheduler ────────────────────────────────────────────────────────────────

def start_scheduler():
    scheduler = BlockingScheduler(timezone="Asia/Kolkata")

    # Research pipeline every N hours
    scheduler.add_job(
        run_research_pipeline,
        trigger=IntervalTrigger(hours=CRAWL_INTERVAL_HOURS),
        id="research_pipeline",
        name="Market Research Pipeline",
        replace_existing=True,
    )

    # Weekly report
    scheduler.add_job(
        run_weekly_report,
        trigger=CronTrigger(
            day_of_week=WEEKLY_REPORT_DAY[:3],  # 'monday' → 'mon'
            hour=WEEKLY_REPORT_HOUR,
            minute=0,
        ),
        id="weekly_report",
        name="Weekly Executive Report",
        replace_existing=True,
    )

    logger.info(
        f"Scheduler started — pipeline every {CRAWL_INTERVAL_HOURS}h, "
        f"weekly report on {WEEKLY_REPORT_DAY}s at {WEEKLY_REPORT_HOUR:02d}:00 IST"
    )
    scheduler.start()


# ─── CLI entry point ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous Market Research Agent")
    parser.add_argument(
        "command",
        choices=["run", "weekly", "schedule"],
        help=(
            "run      — single pipeline execution\n"
            "weekly   — generate weekly report now\n"
            "schedule — start the background scheduler"
        ),
    )
    args = parser.parse_args()

    if args.command == "run":
        result = run_research_pipeline()
        print(json.dumps(result, indent=2))

    elif args.command == "weekly":
        run_weekly_report()

    elif args.command == "schedule":
        start_scheduler()
