"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async (text) => {
    if (!text.trim() || loading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: data.answer, sources: data.sources || [] },
      ]);
    } catch {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Something went wrong. Try again.", sources: [] },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const quickActions = [
    { label: "Scholarships", query: "What scholarships are available at BRAC University?" },
    { label: "Admission", query: "What are the undergraduate admission requirements?" },
    { label: "Housing", query: "Tell me about student accommodation at BRACU" },
    { label: "Calendar", query: "What are the important academic dates?" },
  ];

  return (
    <div className="flex flex-col h-screen max-w-3xl mx-auto w-full px-4">
      <header className="py-6 border-b border-slate-200">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[--primary] flex items-center justify-center text-white font-bold text-sm">
            B
          </div>
          <div>
            <h1 className="text-xl font-semibold text-[--primary]">BRACU Advisor</h1>
            <p className="text-sm text-[--text-muted]">Your BRAC University assistant</p>
          </div>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto py-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-16">
            <div className="w-16 h-16 rounded-full bg-[--primary] flex items-center justify-center text-white text-2xl mx-auto mb-4">
              ?
            </div>
            <h2 className="text-lg font-medium text-[--primary] mb-2">Ask me anything about BRACU</h2>
            <p className="text-sm text-[--text-muted] max-w-md mx-auto">
              Admissions, scholarships, student life, academics, housing, and more.
            </p>
            <div className="flex flex-wrap justify-center gap-2 mt-6">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => sendMessage(action.query)}
                  className="px-4 py-2 rounded-full border border-[--accent] text-sm text-[--primary] hover:bg-[--accent] hover:text-white transition-all cursor-pointer"
                >
                  {action.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 ${
                msg.role === "user"
                  ? "bg-[--primary] text-white rounded-br-md"
                  : "bg-white border border-slate-200 rounded-bl-md"
              }`}
            >
              <p className="text-sm text-[--text] whitespace-pre-wrap">{msg.content}</p>
              {msg.sources && msg.sources.length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200/50">
                  <p className="text-xs font-medium text-[--text-muted] mb-1">Sources:</p>
                  {msg.sources.map((src, j) => (
                    <a
                      key={j}
                      href={src}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block text-xs text-[--primary-light] hover:underline truncate"
                    >
                      {src}
                    </a>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-white border border-slate-200 rounded-2xl rounded-bl-md px-4 py-3">
              <div className="flex gap-1">
                <div className="w-2 h-2 rounded-full bg-slate-300 animate-bounce" />
                <div className="w-2 h-2 rounded-full bg-slate-300 animate-bounce delay-100" />
                <div className="w-2 h-2 rounded-full bg-slate-300 animate-bounce delay-200" />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="py-4 border-t border-slate-200">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            sendMessage(input);
          }}
          className="flex gap-2"
        >
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask about BRAC University..."
            className="flex-1 px-4 py-3 rounded-xl border border-slate-200 bg-white text-sm text-[--text] outline-none focus:border-[--primary] transition-colors"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="px-5 py-3 rounded-xl bg-[--primary] text-white text-sm font-medium hover:bg-[--primary-light] disabled:opacity-50 transition-all cursor-pointer"
          >
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
