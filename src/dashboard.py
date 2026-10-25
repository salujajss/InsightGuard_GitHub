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

# ── Run analytics on FULL data (for stable 7-day baseline) ────────────────────
analysis = calculate_metrics(df.copy(), METRICS)

# Find the latest row WITHIN the selected date range for anomaly detection
analysis_filtered = analysis[(analysis["Date"].dt.date >= start) & (analysis["Date"].dt.date <= end)]

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

if HISTORY.exists():
    h = pd.read_csv(HISTORY)
    h["Date"] = pd.to_datetime(h["Date"], errors="coerce")
    # Filter history by selected range too
    h_filtered = h[(h["Date"].dt.date >= start) & (h["Date"].dt.date <= end)]
    if h_filtered.empty:
        st.info("No alerts recorded for the selected date range.")
    else:
        st.dataframe(h_filtered.sort_values("Date", ascending=False), use_container_width=True, hide_index=True)
else:
    st.info("No alert history available yet. Run main.py to generate it.")

# ── Raw Data Expander ──────────────────────────────────────────────────────────
with st.expander("🔍 View Raw Business Data"):
    st.dataframe(filtered.reset_index(drop=True), use_container_width=True, hide_index=True)

# ── Email Alerts ───────────────────────────────────────────────────────────────
st.divider()
st.subheader("📧 Email Alert")

email_sender   = get_config("EMAIL_SENDER")
email_password = get_config("EMAIL_PASSWORD")
email_receiver = get_config("EMAIL_RECEIVER")

if not email_sender or not email_password:
    st.info(
        "Email alerts are not configured. "
        "Add `EMAIL_SENDER`, `EMAIL_PASSWORD`, and `EMAIL_RECEIVER` to your "
        "`.env` file (local) or Streamlit Cloud **Secrets** (deployed)."
    )
else:
    with st.form("email_form"):
        to_addr = st.text_input("Send alert to", value=email_receiver or "")
        custom_note = st.text_area("Optional note", placeholder="Add any extra context here...")
        send_btn = st.form_submit_button("Send Anomaly Alert Email")

    if send_btn:
        if not anomalies:
            st.warning("No anomalies detected in the selected period — nothing to send.")
        elif not to_addr:
            st.error("Please enter a recipient email address.")
        else:
            from report_generator import generate_executive_summary
            summary = generate_executive_summary(anomalies, insights)
            body = "INSIGHTGUARD BUSINESS ALERT\n\n" + summary + "\n\n"
            for a in anomalies:
                body += f"{a['Metric']}: {a['Direction']} {abs(a['Deviation (%)']):.2f}% [{a['Severity']}]\n"
            if custom_note:
                body += f"\nNote:\n{custom_note}"
            ok = send_email_alert(email_sender, email_password, to_addr,
                                  "InsightGuard - Business Anomaly Detected", body)
            if ok:
                st.success(f"Email sent to {to_addr}!")
            else:
                st.error("Failed to send email. Check your credentials.")

st.caption("InsightGuard | Automated Business Analytics & Anomaly Monitoring System")
