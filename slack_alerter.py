import json
import logging
from datetime import datetime
from typing import Any, Dict, List

import requests

from config.config import (
    SLACK_WEBHOOK_URL,
    NEGATIVE_ALERT_THRESHOLD,
    POSITIVE_SPIKE_THRESHOLD,
)

logger = logging.getLogger(__name__)


def _post(payload: Dict[str, Any]):
    resp = requests.post(
        SLACK_WEBHOOK_URL,
        data=json.dumps(payload),
        headers={"Content-Type": "application/json"},
        timeout=10,
    )
    if resp.status_code != 200:
        logger.error(f"Slack error {resp.status_code}: {resp.text}")
    else:
        logger.info("Slack message sent")


# ─── Alert types ─────────────────────────────────────────────────────────────

def alert_new_trends(trends: List[Dict]):
    if not trends:
        return
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "📈 New Market Trends Detected"},
        },
        {"type": "divider"},
    ]
    for t in trends[:5]:   # cap to avoid Slack block limits
        conf = t.get("confidence", 0)
        conf_bar = "🟢" if conf > 0.7 else ("🟡" if conf > 0.4 else "🔴")
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{t.get('name', 'Unknown')}* {conf_bar} _{conf:.0%} confidence_\n"
                    f"{t.get('description', '')}\n"
                    f"Keywords: `{'`, `'.join(t.get('keywords', [])[:5])}`"
                ),
            },
        })
    blocks.append({
        "type": "context",
        "elements": [{"type": "mrkdwn", "text": f"🕐 {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}"}],
    })
    _post({"blocks": blocks})


def alert_sentiment_spike(sentiment: Dict):
    score = sentiment.get("score", 0)
    if score > POSITIVE_SPIKE_THRESHOLD:
        emoji, label = "🚀", "Positive Spike"
    elif score < NEGATIVE_ALERT_THRESHOLD:
        emoji, label = "⚠️", "Negative Sentiment Alert"
    else:
        return   # within normal range

    _post({
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"{emoji} Sentiment Alert: {label}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f"*Score:* `{score:.2f}`  |  *Confidence:* `{sentiment.get('confidence', 0):.0%}`\n"
                        f"*Article:* <{sentiment.get('url', '#')}|{sentiment.get('title', 'View')}>\n"
                        f"*Summary:* {sentiment.get('summary', '')[:300]}"
                    ),
                },
            },
        ]
    })


def alert_competitor_activity(competitor_batches: List[Dict]):
    high_impact = []
    for batch in competitor_batches:
        for c in batch.get("competitors_mentioned", []):
            if c.get("impact_level") == "high":
                c["_source"] = batch.get("source_url", "")
                high_impact.append(c)

    if not high_impact:
        return

    text = "\n".join(
        f"• *{c['name']}* — {c['activity_type'].replace('_', ' ').title()}: {c['description'][:120]}"
        for c in high_impact[:5]
    )
    _post({
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🕵️ High-Impact Competitor Activity"},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": text}},
        ]
    })


def alert_opportunity_or_risk(opp_risks: Dict):
    high_opps  = [o for o in opp_risks.get("opportunities", []) if o.get("potential_impact") == "high"]
    high_risks = [r for r in opp_risks.get("risks", [])          if r.get("severity") == "high"]

    if not (high_opps or high_risks):
        return

    sections = []
    for o in high_opps[:3]:
        sections.append(f"✅ *Opportunity:* {o['title']}\n_{o['description'][:150]}_")
    for r in high_risks[:3]:
        sections.append(f"🚨 *Risk:* {r['title']}\n_{r['description'][:150]}_")

    _post({
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🔍 Strategic Alerts"},
            },
            {"type": "section", "text": {"type": "mrkdwn", "text": "\n\n".join(sections)}},
        ]
    })


def send_weekly_digest(report_markdown: str):
    """Post the full weekly report as a Slack message (truncated for readability)."""
    preview = report_markdown[:2800]
    _post({
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "📊 Weekly Market Intelligence Report"},
            },
            {"type": "divider"},
            {"type": "section", "text": {"type": "mrkdwn", "text": preview}},
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "Full report saved to Google Sheets → WeeklyReport tab."}
                ],
            },
        ]
    })
