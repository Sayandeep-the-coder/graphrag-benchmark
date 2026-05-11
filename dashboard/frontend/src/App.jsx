/**
 * App.jsx — Main dashboard for GraphRAG Inference Benchmark.
 *
 * Dark-themed professional layout with:
 * - Query input + optional ground truth
 * - Token reduction hero stat
 * - Token usage bar chart
 * - Side-by-side pipeline cards (3 columns)
 * - Metrics comparison table
 */
import { useState, useEffect } from "react";
import PipelineCard from "./components/PipelineCard";
import MetricsTable from "./components/MetricsTable";
import TokenChart from "./components/TokenChart";

const API_URL = "http://localhost:8080";

export default function App() {
  const [query, setQuery] = useState("");
  const [groundTruth, setGroundTruth] = useState("");
  const [showGroundTruth, setShowGroundTruth] = useState(false);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [kbContent, setKbContent] = useState("");
  const [kbTokens, setKbTokens] = useState(0);
  const [kbLoading, setKbLoading] = useState(true);

  useEffect(() => {
    // Fetch knowledge base content on load
    fetch(`${API_URL}/knowledge-base`)
      .then((res) => res.json())
      .then((data) => {
        setKbContent(data.content || "No content found.");
        setKbTokens(data.total_tokens || 0);
      })
      .catch((err) => {
        setKbContent(`Error loading knowledge base: ${err.message}`);
        setKbTokens(0);
      })
      .finally(() => setKbLoading(false));
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    
    // Initialize results state for streaming
    setResults({
      llm_only: { answer: "", status: "Pending", streamingTokens: 0, metrics: {} },
      basic_rag: { answer: "", status: "Pending", streamingTokens: 0, metrics: {} },
      graphrag: { answer: "", status: "Pending", streamingTokens: 0, metrics: {} },
    });

    try {
      const response = await fetch(`${API_URL}/compare/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, top_k: 3, namespace: "medical-rag" }),
      });

      if (!response.ok) {
        throw new Error(`API Error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n\n");
        buffer = lines.pop(); // Keep incomplete chunk in buffer

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.substring(6));
              const { pipeline, type, message, text, tokens, answer } = data;

              setResults((prev) => {
                if (!prev || !prev[pipeline]) return prev;
                const pData = prev[pipeline];

                if (type === "status") {
                  return { ...prev, [pipeline]: { ...pData, status: message } };
                } else if (type === "chunk") {
                  return { 
                    ...prev, 
                    [pipeline]: { 
                      ...pData, 
                      answer: pData.answer + (text || ""), 
                      streamingTokens: tokens > 0 ? tokens : pData.streamingTokens,
                      status: "Generating..."
                    } 
                  };
                } else if (type === "done") {
                  // Merge final data over the streaming state
                  return {
                    ...prev,
                    [pipeline]: {
                      ...pData,
                      ...data, // includes metrics, chunks_retrieved, etc.
                      answer: answer || pData.answer,
                      status: "Complete"
                    }
                  };
                }
                return prev;
              });
            } catch (err) {
              console.error("Error parsing SSE chunk:", err, line);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && e.ctrlKey) {
      handleSubmit();
    }
  };

  // Prepare chart data (use streaming tokens as fallback while generating)
  const chartData = results
    ? [
        { 
          name: "LLM-Only", 
          total_tokens: results.llm_only.metrics?.total_tokens || results.llm_only.streamingTokens || 0 
        },
        { 
          name: "Basic RAG", 
          total_tokens: results.basic_rag.metrics?.total_tokens || results.basic_rag.streamingTokens || 0 
        },
        { 
          name: "GraphRAG", 
          total_tokens: results.graphrag?.metrics?.total_tokens || results.graphrag?.streamingTokens || 0 
        },
      ]
    : null;

  // Prepare metrics table data
  const tableMetrics = results
    ? {
        llm_only: results.llm_only.metrics || {},
        basic_rag: results.basic_rag.metrics || {},
        graphrag: results.graphrag?.metrics || {},
      }
    : null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface-900/80 backdrop-blur-xl border-b border-white/5">
        <div className="max-w-[1600px] mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-indigo-400 flex items-center justify-center text-sm font-bold shadow-[0_0_15px_rgba(59,130,246,0.5)]">
            G
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              GraphRAG Inference Benchmark
            </h1>
            <p className="text-xs text-gray-400">
              Compare LLM-Only · Basic RAG · GraphRAG — side by side
            </p>
          </div>
        </div>
      </header>

      {/* Main Grid Layout */}
      <div className="flex-1 max-w-[1600px] w-full mx-auto px-6 py-8 flex flex-col xl:flex-row gap-8">
        
        {/* Left Pane: Main Application */}
        <main className="flex-1 space-y-8 min-w-0">
          
          {/* Query Input Section */}
          <section className="card card-hover">
            <label
              htmlFor="query-input"
              className="block text-sm font-bold text-gray-200 mb-2"
            >
              Enter your query
            </label>
            <textarea
              id="query-input"
              rows={3}
              className="input-field resize-none font-mono text-sm shadow-inner"
              placeholder="e.g., What are the symptoms of Malaria?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
            />

            {/* Ground Truth Toggle */}
            <div className="mt-3">
              <button
                type="button"
                onClick={() => setShowGroundTruth(!showGroundTruth)}
                className="text-sm text-indigo-400 hover:text-indigo-300 font-semibold transition-colors flex items-center gap-1"
              >
                <svg
                  className={`w-4 h-4 transition-transform ${showGroundTruth ? "rotate-90" : ""}`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
                {showGroundTruth ? "Hide" : "Add"} Ground Truth (for accuracy evaluation)
              </button>

              {showGroundTruth && (
                <textarea
                  id="ground-truth-input"
                  rows={2}
                  className="input-field resize-none font-mono text-sm mt-2 shadow-inner bg-surface-800/50"
                  placeholder="Provide the correct reference answer for accuracy scoring..."
                  value={groundTruth}
                  onChange={(e) => setGroundTruth(e.target.value)}
                />
              )}
            </div>

            {/* Submit Button */}
            <button
              id="run-benchmark-btn"
              onClick={handleSubmit}
              disabled={loading || !query.trim()}
              className="btn-primary mt-6 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  Running Evaluation...
                </>
              ) : (
                <>
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Run Benchmark
                </>
              )}
            </button>

            {/* Error Display */}
            {error && (
              <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-xl text-red-400 text-sm font-medium">
                <strong>Error:</strong> {error}
              </div>
            )}
          </section>

          {/* Results Section */}
          {results && (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
              {/* Token Chart */}
              <TokenChart data={chartData} />

              {/* Pipeline Cards — 3 columns */}
              <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <PipelineCard
                  name="Pipeline 1 — LLM Only"
                  data={results.llm_only}
                  accentColor="red"
                  accuracy={results.accuracy?.["LLM-Only"]}
                />
                <PipelineCard
                  name="Pipeline 2 — Basic RAG"
                  data={results.basic_rag}
                  accentColor="yellow"
                  accuracy={results.accuracy?.["Basic-RAG"]}
                />
                <PipelineCard
                  name="Pipeline 3 — GraphRAG"
                  data={results.graphrag}
                  accentColor="green"
                  accuracy={results.accuracy?.["GraphRAG"]}
                />
              </section>

              {/* Metrics Comparison Table */}
              <MetricsTable metrics={tableMetrics} />
            </div>
          )}
        </main>

        {/* Right Pane: Knowledge Base Sidebar */}
        <aside className="w-full xl:w-[450px] shrink-0">
          <div className="card h-[500px] xl:h-full xl:sticky xl:top-24 xl:max-h-[calc(100vh-8rem)] flex flex-col p-5">
            <h2 className="text-lg font-bold text-gray-100 mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="p-1.5 bg-blue-500/20 text-blue-400 rounded-lg">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                Knowledge Base
              </div>
              {!kbLoading && kbTokens > 0 && (
                <span className="text-xs font-mono font-normal text-gray-400 bg-surface-900/80 px-2 py-1 rounded-md border border-white/5">
                  ~{kbTokens.toLocaleString()} tokens
                </span>
              )}
            </h2>
            <div className="flex-1 overflow-y-auto bg-surface-900/60 rounded-xl p-4 border border-white/5 shadow-inner">
              {kbLoading ? (
                <div className="flex justify-center py-12">
                  <span className="spinner border-blue-500"></span>
                </div>
              ) : (
                <pre className="text-xs text-gray-300 font-mono whitespace-pre-wrap leading-relaxed">
                  {kbContent}
                </pre>
              )}
            </div>
          </div>
        </aside>

      </div>

      {/* Footer */}
      <footer className="border-t border-white/5 py-6 bg-surface-900/50 mt-auto">
        <p className="text-center text-xs text-gray-500 font-medium">
          GraphRAG Inference Benchmark · TigerGraph Hackathon · Built with Gemini + Pinecone + TigerGraph
        </p>
      </footer>
    </div>
  );
}
