import streamlit as st
import requests
import time
import uuid

from multi_agent_app.common.logger import get_logger

logger = get_logger(__name__)

BACKEND_URL = "http://127.0.0.1:8000/chat"


def handle_chat(
    assistant_type,
    llm_type,
    selected_model,
    temperature,
    show_icons,
    allow_search,
    enable_session_cache,
    enable_backend_cache,
    enable_streaming,
    enable_coversational_memory,
    enable_suggestions,
):
    """
    Handles chat input, backend call, caching, and response rendering.
    """

    # Create a unique conversation thread id for LangGraph memory
    # Ensure thread_id exists for LangGraph conversational memory
    if "thread_id" not in st.session_state:
        st.session_state.thread_id = str(uuid.uuid4())

    # ---------------------------------------
    # Handle user input (chat or suggestion)
    # ---------------------------------------

    chat_input = st.chat_input("Type your message")

    # priority 1: user typed message
    if chat_input and chat_input.strip():
        user_input = chat_input.strip()

    # priority 2: suggestion clicked
    elif enable_suggestions and st.session_state.get("suggested_prompt"):
        user_input = st.session_state.pop("suggested_prompt")

    else:
        return

    if not user_input or not user_input.strip():
        return

    # ----------------------------
    # Show user immediately
    # ----------------------------
    with st.chat_message("user"):
        st.markdown(user_input)

    st.session_state.chat_history.append(
        {"role": "user", "message": user_input, "time": None, "mode": None}
    )

    cache_hit = False
    cache_type = "miss"
    cache_key = (
        assistant_type,
        llm_type,
        selected_model,
        temperature,
        user_input,
    )
    ai_reply = ""
    suggestions = []
    duration = 0.0

    # ----------------------------
    # Session Cache logic
    # ----------------------------
    if enable_session_cache and cache_key in st.session_state.cache_store:
        cache_hit = True
        start_time = time.time()
        ai_reply = st.session_state.cache_store[cache_key]
        duration = round(time.time() - start_time, 4)

    else:
        payload = {
            "assistant_type": assistant_type,
            "llm_type": llm_type,
            "model_name": selected_model,
            "messages": [user_input],
            "temperature": temperature,
            "allow_search": allow_search,
            "streaming": enable_streaming,
            "thread_id": st.session_state.thread_id,
            "enable_memory": enable_coversational_memory,
            "enable_cache": enable_backend_cache,  # backend toggle
        }

        try:
            if enable_streaming:
                start_time = time.time()

                response = requests.post(
                    BACKEND_URL.replace("/chat", "/chat-stream"),
                    json=payload,
                    stream=True,
                    timeout=120,
                )

                if response.status_code != 200:
                    st.error(response.text)
                    ai_reply = "Error"
                    duration = 0
                else:
                    with st.chat_message("assistant"):
                        placeholder = st.empty()

                        for chunk in response.iter_content(chunk_size=None):
                            if chunk:
                                text = chunk.decode("utf-8")
                                ai_reply += text
                                placeholder.markdown(ai_reply)

                    duration = round(time.time() - start_time, 2)

            else:
                start_time = time.time()
                response = requests.post(BACKEND_URL, json=payload, timeout=120)
                duration = round(time.time() - start_time, 2)

                if response.status_code == 200:
                    data = response.json()

                    ai_reply = data.get("response", "")
                    # Only enable suggestions if checkbox is ticked
                    if enable_suggestions:
                        suggestions = data.get("suggestions", [])
                    else:
                        suggestions = []
                    cache_type = data.get("cache", "miss")
                    if enable_session_cache and cache_type == "miss":
                        st.session_state.cache_store[cache_key] = ai_reply
                else:
                    st.error(response.text)
                    ai_reply = "Error"

        except Exception as e:
            logger.error(str(e))
            st.error("Connection error")
            ai_reply = "Error"
            duration = 0

    # ----------------------------
    # Mode label
    # ----------------------------

    def icon(name):
        if show_icons:
            return f":material/{name}: "
        return ""

    if cache_hit:
        mode = f"{icon('bolt')}Session cache hit"

    elif cache_type == "exact":
        mode = f"{icon('database')}Global cache hit (exact)"

    elif cache_type == "semantic":
        mode = f"{icon('hub')}Global cache hit (semantic)"

    else:
        if enable_streaming:
            mode = f"{icon('sync')}Live call (streaming, no cache)"

        else:
            if enable_session_cache and enable_backend_cache:
                mode = f"{icon('cloud')}Live call (session + global cache enabled)"

            elif enable_session_cache and not enable_backend_cache:
                mode = f"{icon('cloud')}Live call (session cache only)"

            elif not enable_session_cache and enable_backend_cache:
                mode = f"{icon('cloud')}Live call (global cache only)"

            else:
                mode = f"{icon('block')}Live call (no cache)"

    # ----------------------------
    # Append assistant
    # ----------------------------
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "message": ai_reply,
            "suggestions": suggestions if enable_suggestions else [],
            "time": duration,
            "mode": mode,
            "assistant": assistant_type,
            "model": selected_model,
            "tool": allow_search,
            "session_cache": enable_session_cache,
            "global_cache": enable_backend_cache,
            "memory": enable_coversational_memory,
        }
    )

    st.toast(f"{mode} in {duration} seconds")
    st.rerun()
