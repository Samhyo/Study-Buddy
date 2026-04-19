# 📚 Study Buddy AI

## 👥 Project Authors
- Your Name 1  
- Your Name 2  
- Your Name 3  

---

## 🎥 Demo Video
*(Add link here)*

---

## 🧠 Project Overview (Simplified)

Study Buddy AI is a web-based chatbot designed to help users learn and practice topics interactively.

The application can:
- Explain concepts in a simple way
- Generate quiz questions
- Evaluate user answers
- Use user-provided study material

The system works as a conversational study assistant that adapts between teaching and testing modes.

---

## 🏗️ Architecture

### Backend
- Built with **FastAPI (Python)**
- Handles API requests, AI logic, and session management
- Manages:
  - Chat endpoints
  - File uploads
  - Study logic (quiz & explanation modes)

### Frontend
- Built with **React (Vite + JavaScript)**
- Provides user interface for:
  - Chat interaction
  - Mode switching (Explain / Quiz)
  - File uploads

### LLM Provider
- **Google Gemini API**
- Used for:
  - Text generation
  - Question creation
  - Answer evaluation

---

## ⚙️ Technical Decisions

### Backend
- **FastAPI** → lightweight and fast for building APIs
- **Uvicorn** → ASGI server for running the backend
- **Pydantic** → request validation
- **Streaming (SSE)** → real-time AI responses

### Frontend
- **React** → component-based UI
- **Vite** → fast development environment

### AI Logic
- **Prompt engineering** → controls AI behavior (explain vs quiz)
- **Lightweight RAG (Retrieval-Augmented Generation)**:
  - Text is split into chunks
  - Relevant parts are selected using keyword matching
  - Only relevant content is sent to the AI

---

## 🧪 How to Use

### 1. Start Backend
```bash
python -m uvicorn main:app --reload
