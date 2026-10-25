import streamlit as st
import pandas as pd
from pathlib import Path
from anomaly_detector import calculate_metrics, detect_anomalies
from business_insights import generate_business_insights
from email_alert import send_email_alert
from config import get_config

st.set_page_config(page_title="InsightGuard", page_icon="🛡️", layout="wide")

BASE_DIR  = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "business_data.xlsx"
HISTORY   = BASE_DIR / "output" / "alert_history.csv"
METRICS   = ["Revenue", "Orders", "Traffic", "Conversion", "Cost", "Refunds"]

# ── Load & clean data ──────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_excel(DATA_FILE)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = (df.dropna(subset=["Date"])
            .drop_duplicates()
            .sort_values("Date")
            .reset_index(drop=True))
    return df

df = load_data()

# ── Sidebar controls ───────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Controls")
threshold = st.sidebar.slider("Anomaly Threshold (%)", 5, 50, 20, 5)

min_d = df["Date"].min().date()
max_d = df["Date"].max().date()

# Quick range presets
preset = st.sidebar.selectbox(
    "Quick Date Range",
    ["Custom", "Last 7 Days", "Last 30 Days", "Last 90 Days", "Last 6 Months", "All Time"],
    index=0,
)

if preset == "Last 7 Days":
    start, end = max_d - pd.Timedelta(days=6), max_d
elif preset == "Last 30 Days":
    start, end = max_d - pd.Timedelta(days=29), max_d
elif preset == "Last 90 Days":
    start, end = max_d - pd.Timedelta(days=89), max_d
elif preset == "Last 6 Months":
    start = (pd.Timestamp(max_d) - pd.DateOffset(months=6)).date()
    end   = max_d
elif preset == "All Time":
    start, end = min_d, max_d
else:
    # Custom — show date picker
    raw = st.sidebar.date_input(
        "Custom Date Range",
        value=(min_d, max_d),
        min_value=min_d,
        max_value=max_d,
    )
    # Robust unpacking: handle single-date or tuple
    if isinstance(raw, (list, tuple)):
        if len(raw) == 2:
            start, end = raw[0], raw[1]
        else:
            start = end = raw[0]
    else:
        start = end = raw

# Ensure start <= end
if start > end:
    start, end = end, start

st.sidebar.markdown(f"**Range:** {start} → {end}")
days_selected = (pd.Timestamp(end) - pd.Timestamp(start)).days + 1
st.sidebar.caption(f"{days_selected} day(s) selected")

# ── Filter data ────────────────────────────────────────────────────────────────
filtered = df[(df["Date"].dt.date >= start) & (df["Date"].dt.date <= end)].copy()

if filtered.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

# ── Run analytics on filtered data so KPIs/anomalies reflect the selected range
# We include enough leading rows for the 7-day rolling window to warm up
WINDOW = 7
start_idx = max(0, df[df["Date"].dt.date >= start].index.min() - WINDOW)
extended = df.iloc[start_idx:].copy()
analysis_extended = calculate_metrics(extended, METRICS, window=WINDOW)

# Now slice back to the user's selected date range
analysis_filtered = analysis_extended[
    (analysis_extended["Date"].dt.date >= start) &
    (analysis_extended["Date"].dt.date <= end)
]

if analysis_filtered.empty:
    st.warning("No data available for the selected date range.")
    st.stop()

latest = analysis_filtered.iloc[-1]
anomalies = detect_anomalies(analysis_filtered, METRICS, threshold)
insights  = generate_business_insights(latest, threshold)

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🛡️ InsightGuard")
st.caption("Automated Business Analytics & Anomaly Monitoring")

# ── KPI Metrics row ────────────────────────────────────────────────────────────
st.subheader("📊 Latest Business Performance")
cols = st.columns(6)

def delta_str(col_name):
    """Return a formatted delta string for a metric."""
    dev = latest.get(f"{col_name}_Change", None)
    if dev is None or pd.isna(dev):
        return None
    return f"{dev:+.1f}%"

kpi_defs = [
    ("Revenue",    f"₹{latest['Revenue']:,.0f}",           "Revenue_Change"),
    ("Orders",     f"{latest['Orders']:,.0f}",              "Orders_Change"),
    ("Traffic",    f"{latest['Traffic']:,.0f}",             "Traffic_Change"),
    ("Conversion", f"{latest['Conversion']:.2f}%",         "Conversion_Change"),
    ("Cost",       f"₹{latest['Cost']:,.0f}",              "Cost_Change"),
    ("Refunds",    f"{latest['Refunds']:,.0f}",             "Refunds_Change"),
]

