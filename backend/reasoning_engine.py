from langchain_core.prompts import PromptTemplate
from llm import llm
import logging

logger = logging.getLogger(__name__)

prompt = PromptTemplate(
    input_variables=["kpis"],
    template="""
You are an experienced Chief Operating Officer.

Analyze the following KPIs:
{kpis}

Tasks:
1. Identify key risks
2. Identify opportunities
3. Recommend actions
4. Expected impact
5. Confidence level

Be concise, factual, and executive-level.
"""
)

def generate_recommendation(kpis: str):
    try:
        return llm.invoke(prompt.format(kpis=kpis)).content
    except Exception as e:
        logger.error(f"Error generating recommendation: {e}")
        raise