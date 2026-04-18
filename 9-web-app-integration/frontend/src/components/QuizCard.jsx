import { useState } from 'react'

export default function QuizCard({ quizData }) {
  const [selected, setSelected] = useState({}) // Tracks { questionIndex: chosenOption }
  const [showResults, setShowResults] = useState(false)

  const handleSelect = (qIdx, option) => {
    if (showResults) return
    setSelected({ ...selected, [qIdx]: option })
  }

  return (
    <div className="quiz-card-ui">
      {quizData.map((q, qIdx) => (
        <div key={qIdx} className="q-block">
          <p><strong>{q.question}</strong></p>
          <div className="options">
            {q.options.map(opt => {
              const isSelected = selected[qIdx] === opt
              const isCorrect = opt === q.correct_answer
              
              // Logic for colors
              let className = "opt-button"
              if (showResults) {
                if (isCorrect) className += " correct-ans"
                else if (isSelected) className += " wrong-ans"
              } else if (isSelected) {
                className += " selected-ans"
              }

              return (
                <button 
                  key={opt} 
                  className={className}
                  onClick={() => handleSelect(qIdx, opt)}
                >
                  {opt}
                </button>
              )
            })}
          </div>
        </div>
      ))}
      
      {!showResults && (
        <button 
          className="check-btn"
          disabled={Object.keys(selected).length < quizData.length}
          onClick={() => setShowResults(true)}
        >
          Check My Answers
        </button>
      )}
    </div>
  )
}
