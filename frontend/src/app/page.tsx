"use client";

import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

type UploadResult = {
  filename: string;
  content_type: string;
  size_bytes: number;
  page_count: number;
  character_count: number;
  text_preview: string;
  message: string;
};

type DocumentInfo = {
  filename: string;
  page_count: number;
  character_count: number;
};

type AskResult = {
  question: string;
  answer: string;
  sources: {
    chunk_index: number;
    filename: string;
    page: number;
    similarity: number;
    text: string;
  }[];
};


type ChatMessage = {
  role: "user" | "assistant";
  content: string;
  sources?: AskResult["sources"];
};

export default function Home() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploading, setUploading] = useState(false);

  const [question, setQuestion] = useState("");
  const [askResult, setAskResult] = useState<AskResult | null>(null);
  const [asking, setAsking] = useState(false);
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);

  const [error, setError] = useState<string | null>(null);

  
  useEffect(() => {
    async function checkBackend() {
      try {
        const response = await fetch("http://127.0.0.1:8000/health");

        if (!response.ok) {
          throw new Error("Backend returned an error");
        }

        const data = await response.json();
        setBackendOnline(data.status === "ok");
      } catch {
        setBackendOnline(false);
      }
    }

    checkBackend();
  }, []);

  async function uploadDocument() {
    if (!selectedFile) {
      return;
    }

    setUploading(true);
    setUploadResult(null);
    setAskResult(null);
    setQuestion("");
    setError(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/documents/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail ?? "Upload failed");
      }

      const data = await response.json();
      setUploadResult(data);

      const documentsResponse = await fetch(
        "http://127.0.0.1:8000/documents"
      );

      if (documentsResponse.ok) {
        const documentsData = await documentsResponse.json();
        setDocuments(documentsData.documents);
      }
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Upload failed");
      }
    } finally {
      setUploading(false);
    }
  }

  async function askQuestion() {
    if (!question.trim()) {
      return;
    }

    setAsking(true);
    setAskResult(null);
    setError(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/documents/ask",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            question,
            history: chatHistory.map((message) => ({
            role: message.role,
            content: message.content,
          })),
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json();

        throw new Error(
          errorData.detail ?? "Question request failed"
        );
      }

      const data = await response.json();
      setAskResult(data);
      setChatHistory((previousHistory) => [
        ...previousHistory,
        {
          role: "user",
          content: question,
        },
        {
          role: "assistant",
          content: data.answer,
          sources: data.sources,
        },
      ]);

      setTimeout(() => {
        const messages = document.querySelectorAll('[data-chat-role="user"]');
        const latestQuestion = messages[messages.length - 1];

        latestQuestion?.scrollIntoView({
          behavior: "smooth",
          block: "start",
        });
      }, 100);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Question request failed");
      }
    } finally {
      setAsking(false);
    }
  }


  async function removeDocument(filename: string) {
    setError(null);

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/documents/${encodeURIComponent(filename)}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail ?? "Could not remove document"
        );
      }

      setDocuments((currentDocuments) =>
        currentDocuments.filter(
          (document) => document.filename !== filename
        )
      );

      setAskResult(null);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not remove document");
      }
    }
  }

  async function clearDocuments() {
    setError(null);

    try {
      const response = await fetch(
        "http://127.0.0.1:8000/documents",
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(
          errorData.detail ?? "Could not clear documents"
        );
      }

      setDocuments([]);
      setUploadResult(null);
      setAskResult(null);
      setQuestion("");
      setSelectedFile(null);
      setChatHistory([]);
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not clear documents");
      }
    }
  }

  return (
    <main className="min-h-screen bg-zinc-950 text-white">
      <div className="mx-auto max-w-6xl px-8 py-20">
        <p className="mb-4 text-sm font-medium text-blue-400">
          AI Engineering Platform
        </p>

        <h1 className="text-6xl font-bold tracking-tight">
          FactoryMind
        </h1>

        <p className="mt-6 max-w-2xl text-xl text-zinc-400">
          Intelligent analysis of technical documents, equipment,
          images and industrial data.
        </p>

        <div className="mt-8">
          {backendOnline === null && (
            <p className="text-zinc-400">
              Checking backend...
            </p>
          )}

          {backendOnline === true && (
            <p className="text-green-400">
              ● Backend Online
            </p>
          )}

          {backendOnline === false && (
            <p className="text-red-400">
              ● Backend Offline
            </p>
          )}
        </div>
        

        {documents.length > 0 && (
          <div className="mt-10 max-w-2xl rounded-xl border border-zinc-800 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-xl font-semibold">
                  Uploaded Documents
                </h2>

                <p className="mt-1 text-sm text-zinc-500">
                  {documents.length} document
                  {documents.length !== 1 ? "s" : ""} loaded
                </p>
              </div>

              <button
                onClick={clearDocuments}
                className="text-sm text-red-400 hover:text-red-300"
              >
                Clear all
              </button>
            </div>

            <div className="mt-5 space-y-3">
              {documents.map((document, index) => (
                <div
                  key={`${document.filename}-${index}`}
                  className="flex items-center justify-between rounded-lg bg-zinc-900 px-4 py-3"
                >
                  <div>
                    <p className="font-medium text-zinc-200">
                      {document.filename}
                    </p>

                    <p className="mt-1 text-xs text-zinc-500">
                      {document.page_count} pages ·{" "}
                      {document.character_count.toLocaleString()} characters
                    </p>
                  </div>

                  <div className="flex items-center gap-4">
                    <span className="text-green-400">
                      ✓
                    </span>

                    <button
                      onClick={() =>
                        removeDocument(document.filename)
                      }
                      className="text-sm text-red-400 hover:text-red-300"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <section className="mt-14 max-w-2xl rounded-xl border border-zinc-800 p-6">
          <h2 className="text-2xl font-semibold">
            Upload Technical Document
          </h2>

          <p className="mt-2 text-zinc-400">
            Upload a PDF document for analysis.
          </p>

          <input
            className="mt-6 block w-full text-sm text-zinc-300"
            type="file"
            accept="application/pdf"
            onChange={(event) => {
              setSelectedFile(
                event.target.files?.[0] ?? null
              );

              setUploadResult(null);
              setAskResult(null);
              setQuestion("");
              setError(null);
            }}
          />

          <button
            className="mt-6 rounded-lg bg-white px-5 py-3 font-medium text-black disabled:cursor-not-allowed disabled:opacity-50"
            onClick={uploadDocument}
            disabled={selectedFile === null || uploading}
          >
            {uploading ? "Processing..." : "Upload PDF"}
          </button>

          {error && (
            <div className="mt-6 rounded-lg border border-red-900 bg-red-950/30 p-4 text-red-400">
              {error}
            </div>
          )}

          {uploadResult && (
            <div className="mt-8 space-y-6">
              <div className="rounded-lg bg-zinc-900 p-5">
                <h3 className="text-lg font-semibold">
                  Document processed
                </h3>

                <div className="mt-4 space-y-1 text-sm text-zinc-300">
                  <p>
                    <strong>File:</strong>{" "}
                    {uploadResult.filename}
                  </p>

                  <p>
                    <strong>Size:</strong>{" "}
                    {(uploadResult.size_bytes / 1024).toFixed(1)} KB
                  </p>

                  <p>
                    <strong>Pages:</strong>{" "}
                    {uploadResult.page_count}
                  </p>

                  <p>
                    <strong>Characters:</strong>{" "}
                    {uploadResult.character_count.toLocaleString()}
                  </p>
                </div>

                <p className="mt-4 text-green-400">
                  ✓ {uploadResult.message}
                </p>
              </div>

              <div>
                <h3 className="mb-3 text-lg font-semibold">
                  Extracted text preview
                </h3>

                <div className="max-h-80 overflow-y-auto whitespace-pre-wrap rounded-lg border border-zinc-800 bg-zinc-900 p-5 text-sm leading-6 text-zinc-300">
                  {uploadResult.text_preview ||
                    "No text could be extracted."}
                </div>
              </div>

              

              {chatHistory.length > 0 && (
                <div
                  style={{
                    marginTop: 24,
                    display: "flex",
                    flexDirection: "column",
                    gap: 16,
                  }}
                >
                  {chatHistory.map((message, index) => {
                    return (
                      <div
                        key={index}
                        data-chat-role={message.role}
                        style={{
                          padding: 20,
                          borderRadius: 8,
                          background:
                            message.role === "user" ? "#202124" : "#18181b",
                          border: "1px solid #303036",
                        }}
                      >
                        <div
                          style={{
                            fontWeight: 700,
                            marginBottom: 12,
                          }}
                        >
                          {message.role === "user"
                            ? "You"
                            : "FactoryMind"}
                        </div>

                        <ReactMarkdown
                          remarkPlugins={[remarkGfm, remarkMath]}
                          rehypePlugins={[rehypeKatex]}
                        >
                          {message.content}
                        </ReactMarkdown>

                        {message.role === "assistant" &&
                          message.sources &&
                          message.sources.length > 0 && (
                            <details style={{ marginTop: 16 }}>
                              <summary
                                style={{
                                  cursor: "pointer",
                                  color: "#a1a1aa",
                                }}
                              >
                                Show sources
                              </summary>

                              <div
                                style={{
                                  marginTop: 12,
                                  display: "flex",
                                  flexDirection: "column",
                                  gap: 12,
                                }}
                              >
                                {message.sources.map(
                                  (source, sourceIndex) => (
                                    <div
                                      key={sourceIndex}
                                      style={{
                                        padding: 16,
                                        border: "1px solid #303036",
                                        borderRadius: 8,
                                      }}
                                    >
                                      <div
                                        style={{
                                          color: "#3b82f6",
                                        }}
                                      >
                                        {source.filename} · Page{" "}
                                        {source.page}
                                      </div>

                                      <div
                                        style={{
                                          marginTop: 4,
                                          marginBottom: 12,
                                          fontSize: 12,
                                          color: "#71717a",
                                        }}
                                      >
                                        Chunk {source.chunk_index} ·
                                        Similarity{" "}
                                        {source.similarity.toFixed(3)}
                                      </div>

                                      <div
                                        style={{
                                          whiteSpace: "pre-wrap",
                                        }}
                                      >
                                        {source.text}
                                      </div>
                                    </div>
                                  )
                                )}
                              </div>
                            </details>
                          )}
                      </div>
                    );
                  })}
                </div>
              )}

              <div className="border-t border-zinc-800 pt-6">
                <h3 className="text-xl font-semibold">
                  Ask FactoryMind
                </h3>

                <p className="mt-2 text-sm text-zinc-400">
                  Ask a question about the uploaded document.
                </p>

                <textarea
                  className="mt-4 min-h-28 w-full rounded-lg border border-zinc-800 bg-zinc-900 p-4 text-sm text-white outline-none placeholder:text-zinc-500 focus:border-zinc-600"
                  placeholder="What packages should I import?"
                  value={question}
                  onChange={(event) =>
                    setQuestion(event.target.value)
                  }
                />

                <button
                  className="mt-4 rounded-lg bg-blue-500 px-5 py-3 font-medium text-white disabled:cursor-not-allowed disabled:opacity-50"
                  onClick={askQuestion}
                  disabled={!question.trim() || asking}
                >
                  {asking ? "Thinking..." : "Ask Question"}
                </button>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}