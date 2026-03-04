import streamlit as st
from pathlib import Path
from io import BytesIO
import re

# PDF generation (must use reportlab.platypus)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet


# Load custom CSS from project root
def load_css():
    base_dir = Path(__file__).resolve().parent.parent.parent
    css_file = base_dir / "assets" / "styles.css"

    if css_file.exists():
        css = css_file.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


# Generate PDF of entire conversation history
def generate_pdf(chat_history):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []

    styles = getSampleStyleSheet()
    normal_style = styles["Normal"]

    for item in chat_history:
        role = item["role"].capitalize()
        message = item["message"]
        mode = remove_material_icons(item.get("mode"))
        time_taken = item.get("time")

        elements.append(Paragraph(f"<b>{role}</b>", normal_style))
        elements.append(Spacer(1, 6))
        elements.append(Paragraph(message.replace("\n", "<br/>"), normal_style))
        elements.append(Spacer(1, 6))

        if role == "Assistant":
            elements.append(
                Paragraph(
                    f"<font size=9 color=grey>Mode: {mode} | Session_cache: {item.get('session_cache')} | Global_cache: {item.get('global_cache')} | Assistant: {item.get('assistant')} | "
                    f"Model: {item.get('model')} | Tool: {item.get('tool')} | Time: {time_taken} seconds</font>",
                    normal_style,
                )
            )
            elements.append(Spacer(1, 12))

        elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)
    return buffer


# Remove material icon text from PDF
def remove_material_icons(text):
    if not text:
        return text
    return re.sub(r":material/[^:]+:\s*", "", text)
