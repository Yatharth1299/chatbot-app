# backend/main.py
# FastAPI + FREE HuggingFace embeddings + FAISS + OpenAI chat responses.

import os
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from openai import OpenAI
from io import BytesIO

# Load env
load_dotenv()

# Chat model (only chat uses OpenAI)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")

# FREE embedding model from HuggingFace
embedder = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

PDF_STORE = {}       # pdf_id → {filename, chunks, embeddings, index}
CONVERSATIONS = {}   # conv_id → messages


# ------------------------ PDF Extraction ------------------------
def extract_text_from_pdf_bytes(file_bytes: bytes) -> str:
    pdf_stream = BytesIO(file_bytes)
    reader = PdfReader(pdf_stream)

    text = ""
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
            text += page_text
        except Exception as e:
            print("PDF read error:", e)
    return text


def chunk_text(text: str, max_chars=800):
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + max_chars].strip()
        if chunk:
            chunks.append(chunk)
        start += max_chars
    return chunks


# ------------------------ FREE Embeddings ------------------------
def get_embeddings(texts: List[str]) -> np.ndarray:
    print("Generating FREE embeddings...")
    emb = embedder.encode(texts, convert_to_numpy=True)
    return emb.astype(np.float32)


# ------------------------ FAISS Index ------------------------
def build_faiss_index(embeddings: np.ndarray):
    dim = embeddings.shape[1]
    index = faiss.IndexFlatL2(dim)
    index.add(embeddings)
    return index


def retrieve_top_k(pdf_id: str, query: str, k=4):
    entry = PDF_STORE.get(pdf_id)
    if not entry:
        return []

    query_emb = get_embeddings([query])
    distances, indices = entry["index"].search(query_emb, k)

    results = []
    for idx in indices[0]:
        if 0 <= idx < len(entry["chunks"]):
            results.append(entry["chunks"][idx])

    return results


# ------------------------ Chat (OpenAI) ------------------------
def call_openai_chat(messages: List[dict]) -> str:
    try:
        resp = client.chat.completions.create(
            model=CHAT_MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=700,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"[Chat API Error: {e}]"


# ------------------------ Pydantic Models ------------------------
class ChatRequest(BaseModel):
    conv_id: Optional[str] = None
    message: str
    pdf_id: Optional[str] = None
    top_k: Optional[int] = 4


class ChatResponse(BaseModel):
    conv_id: str
    reply: str


# ------------------------ Upload PDF Endpoint ------------------------
@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):

    content = await file.read()
    text = extract_text_from_pdf_bytes(content)

    if not text.strip():
        raise HTTPException(status_code=400, detail="PDF has no extractable text.")

    chunks = chunk_text(text)
    embeddings = get_embeddings(chunks)
    index = build_faiss_index(embeddings)

    pdf_id = str(uuid.uuid4())

    PDF_STORE[pdf_id] = {
        "filename": file.filename,
        "chunks": chunks,
        "embeddings": embeddings,
        "index": index,
    }

    return {
        "pdf_id": pdf_id,
        "filename": file.filename,
        "num_chunks": len(chunks),
    }


# ------------------------ Chat Endpoint ------------------------
@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):

    conv_id = req.conv_id or str(uuid.uuid4())

    if conv_id not in CONVERSATIONS:
        CONVERSATIONS[conv_id] = []

    # Save user message
    CONVERSATIONS[conv_id].append({"role": "user", "text": req.message})

    # Retrieve PDF context
    context = ""
    if req.pdf_id:
        top_chunks = retrieve_top_k(req.pdf_id, req.message, req.top_k)
        if top_chunks:
            context = "\n\n---- PDF CONTEXT ----\n" + "\n\n".join(top_chunks) + "\n\n"

    # Build chat messages
    messages = [{"role": "system", "content": "You are a helpful assistant."}]

    if context:
        messages.append({"role": "system", "content": context})

    for m in CONVERSATIONS[conv_id][-8:]:
        messages.append({"role": m["role"], "content": m["text"]})

    reply = call_openai_chat(messages)

    # Save assistant msg
    CONVERSATIONS[conv_id].append({"role": "assistant", "text": reply})

    return ChatResponse(conv_id=conv_id, reply=reply)


# ------------------------ Reset ------------------------
@app.post("/reset")
async def reset(conv_id: Optional[str] = Form(None)):
    if conv_id:
        CONVERSATIONS.pop(conv_id, None)
        return {"status": "ok", "message": f"Conversation {conv_id} cleared."}

    CONVERSATIONS.clear()
    return {"status": "ok", "message": "All conversations cleared."}


@app.get("/")
def home():
    return {"status": "OK", "message": "Backend running"}
