import { useState, useEffect, useRef } from "react";

const API_BASE = "http://localhost:8000";

export default function App() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [convId, setConvId] = useState(localStorage.getItem("conv_id") || null);
  const [pdfId, setPdfId] = useState(localStorage.getItem("pdf_id") || null);
  const [uploadInfo, setUploadInfo] = useState(null);

  const fileRef = useRef(null);
  const chatEndRef = useRef(null);

  // Auto-scroll chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Load existing conversation on refresh
  useEffect(() => {
    if (convId) {
      fetch(`${API_BASE}/history?conv_id=${convId}`)
        .then((res) => res.json())
        .then((data) => {
          if (data.messages) {
            setMessages(data.messages.map(m => ({ role: m.role, text: m.text })));
          }
        });
    }
    if (pdfId) setUploadInfo({ pdf_id: pdfId });
  }, []);

  // ---------------- SEND MESSAGE ----------------
  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", text: input };
    setMessages((prev) => [...prev, userMessage]);

    const payload = {
      conv_id: convId,
      message: input,
      pdf_id: pdfId,
    };

    setInput("");

    const response = await fetch(`${API_BASE}/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();

    if (data.conv_id) {
      setConvId(data.conv_id);
      localStorage.setItem("conv_id", data.conv_id);
    }

    const botMessage = { role: "assistant", text: data.reply };
    setMessages((prev) => [...prev, botMessage]);
  };

  // ---------------- UPLOAD PDF ----------------
  const uploadPDF = async () => {
    const file = fileRef.current?.files?.[0];

    if (!file) {
      alert("Please select a PDF first.");
      return;
    }

    const fd = new FormData();
    fd.append("file", file);

    try {
      const response = await fetch(`${API_BASE}/upload_pdf`, {
        method: "POST",
        body: fd,
      });

      const data = await response.json();

      if (data.pdf_id) {
        setPdfId(data.pdf_id);
        setUploadInfo(data);
        localStorage.setItem("pdf_id", data.pdf_id);
        alert("PDF uploaded successfully!");
      } else {
        alert("Failed to upload PDF. No pdf_id returned.");
      }
    } catch (error) {
      console.error("Upload error:", error);
      alert("Upload failed. Check backend logs.");
    }
  };

  // ---------------- RESET ----------------
  const resetChat = async () => {
    await fetch(`${API_BASE}/reset`, { method: "POST" });

    setMessages([]);
    setConvId(null);
    setPdfId(null);
    setUploadInfo(null);

    localStorage.removeItem("conv_id");
    localStorage.removeItem("pdf_id");

    if (fileRef.current) fileRef.current.value = "";
  };

  return (
    <div className="app-container">
      {/* HEADER */}
      <header className="header">
        <h2>✨ AI Chatbot</h2>
        <button className="reset-btn" onClick={resetChat}>Reset</button>
      </header>

      {/* PDF UPLOAD AREA */}
      <div className="upload-box">
        <div className="upload-left">
          <input
            name="pdf"
            ref={fileRef}
            type="file"
            accept="application/pdf"
          />
          <button onClick={uploadPDF} className="upload-btn">
            Upload PDF
          </button>
        </div>

        {uploadInfo ? (
          <div className="upload-info">
            📄 {uploadInfo.filename} <br />
            🔹 {uploadInfo.num_chunks} chunks indexed
          </div>
        ) : (
          <div className="upload-info muted">No PDF uploaded</div>
        )}
      </div>

      {/* CHAT WINDOW */}
      <div className="chat-window">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`chat-bubble ${msg.role === "user" ? "user" : "assistant"}`}
          >
            {msg.text}
          </div>
        ))}
        <div ref={chatEndRef}></div>
      </div>

      {/* INPUT AREA */}
      <div className="input-area">
        <input
          className="text-input"
          placeholder="Type a message..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && sendMessage()}
        />
        <button className="send-btn" onClick={sendMessage}>
          Send
        </button>
      </div>
    </div>
  );
}
