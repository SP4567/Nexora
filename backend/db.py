"""
Database Utility Module
-----------------------
- Manages PostgreSQL connection
- Provides safe query execution
- Returns Pandas DataFrames for analytics & AI reasoning

Used by:
- SQL Agent
- KPI Analytics
- Forecasting
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()


class Database:
    def __init__(self):
        self.db_uri = os.getenv("DB_URI")
        if not self.db_uri:
            raise ValueError("DB_URI not found in environment variables")

        try:
            self.engine = create_engine(self.db_uri)
            logger.info("Database engine created successfully")
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise

    def test_connection(self) -> bool:
        """
        Verifies database connectivity
        """
        try:
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def fetch_dataframe(self, query: str, params: dict = None) -> pd.DataFrame:
        """
        Executes SELECT queries and returns DataFrame
        """
        try:
            with self.engine.connect() as conn:
                df = pd.read_sql(text(query), conn, params=params)
            logger.info(f"Query executed successfully, returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise RuntimeError(f"Query failed: {e}")

    def execute_query(self, query: str, params: dict = None):
        """
        Executes INSERT / UPDATE / DELETE queries
        """
        try:
            with self.engine.begin() as conn:
                conn.execute(text(query), params or {})
            logger.info("Execute query completed successfully")
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            raise RuntimeError(f"Execution failed: {e}")


# --------- Quick Test ---------
if __name__ == "__main__":
    try:
        db = Database()

        if db.test_connection():
            print("✅ Database connection successful")

            df = db.fetch_dataframe("SELECT * FROM sales LIMIT 5")
            print(df)
        else:
            print("❌ Database connection failed")
    except Exception as e:
        print(f"❌ Error: {e}")
