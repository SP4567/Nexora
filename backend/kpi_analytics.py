"""
KPI Analytics Module
-------------------
- Computes KPI trends
- Detects anomalies
- Prepares structured insights for AI reasoning

Used by:
- AI CEO / AI COO reasoning engine
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from typing import Dict, Any


class KPIAnalytics:
    def __init__(self):
        # Tuned for business KPIs (not noisy sensor data)
        self.anomaly_model = IsolationForest(
            contamination=0.05,
            random_state=42
        )

    def compute_trend(self, df: pd.DataFrame, metric: str) -> Dict[str, Any]:
        """
        Computes trend direction and growth rate
        """
        df = df.sort_values("date")

        if len(df) < 2:
            return {
                "trend": "insufficient_data",
                "growth_rate_pct": 0.0
            }

        start = df[metric].iloc[0]
        end = df[metric].iloc[-1]

        if start == 0:
            growth_rate = 0.0
        else:
            growth_rate = round(((end - start) / start) * 100, 2)

        trend = "increasing" if end > start else "decreasing"

        return {
            "trend": trend,
            "growth_rate_pct": growth_rate
        }

    def detect_anomalies(self, df: pd.DataFrame, metric: str) -> pd.DataFrame:
        """
        Detects abnormal KPI behavior
        """
        if len(df) < 10:
            return pd.DataFrame()

        df = df.copy()
        df["anomaly"] = self.anomaly_model.fit_predict(df[[metric]])

        return df[df["anomaly"] == -1][["date", metric]]

    def summarize_kpi(
        self,
        df: pd.DataFrame,
        metric: str,
        department: str = None
    ) -> Dict[str, Any]:
        """
        Full KPI summary for AI CEO reasoning
        """
        summary = {
            "metric": metric,
            "department": department,
            "current_value": round(df[metric].iloc[-1], 2),
            "average": round(df[metric].mean(), 2),
            "min": round(df[metric].min(), 2),
            "max": round(df[metric].max(), 2),
        }

        summary.update(self.compute_trend(df, metric))

        anomalies = self.detect_anomalies(df, metric)
        summary["anomaly_count"] = len(anomalies)
        summary["anomalies"] = anomalies.to_dict(orient="records")

        return summary


# --------- Example Usage (for testing only) ---------
if __name__ == "__main__":
    data = {
        "date": pd.date_range("2025-01-01", periods=15),
        "revenue": np.random.randint(50000, 120000, size=15)
    }

    df = pd.DataFrame(data)

    analytics = KPIAnalytics()
    result = analytics.summarize_kpi(df, metric="revenue", department="Cardiology")

    print(result)
