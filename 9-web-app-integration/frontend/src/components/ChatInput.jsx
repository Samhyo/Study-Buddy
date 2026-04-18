import { useState, useRef } from 'react'

export default function ChatInput({ onSend, onUpload, disabled }) {
  const [text, setText] = useState('')
  const fileInputRef = useRef(null)

  function handleKeyDown(e) {
    // Enter sends; Shift+Enter inserts a newline
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      submit()
    }
  }

  function submit() {
    if (!text.trim() || disabled) return
    onSend(text.trim())
    setText('')
  }

  function handleFileClick() {
    fileInputRef.current.click()
  }

  function handleFileChange(e) {
    const file = e.target.files[0]
    if (file && onUpload) {
      onUpload(file)
      // Reset the input value so the same file can be uploaded twice if needed
      e.target.value = null 
    }
  }

  return (
    <div className="input-area">
      <input
        type="file"
        accept=".pdf"
        ref={fileInputRef}
        onChange={handleFileChange}
        style={{ display: 'none' }}
      />
      
      {/* Upload Button */}
      <button 
        onClick={handleFileClick} 
        disabled={disabled} 
        className="btn-upload"
        title="Upload PDF Study Notes"
      >
        📎
      </button>
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Message Gemini… (Enter to send, Shift+Enter for newline, or upload a PDF file)"
        disabled={disabled}
        rows={2}
        autoFocus
      />
      <button onClick={submit} disabled={disabled || !text.trim()} className="btn-send">
        {disabled ? 'Waiting…' : 'Send'}
      </button>
    </div>
  )
}
