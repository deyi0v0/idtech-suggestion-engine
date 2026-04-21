from fpdf import FPDF
from typing import Dict, Any

def generate_pdf(bundle: Dict[str, Any]) -> bytes:
    """
    Takes a RecommendationBundle dictionary and generates a PDF.
    """
    pdf = FPDF()
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, txt="ID TECH Product Recommendation", ln=True, align='C')
    pdf.ln(10)
    
    # Hardware & Software
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Hardware: {bundle.get('hardware_name', 'N/A')}", ln=True)
    pdf.cell(200, 10, txt=f"Software: {bundle.get('software_name', 'N/A')}", ln=True)
    pdf.ln(5)
    
    # Highlights
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, txt="Key Highlights:", ln=True)
    pdf.set_font("Arial", '', 10)
    highlights = bundle.get('highlights', [])
    if isinstance(highlights, list):
        for item in highlights:
            pdf.multi_cell(0, 10, txt=f"- {item}")
    else:
        pdf.multi_cell(0, 10, txt=str(highlights))
    pdf.ln(5)
    
    # Explanation
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, txt="Technical Rationale:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 10, txt=bundle.get('explanation', 'No explanation provided.'))
    
    return pdf.output(dest='S') # Return as bytes