for col, (label, value, change_col) in zip(cols, kpi_defs):
    delta = delta_str(change_col)
    col.metric(label, value, delta=delta)

# ── Anomaly Monitoring ─────────────────────────────────────────────────────────
st.divider()
st.subheader("🚨 Anomaly Monitoring")

if anomalies:
    adf = pd.DataFrame(anomalies)
    crit = sum(1 for a in anomalies if a["Severity"] == "Critical")
    high = sum(1 for a in anomalies if a["Severity"] == "High")
    med  = sum(1 for a in anomalies if a["Severity"] == "Medium")

    c1, c2, c3 = st.columns(3)
    c1.error(f"🔴 Critical: {crit}")
    c2.warning(f"🟠 High: {high}")
    c3.info(f"🟡 Medium: {med}")

    st.dataframe(adf, use_container_width=True, hide_index=True)
    st.download_button(
        "⬇️ Download Anomaly Report",
        adf.to_csv(index=False),
        "insightguard_anomaly_report.csv",
        "text/csv",
    )
else:
    st.success("✅ No significant anomalies detected for this period.")

# ── Trend Charts ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("📈 Business Trends")

if len(filtered) < 2:
    st.info("Select a wider date range to see trend charts.")
else:
    metric = st.selectbox("Choose a metric to plot", METRICS)
    st.line_chart(filtered[["Date", metric]].set_index("Date"), use_container_width=True)

    col_left, col_right = st.columns(2)
    with col_left:
        st.subheader("💰 Revenue Trend")
        st.area_chart(filtered[["Date", "Revenue"]].set_index("Date"), use_container_width=True)
    with col_right:
        st.subheader("🛒 Orders & Traffic")
        st.line_chart(filtered[["Date", "Orders", "Traffic"]].set_index("Date"), use_container_width=True)

    col_l2, col_r2 = st.columns(2)
    with col_l2:
        st.subheader("🔄 Conversion Rate (%)")
        st.line_chart(filtered[["Date", "Conversion"]].set_index("Date"), use_container_width=True)
    with col_r2:
        st.subheader("⚠️ Refunds Over Time")
        st.bar_chart(filtered[["Date", "Refunds"]].set_index("Date"), use_container_width=True)

    st.subheader("📉 Cost vs Revenue")
    st.line_chart(filtered[["Date", "Revenue", "Cost"]].set_index("Date"), use_container_width=True)

# ── Monthly Summary Table ──────────────────────────────────────────────────────
st.divider()
st.subheader("📅 Monthly Summary")

if not filtered.empty:
    monthly = (
        filtered.copy()
        .assign(Month=filtered["Date"].dt.to_period("M"))
        .groupby("Month")
        .agg(
            Revenue   =("Revenue", "sum"),
            Orders    =("Orders", "sum"),
            Traffic   =("Traffic", "sum"),
            Conversion=("Conversion", "mean"),
            Cost      =("Cost", "sum"),
            Refunds   =("Refunds", "sum"),
        )
        .reset_index()
    )
    monthly["Month"] = monthly["Month"].astype(str)
    monthly["Revenue"]    = monthly["Revenue"].map("₹{:,.0f}".format)
    monthly["Cost"]       = monthly["Cost"].map("₹{:,.0f}".format)
    monthly["Conversion"] = monthly["Conversion"].map("{:.2f}%".format)
    st.dataframe(monthly, use_container_width=True, hide_index=True)

# ── Business Intelligence ──────────────────────────────────────────────────────
st.divider()
st.subheader("🧠 Business Intelligence")

if insights:
    for x in insights:
        st.warning(x)
else:
    st.success("No major business issues detected.")

# ── Alert History ──────────────────────────────────────────────────────────────
st.divider()
st.subheader("📜 Alert History")

# Build history: load CSV (if exists) + always show current anomalies
history_rows = []

if HISTORY.exists():
    try:
        h = pd.read_csv(HISTORY)
        h["Date"] = pd.to_datetime(h["Date"], errors="coerce")
        history_rows.append(h)
    except Exception:
        pass

# Always surface today's detected anomalies
if anomalies:
    today_rows = pd.DataFrame([{
        "Date": latest["Date"].strftime("%Y-%m-%d"),
        "Metric": a["Metric"],
        "Direction": a["Direction"],
        "Deviation (%)": a["Deviation (%)"],
        "Severity": a["Severity"],
    } for a in anomalies])
    today_rows["Date"] = pd.to_datetime(today_rows["Date"])
    history_rows.append(today_rows)

