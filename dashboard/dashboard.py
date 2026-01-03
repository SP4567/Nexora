import streamlit as st
import pandas as pd
import requests
from requests.exceptions import RequestException
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="AI CEO", layout="wide")

st.title("🤖 AI CEO Dashboard")

# API Configuration
API_BASE_URL = "http://127.0.0.1:8000"
API_TIMEOUT = 10

# Load sales from FastAPI
@st.cache_data(ttl=60)
def load_sales():
    try:
        r = requests.get(f"{API_BASE_URL}/sales", timeout=API_TIMEOUT)
        r.raise_for_status()
        return pd.DataFrame(r.json())
    except RequestException as e:
        logger.error(f"Failed to load sales data: {e}")
        st.error("Failed to load sales data. Make sure the backend is running.")
        return pd.DataFrame()

sales = load_sales()

if not sales.empty:
    sales["date"] = pd.to_datetime(sales["date"])
    
    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Revenue", f"₹{sales['revenue'].sum():,.0f}")
    col2.metric("Total Orders", len(sales))
    col3.metric("Avg Revenue", f"₹{sales['revenue'].mean():,.0f}")
else:
    st.warning("No sales data available")

if not sales.empty:
    st.divider()
    
    # Chart
    st.subheader("Revenue Trend")
    daily = sales.groupby("date")["revenue"].sum().reset_index()
    st.line_chart(daily, x="date", y="revenue")
    
    st.divider()

# AI Question
st.subheader("Ask AI CEO")
question = st.text_input("Ask a business question")

if st.button("Ask"):
    if not question.strip():
        st.error("Please enter a question")
    else:
        try:
            res = requests.post(
                f"{API_BASE_URL}/ceo/ask",
                json={"question": question},
                timeout=API_TIMEOUT
            )
            res.raise_for_status()
            response_data = res.json()
            if "response" in response_data:
                st.success(response_data["response"])
            else:
                st.error("Unexpected response format")
        except RequestException as e:
            logger.error(f"Failed to get CEO response: {e}")
            st.error(f"Failed to get response. Please try again. Error: {str(e)}")
