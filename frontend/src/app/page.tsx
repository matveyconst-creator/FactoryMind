
"use client";

import { useEffect, useState } from "react";

export default function Home() {
  const [backendOnline, setBackendOnline] = useState<boolean | null>(null);

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

        <div className="mt-12 flex gap-4">
          <button className="rounded-lg bg-white px-6 py-3 font-medium text-black">
            Get Started
          </button>

          <button className="rounded-lg border border-zinc-700 px-6 py-3 font-medium">
            Explore Platform
          </button>
        </div>
      </div>
    </main>
  );
}