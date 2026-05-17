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
import { motion, AnimatePresence } from "framer-motion";
import { 
  Zap, 
  Activity, 
  Database, 
  Cpu, 
  Search, 
  LayoutDashboard, 
  Share2, 
  Terminal,
  ShieldCheck,
  Globe
} from "lucide-react";
import Sidebar from "./components/Sidebar";
import PipelineCard from "./components/PipelineCard";
import MetricsTable from "./components/MetricsTable";
import TokenChart from "./components/TokenChart";
import SystemConsole from "./components/SystemConsole";
import KnowledgeGraph from "./components/KnowledgeGraph";
import ImplementationStatus from "./components/ImplementationStatus";
import IngestionManager from "./components/IngestionManager";
import BenchmarkRunner from "./components/BenchmarkRunner";
import EvaluationSidepanel from "./components/EvaluationSidepanel";
import { ListPlus } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function App() {
  const [query, setQuery] = useState("");
  const [showGroundTruth, setShowGroundTruth] = useState(false);
  const [groundTruth, setGroundTruth] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [kbContent, setKbContent] = useState("");
  const [kbTokens, setKbTokens] = useState(0);
  const [kbMeta, setKbMeta] = useState(null);
  const [kbLoading, setKbLoading] = useState(true);
  const [events, setEvents] = useState([]);
  const [activeTab, setActiveTab] = useState("dashboard");
  const [implementationStatus, setImplementationStatus] = useState(null);
  const [isSidepanelOpen, setIsSidepanelOpen] = useState(false);

  const clearBenchmark = () => {
    setQuery("");
    setResults(null);
    setEvents([]);
    setError(null);
    addEvent("System cleared. Ready for new benchmark.", "info");
  };

  const addEvent = (message, level = "info") => {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setEvents(prev => [...prev, { timestamp, message, level }]);
  };

  useEffect(() => {
    addEvent("Initializing GraphRAG Benchmark Environment...", "info");
    // Fetch knowledge base metadata on load
    fetch(`${API_URL}/knowledge-base`)
      .then((res) => {
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        return res.json();
      })
      .then((data) => {
        setKbMeta(data);
        // Compute total tokens from corpus records estimate (4 chars per token)
        const estimatedTokens = data.local_corpus_records ? Math.round(data.local_corpus_records * 500) : 0;
        setKbTokens(estimatedTokens);
        addEvent(`Knowledge base loaded: ${data.local_corpus_records?.toLocaleString() || 0} records from ${data.source_path || data.status || "unknown source"}.`, "success");
      })
      .catch((err) => {
        setKbTokens(0);
        setKbMeta(null);
        addEvent(`Failed to synchronize knowledge base: ${err.message}`, "warning");
      })
      .finally(() => setKbLoading(false));

    fetch(`${API_URL}/implementation/status`)
      .then((res) => res.json())
      .then((data) => {
        setImplementationStatus(data);
        addEvent(`Implementation map loaded: ${data.benchmark?.total_questions || 0} benchmark questions.`, "success");
      })
      .catch((err) => {
        addEvent(`Implementation map unavailable: ${err.message}`, "warning");
      });
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setEvents([]); // Clear old logs
    addEvent(`Starting evaluation for query: "${query.substring(0, 40)}..."`, "info");
    
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
        body: JSON.stringify({
          query,
          top_k: 3,
          namespace: "medical-rag",
          ground_truth: showGroundTruth ? groundTruth : null,
        }),
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

              if (type === "accuracy") {
                setResults((prev) => prev ? { ...prev, accuracy: data.accuracy } : prev);
                addEvent("Accuracy evaluation completed.", "success");
                continue;
              }

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

              if (type === "status") {
                addEvent(`[${pipeline}] ${message}`, "info");
              } else if (type === "done") {
                addEvent(`[${pipeline}] Analysis completed successfully.`, "success");
              }
            } catch (err) {
              console.error("Error parsing SSE chunk:", err, line);
            }
          }
        }
      }
    } catch (err) {
      setError(err.message);
      addEvent(`Evaluation error: ${err.message}`, "warning");
    } finally {
      setLoading(false);
      addEvent("Evaluation cycle finished.", "info");
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

  const tgCounts = kbMeta?.tigergraph?.counts || {};
  const graphNodes = kbMeta?.graph?.nodes || [];
  const graphLinks = kbMeta?.graph?.links || [];
  const liveEntityCount = tgCounts.Entity ?? 0;
  const liveRelationshipCount = Math.max(
    0,
    (tgCounts.Document || 0) + (tgCounts.Content || 0) + (tgCounts.DocumentChunk || 0)
  );

  return (
    <div className="min-h-screen bg-[#0D0D0D] flex">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} onOpenEval={() => setIsSidepanelOpen(true)} />
      
      <div className="flex-1 flex flex-col ml-64 overflow-hidden">
        {/* Header - Technical Overlay */}
        <header className="sticky top-0 z-40 bg-[#0D0D0D]/80 backdrop-blur-md border-b border-white/5 py-4 px-8 flex items-center justify-between">
          <div className="flex items-center gap-6">
             <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-accent-neon/10 flex items-center justify-center border border-accent-neon/20 shadow-[0_0_15px_rgba(0,255,163,0.1)]">
                   <Zap className="w-5 h-5 text-accent-neon" />
                </div>
                <div className="flex flex-col">
                   <span className="text-[10px] text-gray-500 font-bold uppercase tracking-widest">Active_Mission</span>
                   <span className="text-xs font-mono text-white flex items-center gap-2">
                     GraphRAG_Inference_Core_v2
                     <span className="w-1 h-1 rounded-full bg-accent-neon animate-pulse"></span>
                   </span>
                </div>
             </div>
             <div className="h-8 w-px bg-white/5"></div>
             <div className="flex items-center gap-8">
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded bg-accent-info/10 flex items-center justify-center border border-accent-info/20">
                      <Database className="w-4 h-4 text-accent-info" />
                   </div>
                   <div className="flex flex-col">
                    <h1 className="text-lg font-black text-white tracking-tighter uppercase italic leading-none">
                      GraphRAG_Inference_Core_v2
                    </h1>
                    <span className="text-[10px] text-accent-neon font-bold tracking-[0.2em] uppercase mt-1">Stabilized_Production_Build</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                   <div className="w-8 h-8 rounded bg-accent-warning/10 flex items-center justify-center border border-accent-warning/20">
                      <Share2 className="w-4 h-4 text-accent-warning" />
                   </div>
                   <div className="flex flex-col">
                      <span className="text-[8px] text-gray-500 font-bold uppercase tracking-widest">Graph_Node</span>
                      <span className="text-[10px] text-accent-warning font-mono uppercase">TigerGraph_v3</span>
                   </div>
                </div>
             </div>
          </div>
          <div className="flex items-center gap-6">
             <div className="flex items-center gap-4">
                <div className="text-right hidden xl:block">
                   <p className="text-[10px] text-white font-mono leading-none">SECURE_CHANNEL</p>
                   <p className="text-[8px] text-gray-500 font-bold uppercase tracking-widest mt-1">AES_256_GCM</p>
                </div>
                <ShieldCheck className="w-5 h-5 text-gray-500" />
             </div>
             <div className="px-4 py-1.5 bg-accent-neon/10 rounded-full border border-accent-neon/20 flex items-center gap-2 shadow-[0_0_20px_rgba(0,255,163,0.05)]">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-neon animate-pulse"></div>
                <span className="text-[9px] text-accent-neon font-black uppercase tracking-widest">System_Online</span>
             </div>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <AnimatePresence mode="wait">
            {activeTab === "dashboard" && (
              <motion.main 
                key="dashboard"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.3 }}
                className="p-8 max-w-[1400px] mx-auto w-full space-y-8"
              >
                <ImplementationStatus status={implementationStatus} />

                {/* Query Selection Area */}
                <section className="card-premium p-8 relative overflow-hidden group">
                  <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-accent-neon/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
                  
                  <div className="flex items-center gap-3 mb-6">
                     <div className="w-5 h-5 flex items-center justify-center rounded bg-accent-neon/10 text-accent-neon">
                        <Terminal size={12} />
                     </div>
                     <h2 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Inference_Query_Configuration</h2>
                  </div>

                  <textarea
                    id="query-input"
                    rows={3}
                    className="w-full bg-black/40 border border-white/10 rounded-lg p-6 text-white font-mono text-sm focus:border-accent-neon/50 outline-none transition-all placeholder:text-gray-700 shadow-inner"
                    placeholder="System awaiting query payload..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                  />

                  {/* Sample Queries */}
                  <div className="mt-4 flex flex-wrap gap-2">
                    {[
                      "Patient is taking warfarin, fluconazole, and aspirin. Trace the full interaction cascade.",
                      "Which guidelines conflict on aspirin use in elderly patients?",
                      "If omeprazole is stopped, which drug interaction paths resolve?"
                    ].map((tag) => (
                      <button
                        key={tag}
                        onClick={() => setQuery(tag)}
                        className="px-3 py-1 rounded bg-white/5 border border-white/5 text-[9px] text-gray-500 font-mono hover:border-accent-neon/30 hover:text-white transition-all uppercase tracking-wider"
                      >
                        {tag}
                      </button>
                    ))}
                    
                    <button
                      onClick={() => setIsSidepanelOpen(true)}
                      className="px-3 py-1 rounded bg-accent-neon/10 border border-accent-neon/30 text-[9px] text-accent-neon font-bold hover:bg-accent-neon/20 transition-all uppercase tracking-wider flex items-center gap-1 ml-auto"
                    >
                      <ListPlus size={10} />
                      Browse 100+ Eval Questions
                    </button>
                  </div>

                  {/* Submit and Reference Controls */}
                  <div className="mt-8 flex flex-col md:flex-row items-stretch md:items-center gap-4">
                    <button
                      id="run-benchmark-btn"
                      onClick={handleSubmit}
                      disabled={loading || !query.trim()}
                      className="btn-primary flex-1 relative group overflow-hidden"
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-accent-neon/0 via-white/10 to-accent-neon/0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
                      {loading ? (
                        <div className="flex items-center justify-center gap-3">
                          <Activity className="w-4 h-4 animate-spin" />
                          Processing Evaluation...
                        </div>
                      ) : (
                        <div className="flex items-center justify-center gap-2">
                           <Zap size={16} fill="currentColor" />
                           Execute Multi-Pipeline Benchmark
                        </div>
                      )}
                    </button>

                    <button
                      type="button"
                      onClick={() => setShowGroundTruth(!showGroundTruth)}
                      className={`px-6 py-3 rounded-lg border font-black uppercase tracking-[0.15em] text-[10px] transition-all flex items-center justify-center gap-2 ${
                        showGroundTruth 
                        ? 'bg-accent-info/10 border-accent-info text-accent-info' 
                        : 'bg-white/5 border-white/10 text-gray-400 hover:text-white hover:border-white/20'
                      }`}
                    >
                      <Database size={14} />
                      {showGroundTruth ? "Reference Loaded" : "Add Ground Truth"}
                    </button>
                    
                    <button
                      onClick={clearBenchmark}
                      className="px-6 py-3 rounded-lg bg-white/5 border border-white/10 text-gray-400 hover:text-red-400 hover:border-red-400/30 transition-all font-black uppercase tracking-[0.15em] text-[10px]"
                    >
                      Reset System
                    </button>
                  </div>

                  {showGroundTruth && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: 'auto' }}
                      className="mt-4"
                    >
                      <textarea
                        id="ground-truth-input"
                        rows={2}
                        className="w-full bg-accent-info/5 border border-accent-info/20 rounded-lg p-4 text-white font-mono text-xs outline-none focus:border-accent-info/50"
                        placeholder="Paste the reference answer for accuracy scoring..."
                        value={groundTruth}
                        onChange={(e) => setGroundTruth(e.target.value)}
                      />
                    </motion.div>
                  )}

                  {/* Error Display */}
                  {error && (
                    <div className="mt-6 p-4 bg-accent-warning/10 border border-accent-warning/20 rounded-xl text-accent-warning text-[11px] font-mono flex items-center gap-3">
                      <div className="w-5 h-5 rounded-full bg-accent-warning/20 flex items-center justify-center shrink-0">!</div>
                      <p><span className="font-bold mr-2">CRITICAL_ERROR:</span> {error}</p>
                    </div>
                  )}

                  {/* System Console */}
                  <div className="mt-8 border-t border-white/5 pt-8">
                    <SystemConsole events={events} />
                  </div>
                </section>

                {/* Results Section */}
                {results && (
                  <div className="space-y-8">
                    <section className="grid grid-cols-1 md:grid-cols-4 gap-4">
                      <div className="metric-box bg-black/30 border-accent-neon/20">
                        <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-1">Detected_Category</p>
                        <p className="text-sm font-black font-mono text-accent-neon uppercase">
                          {results.graphrag?.query_category || "Pending"}
                        </p>
                      </div>
                      <div className="metric-box bg-black/30 border-accent-info/20">
                        <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-1">Graph_Retriever</p>
                        <p className="text-sm font-black font-mono text-accent-info uppercase">
                          {results.graphrag?.retriever || "Pending"}
                        </p>
                      </div>
                      <div className="metric-box bg-black/30 border-white/10">
                        <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-1">Hop_Depth</p>
                        <p className="text-sm font-black font-mono text-white">
                          {results.graphrag?.hop_depth || "-"}
                        </p>
                      </div>
                      <div className="metric-box bg-black/30 border-accent-warning/20">
                        <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-1">Token_Reduction</p>
                        <p className="text-sm font-black font-mono text-accent-warning">
                          {(() => {
                            const rag = results.basic_rag.metrics?.total_tokens || 0;
                            const graph = results.graphrag?.metrics?.total_tokens || 0;
                            if (!rag || !graph) return "Pending";
                            return `${(((rag - graph) / rag) * 100).toFixed(1)}%`;
                          })()}
                        </p>
                      </div>
                    </section>

                    {/* Token Chart */}
                    <div className="card-premium p-8">
                       <div className="flex items-center gap-3 mb-8">
                          <div className="w-5 h-5 flex items-center justify-center rounded bg-accent-info/10 text-accent-info">
                             <Activity size={12} />
                          </div>
                          <h2 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Usage_Efficiency_Metrics</h2>
                       </div>
                       <TokenChart data={chartData} />
                    </div>

                    {/* Pipeline Cards — 3 columns */}
                    <section className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      <PipelineCard
                        name="LLM-ONLY_BASE"
                        data={results.llm_only}
                        accentColor="red"
                        accuracy={results.accuracy?.["LLM-Only"]}
                      />
                      <PipelineCard
                        name="RAG_HYBRID_CORE"
                        data={results.basic_rag}
                        accentColor="yellow"
                        accuracy={results.accuracy?.["Basic-RAG"]}
                      />
                      <PipelineCard
                        name="GRAPHRAG_SENTINEL"
                        data={results.graphrag}
                        accentColor="green"
                        accuracy={results.accuracy?.["GraphRAG"]}
                      />
                    </section>

                    {/* Metrics Comparison Table */}
                    <div className="card-premium p-8">
                       <div className="flex items-center gap-3 mb-8">
                          <div className="w-5 h-5 flex items-center justify-center rounded bg-accent-neon/10 text-accent-neon">
                             <LayoutDashboard size={12} />
                          </div>
                          <h2 className="text-[10px] font-black text-white uppercase tracking-[0.2em]">Comparative_Analysis_Matrix</h2>
                       </div>
                       <MetricsTable metrics={tableMetrics} />
                    </div>
                  </div>
                )}
              </motion.main>
            )}
            
            {activeTab === "knowledge" && (
              <motion.div 
                key="knowledge"
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="p-8 h-[calc(100vh-80px)] overflow-auto"
              >
                <div className="max-w-[1600px] mx-auto space-y-8">
                  {/* Header */}
                  <div className="flex items-center gap-4">
                    <div className="w-12 h-12 rounded-xl bg-accent-info/10 flex items-center justify-center border border-accent-info/20">
                      <Database className="w-6 h-6 text-accent-info" />
                    </div>
                    <div>
                      <h2 className="text-2xl font-black text-white uppercase italic tracking-tighter">Data & Knowledge Management</h2>
                      <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Ingestion • Mapping • Live Updates</p>
                    </div>
                  </div>

                  {/* Two-column layout */}
                  <div className="grid grid-cols-2 gap-8">
                    {/* Left: Ingestion Manager */}
                    <div className="card-premium flex flex-col p-8 relative">
                      <div className="absolute top-0 right-0 w-64 h-64 bg-accent-warning/5 blur-[100px] pointer-events-none"></div>
                      <div className="relative z-10">
                        <h3 className="text-sm font-black text-white uppercase tracking-tight mb-6 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-accent-warning"></span>
                          Data Ingestion Pipeline
                        </h3>
                        <IngestionManager 
                          onIngestStarted={(type, msg) => {
                            setEvents(prev => [{
                              timestamp: new Date().toLocaleTimeString(),
                              service: "BACKEND",
                              message: `Pipeline ingest started [${type}]: ${msg}`,
                              type: "info"
                            }, ...prev]);
                          }}
                        />
                      </div>
                    </div>

                    {/* Right: Knowledge Base Stats */}
                    <div className="card-premium flex flex-col p-8 relative">
                      <div className="absolute top-0 left-0 w-64 h-64 bg-accent-neon/5 blur-[100px] pointer-events-none"></div>
                      <div className="relative z-10">
                        <h3 className="text-sm font-black text-white uppercase tracking-tight mb-6 flex items-center gap-2">
                          <span className="w-2 h-2 rounded-full bg-accent-neon"></span>
                          Knowledge Base Status
                        </h3>
                        
                        {/* Stats grid */}
                        <div className="grid grid-cols-2 gap-3 mb-6">
                          <div className="bg-black/40 rounded-lg p-4 border border-white/5">
                            <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-2">Records</p>
                            <p className="text-2xl font-mono text-accent-neon font-bold">
                              {kbLoading ? "..." : (kbMeta?.local_corpus_records || 0).toLocaleString()}
                            </p>
                          </div>
                          <div className="bg-black/40 rounded-lg p-4 border border-white/5">
                            <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-2">Status</p>
                            <div className="flex items-center gap-2">
                              <div className={`w-2 h-2 rounded-full animate-pulse ${
                                kbMeta?.index_status === "needs_rebuild" ? "bg-accent-warning" : "bg-accent-neon"
                              }`}></div>
                              <p className={`text-[11px] font-mono font-bold ${
                                kbMeta?.index_status === "needs_rebuild" ? "text-accent-warning" : "text-accent-neon"
                              }`}>
                                {kbLoading ? "..." : (kbMeta?.index_status || "unknown").replaceAll("_", " ")}
                              </p>
                            </div>
                          </div>
                        </div>

                        {/* TigerGraph Counts */}
                        <div className="bg-accent-neon/5 border border-accent-neon/20 rounded-lg p-4 mb-6">
                          <p className="text-[9px] text-accent-neon font-black uppercase tracking-widest mb-3 italic">TigerGraph Live Counts</p>
                          <div className="grid grid-cols-2 gap-2">
                            {kbLoading ? (
                              <p className="text-[10px] text-gray-500 col-span-2 italic">Loading...</p>
                            ) : (
                              kbMeta?.tigergraph?.counts ? (
                                Object.entries(kbMeta.tigergraph.counts).map(([name, count]) => (
                                  <div key={name} className="bg-black/30 rounded p-2 border border-white/5">
                                    <p className="text-[8px] text-gray-500 font-mono uppercase">{name}</p>
                                    <p className="text-lg font-mono text-accent-neon font-bold">{(count ?? 0).toLocaleString()}</p>
                                  </div>
                                ))
                              ) : (
                                <p className="text-[10px] text-gray-500 col-span-2">No TigerGraph data</p>
                              )
                            )}
                          </div>
                        </div>

                        {/* Source Breakdown */}
                        <div>
                          <p className="text-[9px] text-gray-600 font-black uppercase tracking-widest mb-2 italic">Source Distribution</p>
                          <div className="space-y-2">
                            {kbLoading ? (
                              <p className="text-[10px] text-gray-500">Loading...</p>
                            ) : (
                              kbMeta?.source_counts ? (
                                Object.entries(kbMeta.source_counts).map(([source, count]) => (
                                  <div key={source} className="flex justify-between items-center bg-black/20 rounded px-3 py-2 border border-white/5">
                                    <span className="text-[9px] text-gray-400 font-mono uppercase">{source}</span>
                                    <span className="text-[10px] text-accent-info font-mono font-bold">{count}</span>
                                  </div>
                                ))
                              ) : (
                                <p className="text-[10px] text-gray-500">No source data</p>
                              )
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Full-width Knowledge Graph */}
                  <div className="card-premium p-8 relative">
                    <div className="absolute top-0 right-0 w-96 h-96 bg-accent-info/5 blur-[120px] pointer-events-none"></div>
                    <h3 className="text-sm font-black text-white uppercase tracking-tight mb-6 flex items-center gap-2 relative z-10">
                      <span className="w-2 h-2 rounded-full bg-accent-info"></span>
                      Knowledge Graph Visualization
                    </h3>
                    <div className="h-[500px] rounded-2xl overflow-hidden border border-white/5 bg-black/40 relative z-10">
                      <KnowledgeGraph nodes={graphNodes} links={graphLinks} />
                    </div>
                  </div>
                </div>
              </motion.div>
            )}

            {activeTab === "benchmark" && (
              <motion.div
                key="benchmark"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 20 }}
              >
                <BenchmarkRunner />
              </motion.div>
            )}

            {activeTab === "evaluations" && (
              <motion.div 
                key="evaluations"
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.98 }}
                className="p-8 max-w-[1200px] mx-auto"
              >
                 <div className="flex items-center justify-between mb-8">
                    <div className="flex items-center gap-4">
                       <div className="w-12 h-12 rounded-xl bg-accent-warning/10 flex items-center justify-center border border-accent-warning/20">
                          <Terminal className="w-6 h-6 text-accent-warning" />
                       </div>
                       <div>
                         <h2 className="text-xl font-black text-white uppercase italic tracking-tighter">System Events</h2>
                         <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Real-time activity log</p>
                       </div>
                    </div>
                    <button 
                      onClick={() => setEvents([])}
                      className="px-6 py-2 bg-white/5 border border-white/10 rounded-lg text-[10px] text-gray-500 hover:text-white hover:border-red-500/30 transition-all uppercase font-black tracking-widest"
                    >
                      Clear Events
                    </button>
                 </div>
                 <SystemConsole events={events} fullWidth />
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
      
      <EvaluationSidepanel 
        isOpen={isSidepanelOpen} 
        onClose={() => setIsSidepanelOpen(false)} 
        onSelect={(q, a) => {
          setQuery(q);
          setGroundTruth(a);
          setShowGroundTruth(!!a);
        }} 
      />
    </div>
  );
}
