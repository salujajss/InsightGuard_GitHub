# 🛡️ InsightGuard
## Automated Business Analytics & Anomaly Monitoring System

InsightGuard reads business data from Excel, calculates historical baselines, detects unusual metric behavior, generates business-friendly insights, displays results in a Streamlit dashboard, and can send email alerts.

### Features
- Excel data ingestion and validation
- Daily metric changes
- 7-day historical baseline
- Threshold-based anomaly detection
- Medium/High/Critical severity
- Business insights and executive summary
- Email alerts
- Alert history
- Interactive Streamlit dashboard
- Trend charts and downloadable reports

### Metrics
Revenue, Orders, Traffic, Conversion, Cost, Refunds.

### Architecture
```text
Excel → Cleaning → Metrics → 7-Day Baseline → Anomaly Detection
      → Business Insights → Executive Summary → Dashboard + Email
```

### Setup
```bash
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and enter your Gmail/App Password details. **Never upload `.env` to GitHub.**

Run analytics:
```bash
python src/main.py
```

Run dashboard:
```bash
streamlit run src/dashboard.py
```

### Project Structure
```text
InsightGuard/
├── data/business_data.xlsx
├── output/
├── src/
│   ├── main.py
│   ├── dashboard.py
│   ├── anomaly_detector.py
│   ├── business_insights.py
│   ├── email_alert.py
│   ├── alert_history.py
│   ├── report_generator.py
│   └── config.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

### Future Improvements
Machine-learning anomaly detection, forecasting, database integration, Slack/Teams alerts, scheduling, and cloud deployment.

## Author
**Angad Singh Sandhu**  
B.Tech Information Technology
