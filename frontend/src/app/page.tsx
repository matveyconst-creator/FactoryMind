"use client";

import { useEffect, useState } from "react";

type UploadResult = {
  filename: string;
  content_type: string;
  size_bytes: number;
  page_count: number;
  character_count: number;
  text_preview: string;
  message: string;
};

export default function Home() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null);
  const [uploading, setUploading] = useState(false);
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
            <p className="text-zinc-400">Checking backend...</p>
          )}

          {backendOnline === true && (
            <p className="text-green-400">● Backend Online</p>
          )}

          {backendOnline === false && (
            <p className="text-red-400">● Backend Offline</p>
          )}
        </div>

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
              setSelectedFile(event.target.files?.[0] ?? null);
              setUploadResult(null);
              setError(null);
            }}
          />

          <button
            className="mt-6 rounded-lg bg-white px-5 py-3 font-medium text-black disabled:cursor-not-allowed disabled:opacity-50"
            onClick={uploadDocument}
            disabled={!selectedFile || uploading}
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
                    <strong>File:</strong> {uploadResult.filename}
                  </p>

                  <p>
                    <strong>Size:</strong>{" "}
                    {(uploadResult.size_bytes / 1024).toFixed(1)} KB
                  </p>

                  <p>
                    <strong>Pages:</strong> {uploadResult.page_count}
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
                  {uploadResult.text_preview || "No text could be extracted."}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>
    </main>
  );
}