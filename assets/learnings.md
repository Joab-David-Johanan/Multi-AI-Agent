# Learnings

---

## Commands For CSS-Only Streamlit Changes

When only `assets/styles.css` changes, rebuild and recreate only the Streamlit service:

```bash
docker compose --profile streamlit build streamlit
docker compose --profile streamlit up -d --force-recreate streamlit
```

Then refresh:

```text
http://127.0.0.1:8501
```

Why this is enough:

- `build streamlit` copies the updated CSS into the Docker image.
- `up -d --force-recreate streamlit` restarts Streamlit with that rebuilt image.
- Docker should reuse cached dependency layers, so CSS-only changes should not reinstall all Python packages.

---

## 1. Chat Input Styling Fix

### Before

The Streamlit chat input was styled only at the `textarea` level:

```css
div[data-testid="stChatInput"] textarea {
    border-radius: 12px !important;
    border: 1px solid #c4f9d3 !important;
    padding: 0.8rem !important;
}
```

This made the input feel visually weak and harder to identify because the outer chat input container still used mostly default Streamlit styling. The pale green border was also too close to the app's other green UI elements, so the input did not stand out clearly. The padding made the input feel taller than necessary.

### What Changed

The fix was intentionally CSS-only in `assets/styles.css`. No chat logic, backend code, cache code, Docker behavior, or agent behavior was changed.

The chat input now has:

- A capped width of `900px` so it does not stretch too far across the page.
- A light blue background (`#eef7ff`) so it is easy to identify.
- A clearer blue border (`#38bdf8`) around the input container.
- Reduced textarea padding and a smaller minimum height.
- A matching blue send button style.
- A white focus state so typing feels clean and readable.

After the change, the CSS became:

```css
div[data-testid="stChatInput"] {
    max-width: 900px !important;
    margin: 0 auto 0.5rem auto !important;
}

div[data-testid="stChatInput"] > div {
    background: #eef7ff !important;
    border: 1.5px solid #38bdf8 !important;
    border-radius: 14px !important;
    box-shadow: 0 8px 24px rgba(14, 165, 233, 0.14) !important;
}

div[data-testid="stChatInput"] textarea {
    min-height: 42px !important;
    max-height: 96px !important;
    background: #eef7ff !important;
    color: #0f172a !important;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.55rem 0.75rem !important;
    line-height: 1.35 !important;
    box-shadow: none !important;
}

div[data-testid="stChatInput"] textarea::placeholder {
    color: #64748b !important;
    opacity: 1 !important;
}

div[data-testid="stChatInput"] textarea:focus {
    background: #ffffff !important;
    outline: none !important;
}

div[data-testid="stChatInput"] button {
    background: #dbeafe !important;
    color: #0369a1 !important;
    border-radius: 10px !important;
    border: 1px solid #bfdbfe !important;
    box-shadow: none !important;
}

div[data-testid="stChatInput"] button:hover {
    background: #bfdbfe !important;
    color: #075985 !important;
}
```

### Why This Approach

The problem was visual, so the safest fix was to keep the change inside CSS. This reduced the risk of breaking message submission, session state, backend calls, caching, or Streamlit rerun behavior.

### Result

The chat input should now look more compact, easier to see, and visually separate from the message cards while preserving the existing app flow.

---

## 2. App Color And Heading Spacing Refresh

### Before

The app used a mostly plain white main area with very saturated red and green chat cards. The layout worked, but the colors felt harsh in the message area and the main heading appeared slightly lower than desired because the Streamlit content container kept its default top spacing.

### What Changed

The update stayed CSS-only in `assets/styles.css`.

The main changes were:

- Added a soft multi-color page background so the app feels brighter without changing the layout.
- Reduced top padding on Streamlit's main `.block-container` so `Choose your AI Assistant to start the chat` appears higher on the page.
- Kept the sidebar in the same position but made its dark background richer with a subtle vertical gradient.
- Replaced the very strong red/green message card gradients with softer coral and teal/green gradients.
- Added a light border and slightly stronger shadow to chat cards so they pop more cleanly.

