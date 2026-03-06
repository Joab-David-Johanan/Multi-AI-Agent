import streamlit as st


# ----------------------------
# Init session state
# ----------------------------
def init_session():
    # Initialize chat history storage
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Initialize session-level cache
    if "cache_store" not in st.session_state:
        st.session_state.cache_store = {}

    # NEW: ensure suggestion state exists
    # This prevents key errors when suggestion buttons are clicked
    if "suggested_prompt" not in st.session_state:
        st.session_state.suggested_prompt = None


# ----------------------------
# Render chat history
# ----------------------------
def render_chat_history():
    for idx, item in enumerate(st.session_state.chat_history):

        with st.chat_message(item["role"]):
            st.markdown(item["message"])

            # ----------------------------
            # Suggestions
            # ----------------------------
            if item["role"] == "assistant" and item.get("suggestions"):

                # Label above suggestion buttons
                st.markdown("**Continue the conversation:**")

                # CHANGE:
                # Force a fixed number of columns (3)
                # This ensures consistent layout even if text length varies
                cols = st.columns(3)

                for i, suggestion in enumerate(item["suggestions"]):

                    # Safety check in case suggestion count changes later
                    if i >= len(cols):
                        break

                    with cols[i]:

                        # CHANGE:
                        # use_container_width=True forces equal width buttons
                        # so longer text does not stretch columns unevenly
                        st.button(
                            suggestion,
                            key=f"suggestion_{idx}_{i}",
                            use_container_width=True,
                            # CHANGE:
                            # use on_click instead of inline if
                            # This avoids Streamlit rerun timing issues
                            on_click=lambda s=suggestion: st.session_state.update(
                                {"suggested_prompt": s}
                            ),
                        )

            # ----------------------------
            # Metadata caption
            # ----------------------------
            if item["role"] == "assistant" and item.get("time") is not None:
                st.caption(
                    f"Mode: {item.get('mode')} | Assistant: {item.get('assistant')} | "
                    f"Memory: {item.get('memory')} | Tool: {item.get('tool')} | "
                    f"Time: {item.get('time')} seconds"
                )
