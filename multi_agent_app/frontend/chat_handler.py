import streamlit as st
import requests
import time

from multi_agent_app.common.logger import get_logger

logger = get_logger(__name__)

BACKEND_URL = "http://127.0.0.1:8000/chat"


def handle_chat(
    assistant_type,
    llm_type,
    selected_model,
    temperature,
    allow_search,
    enable_session_cache,
    enable_backend_cache,
    enable_streaming,
):
    """
    Handles chat input, backend call, caching, and response rendering.
    """

    user_input = st.chat_input("Type your message")

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
    ai_reply = ""
    duration = 0.0

    # ----------------------------
    # Cache logic
    # ----------------------------
    if enable_session_cache and user_input in st.session_state.cache_store:
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
            "temperature": temperature,
            "allow_search": allow_search,
            "streaming": enable_streaming,
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
                    ai_reply = response.json().get("response", "")
                    cache_type = response.json().get("cache", "miss")
                    if enable_session_cache and cache_type == "miss":
                        st.session_state.cache_store[user_input] = ai_reply
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
    if cache_hit:
        mode = ":material/bolt: Session cache hit"

    elif cache_type == "exact":
        mode = ":material/database: Global cache hit (exact)"

    elif cache_type == "semantic":
        mode = ":material/hub: Global cache hit (semantic)"

    # ----- LIVE CALLS -----
    else:
        if enable_streaming:
            mode = ":material/sync: Live call (streaming, no cache)"

        else:
            if enable_session_cache and enable_backend_cache:
                mode = ":material/cloud: Live call (session + global cache enabled)"

            elif enable_session_cache and not enable_backend_cache:
                mode = ":material/cloud: Live call (session cache only)"

            elif not enable_session_cache and enable_backend_cache:
                mode = ":material/cloud: Live call (global cache only)"

            else:
                mode = ":material/block: Live call (no cache)"

    # ----------------------------
    # Append assistant
    # ----------------------------
    st.session_state.chat_history.append(
        {
            "role": "assistant",
            "message": ai_reply,
            "time": duration,
            "mode": mode,
            "assistant": assistant_type,
            "model": selected_model,
            "tool": allow_search,
        }
    )

    st.toast(f"{mode} in {duration} seconds")
    st.rerun()
