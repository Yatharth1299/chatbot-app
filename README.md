✨ AI Chatbot Web App (FastAPI + React + PDF RAG)

This project is a simple AI-powered chatbot that can answer questions, remember chat history, and read information from uploaded PDF files. It uses a FastAPI backend, a React (Vite) frontend, HuggingFace embeddings with FAISS for PDF search, and OpenAI for generating chat responses.

🚀 Features

💬 Chat with an AI assistant

📄 Upload PDF files and ask questions from the content

🔍 Uses HuggingFace embeddings + FAISS for free PDF semantic search

🧠 Conversation memory

🔁 Reset chat anytime

🌐 Clean and responsive UI

🧩 Beginner-friendly, simple code structure

🛠️ Tech Stack
Frontend

React (Vite)

JavaScript

Axios

Backend

FastAPI

HuggingFace Sentence Transformers (local embeddings)

FAISS (vector similarity search)

PyPDF2 (text extraction)

OpenAI API (for chat model only)

📂 Project Structure
chatbot-app/
│── backend/
│   ├── main.py
│   ├── requirements.txt
│   └── .env   (not included)
│
└── frontend/
    ├── src/
    ├── index.html
    └── package.json

🔑 Environment Variables

Create a .env file inside the backend folder:

OPENAI_API_KEY=your_openai_key_here
OPENAI_CHAT_MODEL=gpt-4o-mini


(No HuggingFace key needed — embeddings run locally)

▶️ Running the Project
Backend
cd backend
uvicorn main:app --reload

Frontend
cd frontend
npm install
npm run dev


Open in browser:
👉 http://localhost:5173

🧠 How It Works

User uploads a PDF

Backend extracts text

Text is split into chunks

HuggingFace model generates embeddings locally

FAISS stores vectors and retrieves relevant text

OpenAI generates the final answer using retrieved context

🌍 Deployment

Backend → Render (free)

Frontend → Vercel (free)

Update API URL in frontend/src/App.jsx before deploying

👤 Author

Yatharth 
