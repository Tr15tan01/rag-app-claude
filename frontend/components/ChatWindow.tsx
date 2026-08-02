"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { askQuestion, SourceChunk } from "@/lib/api";

interface Message {
  role: "user" | "assistant";
  content: string;
  sources?: SourceChunk[];
}

export default function ChatWindow({ hasDocuments }: { hasDocuments: boolean }) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function handleSend(e: React.FormEvent) {
    e.preventDefault();
    const query = input.trim();
    if (!query || loading) return;

    setMessages((m) => [...m, { role: "user", content: query }]);
    setInput("");
    setError("");
    setLoading(true);

    try {
      const result = await askQuestion(query);
      setMessages((m) => [...m, { role: "assistant", content: result.answer, sources: result.sources }]);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-2">
        {messages.length === 0 && (
          <div className="h-full flex flex-col items-center justify-center text-center px-8">
            <h2 className="font-display text-2xl font-semibold mb-2">
              {hasDocuments ? "Ask away." : "Upload a document to begin."}
            </h2>
            <p className="text-sm text-ink/50 max-w-sm">
              {hasDocuments
                ? "Every answer will point back to the exact page it came from."
                : "Add a PDF from the sidebar, then come back here to ask questions about it."}
            </p>
          </div>
        )}

        <div className="space-y-6 py-4 max-w-2xl mx-auto">
          {messages.map((msg, i) => (
            <div key={i} className={msg.role === "user" ? "text-right" : ""}>
              {msg.role === "user" ? (
                <span className="inline-block bg-ink text-paper px-4 py-2.5 rounded-2xl rounded-br-sm text-sm max-w-md text-left">
                  {msg.content}
                </span>
              ) : (
                <div className="bg-surface border border-surface-border rounded-2xl rounded-bl-sm px-4 py-3.5 max-w-xl">
                  <div className="prose prose-sm max-w-none prose-p:my-1.5">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3 pt-3 border-t border-surface-border">
                      {msg.sources.map((s, j) => (
                        <span key={j} className="source-chip" title={s.text}>
                          <FileText size={10} />
                          {s.filename} · p.{s.page_number}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-center gap-2 text-sm text-ink/40">
              <Loader2 size={14} className="animate-spin" />
              Reading your documents...
            </div>
          )}

          {error && <p className="text-sm text-red-600">{error}</p>}
          <div ref={bottomRef} />
        </div>
      </div>

      <form onSubmit={handleSend} className="border-t border-surface-border pt-4 pb-1">
        <div className="max-w-2xl mx-auto flex items-center gap-2">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            disabled={!hasDocuments || loading}
            placeholder={hasDocuments ? "Ask a question about your documents..." : "Upload a document first"}
            maxLength={2000}
            className="flex-1 border border-surface-border rounded-full px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-accent-soft disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!hasDocuments || loading || !input.trim()}
            className="w-10 h-10 rounded-full bg-ink text-paper flex items-center justify-center hover:bg-ink/85 transition-colors disabled:opacity-30 shrink-0"
            aria-label="Send"
          >
            <Send size={15} />
          </button>
        </div>
      </form>
    </div>
  );
}
