import { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'

const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000/chat'
const EVALUATION_URL =
  import.meta.env.VITE_EVALUATION_URL || BACKEND_URL.replace(/\/chat$/, '/evaluate')
const EVALUATIONS_URL =
  import.meta.env.VITE_EVALUATIONS_URL || BACKEND_URL.replace(/\/chat$/, '/evaluations')

const assistantTypes = ['General', 'Medical', 'Financial', 'Law']

const providerModels = {
  Groq: ['llama-3.3-70b-versatile', 'llama-3.1-8b-instant', 'qwen/qwen3-32b'],
  OpenAI: ['gpt-5.5', 'gpt-5.4', 'gpt-5.4-mini', 'gpt-5.4-nano'],
}

const starterPrompts = [
  'Hello',
  'Explain semantic caching in this app',
  'Compare session cache and backend cache',
]

const STREAM_CHAR_DELAY_MS = 28
const STREAM_BATCH_SIZE = 2
const STREAM_METADATA_MARKER = '\n[[STREAM_METADATA]]'

function wait(ms) {
  return new Promise((resolve) => {
    setTimeout(resolve, ms)
  })
}

function buildChatHistoryText(messages, runtimeSummary, threadId) {
  const timestamp = new Date().toISOString()
  const lines = [
    'Multi Agent Chat History',
    `Exported: ${timestamp}`,
    `Thread: ${threadId}`,
    `Runtime: ${runtimeSummary}`,
    '',
  ]

  messages.forEach((message, index) => {
    lines.push(`--- Message ${index + 1} ---`)
    lines.push(`Role: ${message.role}`)

    if (message.assistant) {
      lines.push(`Assistant: ${message.assistant}`)
    }

    if (message.meta) {
      lines.push(`Meta: ${message.meta}`)
    }

    if (message.details) {
      lines.push(`Mode: ${message.details.mode}`)
      lines.push(`Routing mode: ${message.details.routingMode}`)
      lines.push(`Selected assistant: ${message.details.selectedAssistant}`)
      lines.push(`Assistant used: ${message.details.assistant}`)
      lines.push(`Suggested assistant: ${message.details.suggestedAssistant}`)
      lines.push(`Provider: ${message.details.provider}`)
      lines.push(`Model: ${message.details.model}`)
      lines.push(`Temperature: ${message.details.temperature}`)
      lines.push(`Memory: ${message.details.memory}`)
      lines.push(`Tool: ${message.details.tool}`)
      lines.push(`Backend cache: ${message.details.backendCache}`)
      lines.push(`Session cache: ${message.details.sessionCache}`)
      lines.push(`Cache result: ${message.details.cacheResult}`)
      lines.push(`Streaming: ${message.details.streaming}`)
      lines.push(`Suggestions: ${message.details.suggestions}`)
      lines.push(`Time: ${message.details.timeSeconds} seconds`)
    }

    lines.push('')
    lines.push(message.content || '')
    lines.push('')
  })

  return lines.join('\n')
}

function downloadTextFile(filename, text) {
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')

  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  link.remove()
  URL.revokeObjectURL(url)
}

function inferAssistantForQuery(query) {
  const normalized = query.toLowerCase()

  const medicalPattern =
    /\b(symptom|symptoms|disease|diagnosis|diagnose|treatment|medicine|medical|health|doctor|patient|fever|pain|infection|diabetes|blood pressure|cancer|vaccine|therapy)\b/
  const financialPattern =
    /\b(finance|financial|stock|stocks|investment|investing|portfolio|market|crypto|bitcoin|ethereum|loan|interest rate|inflation|revenue|profit|budget|tax|bank|trading)\b/
  const legalPattern =
    /\b(law|legal|contract|lawsuit|court|case law|rights|liability|regulation|compliance|attorney|lawyer|jurisdiction|clause|tenant|landlord|copyright|patent|trademark)\b/

  if (medicalPattern.test(normalized)) {
    return 'Medical'
  }

  if (financialPattern.test(normalized)) {
    return 'Financial'
  }

  if (legalPattern.test(normalized)) {
    return 'Law'
  }

  return 'General'
}

const initialMessages = [
  {
    role: 'assistant',
    assistant: 'General',
    content:
      'Choose an assistant, tune the runtime options, then ask a question. I will show cache mode, latency, and follow-up suggestions after each response.',
    meta: 'Ready',
  },
]

function EvaluationResultCard({ result }) {
  return (
    <article className="evaluation-result">
      <div className="result-topline">
        <div>
          <span className={result.passed ? 'result-badge pass' : 'result-badge fail'}>
            {result.passed ? 'Pass' : 'Fail'}
          </span>
          <strong>{result.id}</strong>
        </div>
        <small>{result.score}/5 · {result.latency_seconds}s</small>
      </div>
      <p className="result-prompt">{result.assistant_type}: {result.prompt}</p>
      <div className="response-compare">
        <div>
          <span>Model response</span>
          <p>{result.response || 'No response returned.'}</p>
        </div>
        <div>
          <span>Ground truth response</span>
          <p>{result.ground_truth_response}</p>
        </div>
      </div>
      {result.final && (
        <div className={`final-verdict ${result.final.verdict}`}>
          <span>Final verdict</span>
          <div>
            <strong>{result.final.verdict}</strong>
            <small>{result.final.score}/5</small>
          </div>
        </div>
      )}
      <details>
        <summary>Automated rule checks</summary>
        <p>{result.expected_behavior}</p>
        <ul>
          {result.checks.map((check) => (
            <li key={check.name}>
              <span className={check.passed ? 'check-pass' : 'check-fail'}>
                {check.passed ? 'Pass' : 'Fail'}
              </span>
              {check.name}: {check.note}
            </li>
          ))}
        </ul>
      </details>
      {result.judge?.enabled && (
        <details>
          <summary>LLM judge</summary>
          {result.judge.error ? (
            <p>{result.judge.error}</p>
          ) : (
            <>
              <div className="judge-score-grid">
                {Object.entries(result.judge.scores).map(([dimension, score]) => (
                  <div className="judge-score" key={dimension}>
                    <span>{dimension.replaceAll('_', ' ')}</span>
                    <strong>{score}/5</strong>
                  </div>
                ))}
              </div>
              <p>{result.judge.reasoning}</p>
              <p>Judge verdict: {result.judge.verdict} · {result.judge.overall_score}/5</p>
            </>
          )}
        </details>
      )}
    </article>
  )
}

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
  const [enableSuggestions, setEnableSuggestions] = useState(false)
  const [enableStreaming, setEnableStreaming] = useState(false)
  const [routingMode, setRoutingMode] = useState('auto')
  const [messages, setMessages] = useState(initialMessages)
  const [suggestions, setSuggestions] = useState([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isEvaluating, setIsEvaluating] = useState(false)
  const [error, setError] = useState('')
  const [evaluationMode, setEvaluationMode] = useState(false)
  const [evaluationView, setEvaluationView] = useState('latest')
  const [useLlmJudge, setUseLlmJudge] = useState(false)
  const [evaluationError, setEvaluationError] = useState('')
  const [evaluationResult, setEvaluationResult] = useState(null)
  const [evaluationHistory, setEvaluationHistory] = useState([])
  const [expandedDashboardRun, setExpandedDashboardRun] = useState('')
  const [isLoadingEvaluations, setIsLoadingEvaluations] = useState(false)
  const [threadId, setThreadId] = useState(createThreadId)
  const chatEndRef = useRef(null)

  const currentModels = providerModels[llmType]

  const runtimeSummary = useMemo(() => {
    const expertSummary =
      routingMode === 'manual'
        ? [assistantType, llmType, modelName, `temperature ${temperature.toFixed(1)}`]
        : ['auto routing']

    return [
      ...expertSummary,
      enableMemory ? 'memory on' : 'memory off',
      enableCache ? 'cache on' : 'cache off',
      enableSuggestions ? 'suggestions on' : 'suggestions off',
      enableStreaming ? 'streaming on' : 'streaming off',
      evaluationMode ? 'evaluation mode' : 'chat mode',
      useLlmJudge ? 'judge on' : 'judge off',
    ].join(' / ')
  }, [assistantType, enableCache, enableMemory, enableStreaming, enableSuggestions, evaluationMode, llmType, modelName, routingMode, temperature, useLlmJudge])

  function handleProviderChange(nextProvider) {
    setLlmType(nextProvider)
    setModelName(providerModels[nextProvider][0])
  }

  function resetConversation() {
    setMessages(initialMessages)
    setSuggestions(enableSuggestions && !enableStreaming ? starterPrompts : [])
    setThreadId(createThreadId())
    setError('')
  }

  function downloadChatHistory() {
    const text = buildChatHistoryText(messages, runtimeSummary, threadId)
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    downloadTextFile(`chat-history-${timestamp}.txt`, text)
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
    if (enableStreaming) {
      setSuggestions([])
    }
    setIsLoading(true)

    const startedAt = new Date().getTime()
    const recommendedAssistant = inferAssistantForQuery(trimmedMessage)
    const requestAssistant = routingMode === 'auto' ? recommendedAssistant : assistantType
    const routingMeta =
      routingMode === 'auto'
        ? `auto route: ${recommendedAssistant}`
        : recommendedAssistant === assistantType
          ? 'manual route'
          : `manual route: ${assistantType}, suggested ${recommendedAssistant}`
    const baseDetails = {
      mode: routingMeta,
      routingMode,
      selectedAssistant: assistantType,
      assistant: requestAssistant,
      suggestedAssistant: recommendedAssistant,
      provider: llmType,
      model: modelName,
      temperature: temperature.toFixed(1),
      memory: enableMemory,
      tool: allowSearch,
      backendCache: enableCache,
      sessionCache: false,
      streaming: enableStreaming,
      suggestions: enableSuggestions,
    }

    const payload = {
      assistant_type: requestAssistant,
      llm_type: llmType,
      model_name: modelName,
      messages: [trimmedMessage],
      temperature,
      allow_search: allowSearch,
      streaming: enableStreaming,
      thread_id: threadId,
      enable_memory: enableMemory,
      enable_cache: enableCache,
    }

    try {
      const response = await fetch(
        enableStreaming ? BACKEND_URL.replace(/\/chat$/, '/chat-stream') : BACKEND_URL,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(payload),
        },
      )

      if (!response.ok) {
        throw new Error(await response.text())
      }

      const duration = ((new Date().getTime() - startedAt) / 1000).toFixed(2)

      if (enableStreaming) {
        let streamBuffer = ''
        let metadataBuffer = ''
        let isReadingMetadata = false
        const assistantMessage = {
          role: 'assistant',
          assistant: requestAssistant,
          content: '',
          meta: `${routingMeta} / streaming / ${duration}s`,
          details: {
            ...baseDetails,
            cacheResult: 'streaming_no_cache',
            timeSeconds: duration,
          },
        }

        setMessages((currentMessages) => [...currentMessages, assistantMessage])

        const reader = response.body?.getReader()
        if (!reader) {
          throw new Error('Streaming response is not readable.')
        }

        const decoder = new TextDecoder()

        while (true) {
          const { done, value } = await reader.read()
          if (done) {
            break
          }

          const chunk = decoder.decode(value, { stream: true })
          if (isReadingMetadata) {
            metadataBuffer += chunk
            continue
          }

          const combinedChunk = streamBuffer + chunk
          const markerIndex = combinedChunk.indexOf(STREAM_METADATA_MARKER)
          const safeLength = Math.max(
            0,
            combinedChunk.length - STREAM_METADATA_MARKER.length + 1,
          )

          let displayBuffer = ''

          if (markerIndex >= 0) {
            displayBuffer = combinedChunk.slice(0, markerIndex)
            metadataBuffer = combinedChunk.slice(markerIndex + STREAM_METADATA_MARKER.length)
            streamBuffer = ''
            isReadingMetadata = true
          } else {
            displayBuffer = combinedChunk.slice(0, safeLength)
            streamBuffer = combinedChunk.slice(safeLength)
            metadataBuffer = ''
          }

          while (displayBuffer.length > 0) {
            const batch = displayBuffer.slice(0, STREAM_BATCH_SIZE)
            displayBuffer = displayBuffer.slice(STREAM_BATCH_SIZE)

            setMessages((currentMessages) => {
              const nextMessages = [...currentMessages]
              const lastMessage = nextMessages[nextMessages.length - 1]
              nextMessages[nextMessages.length - 1] = {
                ...lastMessage,
                content: `${lastMessage.content}${batch}`,
              }
              return nextMessages
            })

            await wait(STREAM_CHAR_DELAY_MS)
          }
        }

        if (!isReadingMetadata && streamBuffer.length > 0) {
          while (streamBuffer.length > 0) {
            const batch = streamBuffer.slice(0, STREAM_BATCH_SIZE)
            streamBuffer = streamBuffer.slice(STREAM_BATCH_SIZE)

            setMessages((currentMessages) => {
              const nextMessages = [...currentMessages]
              const lastMessage = nextMessages[nextMessages.length - 1]
              nextMessages[nextMessages.length - 1] = {
                ...lastMessage,
                content: `${lastMessage.content}${batch}`,
              }
              return nextMessages
            })

            await wait(STREAM_CHAR_DELAY_MS)
          }
        }

        if (isReadingMetadata && metadataBuffer.trim()) {
          try {
            const metadata = JSON.parse(metadataBuffer.trim())
            setSuggestions(
              enableSuggestions && metadata.suggestions?.length ? metadata.suggestions : [],
            )
          } catch {
            setSuggestions([])
          }
        } else {
          setSuggestions([])
        }

        const finalDuration = ((new Date().getTime() - startedAt) / 1000).toFixed(2)
        setMessages((currentMessages) => {
          const nextMessages = [...currentMessages]
          const lastMessage = nextMessages[nextMessages.length - 1]
          nextMessages[nextMessages.length - 1] = {
            ...lastMessage,
            meta: `${routingMeta} / streaming / ${finalDuration}s`,
            details: {
              ...lastMessage.details,
              timeSeconds: finalDuration,
              suggestions: enableSuggestions && isReadingMetadata,
            },
          }
          return nextMessages
        })

        return
      }

      const data = await response.json()

      setMessages((currentMessages) => [
        ...currentMessages,
        {
          role: 'assistant',
          assistant: requestAssistant,
          content: data.response || 'No response returned.',
          meta: `${routingMeta} / ${data.cache || 'miss'} / ${data.cache_decision?.reason || 'cache_checked'} / ${duration}s`,
          details: {
            ...baseDetails,
            cacheResult: data.cache || 'miss',
            timeSeconds: duration,
          },
        },
      ])
      setSuggestions(
        enableSuggestions && data.suggestions?.length ? data.suggestions : [],
      )
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
          details: {
            ...baseDetails,
            mode: 'error',
            cacheResult: 'error',
            timeSeconds: ((new Date().getTime() - startedAt) / 1000).toFixed(2),
          },
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

  async function loadEvaluationHistory() {
    setIsLoadingEvaluations(true)

    try {
      const response = await fetch(EVALUATIONS_URL)

      if (!response.ok) {
        throw new Error(await response.text())
      }

      const data = await response.json()
      setEvaluationHistory(data.runs || [])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load evaluation history'
      setEvaluationError(message)
    } finally {
      setIsLoadingEvaluations(false)
    }
  }

  async function runEvaluation() {
    if (isEvaluating || isLoading) {
      return
    }

    setEvaluationError('')
    setEvaluationResult(null)
    setIsEvaluating(true)

    try {
      const response = await fetch(EVALUATION_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          llm_type: llmType,
          model_name: modelName,
          temperature,
          allow_search: allowSearch,
          use_llm_judge: useLlmJudge,
        }),
      })

      if (!response.ok) {
        throw new Error(await response.text())
      }

      const result = await response.json()
      setEvaluationResult(result)
      setEvaluationHistory((currentHistory) => {
        const nextHistory = currentHistory.filter((run) => run.run_id !== result.run_id)
        return [result, ...nextHistory]
      })
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Evaluation failed'
      setEvaluationError(message)
    } finally {
      setIsEvaluating(false)
    }
  }

  async function clearEvaluationHistory() {
    setEvaluationError('')

    try {
      const response = await fetch(EVALUATIONS_URL, {
        method: 'DELETE',
      })

      if (!response.ok) {
        throw new Error(await response.text())
      }

      setEvaluationHistory([])
      setEvaluationResult(null)
      setExpandedDashboardRun('')
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to clear evaluation history'
      setEvaluationError(message)
    }
  }

  useEffect(() => {
    if (evaluationMode) {
      loadEvaluationHistory()
    }
  }, [evaluationMode])

  useEffect(() => {
    setSuggestions(enableSuggestions && !enableStreaming ? starterPrompts : [])
  }, [enableStreaming, enableSuggestions])

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ block: 'end' })
  }, [messages.length])

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
          <h1>Agent Console</h1>
        </div>

        <section className="routing-card">
          <div>
            <p className="routing-kicker">Start here</p>
            <h2>Agent routing</h2>
          </div>
          <div className="routing-choice" role="group" aria-label="Agent routing mode">
            <button
              className={routingMode === 'auto' ? 'active' : ''}
              onClick={() => {
                setRoutingMode('auto')
                setEvaluationMode(false)
              }}
              type="button"
            >
              Auto
            </button>
            <button
              className={routingMode === 'manual' ? 'active' : ''}
              onClick={() => setRoutingMode('manual')}
              type="button"
            >
              Manual
            </button>
          </div>
          <p>
            {routingMode === 'auto'
              ? 'Ask naturally. The app picks the assistant and shows the route after each answer.'
              : 'Choose the assistant, model, and runtime settings yourself.'}
          </p>
        </section>

        {routingMode === 'manual' && (
          <>
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
          </>
        )}

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
          <label className="switch-row">
            <input
              checked={enableSuggestions}
              onChange={(event) => setEnableSuggestions(event.target.checked)}
              type="checkbox"
            />
            <span>Suggestions</span>
          </label>
          <label className="switch-row">
            <input
              checked={enableStreaming}
              onChange={(event) => setEnableStreaming(event.target.checked)}
              type="checkbox"
            />
            <span>Streaming output</span>
          </label>
          {routingMode === 'manual' && (
            <label className="switch-row">
              <input
                checked={evaluationMode}
                onChange={(event) => setEvaluationMode(event.target.checked)}
                type="checkbox"
              />
              <span>Evaluation mode</span>
            </label>
          )}
        </section>

        <button className="secondary-action reset-action" onClick={resetConversation} type="button">
          New conversation
        </button>
        <button
          className="secondary-action download-action"
          disabled={messages.length <= 1}
          onClick={downloadChatHistory}
          type="button"
        >
          Download chat history
        </button>
      </aside>

      <section className="workspace" aria-label="Chat workspace">
        <header className="topbar">
          <div>
            <h2>Ask, compare, and inspect every agent response.</h2>
          </div>
          <div className="status-pill">
            <span className={isLoading || isEvaluating ? 'status-dot busy' : 'status-dot'}></span>
            {isLoading || isEvaluating ? 'Running' : 'Online'}
          </div>
        </header>

        <div className="insight-strip" aria-label="Runtime summary">
          <span>{runtimeSummary}</span>
          <span>Thread {threadId.slice(0, 8)}</span>
        </div>

        {evaluationMode ? (
          <section className="evaluation-panel" aria-label="Evaluation results">
            <div className="evaluation-header">
              <div>
                <p className="eyebrow">Golden dataset</p>
                <h3>{llmType} / {modelName}</h3>
                <p>
                  Runs backend-owned test cases with cache and memory disabled by the evaluator.
                </p>
                <label className="judge-toggle">
                  <input
                    checked={useLlmJudge}
                    onChange={(event) => setUseLlmJudge(event.target.checked)}
                    type="checkbox"
                  />
                  <span>Use LLM judge</span>
                </label>
              </div>
              <button disabled={isEvaluating || isLoading} onClick={runEvaluation} type="button">
                {isEvaluating ? 'Evaluating...' : 'Run evaluation'}
              </button>
            </div>

            <div className="evaluation-tabs" role="group" aria-label="Evaluation views">
              <button
                className={evaluationView === 'latest' ? 'active' : ''}
                onClick={() => setEvaluationView('latest')}
                type="button"
              >
                Latest run
              </button>
              <button
                className={evaluationView === 'dashboard' ? 'active' : ''}
                onClick={() => setEvaluationView('dashboard')}
                type="button"
              >
                Dashboard
              </button>
            </div>

            {evaluationError && <div className="error-banner">{evaluationError}</div>}

            <div className="evaluation-method-note">
              {useLlmJudge
                ? 'Hybrid scoring uses 40% deterministic checks and 60% LLM judge score. High-confidence judge passes can override brittle keyword misses.'
                : 'Rule-only scoring uses deterministic checks from the golden dataset.'}
            </div>

            {evaluationView === 'latest' && !evaluationResult && !evaluationError && (
              <div className="empty-evaluation">
                Select a provider and model, then run the golden dataset.
              </div>
            )}

            {evaluationView === 'latest' && evaluationResult && (
              <>
                <div className="metric-grid">
                  <div className="metric-card">
                    <span>Total tests</span>
                    <strong>{evaluationResult.summary.total}</strong>
                  </div>
                  <div className="metric-card">
                    <span>Passed</span>
                    <strong>{evaluationResult.summary.passed}</strong>
                  </div>
                  <div className="metric-card">
                    <span>Pass rate</span>
                    <strong>{Math.round(evaluationResult.summary.pass_rate * 100)}%</strong>
                  </div>
                  <div className="metric-card">
                    <span>Average score</span>
                    <strong>{evaluationResult.summary.average_score}/5</strong>
                  </div>
                </div>

                <div className="category-grid">
                  {Object.entries(evaluationResult.summary.by_category).map(([category, metrics]) => (
                    <div className="category-card" key={category}>
                      <span>{category}</span>
                      <strong>{Math.round(metrics.pass_rate * 100)}%</strong>
                      <small>
                        {metrics.passed}/{metrics.total} passed / {metrics.average_score}/5
                      </small>
                    </div>
                  ))}
                </div>

                <div className="evaluation-results">
                  {evaluationResult.results.map((result) => (
                    <EvaluationResultCard key={result.id} result={result} />
                  ))}
                </div>
              </>
            )}

            {evaluationView === 'dashboard' && (
              <section className="evaluation-dashboard" aria-label="Evaluation dashboard">
                <div className="dashboard-header">
                  <div>
                    <p className="eyebrow">Saved runs</p>
                    <h3>Model comparison dashboard</h3>
                  </div>
                  <button
                    disabled={!evaluationHistory.length || isLoadingEvaluations}
                    onClick={clearEvaluationHistory}
                    type="button"
                  >
                    Clear history
                  </button>
                </div>

                {isLoadingEvaluations && (
                  <div className="empty-evaluation">Loading saved evaluation runs...</div>
                )}

                {!isLoadingEvaluations && !evaluationHistory.length && (
                  <div className="empty-evaluation">
                    Run evaluations for multiple models to compare their scores here.
                  </div>
                )}

                {!!evaluationHistory.length && (
                  <>
                    <div className="dashboard-bars">
                      {evaluationHistory.map((run) => (
                        <article
                          className={`dashboard-run ${
                            expandedDashboardRun === run.run_id ? 'expanded' : ''
                          }`}
                          key={run.run_id}
                        >
                          <div className="dashboard-run-header">
                            <button
                              aria-expanded={expandedDashboardRun === run.run_id}
                              onClick={() =>
                                setExpandedDashboardRun((currentRun) =>
                                  currentRun === run.run_id ? '' : run.run_id,
                                )
                              }
                              type="button"
                            >
                              {run.model.llm_type} / {run.model.model_name}
                            </button>
                            <span>{run.summary.average_score}/5</span>
                          </div>
                          <div className="score-bar" aria-label="Average score">
                            <span style={{ width: `${(run.summary.average_score / 5) * 100}%` }}></span>
                          </div>
                          <div className="dashboard-run-meta">
                            <span>{Math.round(run.summary.pass_rate * 100)}% pass rate</span>
                            <span>{run.summary.passed}/{run.summary.total} passed</span>
                          </div>
                          {expandedDashboardRun === run.run_id && (
                            <div className="dashboard-run-details">
                              {run.results.map((result) => (
                                <EvaluationResultCard key={result.id} result={result} />
                              ))}
                            </div>
                          )}
                        </article>
                      ))}
                    </div>

                    <div className="dashboard-table">
                      <div className="dashboard-row dashboard-row-head">
                        <span>Model</span>
                        <span>Avg score</span>
                        <span>Pass rate</span>
                        <span>Passed</span>
                      </div>
                      {evaluationHistory.map((run) => (
                        <div className="dashboard-row" key={`${run.run_id}-row`}>
                          <span>{run.model.llm_type} / {run.model.model_name}</span>
                          <span>{run.summary.average_score}/5</span>
                          <span>{Math.round(run.summary.pass_rate * 100)}%</span>
                          <span>{run.summary.passed}/{run.summary.total}</span>
                        </div>
                      ))}
                    </div>

                    <div className="dashboard-categories">
                      {evaluationHistory.map((run) => (
                        <article className="dashboard-category-card" key={`${run.run_id}-categories`}>
                          <strong>{run.model.model_name}</strong>
                          {Object.entries(run.summary.by_category).map(([category, metrics]) => (
                            <div className="category-line" key={category}>
                              <span>{category}</span>
                              <div className="mini-bar">
                                <span style={{ width: `${metrics.pass_rate * 100}%` }}></span>
                              </div>
                              <small>{Math.round(metrics.pass_rate * 100)}%</small>
                            </div>
                          ))}
                        </article>
                      ))}
                    </div>
                  </>
                )}
              </section>
            )}
          </section>
        ) : (
          <>
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

              {isLoading && !enableStreaming && (
                <article className="message assistant loading-message">
                  <div className="message-header">
                    <span>{assistantType}</span>
                    <small>Working</small>
                  </div>
                  <p>Thinking through the request...</p>
                </article>
              )}
              <div ref={chatEndRef} aria-hidden="true"></div>
            </section>

            {error && <div className="error-banner">{error}</div>}

            {enableSuggestions && suggestions.length > 0 && (
              <div className="suggestion-row" aria-label="Suggested prompts">
                {suggestions.slice(0, 3).map((suggestion) => (
                  <button key={suggestion} onClick={() => sendMessage(suggestion)} type="button">
                    {suggestion}
                  </button>
                ))}
              </div>
            )}

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
          </>
        )}
      </section>
    </main>
  )
}

export default App