### After

```css
.stApp {
    background: linear-gradient(135deg, #f8fbff 0%, #fff7ed 45%, #f0fdfa 100%) !important;
}

.block-container {
    padding-top: 3.25rem !important;
    padding-bottom: 2rem !important;
    max-width: 1180px !important;
}

[data-testid="stMain"] h1 {
    margin-top: 0 !important;
    padding-top: 0 !important;
    line-height: 1.08 !important;
    color: #0f172a !important;
    text-shadow: 0 2px 14px rgba(15, 23, 42, 0.08);
}
```

During browser inspection, the actual Streamlit container still had `padding-top: 96px`, so the selector was changed to target `.block-container` directly. This moves the heading higher while keeping enough space below the top Streamlit toolbar.

### Why This Approach

The request was visual, so the change avoided Python, Streamlit state, backend, Docker Compose, cache, and agent logic. The app structure remains the same; only the presentation layer changed.

---

## 3. Sidebar Collapse Control Spacing

### Before

The sidebar expand/collapse control was rendered by Streamlit inside `stSidebarHeader` and `stSidebarCollapseButton`. Browser inspection showed the button was positioned around `y: -3`, which made the `<<` style control feel cramped against the top edge.

### What Changed

The update stayed CSS-only in `assets/styles.css`.

The collapse control now has:

- A small downward offset so it sits inside the visible sidebar area.
- A circular glass-style background.
- A subtle border and shadow so it feels intentional.
- A hover state that uses the app's blue accent color.
- Slightly larger icon sizing for better readability.

### After

```css
div[data-testid="stSidebarCollapseButton"] {
    transform: translateY(16px) !important;
    margin-right: 0.35rem !important;
}

div[data-testid="stSidebarCollapseButton"] button {
    width: 34px !important;
    height: 34px !important;
    border-radius: 999px !important;
    background: rgba(255, 255, 255, 0.14) !important;
    border: 1px solid rgba(255, 255, 255, 0.28) !important;
    box-shadow: 0 8px 22px rgba(0, 0, 0, 0.22) !important;
    backdrop-filter: blur(14px) !important;
}
```

### Why This Approach

Only the sidebar control styling changed. The sidebar layout, inputs, Streamlit state, and app logic were not touched.

---

## 4. Header And Chat Input Area Background Fill

### Before

The middle app area used the soft gradient background, but Streamlit's top header strip and bottom chat input strip still appeared white. This made the page look visually split into three bands: white at the top, gradient in the middle, and white again behind the chat input.

### What Changed

The update stayed CSS-only in `assets/styles.css`.

The same background gradient was applied to:

- `stAppViewContainer`
- `stHeader`
- `stToolbar`
- `stDecoration`
- `stBottom`
- `stBottomBlockContainer`
- `stChatFloatingInputContainer`

Later, the gradient was made darker and more professional for interview/demo use. The original pastel background was too light, so it was changed to a stronger blue-to-teal palette that matches the dark sidebar and blue input styling.

### After

```css
[data-testid="stHeader"],
[data-testid="stToolbar"],
[data-testid="stDecoration"] {
    background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 38%, #ccfbf1 100%) !important;
}

[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stChatFloatingInputContainer"] {
    background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 38%, #ccfbf1 100%) !important;
    border-top: 1px solid rgba(14, 116, 144, 0.18) !important;
    box-shadow: 0 -18px 36px rgba(15, 23, 42, 0.08) !important;
}
```

### Why This Approach

The issue was caused by Streamlit's own wrapper containers, not the app layout. Styling those wrappers keeps the layout and app behavior unchanged while making the background visually continuous.

---

## 5. Minimal Fixed Chat Input Footer

### Before

Streamlit renders `st.chat_input()` inside a sticky bottom wrapper. Browser inspection showed:

