import streamlit as st


# ----------------------------
# Init session state
# ----------------------------
def init_session():
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "cache_store" not in st.session_state:
        st.session_state.cache_store = {}


# ----------------------------
# Render chat history
# ----------------------------
def render_chat_history():
    for item in st.session_state.chat_history:
        with st.chat_message(item["role"]):
            st.markdown(item["message"])

            if item["role"] == "assistant" and item.get("time") is not None:
                st.caption(
                    f"Mode: {item.get('mode')} | Assistant: {item.get('assistant')} | "
                    f"Memory: {item.get('memory')} | Tool: {item.get('tool')} | "
                    f"Time: {item.get('time')} seconds"
                )
