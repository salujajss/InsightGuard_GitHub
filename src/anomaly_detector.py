import pandas as pd


def calculate_metrics(df, metrics, window=7):
    """Compute rolling baseline, deviation, and daily change for each metric."""
    for m in metrics:
        df[f"{m}_Change"]    = df[m].pct_change() * 100
        df[f"{m}_Baseline"]  = df[m].rolling(window).mean().shift(1)
        b = df[f"{m}_Baseline"]
        df[f"{m}_Deviation"] = ((df[m] - b) / b) * 100
        df[f"{m}_Anomaly"]   = df[f"{m}_Deviation"].abs() > 20
    return df


def detect_anomalies(df, metrics, threshold=20):
    """
    Detect anomalies on the LAST row of the provided DataFrame.
    Pass a date-filtered slice so anomalies reflect the selected period.
    Returns [] if the DataFrame is empty or the last row has no valid baseline.
    """
    if df is None or df.empty:
        return []

    latest = df.iloc[-1]
    out = []

    for m in metrics:
        dev_col = f"{m}_Deviation"
        if dev_col not in latest.index:
            continue
        d = latest[dev_col]
        if pd.isna(d) or abs(d) <= threshold:
            continue
        severity = (
            "Critical" if abs(d) >= 50
            else "High"  if abs(d) >= 30
            else "Medium"
        )
        out.append({
            "Metric":        m,
            "Current Value": round(latest[m], 2),
            "Baseline":      round(latest[f"{m}_Baseline"], 2) if not pd.isna(latest[f"{m}_Baseline"]) else None,
            "Deviation (%)": round(d, 2),
            "Direction":     "Increase" if d > 0 else "Decrease",
            "Severity":      severity,
        })

    return out
