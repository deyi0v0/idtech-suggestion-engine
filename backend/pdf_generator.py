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
    
    # Hardware
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(200, 10, txt=f"Hardware: {bundle.get('hardware_name', 'N/A')}", ln=True)
    
    # Software
    software = bundle.get('software', [])
    if software:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(200, 10, txt="Compatible Software:", ln=True)
        pdf.set_font("Arial", '', 11)
        for sw in software:
            name = sw.get('name', 'Unknown')
            url = sw.get('datasheet_url')
            if url:
                pdf.cell(200, 10, txt=f"- {name} (Datasheet: {url})", ln=True)
            else:
                pdf.cell(200, 10, txt=f"- {name}", ln=True)
    pdf.ln(5)
    
    # Highlights
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, txt="Key Highlights:", ln=True)
    pdf.set_font("Arial", '', 10)
    highlights = bundle.get('highlights', [])
    for item in highlights:
        pdf.multi_cell(0, 10, txt=f"- {item}")
    pdf.ln(5)
    
    # Explanation
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(200, 10, txt="Technical Rationale:", ln=True)
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 10, txt=bundle.get('explanation', 'No explanation provided.'))
    pdf.ln(5)

    # Installation Docs
    docs = bundle.get('installation_docs', [])
    if docs:
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(200, 10, txt="Installation Documents:", ln=True)
        pdf.set_font("Arial", '', 10)
        for doc in docs:
            title = doc.get('title', 'Document')
            url = doc.get('url', '#')
            pdf.cell(200, 10, txt=f"- {title}: {url}", ln=True)
    
    return pdf.output(dest='S') # Return as bytes
