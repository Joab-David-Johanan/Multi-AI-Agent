# React Frontend Notes

This file documents the React frontend step by step, assuming no JavaScript or TypeScript background.

---

## 1. Replacing The Vite Starter

### What Was There Before

The React app started as the default Vite starter page. It had:

- Vite and React logos.
- A counter button.
- Documentation links.
- No connection to the FastAPI backend.
- No real chat UI.

That starter is useful for proving React runs, but it is not the actual product experience.

### What Changed

The starter was replaced with a real agent console in:

```text
multi_agent_app/react_frontend/src/App.jsx
multi_agent_app/react_frontend/src/App.css
multi_agent_app/react_frontend/src/index.css
```

The new first screen is the usable app:

- Left configuration panel.
- Assistant selector.
- LLM provider segmented control.
- Model selector.
- Temperature slider.
- Web search, backend cache, and memory toggles.
- Chat conversation area.
- Suggested prompts.
- Message composer.
- Runtime status and thread ID.

---

## 2. What A React Component Is

In this app, `App.jsx` exports one main React component:

```jsx
function App() {
  return (
    <main className="app-shell">
      ...
    </main>
  )
}
```

A component is a JavaScript function that returns UI.

The returned UI looks like HTML, but it is called JSX. JSX lets React describe the screen using tags like:

```jsx
<button>Send</button>
<select>...</select>
<section>...</section>
```

React then turns that JSX into real browser elements.

---

## 3. What `useState` Means

React state is data that can change on the screen.

Example:

```jsx
const [assistantType, setAssistantType] = useState('General')
```

This means:

- `assistantType` is the current value.
- `setAssistantType(...)` changes the value.
- When the value changes, React redraws the relevant UI.

For example, when the user chooses `Medical`, this runs:

```jsx
onChange={(event) => setAssistantType(event.target.value)}
```

That updates `assistantType`, and React refreshes the UI with the new selected assistant.

---

## 4. How React Talks To FastAPI

The backend endpoint is:

```text
POST http://127.0.0.1:8000/chat
```

The React app sends JSON using `fetch`:

```jsx
const response = await fetch(BACKEND_URL, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(payload),
})
```

The important idea:

- React creates a JavaScript object called `payload`.
- `JSON.stringify(payload)` converts it into JSON.
- FastAPI receives that JSON and validates it with `RequestState`.

The payload shape matches the backend:

```jsx
const payload = {
  assistant_type: assistantType,
  llm_type: llmType,
  model_name: modelName,
  messages: [trimmedMessage],
  temperature,
  allow_search: allowSearch,
  streaming: false,
  thread_id: threadId,
  enable_memory: enableMemory,
  enable_cache: enableCache,
}
```

---

## 5. Why We Keep A `threadId`

Conversational memory in the backend depends on `thread_id`.

The React app creates one thread ID when the page opens:

```jsx
const [threadId, setThreadId] = useState(createThreadId)
```

Then every request sends that same `thread_id`.

When the user clicks `New conversation`, the app creates a new thread ID:

```jsx
setThreadId(createThreadId())
```

That gives the backend a clean memory thread.

---

## 6. Design Direction

The React UI is intentionally more polished than the Streamlit UI:

- Dark, focused configuration rail.
- Light workspace with soft glass surfaces.
- Dense but readable operational layout.
- No marketing landing page before the real app.
- Status, cache mode, latency, and thread details visible in the main workflow.

The goal is a professional demo interface, closer to a Stripe-style product console than a notebook-style prototype.

---

## 7. Stripe-Style Animated Ribbon

### What Changed

The React frontend now has a decorative animated color ribbon behind the app surface.

The JSX added this layer near the top of `App.jsx`:

```jsx
<div className="animated-ribbon" aria-hidden="true">
  <div className="ribbon ribbon-one"></div>
  <div className="ribbon ribbon-two"></div>
  <div className="ribbon ribbon-three"></div>
  <div className="ribbon ribbon-four"></div>
</div>
```

This is not app logic. It is only visual decoration.

`aria-hidden="true"` tells screen readers to ignore it because it does not contain useful content.

### How The Animation Works

Each `.ribbon` is a long rounded rectangle with a colorful gradient:

```css
.ribbon-one {
  background: linear-gradient(90deg, #ffb000 0%, #ff6b2b 48%, #ff4fb8 100%);
  transform: translate(10px, 22px) rotate(41deg) scaleX(1.16);
  animation-name: ribbon-drift-one;
}
```

