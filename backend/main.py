"""
AI CEO / AI COO – Main API
-------------------------
End-to-end orchestration:
- Fetch KPIs from PostgreSQL
- Run analytics + forecasting
- Generate executive insights using Gemini
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi import Body
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import logging
import pandas as pd
import concurrent.futures

from db import Database
from kpi_analytics import KPIAnalytics
from forecast import ForecastEngine
from reasoning_engine import generate_recommendation
from sql_agent import ask_ceo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI CEO Decision Intelligence",
    version="1.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy initialization of heavy components to avoid startup failures
db = None
analytics = None
forecast_engine = None

def get_db():
    """Get or create the Database instance."""
    global db
    if db is None:
        try:
            db = Database()
            logger.info("Database initialized on demand")
        except Exception as e:
            logger.error(f"Failed to initialize Database on demand: {e}")
            db = None
    return db

def get_analytics():
    """Get or create the KPIAnalytics instance."""
    global analytics
    if analytics is None:
        try:
            analytics = KPIAnalytics()
            logger.info("KPIAnalytics initialized on demand")
        except Exception as e:
            logger.error(f"Failed to initialize KPIAnalytics on demand: {e}")
            analytics = None
    return analytics

def get_forecast_engine():
    """Get or create the ForecastEngine instance."""
    global forecast_engine
    if forecast_engine is None:
        try:
            forecast_engine = ForecastEngine()
            logger.info("ForecastEngine initialized on demand")
        except Exception as e:
            logger.error(f"Failed to initialize ForecastEngine on demand: {e}")
            forecast_engine = None
    return forecast_engine


@app.get("/health")
def health_check():
    """
    Health check endpoint
    """
    try:
        db_inst = get_db()
        db_status = db_inst.test_connection() if db_inst else False
        return {
            "status": "ok",
            "database_connected": db_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "database_connected": False,
            "error": str(e)
        }


@app.get("/")
def root():
    """Root endpoint with basic API information"""
    return {
        "message": "AI CEO Decision Intelligence",
        "version": "1.0",
        "endpoints": ["/health", "/kpi-analysis", "/ceo/ask", "/docs"]
    }


@app.get("/sales")
def get_sales(limit: int = Query(100, description="Max rows to return")):
    """Return recent sales rows as JSON for the dashboard"""
    try:
        db_inst = get_db()
        if not db_inst:
            raise HTTPException(status_code=503, detail="Database not initialized")

        # Run DB fetch in a thread with a timeout so the endpoint doesn't block the dashboard
        query = "SELECT date, revenue, department FROM sales ORDER BY date DESC LIMIT :lim"
        executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
        future = executor.submit(db_inst.fetch_dataframe, query, {"lim": limit})
        try:
            df = future.result(timeout=8)
        except concurrent.futures.TimeoutError:
            future.cancel()
            logger.error("Database fetch timed out for /sales")
            raise HTTPException(status_code=504, detail="Database request timed out")
        finally:
            executor.shutdown(wait=False)

        if df.empty:
            return []

        # Ensure dates are serializable
        df = df.copy()
        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

        return df.to_dict(orient="records")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching sales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/kpi-analysis")
def kpi_analysis(
    metric: str = Query(..., description="KPI column name (e.g. revenue)"),
    table: str = Query("sales", description="Table name"),
    department: Optional[str] = Query(None, description="Optional department filter"),
    forecast_days: int = Query(30, description="Forecast horizon in days")
):
    """
    Full KPI → Analytics → Forecast → AI Insight pipeline
    """
    try:
        db_inst = get_db()
        analytics_inst = get_analytics()
        forecast_inst = get_forecast_engine()
        if not db_inst or not analytics_inst or not forecast_inst:
            raise HTTPException(status_code=503, detail="Required services not initialized")
        
        # 1. Fetch data from database
        if department:
            query = f"""
            SELECT date, {metric}
            FROM {table}
            WHERE department = :dept
            ORDER BY date
            """
            df = db_inst.fetch_dataframe(query, {"dept": department})
        else:
            query = f"""
            SELECT date, {metric}
            FROM {table}
            ORDER BY date
            """
            df = db_inst.fetch_dataframe(query)

        if df.empty:
            return {
                "error": "No data found for given parameters"
            }

        # 2. KPI Analytics
        kpi_summary = analytics_inst.summarize_kpi(
            df=df,
            metric=metric,
            department=department
        )

        # 3. Forecasting
        forecast_result = forecast_inst.forecast(
            df=df,
            metric=metric,
            periods=forecast_days
        )

        # 4. AI CEO Reasoning (Gemini)
        ai_input = {
            "kpi_summary": kpi_summary,
            "forecast": forecast_result
        }

        ai_insight = generate_recommendation(str(ai_input))

        # 5. Final Executive Response
        return {
            "kpi_summary": kpi_summary,
            "forecast": forecast_result,
            "ai_ceo_insight": ai_insight
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in KPI analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ceo/ask")
@app.get("/ceo/ask")
def ceo_question(question: Optional[str] = Query(None), payload: dict = Body(None)):
    """
    Ask strategic questions to AI CEO
    Supports both POST and GET requests
    """
    try:
        # Accept question via query param or JSON body {"question": "..."}
        if payload and isinstance(payload, dict) and payload.get("question"):
            q = payload.get("question")
        else:
            q = question

        if not q or not str(q).strip():
            raise HTTPException(status_code=400, detail="Question is required")

        response = ask_ceo(q)
        return {"response": response}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing CEO question: {e}")
        raise HTTPException(status_code=500, detail="Failed to process question")