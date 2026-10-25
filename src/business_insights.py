import pandas as pd

def generate_business_insights(latest, threshold=20):
    s=[]
    t,c=latest["Traffic_Deviation"],latest["Conversion_Deviation"]
    r,f=latest["Revenue_Deviation"],latest["Refunds_Deviation"]
    o,cost=latest["Orders_Deviation"],latest["Cost_Deviation"]
    if not pd.isna(t) and not pd.isna(c) and t>threshold and c<-threshold:
        s.append("Traffic increased sharply while conversion declined significantly. This may indicate lower-quality traffic.")
    if not pd.isna(r) and not pd.isna(f) and r>threshold and f>threshold:
        s.append("Revenue increased significantly, but refunds also increased considerably. This may indicate customer satisfaction or product-related issues.")
    if not pd.isna(r) and not pd.isna(o) and r<-threshold and o<-threshold:
        s.append("Revenue and orders both declined significantly, indicating weaker business performance.")
    if not pd.isna(cost) and cost>threshold:
        s.append("Operating cost increased significantly and should be reviewed for possible cost pressure.")
    if not pd.isna(f) and f>threshold:
        s.append("Refunds increased significantly and should be investigated for possible customer or operational issues.")
    return s
