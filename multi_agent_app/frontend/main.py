import streamlit as st

from multi_agent_app.common.logger import get_logger
from multi_agent_app.frontend.utils_ui import load_css
from multi_agent_app.frontend.session import init_session, render_chat_history
from multi_agent_app.frontend.sidebar_ui import render_sidebar
from multi_agent_app.frontend.chat_handler import handle_chat
from multi_agent_app.frontend.history_ui import render_conversation_expander

logger = get_logger(__name__)

# Load custom css
load_css()

st.set_page_config(page_title="Multi AI Agent", layout="wide")

st.title("_Choose_ _your_ :rainbow[AI Assistant] _to_ _start_ _the_ _chat_")
st.subheader(
    ":rainbow[_Compare_ _different_ _assistants_, _models_ _and_ _optimizations_]",
    divider="rainbow",
)

# Initialize session
init_session()

# Render chat history
render_chat_history()

# Render sidebar
sidebar_config = render_sidebar()

assistant_type = sidebar_config["assistant_type"]
llm_type = sidebar_config["llm_type"]
selected_model = sidebar_config["selected_model"]
temperature = sidebar_config["temperature"]
allow_search = sidebar_config["allow_search"]
enable_cache = sidebar_config["enable_cache"]
enable_chat_history = sidebar_config["enable_chat_history"]
enable_suggestions = sidebar_config["enable_suggestions"]
enable_streaming = sidebar_config["enable_streaming"]
enable_model_comparison = sidebar_config["enable_model_comparison"]

# Chat handler
handle_chat(
    assistant_type=assistant_type,
    llm_type=llm_type,
    selected_model=selected_model,
    temperature=temperature,
    allow_search=allow_search,
    enable_cache=enable_cache,
    enable_streaming=enable_streaming,
)

# Render conversation history
render_conversation_expander()
