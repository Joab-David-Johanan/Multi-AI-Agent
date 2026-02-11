import streamlit as st
import requests
import time
from pathlib import Path
from io import BytesIO

# PDF generation (must use reportlab.platypus)
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

from multi_agent_app.common.logger import get_logger
from multi_agent_app.config.settings import settings

logger = get_logger(__name__)

BACKEND_URL = "http://127.0.0.1:8000/chat"


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
        mode = item.get("mode")
        time_taken = item.get("time")

        role_paragraph = Paragraph(f"<b>{role}</b>", normal_style)
        elements.append(role_paragraph)
        elements.append(Spacer(1, 6))

        message_paragraph = Paragraph(message.replace("\n", "<br/>"), normal_style)
        elements.append(message_paragraph)
        elements.append(Spacer(1, 6))

        if role == "Assistant":
            meta_paragraph = Paragraph(
                f"<font size=9 color=grey>Mode: {mode} | Time: {time_taken} seconds</font>",
                normal_style,
            )
            elements.append(meta_paragraph)
            elements.append(Spacer(1, 12))

        elements.append(Spacer(1, 12))

    doc.build(elements)
    buffer.seek(0)

    return buffer


st.set_page_config(page_title="Multi AI Agent", layout="wide")
load_css()

st.markdown("## Multi AI Agent")
st.caption("Latency comparison demo")


# Initialize session state variables
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "cache_store" not in st.session_state:
    st.session_state.cache_store = {}


# Sidebar configuration section
with st.sidebar:

    st.header("Choose your configuration:")

    assistant_type = st.selectbox("Choose your AI assistant:", settings.ASSISTANT_TYPES)

    llm_type = st.radio("LLM provider", settings.ALLOWED_LLM_TYPES)

    if llm_type == "Groq":
        model_options = settings.ALLOWED_GROQ_MODEL_NAMES
    else:
        model_options = settings.ALLOWED_OPENAI_MODEL_NAMES

    selected_model = st.selectbox("Model", model_options)

    allow_search = st.checkbox("Enable web search")

    st.subheader("Choose optimizations:")

    enable_cache = st.checkbox("Enable caching")
    enable_streaming = st.checkbox("Enable streaming output")


st.divider()

user_input = st.chat_input("Type your message")

if user_input and user_input.strip() != "":

    cache_hit = False

    st.session_state.chat_history.append(
        {"role": "user", "message": user_input, "time": None, "mode": None}
    )

    if enable_cache and user_input in st.session_state.cache_store:
        cache_hit = True
        start_time = time.time()
        ai_reply = st.session_state.cache_store[user_input]
        duration = round(time.time() - start_time, 4)

    else:
        payload = {
            "assistant_type": assistant_type,
            "llm_type": llm_type,
            "model_name": selected_model,
            "messages": [user_input],
            "allow_search": allow_search,
        }

        try:
            start_time = time.time()

            response = requests.post(
                BACKEND_URL,
                json=payload,
                timeout=120,
            )

            duration = round(time.time() - start_time, 2)

            if response.status_code == 200:
                ai_reply = response.json().get("response", "")
                if enable_cache:
                    st.session_state.cache_store[user_input] = ai_reply
            else:
                st.error(response.text)
                ai_reply = "Error"

        except Exception as e:
            logger.error(str(e))
            st.error("Connection error")
            ai_reply = "Error"
            duration = 0

    if cache_hit:
        mode = "Cache hit"
    elif enable_streaming and enable_cache:
        mode = "Live call (streaming + caching enabled)"
    elif enable_streaming:
        mode = "Live call (streaming enabled)"
    elif enable_cache:
        mode = "Live call (caching enabled)"
    else:
        mode = "Live call"

    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "message": ai_reply,
            "time": duration,
            "mode": mode,
            "model": selected_model,
            "tool": allow_search,
        }
    )

    st.toast(f"{mode} in {duration} seconds")


# Render chat messages
for item in st.session_state.chat_history:
    with st.chat_message(item["role"]):
        st.markdown(item["message"])

        if item["role"] == "assistant" and item["time"] is not None:
            st.caption(
                f"Mode: {item['mode']} | Model: {item['model']} | Tool: {item['tool']} | Time: {item['time']} seconds"
            )


# Expanded conversation history with action buttons
if any(item["role"] == "assistant" for item in st.session_state.chat_history):

    with st.expander("Conversation history", expanded=False):

        for item in st.session_state.chat_history:
            st.markdown(f"**{item['role'].capitalize()}**")
            st.markdown(item["message"])

            if item["role"] == "assistant":
                st.markdown(f"Mode: {item['mode']}")
                st.markdown(f"Time: {item['time']} seconds")

            st.markdown("---")

        col1, col2 = st.columns(2)

        # Clear conversation button
        with col1:
            if st.button("Clear conversation"):
                st.session_state.chat_history = []
                st.session_state.cache_store = {}
                st.rerun()

        # Download PDF button
        with col2:
            pdf_file = generate_pdf(st.session_state.chat_history)

            st.download_button(
                label="Download conversation (PDF)",
                data=pdf_file,
                file_name="conversation_history.pdf",
                mime="application/pdf",
            )