if history_rows:
    combined = pd.concat(history_rows, ignore_index=True).drop_duplicates()
    combined["Date"] = pd.to_datetime(combined["Date"], errors="coerce")
    combined = combined.sort_values("Date", ascending=False)
    h_filtered = combined[
        (combined["Date"].dt.date >= start) & (combined["Date"].dt.date <= end)
    ]
    if h_filtered.empty:
        st.info("No alerts for the selected date range.")
    else:
        st.dataframe(h_filtered.reset_index(drop=True), use_container_width=True, hide_index=True)
else:
    st.success("No anomalies detected — alert history is empty.")

# ── Raw Data Expander ──────────────────────────────────────────────────────────
with st.expander("🔍 View Raw Business Data"):
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True, hide_index=True)

# ── Auto Email Alerts (Resend API) ────────────────────────────────────────────
resend_api_key   = get_config("RESEND_API_KEY")
default_receiver = get_config("EMAIL_RECEIVER")   # optional — auto-send target

# Fingerprint of current anomaly batch (prevents duplicate sends per session)
anomaly_fingerprint = "|".join(
    f"{a['Metric']}-{a['Direction']}-{a['Deviation (%)']}" for a in anomalies
) if anomalies else ""

if "last_alerted_fingerprint" not in st.session_state:
    st.session_state.last_alerted_fingerprint = ""
if "auto_send_failed" not in st.session_state:
    st.session_state.auto_send_failed = False

def build_alert_body():
    from report_generator import generate_executive_summary
    summary = generate_executive_summary(anomalies, insights)
    body = "INSIGHTGUARD BUSINESS ALERT\n\n" + summary + "\n\nANOMALY DETAILS:\n"
    for a in anomalies:
        body += f"  • {a['Metric']}: {a['Direction']} {abs(a['Deviation (%)']):.2f}% [{a['Severity']}]\n"
    body += f"\nDate analysed: {latest['Date'].strftime('%Y-%m-%d')}"
    body += "\n\n-- InsightGuard Automated Alert System"
    return body

# Auto-send only when: API key set + default receiver set + new anomaly fingerprint
if anomalies and resend_api_key and default_receiver:
    if st.session_state.last_alerted_fingerprint != anomaly_fingerprint:
        ok, err = send_email_alert(
            resend_api_key, default_receiver,
            f"InsightGuard Alert — {len(anomalies)} Anomaly/Anomalies Detected",
            build_alert_body()
        )
        if ok:
            st.session_state.last_alerted_fingerprint = anomaly_fingerprint
            st.session_state.auto_send_failed = False
            st.session_state.auto_send_error = ""
        else:
            st.session_state.auto_send_failed = True
            st.session_state.auto_send_error = err

# ── Email Status + Manual Send ────────────────────────────────────────────────
st.divider()
st.subheader("📧 Email Alerts")

if "auto_send_error" not in st.session_state:
    st.session_state.auto_send_error = ""

if not resend_api_key:
    st.info("Email alerts ready — add `RESEND_API_KEY` to Secrets to activate.")
else:
    # Show auto-send status
    if not anomalies:
        st.success("✅ No anomalies — no alert needed.")
    elif not default_receiver:
        st.info("ℹ️ API key active. Add `EMAIL_RECEIVER` to Secrets for automatic alerts.")
    elif st.session_state.last_alerted_fingerprint == anomaly_fingerprint:
        st.success(f"✅ Auto-alert sent to **{default_receiver}**.")
    elif st.session_state.auto_send_failed:
        st.error(f"❌ Auto-send failed: {st.session_state.auto_send_error or 'unknown error'}")
    else:
        st.info("📤 Sending auto-alert...")

    # Manual send form — anyone can get the report
    st.markdown("**Send this report to any email:**")
    with st.form("manual_email_form"):
        to_addr = st.text_input("Recipient email", placeholder="enter your email...")
        send_btn = st.form_submit_button("Send Report")

    if send_btn:
        if not to_addr:
            st.error("Please enter a recipient email address.")
        elif not anomalies:
            st.warning("No anomalies in the selected period — nothing to send.")
        else:
            ok, err = send_email_alert(
                resend_api_key, to_addr,
                f"InsightGuard Report — {len(anomalies)} Anomaly/Anomalies Detected",
                build_alert_body()
            )
            if ok:
                st.success(f"✅ Report sent to **{to_addr}**!")
            else:
                st.error(f"Failed to send: {err}")



st.caption("InsightGuard | Automated Business Analytics & Anomaly Monitoring System")