The `transform` does three things:

- `translate(...)` moves the ribbon.
- `rotate(...)` turns it diagonally.
- `scaleX(...)` stretches it horizontally.

The movement comes from CSS keyframes:

```css
@keyframes ribbon-drift-one {
  0%,
  100% {
    transform: translate(10px, 22px) rotate(41deg) scaleX(1.16);
  }
  50% {
    transform: translate(-44px, 46px) rotate(44deg) scaleX(1.22);
  }
}
```

This means:

- At the start, the ribbon is in position A.
- Halfway through the animation, it drifts to position B.
- At the end, it returns to position A.
- Because `animation-iteration-count: infinite` is set, the movement loops forever.

Different ribbons use different colors, positions, and animation delays. That makes the motion feel layered instead of robotic.

### Why The Ribbon Does Not Block The App

The ribbon wrapper uses:

```css
.animated-ribbon {
  position: fixed;
  pointer-events: none;
  z-index: 0;
}
```

Important parts:

- `position: fixed` keeps the ribbon attached to the viewport.
- `pointer-events: none` means users can click through it.
- `z-index: 0` keeps it behind the real interface.

The real app panels use:

```css
.control-panel,
.workspace {
  position: relative;
  z-index: 1;
}
```

That places the controls and chat above the animated background.

---

## 8. Color Palette Refresh

### What Changed

The app moved closer to a Stripe-inspired palette:

- White and pale blue main workspace.
- Deep navy configuration panel.
- Purple, blue, orange, and pink accent colors.
- Brighter action buttons.
- Animated orange, pink, purple, and blue ribbons.

The main page background changed to:

```css
.app-shell {
  background: linear-gradient(180deg, #ffffff 0%, #f7fbff 48%, #eef7ff 100%);
}
```

The send button now uses a stronger product-style gradient:

```css
.composer button {
  background: linear-gradient(135deg, #635bff, #7c3aed 54%, #ff8a00);
}
```

The goal is to make the React version feel more like a polished product dashboard than a default developer scaffold.

---

## 9. Keeping Past Assistant Labels Stable

### The Problem

Before this fix, old assistant messages displayed the current selected assistant from the dropdown:

```jsx
<span>{message.role === 'user' ? 'You' : assistantType}</span>
```

That means if a user asked a question with `Medical`, then later changed the dropdown to `Law`, the old Medical response could appear as if it came from Law.

That is confusing because conversation history should not rewrite itself.

### The Fix

When the user sends a message, the app now captures the assistant selected at that moment:

```jsx
const requestAssistant = assistantType
```

Then assistant responses store that value:

```jsx
{
  role: 'assistant',
  assistant: requestAssistant,
  content: data.response || 'No response returned.',
  meta: `${data.cache || 'miss'} / ${duration}s`,
}
```

The message header now reads from the message itself:

```jsx
<span>{message.role === 'user' ? 'You' : message.assistant}</span>
```

Now old messages keep the correct assistant label, even if the dropdown changes later.

---

## 10. Bright Ribbon-Matched Message Bubbles

### What Changed

User and assistant messages now use bright gradients that match the animated ribbon palette.

User messages use the warmer ribbon colors:

```css
.message.user {
  background: linear-gradient(135deg, #ffb000 0%, #ff6b2b 38%, #ff4fb8 68%, #6547ff 100%);
  color: #ffffff;
}
```

That gradient moves through:

- yellow/orange
- coral
- pink
- purple

Assistant messages use the cooler ribbon colors:

```css
.message.assistant {
  background: linear-gradient(135deg, #8bd3ff 0%, #b79cff 42%, #ff68c9 100%);
  color: #07132f;
}
```

That gradient moves through:

- sky blue
- lavender/purple
- bright pink

Loading assistant messages use a temporary yellow/orange/blue gradient:

```css
.message.assistant.loading-message {
  background: linear-gradient(135deg, #ffd34e 0%, #ff8a3d 44%, #7dd3fc 100%);
  color: #08132d;
}
```

### Why Different Gradients Are Used

- User messages are warm and energetic, so they stand out as the user's input.
- Assistant messages are cooler and slightly softer, so longer answers remain readable.
- Both bubble styles reuse colors already present in the animated ribbons, making the UI feel cohesive.
- Text colors were chosen for contrast: user bubbles use white text, assistant bubbles use dark navy text.
