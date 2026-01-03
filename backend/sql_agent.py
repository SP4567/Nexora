"""
SQL Agent Module
----------------
- Natural language → SQL via LLM
- Query execution with safety checks
"""

import logging
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from llm import llm
from db import Database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLAgent:
    def __init__(self):
        self.db_instance = Database()
        self.agent = None
        try:
            # Initialize SQLDatabase with proper connection string
            self.sql_db = SQLDatabase.from_uri(
                self.db_instance.db_uri,
                include_tables=["sales", "customers", "operations"],
                sample_rows=3
            )
            logger.info("SQL Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SQL Database: {e}")
            self.sql_db = None
    
    def query(self, question: str) -> str:
        """
        Execute natural language query against database
        """
        try:
            logger.info("SQLAgent.query called")
            if not self.sql_db:
                logger.info("No SQL DB available — using LLM fallback")
                try:
                    resp = llm.invoke(question)
                    return getattr(resp, "content", str(resp))
                except Exception as e:
                    logger.error(f"LLM fallback failed: {e}")
                    return "Database access unavailable and LLM fallback failed"

            # Try simple rule-based DB queries first for common analytics
            simple_answer = self._handle_simple_question(question)
            if simple_answer is not None:
                logger.info("Answered via simple DB handler")
                return simple_answer

            # Lazy initialization of agent
            if not self.agent:
                try:
                    logger.info("Initializing SQL agent...")
                    self.agent = create_sql_agent(
                        llm=llm,
                        db=self.sql_db,
                        verbose=True,
                    )
                    logger.info("SQL agent initialized")
                except Exception as e:
                    logger.error(f"Failed to create SQL agent: {e}")
                    logger.info("Falling back to LLM direct response")
                    try:
                        resp = llm.invoke(question)
                        return getattr(resp, "content", str(resp))
                    except Exception as e2:
                        logger.error(f"LLM fallback failed: {e2}")
                        return "Service unavailable"

            # Use agent to answer question (should be DB-grounded)
            logger.info("Running SQL agent for question")
            result = self.agent.run(question)
            logger.info(f"SQL agent result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error executing SQL Agent query: {e}")
            return f"Error: {str(e)}"

    def _handle_simple_question(self, question: str) -> str | None:
        """Handle a few common business questions directly from the DB.

        Returns a string answer when a pattern is matched, otherwise None.
        """
        q = question.lower()

        # Ensure DB connection
        try:
            db = self.db_instance
        except Exception:
            return None

        # total revenue
        if "total revenue" in q or "sum revenue" in q or "total sales" in q:
            try:
                df = db.fetch_dataframe("SELECT SUM(revenue) as total_revenue FROM sales")
                total = float(df['total_revenue'].iloc[0]) if not df.empty else 0.0
                return f"Total revenue: {total:,.2f}"
            except Exception as e:
                logger.error(f"Error computing total revenue: {e}")
                return None

        # total orders / count
        if "total orders" in q or ("orders" in q and "total" in q) or "number of orders" in q:
            try:
                df = db.fetch_dataframe("SELECT COUNT(*) as orders_count FROM sales")
                cnt = int(df['orders_count'].iloc[0]) if not df.empty else 0
                return f"Total orders: {cnt}"
            except Exception as e:
                logger.error(f"Error computing orders count: {e}")
                return None

        # average revenue
        if "avg revenue" in q or "average revenue" in q:
            try:
                df = db.fetch_dataframe("SELECT AVG(revenue) as avg_revenue FROM sales")
                avg = float(df['avg_revenue'].iloc[0]) if not df.empty else 0.0
                return f"Average revenue: {avg:,.2f}"
            except Exception as e:
                logger.error(f"Error computing average revenue: {e}")
                return None

        # revenue trend (last N days)
        import re
        m = re.search(r"last (\d+) (day|days)", q)
        if "revenue" in q and m:
            days = int(m.group(1))
            try:
                df = db.fetch_dataframe(
                    "SELECT date, SUM(revenue) as revenue FROM sales GROUP BY date ORDER BY date DESC LIMIT :lim",
                    {"lim": days}
                )
                if df.empty:
                    return None
                df = df.sort_values("date")
                start = df['revenue'].iloc[0]
                end = df['revenue'].iloc[-1]
                trend = "increasing" if end > start else "decreasing" if end < start else "flat"
                return f"Revenue trend over last {days} days: {trend} (start {start:,.2f} → end {end:,.2f})"
            except Exception as e:
                logger.error(f"Error computing revenue trend: {e}")
                return None

        return None

# Singleton instance - lazy initialization to avoid startup errors
_sql_agent = None

def get_sql_agent():
    """
    Get or create SQL Agent instance with lazy initialization
    """
    global _sql_agent
    if _sql_agent is None:
        try:
            _sql_agent = SQLAgent()
        except Exception as e:
            logger.error(f"Failed to initialize SQL Agent: {e}")
            _sql_agent = None
    return _sql_agent

def ask_ceo(question: str) -> str:
    """
    Wrapper for SQL Agent query
    """
    agent = get_sql_agent()
    if not agent:
        # No SQL agent available; use LLM directly
        try:
            resp = llm.invoke(question)
            return getattr(resp, "content", str(resp))
        except Exception as e:
            logger.error(f"LLM direct call failed: {e}")
            return "Service unavailable: cannot answer the question at this time"

    return agent.query(question)
