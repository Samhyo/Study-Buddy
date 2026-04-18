import QuizCard from './QuizCard'

export default function MessageList({ messages, isStreaming }) {
  if (messages.length === 0) {
    return (
      <div className="messages empty">
        <p className="empty-hint">
          Ask anything. Toggle <strong>Streaming</strong> in the header to compare the experience. Upload PDF to generate quiz.
        </p>
      </div>
    )
  }

  return (
    <div className="messages">
      {messages.map((msg, i) => {

        return (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-label">
              {msg.role === 'user' ? 'You' : 'Gemini'}
            </div>
            <div className="message-content">
              {msg.content || <span className="thinking">thinking…</span>}
            </div>
            {msg.quizData && (
              <div className="quiz-payload">
                <QuizCard quizData={msg.quizData} />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
