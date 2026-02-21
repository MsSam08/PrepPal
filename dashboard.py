# dashboard.py
# PrepPal AI Dashboard — Streamlit Frontend
# Run: streamlit run dashboard.py
#
# Make sure your API is running first:
#   uvicorn api:app --host 0.0.0.0 --port 8000

import streamlit as st
import requests
from datetime import date, timedelta
import pandas as pd

# ── CONFIG ────────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="PrepPal AI Dashboard",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CUSTOM STYLES ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }

    .main { background-color: #0f1117; }

    .stApp {
        background: linear-gradient(135deg, #0f1117 0%, #1a1f2e 100%);
    }

    /* Header */
    .hero-title {
        font-size: 2.8rem;
        font-weight: 700;
        background: linear-gradient(135deg, #4ade80, #22d3ee);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }

    .hero-sub {
        color: #94a3b8;
        font-size: 1rem;
        font-weight: 400;
        margin-bottom: 2rem;
    }

    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.04);
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.2s ease;
    }

    .metric-card:hover {
        border-color: rgba(74,222,128,0.3);
        background: rgba(74,222,128,0.05);
    }

    .metric-value {
        font-size: 2.4rem;
        font-weight: 700;
        color: #f1f5f9;
        font-family: 'DM Mono', monospace;
        line-height: 1;
    }

    .metric-label {
        font-size: 0.78rem;
        color: #64748b;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-top: 0.4rem;
        font-weight: 500;
    }

    .metric-sub {
        font-size: 0.85rem;
        color: #94a3b8;
        margin-top: 0.3rem;
    }

    /* Risk badge */
    .risk-high   { background: rgba(239,68,68,0.15);  border: 1px solid rgba(239,68,68,0.4);  color: #f87171; border-radius: 12px; padding: 1rem 1.5rem; text-align: center; }
    .risk-medium { background: rgba(234,179,8,0.15);  border: 1px solid rgba(234,179,8,0.4);  color: #fbbf24; border-radius: 12px; padding: 1rem 1.5rem; text-align: center; }
    .risk-low    { background: rgba(74,222,128,0.15); border: 1px solid rgba(74,222,128,0.4); color: #4ade80; border-radius: 12px; padding: 1rem 1.5rem; text-align: center; }

    .risk-label { font-size: 1.6rem; font-weight: 700; }
    .risk-detail { font-size: 0.85rem; margin-top: 0.3rem; opacity: 0.8; }

    /* Confidence badge */
    .conf-high   { color: #4ade80; font-weight: 700; }
    .conf-medium { color: #fbbf24; font-weight: 700; }
    .conf-low    { color: #f87171; font-weight: 700; }

    /* Section header */
    .section-header {
        font-size: 1rem;
        font-weight: 600;
        color: #cbd5e1;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.06);
    }

    /* Explanation box */
    .explain-box {
        background: rgba(34,211,238,0.07);
        border-left: 3px solid #22d3ee;
        border-radius: 0 8px 8px 0;
        padding: 0.8rem 1rem;
        color: #94a3b8;
        font-size: 0.88rem;
        margin-top: 0.5rem;
    }

    /* Status pill */
    .status-online  { background: rgba(74,222,128,0.2); color: #4ade80; padding: 0.2rem 0.7rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }
    .status-offline { background: rgba(239,68,68,0.2);  color: #f87171; padding: 0.2rem 0.7rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(15,17,23,0.95);
        border-right: 1px solid rgba(255,255,255,0.06);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #4ade80, #22d3ee);
        color: #0f1117;
        font-weight: 700;
        font-family: 'DM Sans', sans-serif;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1.5rem;
        font-size: 0.95rem;
        width: 100%;
        transition: opacity 0.2s;
    }

    .stButton > button:hover { opacity: 0.85; }

    /* Forecast table */
    .forecast-row {
        display: flex;
        align-items: center;
        padding: 0.65rem 1rem;
        border-radius: 10px;
        margin-bottom: 0.4rem;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.05);
    }

    .day-name { color: #e2e8f0; font-weight: 600; width: 110px; font-size: 0.9rem; }
    .day-demand { font-family: 'DM Mono', monospace; color: #4ade80; font-size: 1.1rem; font-weight: 700; width: 70px; }
    .day-rec { color: #94a3b8; font-size: 0.82rem; }
    .day-conf { font-size: 0.75rem; margin-left: auto; }

    /* Divider */
    hr { border-color: rgba(255,255,255,0.06); }

    /* Input labels */
    label { color: #94a3b8 !important; font-size: 0.85rem !important; }

    /* Selectbox, number input */
    .stSelectbox > div > div, .stNumberInput > div > div {
        background: rgba(255,255,255,0.04) !important;
        border-color: rgba(255,255,255,0.1) !important;
        color: #f1f5f9 !important;
    }
</style>
""", unsafe_allow_html=True)


# ── HELPERS ───────────────────────────────────────────────────────────────────
def check_health():
    try:
        r = requests.get(f"{API_URL}/api/health", timeout=3)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def call_predict(payload):
    try:
        r = requests.post(f"{API_URL}/api/predict", json=payload, timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def call_predict_week(payload):
    try:
        r = requests.post(f"{API_URL}/api/predict-week", json=payload, timeout=10)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def call_risk(predicted, planned):
    try:
        r = requests.post(f"{API_URL}/api/risk-alert",
                          json={"predicted_demand": predicted, "planned_quantity": planned},
                          timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def call_recommend(predicted, current_plan):
    try:
        r = requests.post(f"{API_URL}/api/recommend",
                          json={"predicted_demand": predicted, "current_plan": current_plan},
                          timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def confidence_class(c):
    return {"High": "conf-high", "Medium": "conf-medium", "Low": "conf-low"}.get(c, "conf-medium")


# ── SIDEBAR ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🍽️ PrepPal AI")
    st.markdown("---")

    health = check_health()
    if health and health.get("model_loaded"):
        st.markdown('<span class="status-online">● API Online</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-offline">● API Offline</span>', unsafe_allow_html=True)
        st.error("Start your API: uvicorn api:app --port 8000")

    st.markdown("---")
    st.markdown('<div class="section-header">Item Details</div>', unsafe_allow_html=True)

    item_name = st.text_input("Item Name", value="Jollof Rice")
    business_type = st.selectbox("Business Type", ["Restaurant", "Cafe", "Bakery"])
    price = st.number_input("Price (₦)", min_value=1.0, value=50.0, step=5.0)
    shelf_life = st.number_input("Shelf Life (hours)", min_value=0.1, value=4.0, step=0.5)

    st.markdown("---")
    st.markdown('<div class="section-header">Conditions</div>', unsafe_allow_html=True)

    pred_date = st.date_input("Date", value=date.today() + timedelta(days=1))
    weather = st.selectbox("Weather", ["Clear", "Rainy"])
    is_holiday = st.checkbox("Public Holiday")
    planned_qty = st.number_input("Your Planned Quantity", min_value=0, value=50, step=1)

    st.markdown("---")
    predict_btn = st.button("Run Prediction")


# ── MAIN ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="hero-title">PrepPal AI Dashboard</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Smart demand forecasting for restaurants, cafes and bakeries</div>', unsafe_allow_html=True)

if not predict_btn:
    # Empty state
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">8.12%</div>
            <div class="metric-label">Model MAPE</div>
            <div class="metric-sub">59% better than target</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">34</div>
            <div class="metric-label">Features</div>
            <div class="metric-sub">Engineered for accuracy</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-value">7</div>
            <div class="metric-label">API Endpoints</div>
            <div class="metric-sub">All PRD requirements met</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("#### 👈 Fill in the item details and click **Run Prediction** to get started")

else:
    # ── SINGLE DAY PREDICTION ─────────────────────────────────────────────────
    with st.spinner("Getting prediction..."):
        result = call_predict({
            "item_name":        item_name,
            "business_type":    business_type,
            "date":             str(pred_date),
            "price":            price,
            "shelf_life_hours": shelf_life,
            "weather":          weather,
            "is_holiday":       1 if is_holiday else 0,
        })

    if not result or not result.get("success"):
        st.error("Prediction failed. Make sure your API is running.")
        st.stop()

    predicted = result["predicted_demand"]
    recommended = result["recommended_quantity"]
    confidence = result["confidence"]
    explanation = result.get("explanation", "")
    is_new = result.get("is_new_item", False)

    # ── METRICS ROW ──────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">Tomorrow\'s Forecast</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{predicted}</div>
            <div class="metric-label">Predicted Demand</div>
            <div class="metric-sub">units expected</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{recommended}</div>
            <div class="metric-label">Recommended Qty</div>
            <div class="metric-sub">with 5% buffer</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        conf_cls = confidence_class(confidence)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value"><span class="{conf_cls}">{confidence}</span></div>
            <div class="metric-label">Confidence</div>
            <div class="metric-sub">{result['confidence_score']*100:.0f}% score</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        item_type = "New Item" if is_new else "Known Item"
        item_color = "#fbbf24" if is_new else "#4ade80"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value" style="font-size:1.4rem; color:{item_color}">{item_type}</div>
            <div class="metric-label">Item Status</div>
            <div class="metric-sub">{item_name}</div>
        </div>""", unsafe_allow_html=True)

    if explanation:
        st.markdown(f'<div class="explain-box">💡 {explanation}</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── RISK + RECOMMENDATION ─────────────────────────────────────────────────
    col_risk, col_rec = st.columns(2)

    with col_risk:
        st.markdown('<div class="section-header">Waste Risk Alert</div>', unsafe_allow_html=True)
        risk = call_risk(predicted, planned_qty)
        if risk and risk.get("success"):
            level = risk["risk_level"]
            cls   = {"HIGH": "risk-high", "MEDIUM": "risk-medium", "LOW": "risk-low"}.get(level, "risk-low")
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(level, "🟢")
            st.markdown(f"""
            <div class="{cls}">
                <div class="risk-label">{emoji} {level} RISK</div>
                <div class="risk-detail">{risk['waste_percentage']}% waste · {risk['expected_waste']} units</div>
                <div class="risk-detail" style="margin-top:0.4rem">{risk['message']}</div>
            </div>""", unsafe_allow_html=True)

    with col_rec:
        st.markdown('<div class="section-header">Smart Recommendation</div>', unsafe_allow_html=True)
        rec = call_recommend(predicted, planned_qty)
        if rec and rec.get("success"):
            action = rec["action"]
            if "REDUCE" in action:
                action_color, action_emoji = "#f87171", "📉"
            elif "INCREASE" in action:
                action_color, action_emoji = "#4ade80", "📈"
            else:
                action_color, action_emoji = "#22d3ee", "✅"
            st.markdown(f"""
            <div class="metric-card" style="text-align:left">
                <div style="font-size:1.2rem; font-weight:700; color:{action_color}">{action_emoji} {action}</div>
                <div style="color:#94a3b8; font-size:0.85rem; margin-top:0.5rem">{rec['reason']}</div>
                <div style="color:#64748b; font-size:0.8rem; margin-top:0.4rem">{rec['explanation']}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── 7-DAY FORECAST ────────────────────────────────────────────────────────
    st.markdown('<div class="section-header">7-Day Forecast</div>', unsafe_allow_html=True)

    with st.spinner("Loading 7-day forecast..."):
        week_result = call_predict_week({
            "item_name":        item_name,
            "business_type":    business_type,
            "price":            price,
            "shelf_life_hours": shelf_life,
            "starting_date":    str(pred_date),
            "weather_forecast": [weather] * 7,
            "holiday_flags":    [1 if is_holiday else 0] + [0] * 6,
        })

    if week_result and week_result.get("success"):
        forecast = week_result["forecast"]

        # Chart
        chart_df = pd.DataFrame({
            "Day":    [d["day_name"] for d in forecast],
            "Demand": [d["predicted_demand"] for d in forecast],
            "Recommended": [d["recommended_quantity"] for d in forecast],
        }).set_index("Day")
        st.line_chart(chart_df, color=["#4ade80", "#22d3ee"])

        # Table rows
        st.markdown("<br>", unsafe_allow_html=True)
        for d in forecast:
            conf_cls  = confidence_class(d["confidence"])
            weather_icon = "🌧️" if d["weather"] == "Rainy" else "☀️"
            holiday_icon = "🎉" if d["is_holiday"] == "Yes" else ""
            st.markdown(f"""
            <div class="forecast-row">
                <div class="day-name">{d['day_name'][:3]} {holiday_icon}</div>
                <div class="day-demand">{d['predicted_demand']}</div>
                <div class="day-rec">rec: {d['recommended_quantity']} &nbsp; {weather_icon}</div>
                <div class="day-conf"><span class="{conf_cls}">{d['confidence']}</span></div>
            </div>""", unsafe_allow_html=True)
    else:
        st.warning("Could not load 7-day forecast.")

    # ── FOOTER ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        '<p style="color:#334155; font-size:0.75rem; text-align:center">PrepPal AI · Built by Euodia Sam · Data Science Lead</p>',
        unsafe_allow_html=True
    )