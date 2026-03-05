# TODO: Implement generate_pdf(products: list[dict], explanations: list[str]) -> bytes:
#   Use fpdf2 to create a simple PDF with a title, and a section per product (name, details, explanation).
#   Return the PDF as bytes.

from typing import List, Dict, Any
from fpdf import FPDF

def generate_pdf(products: List[Dict[str, Any]], explanations: List[str]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Recommended Products", ln=True)
    pdf.ln(5)

    for i, product in enumerate(products):
        explanation = explanations[i] if i < len(explanations) else ""

        # Product name (fallbacks)
        name = (
            product.get("product_name")
            or product.get("name")
            or product.get("model")
            or "Unnamed Product"
        )

        # Header
        pdf.set_font("Arial", "B", 14)
        pdf.multi_cell(0, 8, name)

        # Details (key/value)
        pdf.set_font("Arial", "", 12)
        for key, value in product.items():
            if key in {"product_name", "name", "model"}:
                continue

            # Make lists readable
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value)
            else:
                value_str = str(value)

            pdf.multi_cell(0, 6, f"{key}: {value_str}")

        pdf.ln(2)

        # Explanation
        if explanation:
            pdf.set_font("Arial", "I", 12)
            pdf.multi_cell(0, 6, f"Explanation: {explanation}")

        pdf.ln(10)

    # Return bytes
    return 0