```text
stBottom height: 150px
stBottomBlockContainer padding: 16px 80px 56px 80px
```

Because the whole wrapper had a visible background, it looked like a large fixed footer instead of just a chat input. This made scrolling feel awkward, especially after messages were added.

### What Changed

The update stayed CSS-only in `assets/styles.css`.

The bottom wrapper now:

- Uses the same professional blue-to-teal gradient as the rest of the main app area.
- Has no top border or large shadow.
- Uses much smaller padding.
- Disables pointer events on the empty wrapper area.
- Re-enables pointer events only on the actual chat input.

### After

```css
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"],
[data-testid="stChatFloatingInputContainer"] {
    background: linear-gradient(135deg, #dbeafe 0%, #e0f2fe 38%, #ccfbf1 100%) !important;
    border-top: none !important;
    box-shadow: none !important;
}

[data-testid="stBottomBlockContainer"] {
    padding: 0.5rem 5rem 1rem 5rem !important;
    pointer-events: none !important;
}

div[data-testid="stChatInput"] {
    pointer-events: auto !important;
}
```

### Why This Approach

Streamlit controls the chat input positioning internally, so the safest fix was to reduce and hide the wrapper instead of replacing `st.chat_input()` with a custom input. The chat submission logic remains unchanged.

Follow-up adjustment: the wrapper was briefly made transparent, but that made the bottom area appear white. The final version keeps the reduced-height wrapper while restoring the same blue-to-teal gradient as the rest of the app.

---

## 6. Greeting And Prompt Contract Fix

### Before

When the user typed a simple greeting like `Hello`, domain-specific assistants could reject it as out-of-domain because their prompts said things like:

```text
You MUST ONLY answer questions related to medicine, health, diseases, treatments, or healthcare.
Do not greet the user.
```

The app also expects model responses to follow the structured contract:

```text
ANSWER:
<final answer>

SUGGESTIONS:
1. ...
2. ...
3. ...
```

If the model refused awkwardly or did not follow that format, the frontend could show `Error` instead of a friendly greeting.

### What Changed

The fix was made in two places:

- `multi_agent_app/config/settings.py`
- `multi_agent_app/core/agent.py`

The assistant prompts now allow safe small-talk messages such as greetings, thanks, and questions about what the assistant can help with. The domain boundaries are still preserved, so Medical, Financial, and Law assistants still refuse unrelated real questions.

The backend also now handles obvious greetings before calling the LLM. This avoids spending tokens and prevents prompt conflicts for simple inputs like `Hello`.

### After

The base prompt now explicitly says the output format is mandatory for all response types:

```python
- If the user only sends a greeting, thanks, or a short conversational setup message, respond briefly and politely.
- Do not treat greetings, thanks, or "what can you do?" as out-of-domain requests.

This output format is mandatory for every response, including greetings, refusals, and safety disclaimers.
```

The backend now catches obvious greetings:

```python
small_talk_response = get_small_talk_response(assistant_type, query)

if small_talk_response:
    if enable_streaming:
        return as_streaming_response(small_talk_response["answer"])

    return small_talk_response
```

Example result for the Medical assistant:

```python
{
    "answer": "Hello. I can help with general health and medical information, but I cannot diagnose conditions.",
    "suggestions": [
        "Ask about a health condition",
        "Review general symptom information",
        "Discuss treatment options to ask a clinician about",
    ],
}
```

### Why This Approach

The safest fix is both prompt-level and code-level:

- The prompts guide the model correctly for real conversations.
- The deterministic greeting handler prevents simple greetings from depending on model behavior.
- The existing frontend response shape stays unchanged.
- The domain assistants remain domain-restricted for actual questions.

### Verification

The backend container was rebuilt and tested with `Hello` for:

- General
- Medical
- Financial
- Law

All four returned a valid `answer` and `suggestions` response instead of `Error`.
