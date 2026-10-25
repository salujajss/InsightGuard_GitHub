from pathlib import Path
import pandas as pd

def save_alert_history(anomalies,output_dir,analysis_date):
    if not anomalies: return
    p=Path(output_dir)/"alert_history.csv"
    new=pd.DataFrame([{"Date":analysis_date,"Metric":a["Metric"],"Direction":a["Direction"],
                       "Deviation (%)":a["Deviation (%)"],"Severity":a["Severity"]} for a in anomalies])
    final=pd.concat([pd.read_csv(p),new],ignore_index=True) if p.exists() else new
    final.to_csv(p,index=False)
