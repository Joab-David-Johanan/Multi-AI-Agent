import { useMemo, useState } from 'react'
import './App.css'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000/chat'

const assistantTypes = ['General', 'Medical', 'Financial', 'Law']

const providerModels = {
  Groq: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'qwen/qwen3-32b'],
  OpenAI: ['gpt-5-nano-2025-08-07', 'gpt-4.1-nano-2025-04-14', 'gpt-5-mini-2025-08-07'],
}

const starterPrompts = [
  'Hello',
  'Explain semantic caching in this app',
  'Compare session cache and backend cache',
]

const initialMessages = [
  {
    role: 'assistant',
    assistant: 'General',
    content:
      'Choose an assistant, tune the runtime options, then ask a question. I will show cache mode, latency, and follow-up suggestions after each response.',
    meta: 'Ready',
  },
]

function createThreadId() {
  if (crypto.randomUUID) {
    return crypto.randomUUID()
  }
  return `thread-${Date.now()}`
}

function App() {
  const [assistantType, setAssistantType] = useState('General')
  const [llmType, setLlmType] = useState('Groq')
  const [modelName, setModelName] = useState(providerModels.Groq[0])
  const [temperature, setTemperature] = useState(0)
  const [allowSearch, setAllowSearch] = useState(false)
  const [enableCache, setEnableCache] = useState(true)
  const [enableMemory, setEnableMemory] = useState(false)
  const [messages, setMessages] = useState(initialMessages)
  const [suggestions, setSuggestions] = useState(starterPrompts)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [threadId, setThreadId] = useState(createThreadId)

  const currentModels = providerModels[llmType]

  const runtimeSummary = useMemo(() => {
    return [
      assistantType,
      llmType,
      modelName,
      `temperature ${temperature.toFixed(1)}`,
      enableMemory ? 'memory on' : 'memory off',
      enableCache ? 'cache on' : 'cache off',
    ].join(' / ')
  }, [assistantType, enableCache, enableMemory, llmType, modelName, temperature])

  function handleProviderChange(nextProvider) {
    setLlmType(nextProvider)
    setModelName(providerModels[nextProvider][0])
  }

  function resetConversation() {
    setMessages(initialMessages)
    setSuggestions(starterPrompts)
    setThreadId(createThreadId())
    setError('')
  }

  async function sendMessage(messageText = input) {
    const trimmedMessage = messageText.trim()

    if (!trimmedMessage || isLoading) {
      return
    }

    const userMessage = {
      role: 'user',
      content: trimmedMessage,
      meta: 'You',
    }

    setMessages((currentMessages) => [...currentMessages, userMessage])
    setInput('')
    setError('')
    setIsLoading(true)

    const startedAt = new Date().getTime()
    const requestAssistant = assistantType

    const payload = {
      assistant_type: requestAssistant,
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

    try {
      const response = await fetch(BACKEND_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error(await response.text())
      }

      const data = await response.json()
      const duration = ((new Date().getTime() - startedAt) / 1000).toFixed(2)

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: 'assistant',
          assistant: requestAssistant,
          content: data.response || 'No response returned.',
          meta: `${data.cache || 'miss'} / ${duration}s`,
        },
      ])
      setSuggestions(data.suggestions?.length ? data.suggestions : starterPrompts)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Request failed'
      setError(message)
      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: 'assistant',
          assistant: requestAssistant,
          content: 'The backend request failed. Check that FastAPI is running and reachable.',
          meta: 'Error',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  function handleSubmit(event) {
    event.preventDefault()
    sendMessage()
  }

  return (
    <main className="app-shell">
      <div className="animated-ribbon" aria-hidden="true">
        <div className="ribbon ribbon-one"></div>
        <div className="ribbon ribbon-two"></div>
        <div className="ribbon ribbon-three"></div>
        <div className="ribbon ribbon-four"></div>
      </div>

      <aside className="control-panel" aria-label="Assistant configuration">
        <div className="brand-lockup">
          <div className="brand-mark">AI</div>
          <div>
            <p className="eyebrow">Multi Agent Console</p>
            <h1>Agent workspace</h1>
          </div>
        </div>

        <section className="panel-section">
          <label htmlFor="assistant-type">Assistant</label>
          <select
            id="assistant-type"
            value={assistantType}
            onChange={(event) => setAssistantType(event.target.value)}
          >
            {assistantTypes.map((assistant) => (
              <option key={assistant}>{assistant}</option>
            ))}
          </select>
        </section>

        <section className="panel-section">
          <label>Provider</label>
          <div className="segmented-control" role="group" aria-label="LLM provider">
            {Object.keys(providerModels).map((provider) => (
              <button
                className={llmType === provider ? 'active' : ''}
                key={provider}
                onClick={() => handleProviderChange(provider)}
                type="button"
              >
                {provider}
              </button>
            ))}
          </div>
        </section>

        <section className="panel-section">
          <label htmlFor="model-name">Model</label>
          <select
            id="model-name"
            value={modelName}
            onChange={(event) => setModelName(event.target.value)}
          >
            {currentModels.map((model) => (
              <option key={model}>{model}</option>
            ))}
          </select>
        </section>

        <section className="panel-section">
          <div className="range-row">
            <label htmlFor="temperature">Temperature</label>
            <span>{temperature.toFixed(1)}</span>
          </div>
          <input
            id="temperature"
            max="1"
            min="0"
            onChange={(event) => setTemperature(Number(event.target.value))}
            step="0.1"
            type="range"
            value={temperature}
          />
        </section>

        <section className="panel-section switch-list">
          <label className="switch-row">
            <input
              checked={allowSearch}
              onChange={(event) => setAllowSearch(event.target.checked)}
              type="checkbox"
            />
            <span>Web search</span>
          </label>
          <label className="switch-row">
            <input
              checked={enableCache}
              onChange={(event) => setEnableCache(event.target.checked)}
              type="checkbox"
            />
            <span>Backend cache</span>
          </label>
          <label className="switch-row">
            <input
              checked={enableMemory}
              onChange={(event) => setEnableMemory(event.target.checked)}
              type="checkbox"
            />
            <span>Conversational memory</span>
          </label>
        </section>

        <button className="secondary-action" onClick={resetConversation} type="button">
          New conversation
        </button>
      </aside>

      <section className="workspace" aria-label="Chat workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Production-style React frontend</p>
            <h2>Ask, compare, and inspect every agent response.</h2>
          </div>
          <div className="status-pill">
            <span className={isLoading ? 'status-dot busy' : 'status-dot'}></span>
            {isLoading ? 'Running' : 'Online'}
          </div>
        </header>

        <div className="insight-strip" aria-label="Runtime summary">
          <span>{runtimeSummary}</span>
          <span>Thread {threadId.slice(0, 8)}</span>
        </div>

        <section className="chat-panel" aria-label="Conversation">
          {messages.map((message, index) => (
            <article className={`message ${message.role}`} key={`${message.role}-${index}`}>
              <div className="message-header">
                <span>{message.role === 'user' ? 'You' : message.assistant}</span>
                <small>{message.meta}</small>
              </div>
              <p>{message.content}</p>
            </article>
          ))}

          {isLoading && (
            <article className="message assistant loading-message">
              <div className="message-header">
                <span>{assistantType}</span>
                <small>Working</small>
              </div>
              <p>Thinking through the request...</p>
            </article>
          )}
        </section>

        {error && <div className="error-banner">{error}</div>}

        <div className="suggestion-row" aria-label="Suggested prompts">
          {suggestions.slice(0, 3).map((suggestion) => (
            <button key={suggestion} onClick={() => sendMessage(suggestion)} type="button">
              {suggestion}
            </button>
          ))}
        </div>

        <form className="composer" onSubmit={handleSubmit}>
          <input
            aria-label="Message"
            onChange={(event) => setInput(event.target.value)}
            placeholder="Ask your agent..."
            value={input}
          />
          <button disabled={isLoading || !input.trim()} type="submit">
            Send
          </button>
        </form>
      </section>
    </main>
  )
}

export default App
