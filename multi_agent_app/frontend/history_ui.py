import streamlit as st
from multi_agent_app.frontend.utils_ui import generate_pdf


def render_conversation_expander():
    """
    Shows expandable conversation history with:
    - metadata
    - clear button
    - pdf download
    """

    if not any(item["role"] == "assistant" for item in st.session_state.chat_history):
        return

    with st.expander("Conversation history", expanded=False):

        for item in st.session_state.chat_history:
            st.markdown(f"**{item['role'].capitalize()}**")
            st.markdown(item["message"])

            if item["role"] == "assistant":
                st.markdown(f"Mode: {item.get('mode')}")
                st.markdown(f"Assistant: {item.get('assistant')}")
                st.markdown(f"Model: {item.get('model')}")
                st.markdown(f"Tool: {item.get('tool')}")
                st.markdown(f"Time: {item.get('time')} seconds")

            st.markdown("---")

        col1, col2 = st.columns(2)

        # ----------------------------
        # Clear conversation
        # ----------------------------
        with col1:
            if st.button("Clear conversation"):
                st.session_state.chat_history = []
                st.session_state.cache_store = {}
                st.rerun()

        # ----------------------------
        # Download PDF
        # ----------------------------
        with col2:
            pdf_file = generate_pdf(st.session_state.chat_history)

            st.download_button(
                label="Download conversation (PDF)",
                data=pdf_file,
                file_name="conversation_history.pdf",
                mime="application/pdf",
            )
