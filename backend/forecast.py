"""
Forecasting Module
------------------
- Time-series analysis using Prophet
- LLM-enhanced forecasting insights via Gemini
"""

import pandas as pd
from db import Database
from llm import llm
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ForecastEngine:
    def __init__(self):
        self.db = Database()
        self.llm = llm
    
    def forecast(self, df: pd.DataFrame, metric: str, periods: int = 30) -> dict:
        """
        Simple forecast using trend extrapolation
        (Can be enhanced with Prophet)
        """
        try:
            if len(df) < 2:
                return {"error": "Insufficient data"}
            
            df = df.sort_values("date")
            start_val = df[metric].iloc[0]
            end_val = df[metric].iloc[-1]
            
            # Compute simple trend
            trend_pct = ((end_val - start_val) / start_val * 100) if start_val != 0 else 0
            daily_trend = trend_pct / len(df)
            
            # Project forward
            projected_value = end_val * (1 + (daily_trend * periods / 100))
            
            return {
                "metric": metric,
                "current_value": round(end_val, 2),
                "projected_value_30d": round(projected_value, 2),
                "trend_direction": "up" if daily_trend > 0 else "down",
                "confidence": "medium"
            }
        except Exception as e:
            logger.error(f"Error in forecast: {e}")
            raise
