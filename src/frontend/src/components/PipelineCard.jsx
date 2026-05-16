/**
 * PipelineCard — Display a single pipeline's answer and metrics.
 *
 * Props:
 *   name: string — pipeline display name
 *   data: { answer, metrics, ...extra } — pipeline result
 *   accentColor: "red" | "yellow" | "green"
 *   accuracy: object | null — accuracy data for this pipeline
 */
import AccuracyBadge from "./AccuracyBadge";

const ACCENT_CLASSES = {
  red: {
    border: "border-accent-warning/20",
    dot: "bg-accent-warning",
    header: "text-accent-warning",
    glow: "shadow-accent-warning/5",
  },
  yellow: {
    border: "border-accent-info/20",
    dot: "bg-accent-info",
    header: "text-accent-info",
    glow: "shadow-accent-info/5",
  },
  green: {
    border: "border-accent-neon/20",
    dot: "bg-accent-neon",
    header: "text-accent-neon",
    glow: "shadow-accent-neon/5",
  },
};

export default function PipelineCard({ name, data, accentColor, accuracy }) {
  if (!data) return null;

  const accent = ACCENT_CLASSES[accentColor] || ACCENT_CLASSES.green;
  const m = data.metrics || {};
  const isComplete = data.status === "Complete" || (m.total_tokens > 0 && !data.status);
  const signals = data.clinical_signals || {};
  const warnings = signals.warnings || [];
  const paths = signals.paths || [];
  const isGraphRag = name.toUpperCase().includes("GRAPHRAG");

  return (
    <div className={`card ${accent.border} ${accent.glow} shadow-lg flex flex-col relative overflow-hidden group`}>
      {/* Decorative Corner */}
      <div className={`absolute top-0 right-0 w-16 h-16 bg-gradient-to-bl from-white/5 to-transparent pointer-events-none`}></div>
      
      {/* Streaming Progress Bar */}
      {!isComplete && data.status !== "Pending" && (
        <div className="absolute top-0 left-0 w-full h-1 bg-surface-700 z-10">
          <div className={`h-full ${accent.dot} animate-pulse w-full shadow-[0_0_10px_rgba(0,255,163,0.5)]`}></div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-6 relative z-10">
        <div className="flex items-center gap-3">
          <div className={`w-3 h-3 rounded-sm ${isComplete ? accent.dot : "bg-gray-700 animate-pulse"} rotate-45`}></div>
          <h3 className={`text-sm font-black uppercase tracking-widest ${accent.header}`}>{name}</h3>
        </div>
        <div className="flex items-center gap-2">
           <span className="text-[10px] font-mono text-gray-500 bg-surface-900 px-2 py-0.5 rounded border border-white/5 uppercase">
             {isGraphRag ? "Gemma + Graph" : name.includes("RAG") ? "Gemma + Vector" : "Gemma"}
           </span>
        </div>
      </div>

      {/* Answer */}
      <div className="mb-6 flex-1 flex flex-col">
        <div className="flex items-center justify-between mb-3">
          <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em]">Output_Stream</p>
          {isComplete && (
            <span className="text-[10px] text-accent-neon font-mono">COMPLETE_OK</span>
          )}
        </div>
        <div className="flex-1 min-h-[180px] max-h-[300px] overflow-y-auto bg-black/40 rounded-xl p-4 border border-white/5 relative group-hover:border-white/10 transition-colors custom-scrollbar">
          <p className="text-gray-300 text-[13px] leading-relaxed font-mono whitespace-pre-wrap">
            {data.answer || (data.status === "Pending" ? "// AWAITING_INPUT..." : "")}
            {!isComplete && data.status === "Generating..." && (
              <span className={`inline-block w-2 h-4 ml-1 align-middle ${accent.dot} animate-pulse shadow-[0_0_10px_currentColor]`}></span>
            )}
          </p>
        </div>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-2 text-sm mb-4">
        <div className="metric-box !py-3 !px-4">
          <p className="text-gray-600 text-[9px] font-black uppercase tracking-widest mb-1">In_Tokens</p>
          <p className="text-gray-200 font-mono text-xs font-bold">
            {isComplete ? m.prompt_tokens?.toLocaleString() : "---"}
          </p>
        </div>
        <div className="metric-box !py-3 !px-4">
          <p className="text-gray-600 text-[9px] font-black uppercase tracking-widest mb-1">Out_Tokens</p>
          <p className="text-gray-200 font-mono text-xs font-bold">
            {isComplete ? m.completion_tokens?.toLocaleString() : "---"}
          </p>
        </div>
        <div className={`metric-box col-span-2 !py-4 !px-5 border border-white/5 relative overflow-hidden ${!isComplete && data.status !== "Pending" ? 'animate-pulse' : ''}`}>
          <div className="flex justify-between items-center relative z-10">
            <div>
              <p className="text-gray-500 text-[9px] font-black uppercase tracking-widest mb-1">
                {isComplete ? "Total_Consumption" : "Live_Throughput"}
              </p>
              <p className="text-white text-3xl font-black font-mono tracking-tighter">
                {!isComplete 
                  ? (data.streamingTokens || 0).toLocaleString() 
                  : (m.total_tokens || 0).toLocaleString()}
                <span className="text-xs text-gray-600 ml-2 font-bold uppercase">TKN</span>
              </p>
            </div>
            {!isComplete && data.status !== "Pending" && (
              <div className="flex flex-col items-end">
                <span className="flex h-2 w-2 relative mb-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-info opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-info"></span>
                </span>
                <span className="text-[10px] text-accent-info font-black uppercase">Sampling...</span>
              </div>
            )}
          </div>
          {/* Subtle background gauge */}
          <div className="absolute bottom-0 left-0 h-1 bg-surface-700 w-full opacity-20"></div>
        </div>
        <div className="metric-box !py-3 !px-4">
          <p className="text-gray-600 text-[9px] font-black uppercase tracking-widest mb-1">Latency</p>
          <p className="text-accent-info font-mono text-xs font-bold">
            {isComplete && m.latency_ms ? `${m.latency_ms.toFixed(0)}ms` : "---"}
          </p>
        </div>
        <div className="metric-box !py-3 !px-4">
          <p className="text-gray-600 text-[9px] font-black uppercase tracking-widest mb-1">Est_Cost</p>
          <p className="text-accent-warning font-mono text-xs font-bold">
            {isComplete && m.cost_usd ? `$${m.cost_usd.toFixed(6)}` : "---"}
          </p>
        </div>
      </div>

      {/* Reasoning Traversal Path (Technical Node List) */}
      {isGraphRag && (
        <div className="mb-8 border-t border-white/5 pt-6">
           <div className="flex items-center justify-between mb-4">
              <p className="text-[10px] text-gray-500 font-black uppercase tracking-[0.2em]">Reasoning_Path</p>
              <span className="text-[8px] text-accent-neon font-mono uppercase tracking-widest animate-pulse">
                {data.query_category || "Live_Compute"}
              </span>
           </div>
           {(data.retriever || data.hop_depth) && (
             <div className="mb-4 grid grid-cols-2 gap-2">
               <div className="metric-box !py-2 !px-3 bg-black/30">
                 <p className="text-gray-600 text-[8px] font-black uppercase tracking-widest mb-1">Retriever</p>
                 <p className="text-accent-neon font-mono text-[10px] uppercase">{data.retriever || "-"}</p>
               </div>
               <div className="metric-box !py-2 !px-3 bg-black/30">
                 <p className="text-gray-600 text-[8px] font-black uppercase tracking-widest mb-1">Hop_Depth</p>
                 <p className="text-accent-info font-mono text-[10px] uppercase">{data.hop_depth || "-"}</p>
               </div>
             </div>
           )}
           {warnings.length > 0 && (
             <div className="mb-4 rounded-xl border border-accent-warning/30 bg-accent-warning/10 p-4">
               <div className="flex items-center justify-between mb-2">
                 <p className="text-[9px] text-accent-warning font-black uppercase tracking-widest">Clinical_Warnings</p>
                 {signals.authority_score && (
                   <span className="text-[9px] text-accent-neon font-mono">
                     AUTH {Number(signals.authority_score).toFixed(2)}
                   </span>
                 )}
               </div>
               <div className="space-y-2">
                 {warnings.map((warning, idx) => (
                   <div key={idx} className="text-[11px] font-mono text-gray-300 leading-relaxed">
                     <span className="text-accent-warning font-black uppercase mr-2">
                       {warning.severity || "clinical"}
                     </span>
                     {warning.drugs?.length > 0 && (
                       <span className="text-white mr-2">{warning.drugs.join(" + ")}</span>
                     )}
                     <span>{warning.mechanism || warning.action}</span>
                   </div>
                 ))}
               </div>
             </div>
           )}
           {paths.length > 0 && (
             <div className="mb-4 rounded-xl border border-accent-neon/20 bg-accent-neon/5 p-4">
               <p className="text-[9px] text-accent-neon font-black uppercase tracking-widest mb-2">Graph_Path</p>
               <div className="space-y-1">
                 {paths.slice(0, 3).map((path, idx) => (
                   <p key={idx} className="text-[10px] font-mono text-gray-400 break-words">
                     {typeof path === "string" ? path : JSON.stringify(path)}
                   </p>
                 ))}
               </div>
             </div>
           )}
           <div className="space-y-0 px-2">
              {[
                { label: "Entity Extraction", status: isComplete ? "done" : "active" },
                { label: "Community Summary Retrieval", status: isComplete ? "done" : data.status?.includes("Community") ? "active" : "pending" },
                { label: "Global Aggregation", status: isComplete ? "done" : data.status?.includes("Aggregation") ? "active" : "pending" },
                { label: "Response Synthesis", status: isComplete ? "done" : data.status?.includes("Synthesis") ? "active" : "pending" }
              ].map((step, idx) => (
                <div key={idx} className="traversal-node">
                   <div className="flex items-center justify-between">
                      <span className={`text-[11px] font-mono ${step.status === 'done' ? 'text-gray-400' : step.status === 'active' ? 'text-accent-neon font-bold' : 'text-gray-700'}`}>
                         {step.label}
                      </span>
                      {step.status === 'active' && (
                        <span className="text-[8px] text-accent-neon font-mono animate-pulse">PROCESS_RUNNING</span>
                      )}
                      {step.status === 'done' && (
                        <svg className="w-3 h-3 text-accent-neon" fill="currentColor" viewBox="0 0 20 20"><path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"/></svg>
                      )}
                   </div>
                </div>
              ))}
           </div>
        </div>
      )}

      {/* Accuracy Section */}
      {accuracy && (
        <>
          <div className="border-t border-surface-600 my-4"></div>
          <div className="space-y-3">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Accuracy</p>

            {/* LLM-Judge */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-400">LLM-Judge</span>
              <AccuracyBadge
                verdict={
                  accuracy.llm_judge?.individual?.[0]?.verdict || "FAIL"
                }
              />
            </div>

            {/* BERTScore F1 */}
            {accuracy.bertscore && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-400">BERTScore F1</span>
                  <span className="text-sm font-mono text-gray-200">
                    {accuracy.bertscore.f1_rescaled?.toFixed(3)}
                  </span>
                </div>
                <div className="w-full bg-surface-700 rounded-full h-2">
                  <div
                    className="h-2 rounded-full bg-gradient-to-r from-blue-500 to-green-400 transition-all duration-500"
                    style={{
                      width: `${Math.max(0, Math.min(100, accuracy.bertscore.f1_rescaled * 100))}%`,
                    }}
                  ></div>
                </div>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
