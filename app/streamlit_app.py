"""
FAKTA - Streamlit Demo UI
Apple-grade glassmorphism design.
"""

import os
import sys
import json
import time
import base64
from pathlib import Path
from datetime import datetime

try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).parent.parent / ".env"
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass

import streamlit as st
import requests

# ============================================================
# Page Config
# ============================================================
st.set_page_config(
    page_title="FAKTA",
    page_icon="\U0001f50d",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ============================================================
# Global CSS — Apple Design Language
# ============================================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

    /* === BASE RESET === */
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif !important; }
    .stApp { background: transparent !important; }
    #root > div:first-child { background: transparent !important; }
    .element-container { background: transparent !important; }
    [data-testid="stAppViewContainer"] > div { background: transparent !important; }
    [data-testid="stHeader"] { background: transparent !important; }

    /* === DEEP BACKGROUND === */
    .bg-layer {
        position: fixed;
        top: 0; left: 0;
        width: 100vw; height: 100vh;
        z-index: -1;
        background: #0a0a0f;
        overflow: hidden;
    }
    /* Subtle radial glow — top-left */
    .bg-layer::before {
        content: '';
        position: absolute;
        top: -20%; left: -10%;
        width: 70vw; height: 70vh;
        background: radial-gradient(ellipse, rgba(59, 130, 246, 0.08) 0%, transparent 70%);
        pointer-events: none;
    }
    /* Subtle radial glow — bottom-right */
    .bg-layer::after {
        content: '';
        position: absolute;
        bottom: -20%; right: -10%;
        width: 60vw; height: 60vh;
        background: radial-gradient(ellipse, rgba(139, 92, 246, 0.06) 0%, transparent 70%);
        pointer-events: none;
    }

    /* === ANIMATED GLOW ORBS === */
    .glow-orb {
        position: absolute;
        border-radius: 50%;
        pointer-events: none;
        will-change: transform;
    }
    .glow-orb--a {
        width: 500px; height: 500px;
        background: radial-gradient(circle, rgba(59, 130, 246, 0.09) 0%, transparent 70%);
        top: 15%; left: 20%;
        animation: drift-a 40s ease-in-out infinite alternate;
    }
    .glow-orb--b {
        width: 400px; height: 400px;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.07) 0%, transparent 70%);
        top: 55%; right: 15%;
        animation: drift-b 35s ease-in-out infinite alternate-reverse;
    }
    .glow-orb--c {
        width: 350px; height: 350px;
        background: radial-gradient(circle, rgba(6, 182, 212, 0.06) 0%, transparent 70%);
        bottom: 10%; left: 40%;
        animation: drift-c 30s ease-in-out infinite alternate;
    }
    @keyframes drift-a {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(80px, -60px); }
    }
    @keyframes drift-b {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(-70px, 50px); }
    }
    @keyframes drift-c {
        0%   { transform: translate(0, 0); }
        100% { transform: translate(60px, -40px); }
    }

    /* === GLASS SURFACE === */
    .surface {
        background: rgba(255, 255, 255, 0.03);
        -webkit-backdrop-filter: blur(24px);
        backdrop-filter: blur(24px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 16px;
    }

    /* === FROSTED CARD === */
    .card {
        background: rgba(255, 255, 255, 0.04);
        -webkit-backdrop-filter: blur(20px);
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 24px 28px;
        transition: background 0.25s ease, border-color 0.25s ease;
    }
    .card:hover {
        background: rgba(255, 255, 255, 0.055);
        border-color: rgba(255, 255, 255, 0.09);
    }

    /* === INPUTS === */
    .stTextInput > div > div,
    .stTextArea > div > div {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        border-radius: 10px !important;
        transition: all 0.2s ease !important;
    }
    .stTextInput > div > div:focus-within,
    .stTextArea > div > div:focus-within {
        border-color: rgba(255, 255, 255, 0.18) !important;
        box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.03) !important;
        background: rgba(255, 255, 255, 0.05) !important;
    }
    .stTextInput input, .stTextArea textarea {
        color: rgba(255, 255, 255, 0.9) !important;
        font-size: 15px !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder {
        color: rgba(255, 255, 255, 0.2) !important;
    }

    /* === BUTTONS === */
    .stButton > button {
        background: rgba(255, 255, 255, 0.06) !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
        color: rgba(255, 255, 255, 0.9) !important;
        font-weight: 500 !important;
        font-size: 14px !important;
        padding: 10px 28px !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.15) !important;
    }
    .stButton > button[kind="primary"] {
        background: rgba(255, 255, 255, 0.95) !important;
        color: #0a0a0f !important;
        border-color: transparent !important;
        font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover {
        background: #fff !important;
        box-shadow: 0 2px 16px rgba(255, 255, 255, 0.08) !important;
    }

    /* === STAT PILL === */
    .stat-pill {
        text-align: center;
        padding: 20px 0;
    }
    .stat-pill__value {
        font-size: 30px;
        font-weight: 700;
        letter-spacing: -0.03em;
        line-height: 1;
        margin: 0;
    }
    .stat-pill__label {
        font-size: 11px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.3);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 8px;
    }

    /* === GAUGE === */
    .gauge {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 999px;
        height: 4px;
        overflow: hidden;
    }
    .gauge__fill {
        height: 100%;
        border-radius: 999px;
        transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .gauge__label {
        font-size: 12px;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.35);
        margin-top: 6px;
    }

    /* === VERDICT HEADER === */
    .verdict {
        border-radius: 16px;
        padding: 28px 32px;
        border: 1px solid;
        background: rgba(255, 255, 255, 0.02);
        -webkit-backdrop-filter: blur(16px);
        backdrop-filter: blur(16px);
    }
    .verdict--hoax  { border-color: rgba(239, 68, 68, 0.2); }
    .verdict--valid { border-color: rgba(34, 197, 94, 0.2); }
    .verdict--nei   { border-color: rgba(234, 179, 8, 0.2); }

    .verdict__title {
        font-size: 22px;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin: 0 0 6px;
    }
    .verdict__title--hoax  { color: #f87171; }
    .verdict__title--valid { color: #4ade80; }
    .verdict__title--nei   { color: #facc15; }

    .verdict__summary {
        color: rgba(255, 255, 255, 0.45);
        font-size: 14px;
        line-height: 1.55;
        margin: 0;
    }

    /* === BADGE === */
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 600;
        letter-spacing: 0.05em;
        text-transform: uppercase;
    }
    .badge--hoax  { background: rgba(239, 68, 68, 0.12); color: #f87171; }
    .badge--valid { background: rgba(34, 197, 94, 0.1); color: #4ade80; }
    .badge--nei   { background: rgba(234, 179, 8, 0.1); color: #facc15; }
    .badge--info  { background: rgba(255, 255, 255, 0.05); color: rgba(255, 255, 255, 0.4); }

    /* === SIDEBAR === */
    [data-testid="stSidebar"] {
        background: rgba(10, 10, 15, 0.85) !important;
        -webkit-backdrop-filter: blur(24px) !important;
        backdrop-filter: blur(24px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.04) !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label {
        color: rgba(255, 255, 255, 0.7) !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] > div {
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 10px !important;
    }

    /* === EXPANDERS === */
    div[data-testid="stExpander"] {
        border: 1px solid rgba(255, 255, 255, 0.04) !important;
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] > summary {
        background: rgba(255, 255, 255, 0.02) !important;
        color: rgba(255, 255, 255, 0.65) !important;
        font-weight: 500 !important;
        font-size: 14px !important;
    }
    div[data-testid="stExpander"] > summary:hover {
        background: rgba(255, 255, 255, 0.03) !important;
    }
    div[data-testid="stExpander"] > div {
        background: transparent !important;
    }

    /* === DIVIDERS === */
    .stDivider {
        border-color: rgba(255, 255, 255, 0.04) !important;
    }

    /* === SECTION HEADING === */
    .heading {
        font-size: 13px;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.35);
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 12px;
    }

    /* === EXPORT LINK === */
    .export-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 8px;
        color: rgba(255, 255, 255, 0.5) !important;
        text-decoration: none !important;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .export-link:hover {
        background: rgba(255, 255, 255, 0.07);
        color: rgba(255, 255, 255, 0.7) !important;
    }

    /* === FOOTER === */
    .footer {
        color: rgba(255, 255, 255, 0.15);
        font-size: 11px;
        text-align: center;
        padding: 24px 0 12px;
    }

    /* === HISTORY ROW === */
    .history-row {
        padding: 8px 12px;
        margin: 4px 0;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.03);
        border-radius: 8px;
        font-size: 12px;
        color: rgba(255, 255, 255, 0.5);
    }

    /* === RADIO BUTTON === */
    .stRadio > label {
        color: rgba(255, 255, 255, 0.5) !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }

    /* === ALERTS === */
    .stAlert {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 10px !important;
    }

    /* === HIDE STREAMLIT BRANDING === */
    #MainMenu { visibility: hidden !important; }
    footer { visibility: hidden !important; }

    /* === SCROLLBAR === */
    ::-webkit-scrollbar { width: 4px !important; }
    ::-webkit-scrollbar-track { background: transparent !important; }
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.06) !important;
        border-radius: 2px !important;
    }

    /* === JSON VIEWER === */
    .stJson {
        background: rgba(0, 0, 0, 0.15) !important;
        border-radius: 10px !important;
    }

    /* === ST SPINNER === */
    .stSpinner > div {
        border-color: rgba(255, 255, 255, 0.15) !important;
        border-top-color: rgba(255, 255, 255, 0.4) !important;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Background Layer
# ============================================================
st.markdown("""
<div class="bg-layer">
    <div class="glow-orb glow-orb--a"></div>
    <div class="glow-orb glow-orb--b"></div>
    <div class="glow-orb glow-orb--c"></div>
</div>
""", unsafe_allow_html=True)


# ============================================================
# Helpers
# ============================================================

API_URL = os.environ.get("FAKTA_API_URL", "http://localhost:8000")


def check_article(text: str, title: str = "") -> dict | None:
    payload = {"text": text, "title": title}
    try:
        response = requests.post(f"{API_URL}/check", json=payload, timeout=120)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error("Cannot connect to API. Make sure the server is running.")
        return None
    except Exception as e:
        st.error(f"Error: {e}")
        return None


def submit_feedback(claim, system_verdict, human_verdict, is_correct, notes=""):
    payload = {
        "claim": claim,
        "system_verdict": system_verdict,
        "human_verdict": human_verdict,
        "is_correct": is_correct,
        "notes": notes,
    }
    try:
        return requests.post(f"{API_URL}/feedback", json=payload, timeout=10).status_code == 200
    except Exception:
        return False


def get_stats() -> dict | None:
    try:
        r = requests.get(f"{API_URL}/stats", timeout=5)
        return r.json() if r.status_code == 200 else None
    except Exception:
        return None


def verdict_variant(v: str) -> str:
    if "Hoax" in v and "Tidak" not in v:
        return "hoax"
    elif "Tidak Hoax" in v:
        return "valid"
    return "nei"


def badge_cls(v: str) -> str:
    if "Hoax" in v and "Tidak" not in v:
        return "badge--hoax"
    elif "Tidak Hoax" in v:
        return "badge--valid"
    return "badge--nei"


def gauge(value: float, color: str = "rgba(255,255,255,0.4)") -> str:
    pct = min(value * 100, 100)
    return f"""
    <div class="gauge">
        <div class="gauge__fill" style="width:{pct}%;background:{color};"></div>
    </div>
    <div class="gauge__label">{value:.0%}</div>
    """


def export_link(result: dict) -> str:
    j = json.dumps(result, indent=2, ensure_ascii=False)
    b64 = base64.b64encode(j.encode()).decode()
    fn = f"fakta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    return f'<a class="export-link" href="data:application/json;base64,{b64}" download="{fn}">Export JSON</a>'


# ============================================================
# Session State
# ============================================================
if "history" not in st.session_state:
    st.session_state.history = []
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ============================================================
# Sidebar
# ============================================================
with st.sidebar:
    st.markdown("### FAKTA")
    st.caption("Fact-Checking AI")
    st.divider()

    # Connection status
    try:
        r = requests.get(f"{API_URL}/", timeout=3)
        if r.status_code == 200:
            st.success("Connected")
        else:
            st.warning("Unresponsive")
    except:
        st.error("Disconnected")

    st.divider()

    with st.expander("Statistics"):
        s = get_stats()
        if s:
            if s.get("pipeline_initialized"):
                st.success("Pipeline active")
            else:
                st.warning("Pipeline not initialized")
            c = s.get("cache_stats", {})
            if c:
                st.json(c)
        else:
            st.info("Unavailable")

    st.divider()

    with st.expander("History"):
        if st.session_state.history:
            for ts, snippet, v, _ in reversed(st.session_state.history[-10:]):
                badge = badge_cls(v)
                short = snippet[:35] + ("..." if len(snippet) > 35 else "")
                st.markdown(
                    f'<div class="history-row">'
                    f'<span class="badge {badge}">{v}</span><br>'
                    f'{short}<br>'
                    f'<span style="color:rgba(255,255,255,0.2);font-size:10px;">{ts}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No history yet.")

    st.divider()
    st.markdown("### Evidence Sources")
    st.markdown("""
    - Google Fact Check API
    - TurnBackHoax / MAFINDO
    - Official sources (BPOM, BMKG)
    - Wikipedia (fallback)
    """)


# ============================================================
# Main
# ============================================================

# --- Header ---
st.markdown("""
<div style="padding: 32px 0 24px;">
    <h1 style="font-size:28px;font-weight:700;color:rgba(255,255,255,0.95);margin:0;letter-spacing:-0.03em;">FAKTA</h1>
    <p style="color:rgba(255,255,255,0.3);margin:4px 0 0;font-size:14px;font-weight:400;">
        Hybrid LSTM + LLM + Evidence &mdash; Indonesian Hoax Detection
    </p>
</div>
""", unsafe_allow_html=True)

# --- Input ---
st.markdown('<div class="card">', unsafe_allow_html=True)

mode = st.radio("Input Mode", ["Text", "URL"], horizontal=True, label_visibility="collapsed")

if mode == "Text":
    title_input = st.text_input("Title", placeholder="Optional")
    text_input = st.text_area(
        "Text",
        placeholder="Paste the article or post text here...",
        height=150,
        label_visibility="collapsed" if not text_input else "visible",
    )
else:
    url_val = st.text_input("Article URL", placeholder="https://example.com/article")
    st.caption("The URL content will be fetched and analyzed.")
    title_input = ""
    text_input = url_val

b1, b2, _ = st.columns([1, 1, 4])
with b1:
    submitted = st.form_submit_button("Check", use_container_width=True, type="primary")
with b2:
    clear_btn = st.form_submit_button("Reset", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

if clear_btn:
    st.session_state.last_result = None
    st.rerun()

# ============================================================
# Process
# ============================================================
if submitted:
    check_text = text_input.strip()
    if not check_text:
        st.warning("Enter text or a URL to proceed.")
        st.stop()

    with st.spinner("Analyzing..."):
        result = check_article(check_text, title_input)

    if not result:
        st.stop()

    st.session_state.last_result = result

    ts = datetime.now().strftime("%H:%M")
    snippet = title_input or check_text
    st.session_state.history.append((ts, snippet, result["verdict"], result))

    v = verdict_variant(result["verdict"])

    # --- Verdict Banner ---
    color_map = {"hoax": "#f87171", "valid": "#4ade80", "nei": "#facc15"}
    v_color = color_map[v]

    st.markdown(
        f'<div class="verdict verdict--{v}">'
        f'<p class="verdict__title verdict__title--{v}">{result["verdict"]}</p>'
        f'<p class="verdict__summary">{result.get("summary", "")}</p>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # --- Metrics ---
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            f'<div class="stat-pill">'
            f'<p class="stat-pill__value" style="color:{v_color};">{result["confidence"]:.0%}</p>'
            f'<p class="stat-pill__label">Confidence</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c2:
        hs_c = "#f87171" if result["avg_hoax_score"] > 0.6 else ("#4ade80" if result["avg_hoax_score"] < 0.3 else "#facc15")
        st.markdown(
            f'<div class="stat-pill">'
            f'<p class="stat-pill__value" style="color:{hs_c};">{result["avg_hoax_score"]:.2f}</p>'
            f'<p class="stat-pill__label">Hoax Score</p>'
            f'</div>',
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f'<div class="stat-pill">'
            f'<p class="stat-pill__value" style="color:rgba(255,255,255,0.5);">{result.get("processing_time_ms", 0):.0f}</p>'
            f'<p class="stat-pill__label">ms</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # --- Gauges ---
    st.markdown('<p class="heading">Analysis Signals</p>', unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        conf = result["confidence"]
        gc = v_color if conf > 0.5 else "rgba(255,255,255,0.25)"
        st.markdown(gauge(conf, gc), unsafe_allow_html=True)
    with g2:
        hs = result["avg_hoax_score"]
        hc = "#f87171" if hs > 0.6 else ("#4ade80" if hs < 0.3 else "#facc15")
        st.markdown(gauge(hs, hc), unsafe_allow_html=True)

    # --- Claim Details ---
    if result.get("claims"):
        st.markdown('<p class="heading" style="margin-top:28px;">Claims</p>', unsafe_allow_html=True)

        for i, claim in enumerate(result["claims"], 1):
            c_badge = badge_cls(claim["verdict"])
            claim_type = claim.get("claim_type", "").capitalize()

            with st.expander(f"Claim {i}: {claim['claim_text'][:70]}{'...' if len(claim['claim_text']) > 70 else ''}"):
                st.markdown(
                    f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:16px;">'
                    f'<span class="badge {c_badge}">{claim["verdict"]}</span>'
                    f'<span class="badge badge--info">{claim_type}</span>'
                    f'<span class="badge badge--info">{claim["mode"]}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Signals row
                s1, s2, s3 = st.columns(3)
                with s1:
                    st.markdown("##### LSTM")
                    lh = claim.get("lstm_hoax_proba", 0)
                    lc = "#f87171" if lh > 0.5 else "#4ade80"
                    st.markdown(gauge(lh, lc), unsafe_allow_html=True)
                with s2:
                    st.markdown("##### LLM Judge")
                    st.markdown(f'**{claim["llm_verdict"]}**')
                    st.markdown(gauge(claim.get("llm_confidence", 0), "#a78bfa"), unsafe_allow_html=True)
                with s3:
                    st.markdown("##### Evidence")
                    sources = claim.get("evidence_sources", [])
                    st.caption(", ".join(sources) if sources else "None found")
                    st.caption(f"Mode: {claim['mode']}")

                # Fusion
                st.markdown("###### Fusion Result")
                fc = claim.get("confidence", 0)
                st.markdown(gauge(fc, v_color), unsafe_allow_html=True)
                st.caption(claim.get("reasoning", ""))

    # --- Claim Stats ---
    if result.get("claim_stats"):
        cs = result["claim_stats"]
        st.markdown('<p class="heading" style="margin-top:28px;">Claim Summary</p>', unsafe_allow_html=True)

        total = cs.get("total_claims", 0)
        hoax = cs.get("hoax_claims", 0)
        valid = cs.get("valid_claims", 0)
        nei = cs.get("nei_claims", 0) or cs.get("uncertain_claims", 0)

        s1, s2, s3, s4 = st.columns(4)
        with s1:
            st.markdown(f'<div class="stat-pill"><p class="stat-pill__value">{total}</p><p class="stat-pill__label">Total</p></div>', unsafe_allow_html=True)
        with s2:
            st.markdown(f'<div class="stat-pill"><p class="stat-pill__value" style="color:#f87171;">{hoax}</p><p class="stat-pill__label">Hoax</p></div>', unsafe_allow_html=True)
        with s3:
            st.markdown(f'<div class="stat-pill"><p class="stat-pill__value" style="color:#4ade80;">{valid}</p><p class="stat-pill__label">Valid</p></div>', unsafe_allow_html=True)
        with s4:
            st.markdown(f'<div class="stat-pill"><p class="stat-pill__value" style="color:#facc15;">{nei}</p><p class="stat-pill__label">Insufficient Evidence</p></div>', unsafe_allow_html=True)

    # --- Export ---
    st.markdown("---")
    st.markdown(export_link(result), unsafe_allow_html=True)

    with st.expander("Raw JSON"):
        st.json(result)

    # --- Feedback ---
    st.markdown("---")
    st.markdown('<p class="heading">Feedback</p>', unsafe_allow_html=True)
    st.caption("Help us improve accuracy by providing your assessment.")

    if result.get("claims"):
        opts = [f"Claim {i+1}: {c['claim_text'][:50]}{'...' if len(c['claim_text']) > 50 else ''}" for i, c in enumerate(result["claims"])]
        idx = st.selectbox("Select Claim", range(len(opts)), format_func=lambda i: opts[i])
        sel = result["claims"][idx]

        f1, f2 = st.columns([3, 2])
        with f1:
            hv = st.radio("Your verdict", ["Hoax", "Valid", "Insufficient Evidence"], horizontal=True)
        with f2:
            notes = st.text_input("Notes (optional)")

        if st.button("Submit Feedback", use_container_width=True):
            ok = submit_feedback(sel["claim_text"], sel["verdict"], hv, hv == sel["verdict"], notes)
            if ok:
                st.success("Feedback submitted.")
            else:
                st.warning("API unavailable, but feedback noted locally.")

else:
    # --- Examples ---
    st.markdown("---")
    st.markdown('<p class="heading">Try an Example</p>', unsafe_allow_html=True)

    examples = [
        ("Hoax Example", "VIRAL!!! Matcha menyebabkan gagal ginjal dan sudah banyak korban meninggal!! Sebarkan sebelum dihapus!! Obat ini disembunyikan oleh pemerintah!!"),
        ("Valid Example", "BMKG mencatat gempa magnitudo 5.2 di Maluku pada tanggal 15 Januari 2025. Gempa tidak berpotensi tsunami. Warga dihimbau tetap tenang."),
        ("Uncertain Example", "Kabar beredar bahwa harga BBM akan naik bulan depan. Pemerintah belum memberikan konfirmasi resmi mengenai hal ini."),
    ]

    for label, txt in examples:
        if st.button(label, use_container_width=True):
            st.session_state.example_text = txt
            st.rerun()

    if "example_text" in st.session_state:
        st.info("Click **Check** to analyze the example text.")

# Footer
st.markdown("---")
st.markdown('<p class="footer">FAKTA v2.0</p>', unsafe_allow_html=True)
