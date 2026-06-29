import os
import sys
from datetime import datetime, timedelta
 
import pandas as pd
import streamlit as st
 
# ── Path fix so config/modules resolve from project root ─────────────────────
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
 
from config.config import (
    SPREADSHEET_ID,
    SHEET_TRENDS,
    SHEET_SENTIMENT,
    SHEET_COMPETITORS,
    SHEET_OPPORTUNITIES,
    SHEET_WEEKLY_REPORT,
    SHEET_RAW_DATA,
)
from modules.sheets_manager import SheetsManager
 
# ─────────────────────────────────────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Market Intelligence Hub",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)
 
# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS — dark intelligence theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ── Base ── */
[data-testid="stAppViewContainer"] { background: #0d1117; }
[data-testid="stSidebar"]          { background: #161b22; border-right: 1px solid #30363d; }
[data-testid="stHeader"]           { background: transparent; }
 
/* ── Typography ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #e6edf3; }
h1 { font-size: 1.6rem !important; font-weight: 700 !important; letter-spacing: -0.5px; color: #f0f6fc !important; }
h2, h3 { color: #cdd9e5 !important; font-weight: 600 !important; }
 
/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 16px 20px;
    transition: border-color .2s;
}
[data-testid="metric-container"]:hover { border-color: #388bfd; }
[data-testid="stMetricValue"]  { font-size: 2rem !important; font-weight: 700 !important; color: #58a6ff !important; }
[data-testid="stMetricLabel"]  { font-size: 0.78rem !important; color: #8b949e !important; text-transform: uppercase; letter-spacing: .5px; }
[data-testid="stMetricDelta"]  { font-size: 0.82rem !important; }
 
/* ── Tabs ── */
[data-testid="stTabs"] button {
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    color: #8b949e !important;
    border-bottom: 2px solid transparent !important;
    padding-bottom: 8px !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #58a6ff !important;
    border-bottom-color: #58a6ff !important;
}
 
/* ── Dataframe ── */
[data-testid="stDataFrame"] { border: 1px solid #30363d !important; border-radius: 8px; }
 
/* ── Buttons ── */
[data-testid="stButton"] > button {
    background: #21262d;
    border: 1px solid #30363d;
    color: #cdd9e5;
    border-radius: 6px;
    font-size: 0.82rem;
    padding: 6px 14px;
    transition: all .2s;
}
[data-testid="stButton"] > button:hover { background: #388bfd22; border-color: #388bfd; color: #58a6ff; }
 
/* ── Info/alert boxes ── */
[data-testid="stInfo"]    { background: #1c2b3a; border-left: 3px solid #388bfd; border-radius: 6px; }
[data-testid="stSuccess"] { background: #1a2e22; border-left: 3px solid #3fb950; border-radius: 6px; }
[data-testid="stWarning"] { background: #2d2008; border-left: 3px solid #d29922; border-radius: 6px; }
 
/* ── Sidebar widgets ── */
[data-testid="stSidebar"] label { color: #8b949e !important; font-size: 0.82rem !important; }
[data-testid="stSidebar"] .stSelectbox > div > div { background: #21262d; border-color: #30363d; }
 
/* ── Divider ── */
hr { border-color: #21262d !important; }
 
/* ── Trend card ── */
.trend-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-left: 3px solid #58a6ff;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 10px;
    transition: border-color .2s;
}
.trend-card:hover { border-left-color: #79c0ff; }
.trend-name  { font-size: 0.95rem; font-weight: 600; color: #f0f6fc; margin-bottom: 4px; }
.trend-desc  { font-size: 0.82rem; color: #8b949e; margin-bottom: 8px; line-height: 1.5; }
.trend-meta  { font-size: 0.75rem; color: #6e7681; }
.badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 0.72rem;
    font-weight: 600;
    margin-right: 4px;
}
.badge-high    { background: #3fb95022; color: #3fb950; border: 1px solid #3fb95044; }
.badge-medium  { background: #d2992222; color: #d29922; border: 1px solid #d2992244; }
.badge-low     { background: #58a6ff22; color: #58a6ff; border: 1px solid #58a6ff44; }
.badge-pos     { background: #3fb95022; color: #3fb950; border: 1px solid #3fb95044; }
.badge-neg     { background: #f8514922; color: #f85149; border: 1px solid #f8514944; }
.badge-neu     { background: #8b949e22; color: #8b949e; border: 1px solid #8b949e44; }
 
/* ── Stat pill ── */
.stat-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #21262d; border: 1px solid #30363d;
    border-radius: 20px; padding: 4px 12px;
    font-size: 0.78rem; color: #8b949e; margin-right: 6px;
}
.stat-pill span { color: #58a6ff; font-weight: 600; }
 
/* ── Report box ── */
.report-box {
    background: #161b22; border: 1px solid #30363d; border-radius: 8px;
    padding: 20px 24px; font-size: 0.86rem; line-height: 1.7; color: #cdd9e5;
    max-height: 520px; overflow-y: auto;
}
.report-box h2 { color: #58a6ff !important; font-size: 1rem !important; margin-top: 16px; }
.report-box h3 { color: #79c0ff !important; font-size: 0.9rem !important; }
 
/* ── Sidebar logo area ── */
.sidebar-brand {
    font-size: 1rem; font-weight: 700; color: #f0f6fc;
    padding: 0 0 16px 0; border-bottom: 1px solid #30363d; margin-bottom: 20px;
}
.sidebar-brand span { color: #58a6ff; }
</style>
""", unsafe_allow_html=True)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Data loading
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource(ttl=300)
def get_sheets():
    return SheetsManager()
 
@st.cache_data(ttl=300)
def load_data():
    sm = get_sheets()
    spreadsheet = sm.spreadsheet
 
    def ws_df(name):
        try:
            records = spreadsheet.worksheet(name).get_all_records()
            return pd.DataFrame(records) if records else pd.DataFrame()
        except Exception:
            return pd.DataFrame()
 
    return {
        "trends":        ws_df(SHEET_TRENDS),
        "sentiment":     ws_df(SHEET_SENTIMENT),
        "competitors":   ws_df(SHEET_COMPETITORS),
        "opportunities": ws_df(SHEET_OPPORTUNITIES),
        "raw":           ws_df(SHEET_RAW_DATA),
        "weekly":        ws_df(SHEET_WEEKLY_REPORT),
    }
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def sentiment_badge(val: str) -> str:
    val = str(val).lower()
    if "positive" in val:   return '<span class="badge badge-pos">Positive</span>'
    if "negative" in val:   return '<span class="badge badge-neg">Negative</span>'
    return '<span class="badge badge-neu">Neutral</span>'
 
def impact_badge(val: str) -> str:
    val = str(val).lower()
    if val == "high":   return '<span class="badge badge-high">High</span>'
    if val == "medium": return '<span class="badge badge-medium">Medium</span>'
    return '<span class="badge badge-low">Low</span>'
 
def score_color(score: float) -> str:
    if score >= 0.5:  return "#3fb950"
    if score <= -0.5: return "#f85149"
    return "#d29922"
 
def filter_by_days(df: pd.DataFrame, col: str, days: int) -> pd.DataFrame:
    if df.empty or col not in df.columns:
        return df
    try:
        df[col] = pd.to_datetime(df[col], errors="coerce")
        cutoff  = datetime.utcnow() - timedelta(days=days)
        return df[df[col] >= cutoff]
    except Exception:
        return df
 
def delta_label(current: int, previous: int) -> str:
    diff = current - previous
    return f"+{diff}" if diff >= 0 else str(diff)
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">📡 Market<span>Intel</span></div>', unsafe_allow_html=True)
 
    st.markdown("**Controls**")
    time_window = st.selectbox(
        "Time window",
        ["Last 7 days", "Last 14 days", "Last 30 days", "All time"],
        index=2,
    )
    days_map = {"Last 7 days": 7, "Last 14 days": 14, "Last 30 days": 30, "All time": 9999}
    selected_days = days_map[time_window]
 
    st.divider()
    st.markdown("**Actions**")
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
 
    if st.button("▶ Run Pipeline Now"):
        with st.spinner("Running pipeline..."):
            try:
                import subprocess, sys
                subprocess.Popen([sys.executable, "main.py", "run"])
                st.success("Pipeline started! Refresh in ~2 min.")
            except Exception as e:
                st.error(f"Could not start: {e}")
 
    st.divider()
    st.markdown("**About**")
    st.caption(f"Sheet ID: `{SPREADSHEET_ID[:12]}…`")
    st.caption(f"Last loaded: {datetime.utcnow().strftime('%H:%M UTC')}")
    st.caption("Powered by Groq · Firecrawl · Memento")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Load data
# ─────────────────────────────────────────────────────────────────────────────
data = load_data()
 
# Apply time window filter
trends_df  = filter_by_days(data["trends"].copy(),        "Date",         selected_days)
sent_df    = filter_by_days(data["sentiment"].copy(),     "Date",         selected_days)
comp_df    = filter_by_days(data["competitors"].copy(),   "Date",         selected_days)
opp_df     = filter_by_days(data["opportunities"].copy(), "Date",         selected_days)
raw_df     = filter_by_days(data["raw"].copy(),           "Collected At", selected_days)
weekly_df  = data["weekly"].copy()
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("## 📡 Market Intelligence Hub")
st.caption(f"Autonomous Market Research & Trend Analyst  •  {time_window}  •  {datetime.utcnow().strftime('%d %b %Y, %H:%M UTC')}")
 
st.divider()
 
# ─────────────────────────────────────────────────────────────────────────────
# KPI Row
# ─────────────────────────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
 
# Compute sentiment avg
sent_scores = pd.to_numeric(sent_df.get("Score", pd.Series()), errors="coerce").dropna() if not sent_df.empty else pd.Series()
avg_score   = sent_scores.mean() if len(sent_scores) else 0
 
k1.metric("Trends Detected",     len(trends_df),  help="Unique market trends identified by LLM")
k2.metric("Articles Processed",  len(raw_df),     help="Total articles crawled and stored")
k3.metric("Sentiment Avg",       f"{avg_score:+.2f}", help="Average sentiment score (-1 to +1)")
k4.metric("Competitor Signals",  len(comp_df),    help="Competitor activities tracked")
k5.metric("Opps & Risks",        len(opp_df),     help="Opportunities and risks identified")
 
st.divider()
 
# ─────────────────────────────────────────────────────────────────────────────
# Tabs
# ─────────────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Trends",
    "💬 Sentiment",
    "🕵️ Competitors",
    "🔍 Opps & Risks",
    "📰 Raw Articles",
    "📋 Weekly Reports",
])
 
 
# ── TAB 1: Trends ─────────────────────────────────────────────────────────────
with tab1:
    c_left, c_right = st.columns([2, 1])
    with c_left:
        st.markdown("### Detected Market Trends")
    with c_right:
        min_conf = st.slider("Min confidence", 0.0, 1.0, 0.0, 0.05, key="trend_conf")
 
    if not trends_df.empty:
        df = trends_df.copy()
        if "Confidence" in df.columns:
            df["Confidence"] = pd.to_numeric(df["Confidence"], errors="coerce").fillna(0)
            df = df[df["Confidence"] >= min_conf]
 
        # Cards view
        if not df.empty:
            df_sorted = df.sort_values("Confidence", ascending=False) if "Confidence" in df.columns else df
 
            for _, row in df_sorted.head(20).iterrows():
                conf = float(row.get("Confidence", 0))
                conf_pct = f"{conf:.0%}"
                keywords = str(row.get("Keywords", ""))
                kw_pills = " ".join(
                    f'<span class="badge badge-neu">{k.strip()}</span>'
                    for k in keywords.split(",")[:5] if k.strip()
                )
                st.markdown(f"""
                <div class="trend-card">
                    <div class="trend-name">{row.get("Trend Name", "—")}</div>
                    <div class="trend-desc">{str(row.get("Description", ""))[:200]}</div>
                    <div>{kw_pills}</div>
                    <div class="trend-meta" style="margin-top:8px">
                        Confidence: <strong style="color:#58a6ff">{conf_pct}</strong>
                        &nbsp;·&nbsp; {str(row.get("Date", ""))[:16]}
                    </div>
                </div>
                """, unsafe_allow_html=True)
 
            # Confidence chart
            if "Confidence" in df.columns and len(df) > 0:
                st.markdown("#### Confidence by Trend")
                chart_data = df_sorted.head(10).set_index("Trend Name")[["Confidence"]]
                st.bar_chart(chart_data)
        else:
            st.info("No trends match the current confidence filter.")
    else:
        st.info("No trend data in this time window. Run the pipeline first.")
 
 
# ── TAB 2: Sentiment ──────────────────────────────────────────────────────────
with tab2:
    st.markdown("### Sentiment Analysis")
 
    if not sent_df.empty:
        df = sent_df.copy()
        df["Score"] = pd.to_numeric(df.get("Score", 0), errors="coerce").fillna(0)
 
        # Summary metrics row
        pos = (df["Score"] > 0.2).sum()
        neg = (df["Score"] < -0.2).sum()
        neu = len(df) - pos - neg
 
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg Score",  f"{df['Score'].mean():+.3f}")
        m2.metric("Positive",   int(pos), delta=None)
        m3.metric("Neutral",    int(neu), delta=None)
        m4.metric("Negative",   int(neg), delta=None)
 
        st.divider()
 
        col_chart, col_dist = st.columns(2)
 
        with col_chart:
            st.markdown("#### Score Over Time")
            if "Date" in df.columns:
                ts = df.copy()
                ts["Date"] = pd.to_datetime(ts["Date"], errors="coerce")
                ts = ts.dropna(subset=["Date"]).set_index("Date").sort_index()
                if not ts.empty:
                    st.line_chart(ts[["Score"]])
 
        with col_dist:
            st.markdown("#### Sentiment Distribution")
            if "Sentiment" in df.columns:
                counts = df["Sentiment"].str.lower().value_counts()
                st.bar_chart(counts)
 
        st.divider()
        st.markdown("#### Article-Level Sentiment")
 
        # Sentiment filter
        sent_filter = st.multiselect(
            "Filter by sentiment",
            ["positive", "negative", "neutral"],
            default=["positive", "negative", "neutral"],
            key="sent_filter",
        )
        if "Sentiment" in df.columns:
            df_show = df[df["Sentiment"].str.lower().isin(sent_filter)]
        else:
            df_show = df
 
        # Render as cards
        for _, row in df_show.sort_values("Score", ascending=False).head(20).iterrows():
            score = float(row.get("Score", 0))
            color = score_color(score)
            badge = sentiment_badge(str(row.get("Sentiment", "")))
            themes = str(row.get("Key Themes", ""))
            st.markdown(f"""
            <div class="trend-card" style="border-left-color:{color}">
                <div class="trend-name">{str(row.get("Title", "—"))[:90]}</div>
                <div class="trend-desc">{str(row.get("Summary", ""))[:180]}</div>
                <div>{badge}
                    <span class="stat-pill">Score <span style="color:{color}">{score:+.2f}</span></span>
                    <span class="stat-pill">Conf <span>{float(row.get("Confidence", 0)):.0%}</span></span>
                </div>
                <div class="trend-meta" style="margin-top:6px">
                    Themes: {themes[:100]} &nbsp;·&nbsp; {str(row.get("Date",""))[:16]}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No sentiment data in this time window.")
 
 
# ── TAB 3: Competitors ────────────────────────────────────────────────────────
with tab3:
    st.markdown("### Competitor Activity")
 
    if not comp_df.empty:
        df = comp_df.copy()
 
        # Filters row
        f1, f2 = st.columns(2)
        with f1:
            impact_filter = st.multiselect(
                "Impact level", ["high", "medium", "low"],
                default=["high", "medium"],
                key="comp_impact",
            )
        with f2:
            if "Activity Type" in df.columns:
                types = df["Activity Type"].dropna().unique().tolist()
                type_filter = st.multiselect("Activity type", types, default=types, key="comp_type")
            else:
                type_filter = []
 
        # Apply filters
        if "Impact Level" in df.columns and impact_filter:
            df = df[df["Impact Level"].str.lower().isin(impact_filter)]
        if "Activity Type" in df.columns and type_filter:
            df = df[df["Activity Type"].isin(type_filter)]
 
        if not df.empty:
            # Competitor frequency chart
            if "Competitor" in df.columns:
                st.markdown("#### Most Active Competitors")
                freq = df["Competitor"].value_counts().head(10)
                st.bar_chart(freq)
 
            st.divider()
            st.markdown("#### Activity Log")
 
            for _, row in df.sort_values("Date", ascending=False).head(30).iterrows():
                badge = impact_badge(str(row.get("Impact Level", "")))
                act = str(row.get("Activity Type", "")).replace("_", " ").title()
                src = str(row.get("Source URL", ""))
                link = f'<a href="{src}" target="_blank" style="color:#58a6ff;font-size:0.75rem">Source ↗</a>' if src.startswith("http") else ""
                st.markdown(f"""
                <div class="trend-card">
                    <div class="trend-name">{row.get("Competitor", "—")}
                        <span class="badge badge-neu" style="margin-left:8px;font-weight:400">{act}</span>
                    </div>
                    <div class="trend-desc">{str(row.get("Description", ""))[:220]}</div>
                    <div>{badge} {link}
                        <span class="trend-meta" style="margin-left:8px">{str(row.get("Date",""))[:16]}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No competitor records match the current filters.")
    else:
        st.info("No competitor data in this time window.")
 
 
# ── TAB 4: Opportunities & Risks ──────────────────────────────────────────────
with tab4:
    st.markdown("### Opportunities & Risks")
 
    if not opp_df.empty:
        df = opp_df.copy()
        opps  = df[df["Type"] == "Opportunity"]
        risks = df[df["Type"] == "Risk"]
 
        # Summary
        s1, s2 = st.columns(2)
        s1.metric("Opportunities", len(opps))
        s2.metric("Risks",         len(risks))
 
        st.divider()
        col_o, col_r = st.columns(2)
 
        with col_o:
            st.markdown("#### ✅ Opportunities")
            high_opps = opps[opps.get("Impact/Severity", pd.Series(dtype=str)).str.lower() == "high"] if "Impact/Severity" in opps.columns else opps
            for _, row in opps.sort_values("Date", ascending=False).head(15).iterrows():
                impact = str(row.get("Impact/Severity", ""))
                badge  = impact_badge(impact)
                tf     = str(row.get("Timeframe", ""))
                st.markdown(f"""
                <div class="trend-card" style="border-left-color:#3fb950">
                    <div class="trend-name">{str(row.get("Title","—"))[:80]}</div>
                    <div class="trend-desc">{str(row.get("Description",""))[:180]}</div>
                    <div>{badge}
                        {'<span class="badge badge-neu">'+tf+'</span>' if tf else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
 
        with col_r:
            st.markdown("#### 🚨 Risks")
            for _, row in risks.sort_values("Date", ascending=False).head(15).iterrows():
                sev  = str(row.get("Impact/Severity", ""))
                like = str(row.get("Likelihood", ""))
                badge = impact_badge(sev)
                st.markdown(f"""
                <div class="trend-card" style="border-left-color:#f85149">
                    <div class="trend-name">{str(row.get("Title","—"))[:80]}</div>
                    <div class="trend-desc">{str(row.get("Description",""))[:180]}</div>
                    <div>{badge}
                        {'<span class="badge badge-medium">Likelihood: '+like+'</span>' if like else ''}
                    </div>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("No opportunity/risk data in this time window.")
 
 
# ── TAB 5: Raw Articles ───────────────────────────────────────────────────────
with tab5:
    st.markdown("### Crawled Articles")
 
    if not raw_df.empty:
        df = raw_df.copy()
 
        # Search box
        search = st.text_input("Search by title or URL", placeholder="e.g. AI, startup, funding…", key="raw_search")
        if search:
            mask = (
                df.get("Title", pd.Series(dtype=str)).str.contains(search, case=False, na=False) |
                df.get("URL",   pd.Series(dtype=str)).str.contains(search, case=False, na=False)
            )
            df = df[mask]
 
        st.caption(f"{len(df)} articles")
        # Render as a clean table with clickable URLs
        display_cols = [c for c in ["Collected At", "Title", "Author", "Tags", "URL"] if c in df.columns]
        st.dataframe(
            df[display_cols].sort_values("Collected At", ascending=False).head(100),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No raw article data in this time window.")
 
 
# ── TAB 6: Weekly Reports ─────────────────────────────────────────────────────
with tab6:
    st.markdown("### Weekly Executive Reports")
 
    if not weekly_df.empty:
        # Report selector
        weeks = weekly_df.get("Week Of", pd.Series()).tolist()
        if weeks:
            selected_week = st.selectbox("Select report week", weeks[::-1], key="week_select")
            row = weekly_df[weekly_df["Week Of"] == selected_week].iloc[0]
            report_text = str(row.get("Report", "No content available."))
 
            st.download_button(
                label="⬇ Download as .md",
                data=report_text,
                file_name=f"market_report_{selected_week}.md",
                mime="text/markdown",
            )
            st.markdown(f'<div class="report-box">{report_text.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        else:
            st.info("No weekly reports yet. Run `python main.py weekly` to generate one.")
    else:
        st.info("No weekly reports found. Run `python main.py weekly` to generate the first one.")
 
 
# ─────────────────────────────────────────────────────────────────────────────
# Footer
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption("Autonomous Market Research & Trend Analyst  •  Groq + Firecrawl + Memento + Google Sheets  •  Vansh Kapoor")