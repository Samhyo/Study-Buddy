# 📚 Study Buddy AI

## 👥 Project Authors
- Your Name 1  
- Your Name 2  
- Your Name 3  

---

## 🎥 Demo Video
*(Add link here)*

---

## 🧠 Project Overview

Study Buddy AI is an interactive chatbot that helps users learn and practice topics.

It can:
- Explain concepts clearly
- Ask quiz questions
- Evaluate answers
- Use your own study material

---

## 🏗️ Architecture

### 🔹 Backend (FastAPI)

The backend is built using **FastAPI**, which is a lightweight and high-performance Python web framework. 
It was chosen because it is easy to set up, supports async operations, and integrates well with modern AI APIs. 
FastAPI handles all core logic including request handling, session management, file processing, and communication with the AI model.

---

### 🔹 Frontend (React + Vite)

The frontend is implemented with **React** and powered by **Vite** for fast development and hot reloading. 
React allows building a dynamic and responsive user interface for chat interaction, while Vite ensures quick startup and efficient development workflow. 
The frontend communicates with the backend via REST API and streaming responses.

---

### 🔹 AI Model (Google Gemini API)

The application uses the **Google Gemini API**, specifically a lightweight model suitable for real-time applications. 
It was chosen because it provides a free tier, fast response times, and good performance for conversational tasks like explanations and quiz generation. 
The model operates with token limits, meaning both the input (prompt + context) and output must stay within a maximum size. 
To handle this, the system trims context and only sends relevant parts of the uploaded material to the model.

---

### 🔹 Context Retrieval (Lightweight RAG)

The system uses a simple **Retrieval-Augmented Generation (RAG)** approach. 
Uploaded text is split into smaller chunks, and only the most relevant parts are selected based on the user’s query. 
This reduces token usage, improves response quality, and keeps the system efficient without requiring a full vector database.

---

### 🔹 Streaming (Server-Sent Events)

Responses are streamed from the backend using **Server-Sent Events (SSE)**. 
This allows the user to see the AI response in real time instead of waiting for the full output.
It improves user experience and makes the application feel faster and more interactive.

---

## ⚙️ Technical Decisions

- FastAPI → lightweight backend  
- React → modern UI  
- Streaming → real-time responses  
- Lightweight RAG → chunking + keyword retrieval  

---

## 🧪 How to Run and Use the Project

Follow these steps:

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd <your-repo-folder>
```
### 2. Start backend and frontend
#### BACKEND
Go to backend folder:
```bash
cd backend
```
Install python dependencies:
```bash
pip install -r requirements.txt
```
Make sure you have a .env file with your API key:
```bash
GEMINI_API_KEY=your_api_key_here
```
Start the backend server:
```bash
python -m uvicorn main:app --reload
```
The Backend will run at:
```bash
http://localhost:8000
```
#### FRONTEND
Open a new terminal and go to the frontend folder:
```bash
cd frontend
```
Install dependencies:
```bash
npm install
```
Start the development server:
```bash
npm run dev
```
Open in browser:
http://localhost:5173

### 3. Using the application

**1. Upload a file:**
- Supported formats: `.txt`, `.pdf`
- The system extracts and processes the content
  
**2. Choose a mode:**
- **Explain mode** -> AI explains the content
- **Quiz mode** -> AI asks questions about the files

**3. Start chatting:**
- Ask questions
- Request explanations
- Answer quiz questions

### 4. Example flow
1. Upload study material (e.e. notes or PDF)
2. Ask:
```bash
Explain this topic
```
3. Switch to quiz mode:
```bash
Start quiz
```
4. Choose a correct answer

### 5. Project structure simplified
```bash
backend/
├── main.py
├── services/
│   ├── parser.py
│   └── gemini_service.py

frontend/
├── src/
├── components/
```
### Notes
- Make sure backend is running before using frontend
- Uploaded files are stored per session (not permanent)
- Refreshing the page may reset the session

---

## ⚠️ Limitations & Future Work

### Current Limitations

- The system uses simple keyword-based retrieval instead of semantic search, which may miss relevant information in some cases.
- Only `.txt` and basic `.pdf` files are supported, and text extraction from PDFs may not always be accurate.
- There is no persistent storage — all data is stored in memory and lost when the server restarts.
- The application does not include user authentication or multi-user data separation.
- The system relies on a lightweight LLM model, which may produce less detailed or precise answers compared to larger models.

---

### Future Improvements

To make this system production-ready, the following improvements would be needed:

- Implement a **vector database** (e.g. FAISS) for better semantic search and retrieval
- Add **embedding-based retrieval** instead of keyword matching
- Improve **PDF parsing** and support more file formats
- Add **user authentication and accounts**
- Store data in a **database** instead of memory
- Deploy the system to a **cloud environment**
- Improve prompt design for more consistent quiz evaluation
