import streamlit as st


# ---------------------------------------------------
# Initialize session state variables
# ---------------------------------------------------
def init_session():

    # Chat history storage
    # Keeps conversation messages across reruns
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # Session-level cache
    # Used to avoid duplicate LLM calls within a session
    if "cache_store" not in st.session_state:
        st.session_state.cache_store = {}

    # Suggested prompt placeholder
    # Used when suggestion buttons are clicked
    if "suggested_prompt" not in st.session_state:
        st.session_state.suggested_prompt = None


# ---------------------------------------------------
# Render chat messages
# ---------------------------------------------------
def render_chat_history():

    for idx, item in enumerate(st.session_state.chat_history):

        # Render message bubble (user or assistant)
        with st.chat_message(item["role"]):

            st.markdown(item["message"])

            # ---------------------------------------------------
            # Display follow-up suggestion buttons
            # ---------------------------------------------------
            if item["role"] == "assistant" and item.get("suggestions"):

                st.markdown("**Continue the conversation:**")

                # Create 3 fixed columns for consistent layout
                cols = st.columns(3)

                for i, suggestion in enumerate(item["suggestions"]):

                    # Prevent overflow if suggestions > columns
                    if i >= len(cols):
                        break

                    with cols[i]:

                        st.button(
                            suggestion,
                            key=f"suggestion_{idx}_{i}",
                            use_container_width=True,
                            # Clicking a suggestion stores it
                            # Then chat_handler processes it
                            on_click=lambda s=suggestion: st.session_state.update(
                                {"suggested_prompt": s}
                            ),
                        )

            # ---------------------------------------------------
            # Metadata display
            # Shows execution information
            # ---------------------------------------------------
            if item["role"] == "assistant" and item.get("time") is not None:

                st.caption(
                    f"Mode: {item.get('mode')} | "
                    f"Assistant: {item.get('assistant')} | "
                    f"Memory: {item.get('memory')} | "
                    f"Tool: {item.get('tool')} | "
                    f"Time: {item.get('time')} seconds"
                )
