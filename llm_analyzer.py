import json
import logging
from typing import Any, Dict, List

from groq import Groq

from config.config import GROQ_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS

logger = logging.getLogger(__name__)

client = Groq(api_key=GROQ_API_KEY)


def _chat(system: str, user: str) -> str:
    """Single-turn Groq call. Returns assistant message text."""
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
    )
    return resp.choices[0].message.content.strip()

def _json_chat(system: str, user: str) -> Any:
    """Like _chat but parses the JSON response."""
    raw = _chat(system, user)
    clean = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    try:
        parsed = json.loads(clean)
        # If model returned a string instead of dict, wrap it
        if isinstance(parsed, str):
            return {}
        return parsed
    except json.JSONDecodeError:
        logger.warning("LLM returned non-JSON; returning empty dict")
        return {}


# ─── 1. Trend Analysis ───────────────────────────────────────────────────────

TREND_SYSTEM = """
You are an expert market research analyst. Given a batch of article content,
identify the top emerging trends. Return ONLY valid JSON:
{
  "trends": [
    {
      "name": "...",
      "description": "...",
      "confidence": 0.0-1.0,
      "keywords": ["...", "..."],
      "relevant_urls": ["..."]
    }
  ]
}
""".strip()

def analyze_trends(articles: List[Dict]) -> Dict:
    batch = "\n\n---\n\n".join(
        f"Title: {a['title']}\nURL: {a['url']}\nContent: {a['content'][:800]}"
        for a in articles
    )
    user = f"Analyze these articles and identify top market trends:\n\n{batch}"
    result = _json_chat(TREND_SYSTEM, user)
    # Ensure it's always a dict with a 'trends' key
    if not isinstance(result, dict):
        return {"trends": []}
    if "trends" not in result:
        return {"trends": []}
    return result


# ─── 2. Sentiment Analysis ───────────────────────────────────────────────────

SENTIMENT_SYSTEM = """
You are a sentiment analysis expert. Analyze the given text and return ONLY valid JSON:
{
  "overall_sentiment": "positive|negative|neutral",
  "score": -1.0 to 1.0,
  "confidence": 0.0-1.0,
  "key_themes": ["..."],
  "notable_quotes": ["..."],
  "summary": "..."
}
""".strip()

def analyze_sentiment(article: Dict) -> Dict:
    user = f"Title: {article['title']}\n\nContent: {article['content'][:1500]}"
    result = _json_chat(SENTIMENT_SYSTEM, user)
    if isinstance(result, dict):
        result["url"]   = article.get("url", "")
        result["title"] = article.get("title", "")
    return result


def batch_sentiment(articles: List[Dict]) -> List[Dict]:
    results = []
    for article in articles:
        try:
            results.append(analyze_sentiment(article))
        except Exception as exc:
            logger.error(f"Sentiment failed for {article.get('url')}: {exc}")
    return results


# ─── 3. Competitor Monitoring ─────────────────────────────────────────────────

COMPETITOR_SYSTEM = """
You are a competitive intelligence analyst. Extract competitor activities from
the article. Return ONLY valid JSON:
{
  "competitors_mentioned": [
    {
      "name": "...",
      "activity_type": "product_launch|pricing|partnership|marketing|acquisition|other",
      "description": "...",
      "impact_level": "high|medium|low",
      "date": "..."
    }
  ],
  "has_competitor_info": true
}
""".strip()

def monitor_competitors(article: Dict) -> Dict:
    user = f"Title: {article['title']}\nURL: {article['url']}\n\nContent: {article['content'][:1500]}"
    result = _json_chat(COMPETITOR_SYSTEM, user)
    if isinstance(result, dict):
        result["source_url"] = article.get("url", "")
    return result


def batch_competitor_monitor(articles: List[Dict]) -> List[Dict]:
    results = []
    for article in articles:
        try:
            data = monitor_competitors(article)
            if isinstance(data, dict) and data.get("has_competitor_info"):
                results.append(data)
        except Exception as exc:
            logger.error(f"Competitor monitor failed for {article.get('url')}: {exc}")
    return results


# ─── 4. Opportunity & Risk Detection ─────────────────────────────────────────

OPP_RISK_SYSTEM = """
You are a strategic business analyst. Identify opportunities and risks from the content.
Return ONLY valid JSON:
{
  "opportunities": [
    {"title": "...", "description": "...", "potential_impact": "high|medium|low", "timeframe": "short|medium|long"}
  ],
  "risks": [
    {"title": "...", "description": "...", "severity": "high|medium|low", "likelihood": "high|medium|low"}
  ]
}
""".strip()

def detect_opportunities_risks(articles: List[Dict]) -> Dict:
    batch = "\n\n---\n\n".join(
        f"Title: {a['title']}\nContent: {a['content'][:600]}"
        for a in articles
    )
    return _json_chat(OPP_RISK_SYSTEM, batch)


# ─── 5. Strategic Recommendations ────────────────────────────────────────────

RECOMMENDATIONS_SYSTEM = """
You are a chief strategy officer. Based on market research data provided, generate
actionable strategic recommendations. Return ONLY valid JSON:
{
  "recommendations": [
    {
      "priority": "high|medium|low",
      "action": "...",
      "rationale": "...",
      "expected_outcome": "...",
      "timeline": "..."
    }
  ],
  "executive_summary": "..."
}
""".strip()

def generate_recommendations(trends: Dict, sentiment_summary: str, opp_risks: Dict) -> Dict:
    user = f"""
Market Trends:
{json.dumps(trends, indent=2)}

Sentiment Summary:
{sentiment_summary}

Opportunities & Risks:
{json.dumps(opp_risks, indent=2)}
""".strip()
    return _json_chat(RECOMMENDATIONS_SYSTEM, user)


# ─── 6. Weekly Report Narrative ───────────────────────────────────────────────

WEEKLY_REPORT_SYSTEM = """
You are a senior market research director. Write a professional weekly executive
intelligence report in markdown, suitable for C-suite distribution. Be concise,
data-driven, and actionable. Use this structure:
## Executive Summary
## Top Market Trends
## Sentiment Overview
## Competitor Activity
## Opportunities & Risks
## Strategic Recommendations
## Outlook for Next Week
""".strip()

def generate_weekly_report(context: Dict) -> str:
    user = f"Generate the weekly market intelligence report from this data:\n\n{json.dumps(context, indent=2)}"
    return _chat(WEEKLY_REPORT_SYSTEM, user)
