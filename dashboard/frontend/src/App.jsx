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
import { useState } from "react";
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

  const handleSubmit = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const body = { query: query.trim() };
      if (showGroundTruth && groundTruth.trim()) {
        body.ground_truth = groundTruth.trim();
      }

      const res = await fetch(`${API_URL}/compare`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`API error: ${res.status} ${res.statusText}`);
      }

      const data = await res.json();
      setResults(data);
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

  // Prepare chart data
  const chartData = results
    ? [
        { name: "LLM-Only", total_tokens: results.llm_only.metrics.total_tokens },
        { name: "Basic RAG", total_tokens: results.basic_rag.metrics.total_tokens },
      ]
    : null;

  // Prepare metrics table data
  const tableMetrics = results
    ? {
        llm_only: results.llm_only.metrics,
        basic_rag: results.basic_rag.metrics,
      }
    : null;

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-surface-900/80 backdrop-blur-xl border-b border-surface-700">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-green-400 flex items-center justify-center text-sm font-bold">
            G
          </div>
          <div>
            <h1 className="text-xl font-bold text-white tracking-tight">
              GraphRAG Inference Benchmark
            </h1>
            <p className="text-xs text-gray-400">
              Compare LLM-Only · Basic RAG — side by side
            </p>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8 space-y-8">
        {/* Query Input Section */}
        <section className="card">
          <label
            htmlFor="query-input"
            className="block text-sm font-medium text-gray-300 mb-2"
          >
            Enter your query
          </label>
          <textarea
            id="query-input"
            rows={3}
            className="input-field resize-none font-mono text-sm"
            placeholder="e.g., Who invented the World Wide Web and what organization did they work for?"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
          />

          {/* Ground Truth Toggle */}
          <div className="mt-3">
            <button
              type="button"
              onClick={() => setShowGroundTruth(!showGroundTruth)}
              className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
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
                className="input-field resize-none font-mono text-sm mt-2"
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
            className="btn-primary mt-4 flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <span className="spinner"></span>
                Running 2 pipelines...
              </>
            ) : (
              <>
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Run Benchmark
              </>
            )}
          </button>

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              <strong>Error:</strong> {error}
            </div>
          )}
        </section>

        {/* Results Section */}
        {results && (
          <>
            {/* Token Chart */}
            <TokenChart data={chartData} />

            {/* Pipeline Cards — 2 columns */}
            <section className="grid grid-cols-1 md:grid-cols-2 gap-6">
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
            </section>

            {/* Metrics Comparison Table */}
            <MetricsTable metrics={tableMetrics} />
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-surface-700 py-4">
        <p className="text-center text-xs text-gray-600">
          GraphRAG Inference Benchmark · TigerGraph Hackathon · Built with Gemini + Pinecone + TigerGraph
        </p>
      </footer>
    </div>
  );
}
