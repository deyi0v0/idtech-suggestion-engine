from typing import List, Dict, Any, Optional
from fpdf import FPDF
from fpdf.enums import XPos, YPos


LABEL_MAP = {
    "model_name": "Model",
    "hardware_name": "Model",
    "product_name": "Model",
    "name": "Model",
    "model": "Model",
    "info": "Description",
    "input_power": "Input Power",
    "interface": "Interface",
    "operate_temperature": "Operating Temperature",
    "ip_rating": "IP Rating",
    "ik_rating": "IK Rating",
    "extra_specs": "Additional Specifications",
    "software_name": "Compatible Software",
    "highlights": "Highlights",
    "installation_docs": "Installation Documents",
    "datasheet_url": "Datasheet",
}

NAME_KEYS = ("hardware_name", "product_name", "name", "model_name", "model")
SPEC_KEYS = ("input_power", "interface", "operate_temperature", "ip_rating", "ik_rating")


def _safe(text: Any) -> str:
    return str(text).encode("latin-1", "replace").decode("latin-1")


def _humanize(key: str) -> str:
    return LABEL_MAP.get(key, key.replace("_", " ").title())


def _format_scalar(value: Any) -> str:
    if isinstance(value, list):
        return ", ".join(str(v) for v in value if v is not None)
    if isinstance(value, dict):
        return ", ".join(f"{_humanize(str(k))}: {v}" for k, v in value.items())
    return str(value)


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, (list, tuple)):
        return list(value)
    return [value]


def _flatten(product: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(product)
    nested = out.pop("explanation_metadata", None)
    if isinstance(nested, dict):
        for k, v in nested.items():
            out.setdefault(k, v)
    return out


def _resolve_name(product: Dict[str, Any]) -> str:
    for k in NAME_KEYS:
        if product.get(k):
            return str(product[k])
    return "Unnamed Product"


def _section_heading(pdf: FPDF, text: str) -> None:
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 6, _safe(text), new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)


def _render_kv(pdf: FPDF, label: str, value: str, width: float) -> None:
    label_text = f"  {label}: "
    pdf.set_font("Helvetica", "B", 11)
    label_w = pdf.get_string_width(label_text) + 1
    pdf.cell(label_w, 5.5, _safe(label_text))
    pdf.set_font("Helvetica", "", 11)
    pdf.multi_cell(width - label_w, 5.5, _safe(value),
                   new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _render_bullet(pdf: FPDF, text: str, url: Optional[str], width: float) -> None:
    bullet = "  - "
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(0, 0, 0)
    bullet_w = pdf.get_string_width(bullet) + 1
    pdf.cell(bullet_w, 5.5, _safe(bullet))
    if url:
        pdf.set_text_color(20, 80, 200)
        pdf.set_font("Helvetica", "U", 11)
        pdf.multi_cell(width - bullet_w, 5.5, _safe(text), link=url,
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "", 11)
        pdf.set_text_color(0, 0, 0)
    else:
        pdf.multi_cell(width - bullet_w, 5.5, _safe(text),
                       new_x=XPos.LMARGIN, new_y=YPos.NEXT)


def _hr(pdf: FPDF) -> None:
    y = pdf.get_y()
    pdf.set_draw_color(190, 190, 190)
    pdf.line(pdf.l_margin, y, pdf.l_margin + pdf.epw, y)


def generate_pdf(products: List[Dict[str, Any]], explanations: List[str]) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    width = pdf.epw

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(width, 12, _safe("Recommended Products"), align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    _hr(pdf)
    pdf.ln(5)

    for i, raw in enumerate(products):
        product = _flatten(raw)
        explanation = explanations[i] if i < len(explanations) else ""

        pdf.set_font("Helvetica", "B", 14)
        pdf.set_text_color(25, 60, 120)
        pdf.cell(width, 9, _safe(_resolve_name(product)),
                 new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

        if product.get("info"):
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(width, 5.5, _safe(product["info"]),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(1)

        highlights = product.get("highlights")
        if highlights:
            _section_heading(pdf, "Highlights")
            text = ", ".join(str(h) for h in _as_list(highlights) if h)
            pdf.set_font("Helvetica", "", 11)
            pdf.multi_cell(width, 5.5, _safe(f"  {text}"),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(1)

        spec_pairs = [(_humanize(k), _format_scalar(product[k]))
                      for k in SPEC_KEYS if product.get(k)]
        extra = product.get("extra_specs")
        if spec_pairs or extra:
            _section_heading(pdf, "Specifications")
            for label, value in spec_pairs:
                _render_kv(pdf, label, value, width)
            if isinstance(extra, dict):
                for k, v in extra.items():
                    _render_kv(pdf, _humanize(str(k)), _format_scalar(v), width)
            elif extra:
                _render_kv(pdf, "Additional", _format_scalar(extra), width)
            pdf.ln(1)

        software = product.get("software_name") or product.get("software")
        if software:
            _section_heading(pdf, "Compatible Software")
            for item in _as_list(software):
                if isinstance(item, dict):
                    name = item.get("name") or item.get("title") or "Software"
                    url = item.get("datasheet_url") or item.get("url")
                    _render_bullet(pdf, name, url, width)
                else:
                    _render_bullet(pdf, str(item), None, width)
            pdf.ln(1)

        docs = product.get("installation_docs")
        if docs:
            _section_heading(pdf, "Installation Documents")
            for doc in _as_list(docs):
                if isinstance(doc, dict):
                    title = doc.get("title") or doc.get("name") or "Document"
                    url = doc.get("url")
                    _render_bullet(pdf, title, url, width)
                else:
                    _render_bullet(pdf, str(doc), None, width)
            pdf.ln(1)

        if explanation:
            _section_heading(pdf, "Why this recommendation")
            pdf.set_font("Helvetica", "I", 11)
            pdf.multi_cell(width, 5.5, _safe(explanation),
                           new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.ln(6)

    return bytes(pdf.output())
