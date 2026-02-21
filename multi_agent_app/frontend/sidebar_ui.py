import streamlit as st
from multi_agent_app.config.settings import settings


def render_sidebar():
    # Sidebar configuration section
    with st.sidebar:
        st.header("Choose your configuration:")

        assistant_type = st.selectbox(
            "Choose your AI assistant:", settings.ASSISTANT_TYPES
        )

        llm_type = st.radio("LLM provider: ", settings.ALLOWED_LLM_TYPES)

        if llm_type == "Groq":
            model_options = settings.ALLOWED_GROQ_MODEL_NAMES
        else:
            model_options = settings.ALLOWED_OPENAI_MODEL_NAMES

        selected_model = st.selectbox("Model versions: ", model_options)

        temperature = st.slider(
            "Choose model temperature: ", min_value=0.0, max_value=1.0, step=0.1
        )

        allow_search = st.checkbox("Enable web search")

        st.subheader("Choose optimizations:")
        enable_cache = st.checkbox("Enable caching")
        enable_chat_history = st.checkbox("Enable chat history")
        enable_suggestions = st.checkbox("Enable chat suggestions")
        enable_model_comparison = st.checkbox("Enable model comparison")
        enable_streaming = st.checkbox("Enable streaming output")

    # RETURN all variables
    return {
        "assistant_type": assistant_type,
        "llm_type": llm_type,
        "selected_model": selected_model,
        "temperature": temperature,
        "allow_search": allow_search,
        "enable_cache": enable_cache,
        "enable_chat_history": enable_chat_history,
        "enable_suggestions": enable_suggestions,
        "enable_streaming": enable_streaming,
        "enable_model_comparison": enable_model_comparison,
    }
