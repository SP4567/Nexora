from fpdf import FPDF
import logging

logger = logging.getLogger(__name__)

def generate_board_report(summary_text):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8, summary_text)
        pdf.output("weekly_board_report.pdf")
        logger.info("Board report generated successfully: weekly_board_report.pdf")
    except Exception as e:
        logger.error(f"Error generating board report: {e}")
        raise
