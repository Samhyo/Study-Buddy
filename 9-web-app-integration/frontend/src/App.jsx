/**
 * Day 9 Demo: LLM Chat with Streaming
 *
 * Key things to point out during demo:
 * 1. Toggle streaming ON/OFF to feel the UX difference
 * 2. The fetch + ReadableStream pattern (not EventSource — we need POST)
 * 3. Conversation history is maintained client-side and sent each request
 * 4. Token cost shows up after each response
 */

import { useState } from 'react'
import ChatInput from './components/ChatInput'
import MessageList from './components/MessageList'
import UsageBar from './components/UsageBar'

const API_BASE = 'http://localhost:8000'

// Generate a stable session ID per browser tab
const SESSION_ID = `session-${Math.random().toString(36).slice(2, 9)}`

export default function App() {
  const [messages, setMessages] = useState([])
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamingEnabled, setStreamingEnabled] = useState(true)
  const [lastUsage, setLastUsage] = useState(null)
  const [error, setError] = useState(null)

  // Handle PDF upload
  async function uploadFile(file) {
    if (isStreaming) return;
    
    setError(null);
    setIsStreaming(true);

    setMessages(prev => [...prev, { role: 'user', content: `Uploaded file: ${file.name}` }]);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${API_BASE}/upload-pdf`, {
        method: 'POST',
        body: formData, // No Content-Type header; browser sets it with boundary
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || "Failed to process PDF");
      }

      const data = await response.json();

      // Add the Quiz to the chat
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: "I've generated a quiz based on your notes!",
        quizData: data.quiz // Store the structured quiz data here
      }]);

    } catch (err) {
      setError(err.message);
    } finally {
      setIsStreaming(false);
    }
  }

  async function sendMessage(text) {
    if (!text.trim() || isStreaming) return

    setError(null)
    const userMsg = { role: 'user', content: text }
    const updatedMessages = [...messages, userMsg]
    setMessages(updatedMessages)
    setIsStreaming(true)

    // Pass history as-is — the backend converts it to the Gemini format.
    // History is everything before the new user message.
    const history = messages

    try {
      if (streamingEnabled) {
        await streamResponse(text, history, updatedMessages)
      } else {
        await fetchResponse(text, history, updatedMessages)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsStreaming(false)
    }
  }

  // ── Streaming: fetch + ReadableStream ─────────────────────────────────────
  // message        — the new user text to send
  // history        — prior communication
  // currentMessages — full React message list including the new user message,
  //                   used to append the assistant reply at the correct index
  async function streamResponse(message, history, currentMessages) {
    const response = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, session_id: SESSION_ID }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || `Server error: ${response.status}`)
    }

    // Add an empty assistant message slot — we'll fill it in as chunks arrive
    const assistantIndex = currentMessages.length
    setMessages([...currentMessages, { role: 'assistant', content: '' }])

    // https://developer.mozilla.org/en-US/docs/Web/API/ReadableStream/getReader
    // The getReader() method of the ReadableStream interface creates a reader and locks the stream to it. 
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })

      // SSE events are separated by "\n\n"
      const events = buffer.split('\n\n')
      buffer = events.pop() // last item may be incomplete

      for (const event of events) {
        if (!event.startsWith('data: ')) continue
        const data = JSON.parse(event.slice(6))

        // data is one of:
        //   { type: 'text', content: '<token(s)>' }
        //   { type: 'done', usage: { input_tokens: 42, output_tokens: 9, estimated_cost_usd: 0.000008 } }
        if (data.type === 'text') {
          fullText += data.content

          setMessages((prev) => {
            const updated = [...prev]
            updated[assistantIndex] = { role: 'assistant', content: fullText }
            return updated
          })
        } else if (data.type === 'done') {
          setLastUsage(data.usage)
        }
      }
    }
  }

  // ── Non-streaming: regular fetch ──────────────────────────────────────────
  async function fetchResponse(message, history, currentMessages) {
    const response = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, history, session_id: SESSION_ID }),
    })

    if (!response.ok) {
      const err = await response.json()
      throw new Error(err.detail || `Server error: ${response.status}`)
    }

    const data = await response.json()
    setMessages([...currentMessages, { role: 'assistant', content: data.response }])
    setLastUsage(data.usage)
  }

  function clearChat() {
    setMessages([])
    setLastUsage(null)
    setError(null)
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-title">
          <h1>LLM Chat Demo</h1>
          <span className="session-id">Session: {SESSION_ID}</span>
        </div>
        <div className="header-controls">
          <label className="streaming-toggle">
            <input
              type="checkbox"
              checked={streamingEnabled}
              onChange={(e) => setStreamingEnabled(e.target.checked)}
              disabled={isStreaming}
            />
            <span>Streaming</span>
          </label>
          <button onClick={clearChat} className="btn-clear" disabled={isStreaming}>
            Clear chat
          </button>
        </div>
      </header>

      <ChatInput onSend={sendMessage} onUpload={uploadFile} disabled={isStreaming} />

      {lastUsage && <UsageBar usage={lastUsage} />}

      {error && <div className="error-banner">{error}</div>}

      <MessageList messages={messages} isStreaming={isStreaming} />
    </div>
  )
}
