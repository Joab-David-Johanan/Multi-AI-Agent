import streamlit as st

from multi_agent_app.common.logger import get_logger
from multi_agent_app.frontend.utils_ui import load_css
from multi_agent_app.frontend.session import init_session, render_chat_history
from multi_agent_app.frontend.sidebar_ui import render_sidebar
from multi_agent_app.frontend.chat_handler import handle_chat
from multi_agent_app.frontend.history_ui import render_conversation_expander

logger = get_logger(__name__)

# ---------------------------------------------------
# Streamlit requirement:
# set_page_config must be the FIRST Streamlit command
# ---------------------------------------------------
st.set_page_config(page_title="Multi AI Agent", layout="wide")

# Load custom CSS styling
load_css()

# ---------------------------------------------------
# Page header
# ---------------------------------------------------
st.title("_Choose_ _your_ :rainbow[AI Assistant] _to_ _start_ _the_ _chat_")

st.subheader(
    ":rainbow[_Compare_ _different_ _assistants_, _models_ _and_ _optimizations_]",
    divider="rainbow",
)

# ---------------------------------------------------
# Initialize session state
# (chat history, cache store, suggestions)
# ---------------------------------------------------
init_session()

# ---------------------------------------------------
# Render sidebar and capture configuration
# ---------------------------------------------------
sidebar_config = render_sidebar()

assistant_type = sidebar_config["assistant_type"]
llm_type = sidebar_config["llm_type"]
selected_model = sidebar_config["selected_model"]
temperature = sidebar_config["temperature"]
show_icons = sidebar_config["show_icons"]
allow_search = sidebar_config["allow_search"]
enable_session_cache = sidebar_config["enable_session_cache"]
enable_backend_cache = sidebar_config["enable_backend_cache"]
enable_chat_history = sidebar_config["enable_chat_history"]
enable_suggestions = sidebar_config["enable_suggestions"]
enable_streaming = sidebar_config["enable_streaming"]

# ---------------------------------------------------
# Handle chat interaction
# IMPORTANT:
# This function internally renders st.chat_input()
# so it must be called before rendering history
# ---------------------------------------------------
handle_chat(
    assistant_type=assistant_type,
    llm_type=llm_type,
    selected_model=selected_model,
    temperature=temperature,
    show_icons=show_icons,
    allow_search=allow_search,
    enable_session_cache=enable_session_cache,
    enable_backend_cache=enable_backend_cache,
    enable_streaming=enable_streaming,
    enable_coversational_memory=enable_chat_history,
    enable_suggestions=enable_suggestions,
)

# ---------------------------------------------------
# Render conversation messages
# ---------------------------------------------------
render_chat_history()

# ---------------------------------------------------
# Expandable conversation viewer
# ---------------------------------------------------
render_conversation_expander()

# ---------------------------------------------------
# Optional observability dashboard
# Placed in an expander so it does not interfere
# with chat layout
# ---------------------------------------------------
with st.expander("📊 System Metrics & Observability", expanded=False):

    st.components.v1.iframe(
        "http://localhost:3000/d/adxzmm8/total-ai-agent-requests?orgId=1&from=now-5m&to=now&timezone=browser&kiosk&refresh=5s",
        height=900,
        scrolling=True,
    )
