import pandas as pd
from config import DATA_FILE,OUTPUT_DIR,EMAIL_SENDER,EMAIL_PASSWORD,EMAIL_RECEIVER,THRESHOLD
from anomaly_detector import calculate_metrics,detect_anomalies
from business_insights import generate_business_insights
from report_generator import generate_executive_summary
from email_alert import send_email_alert
from alert_history import save_alert_history

METRICS=["Revenue","Orders","Traffic","Conversion","Cost","Refunds"]
df=pd.read_excel(DATA_FILE)
df["Date"]=pd.to_datetime(df["Date"],errors="coerce")
df=df.dropna(subset=["Date"]).drop_duplicates().sort_values("Date").reset_index(drop=True)
df=calculate_metrics(df,METRICS)
anomalies=detect_anomalies(df,METRICS,THRESHOLD)
latest=df.iloc[-1]
insights=generate_business_insights(latest,THRESHOLD)
executive_summary=generate_executive_summary(anomalies,insights)

print("="*60); print("INSIGHTGUARD"); print("="*60)
print(f"Anomalies detected: {len(anomalies)}")
for a in anomalies: print(f"{a['Metric']}: {a['Direction']} {abs(a['Deviation (%)']):.2f}% [{a['Severity']}]")
print("\nEXECUTIVE SUMMARY\n"+executive_summary)

pd.DataFrame(anomalies).to_csv(OUTPUT_DIR/"anomaly_report.csv",index=False)
with open(OUTPUT_DIR/"business_summary.txt","w",encoding="utf-8") as f:
    f.write("INSIGHTGUARD BUSINESS SUMMARY\n\n"+executive_summary+"\n\n")
    for i,x in enumerate(insights,1): f.write(f"{i}. {x}\n")
df.to_excel(OUTPUT_DIR/"analyzed_data.xlsx",index=False)
save_alert_history(anomalies,OUTPUT_DIR,latest["Date"].strftime("%Y-%m-%d"))

if anomalies:
    body="INSIGHTGUARD BUSINESS ALERT\n\n"+executive_summary+"\n\n"
    for a in anomalies: body+=f"{a['Metric']}: {a['Direction']} {abs(a['Deviation (%)']):.2f}% [{a['Severity']}]\n"
    send_email_alert(EMAIL_SENDER,EMAIL_PASSWORD,EMAIL_RECEIVER,"InsightGuard - Business Anomaly Detected",body)
print("\nCompleted successfully.")
