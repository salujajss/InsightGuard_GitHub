def generate_executive_summary(anomalies, insights):
    if not anomalies:
        return "Overall business performance appears stable. No significant metric deviations were detected."
    c=sum(a["Severity"]=="Critical" for a in anomalies)
    h=sum(a["Severity"]=="High" for a in anomalies)
    m=sum(a["Severity"]=="Medium" for a in anomalies)
    parts=[f"InsightGuard detected {len(anomalies)} significant business anomalies."]
    if c: parts.append(f"{c} critical anomaly/anomalies require immediate attention.")
    if h: parts.append(f"{h} high-severity anomaly/anomalies should be reviewed.")
    if m: parts.append(f"{m} medium-severity anomaly/anomalies should be monitored.")
    if insights: parts.append(insights[0])
    return " ".join(parts)
