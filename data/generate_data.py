"""
Generates a rich 9-month daily business dataset for InsightGuard.
Run once: python data/generate_data.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

np.random.seed(42)

# --- Date range: Feb 2024 → Oct 2024 (9 months, ~274 days) ---
dates = pd.date_range(start="2024-02-01", end="2024-10-25", freq="D")
n = len(dates)

# ── Base trends (slow growth over months) ──────────────────────
t = np.linspace(0, 1, n)  # time 0→1

# Revenue: upward trend + seasonality + noise
revenue_base = 80_000 + 40_000 * t
revenue_season = 8_000 * np.sin(2 * np.pi * t * 9)   # ~9 peaks
revenue_noise = np.random.normal(0, 3_000, n)
revenue = revenue_base + revenue_season + revenue_noise

# Orders: correlated with revenue
orders_base = 400 + 200 * t
orders_noise = np.random.normal(0, 25, n)
orders = orders_base + orders_noise

# Traffic: higher volatility
traffic_base = 12_000 + 6_000 * t
traffic_season = 1_500 * np.sin(2 * np.pi * t * 12)
traffic_noise = np.random.normal(0, 700, n)
traffic = traffic_base + traffic_season + traffic_noise

# Conversion rate (%): slight downward pressure over time
conversion_base = 4.5 - 0.5 * t
conversion_noise = np.random.normal(0, 0.2, n)
conversion = np.clip(conversion_base + conversion_noise, 1.5, 7.0)

# Cost: rises with scale
cost_base = 35_000 + 20_000 * t
cost_noise = np.random.normal(0, 2_000, n)
cost = cost_base + cost_noise

# Refunds: occasional spikes
refunds_base = 30 + 20 * t
refunds_noise = np.random.normal(0, 8, n)
refunds = np.clip(refunds_base + refunds_noise, 0, None)

# ── Inject realistic anomalies ──────────────────────────────────
def spike(arr, idx, factor):
    arr = arr.copy()
    arr[idx] = arr[idx] * factor
    return arr

# March flash sale: revenue/orders/traffic spike
march_start = list(dates).index(pd.Timestamp("2024-03-15"))
for i in range(5):
    revenue = spike(revenue, march_start + i, 1.6)
    orders  = spike(orders,  march_start + i, 1.5)
    traffic = spike(traffic, march_start + i, 1.8)

# May product issue: refunds spike, conversion drops
may_start = list(dates).index(pd.Timestamp("2024-05-10"))
for i in range(4):
    refunds    = spike(refunds,    may_start + i, 4.5)
    conversion = spike(conversion, may_start + i, 0.55)

# July cost overrun
jul_start = list(dates).index(pd.Timestamp("2024-07-08"))
for i in range(3):
    cost = spike(cost, jul_start + i, 1.55)

# September traffic drop (SEO issue)
sep_start = list(dates).index(pd.Timestamp("2024-09-05"))
for i in range(6):
    traffic    = spike(traffic,    sep_start + i, 0.45)
    conversion = spike(conversion, sep_start + i, 1.3)

# October anomaly (matches original data feel)
oct_start = list(dates).index(pd.Timestamp("2024-10-20"))
for i in range(5):
    revenue = spike(revenue, oct_start + i, 1.56)
    traffic = spike(traffic, oct_start + i, 1.87)
    refunds = spike(refunds, oct_start + i, 4.27)
    conversion = spike(conversion, oct_start + i, 0.56)
    cost    = spike(cost,    oct_start + i, 1.44)

# ── Build DataFrame ──────────────────────────────────────────────
df = pd.DataFrame({
    "Date":       dates,
    "Revenue":    np.round(revenue, 2),
    "Orders":     np.round(orders).astype(int),
    "Traffic":    np.round(traffic).astype(int),
    "Conversion": np.round(conversion, 3),
    "Cost":       np.round(cost, 2),
    "Refunds":    np.round(refunds).astype(int),
})

out = Path(__file__).parent / "business_data.xlsx"
df.to_excel(out, index=False)
print(f"✅ Generated {len(df)} rows ({dates[0].date()} → {dates[-1].date()}) → {out}")
