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
    border: "border-red-500/40",
    dot: "bg-red-500",
    header: "text-red-400",
    glow: "shadow-red-500/5",
  },
  yellow: {
    border: "border-yellow-500/40",
    dot: "bg-yellow-500",
    header: "text-yellow-400",
    glow: "shadow-yellow-500/5",
  },
  green: {
    border: "border-green-500/40",
    dot: "bg-green-500",
    header: "text-green-400",
    glow: "shadow-green-500/5",
  },
};

export default function PipelineCard({ name, data, accentColor, accuracy }) {
  if (!data) return null;

  const accent = ACCENT_CLASSES[accentColor] || ACCENT_CLASSES.green;
  const m = data.metrics || {};
  const isComplete = data.status === "Complete" || (m.total_tokens > 0 && !data.status);

  return (
    <div className={`card ${accent.border} ${accent.glow} shadow-lg flex flex-col relative overflow-hidden`}>
      {/* Streaming Progress Bar */}
      {!isComplete && data.status !== "Pending" && (
        <div className="absolute top-0 left-0 w-full h-1 bg-surface-700">
          <div className={`h-full ${accent.dot} animate-pulse w-full`}></div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={`w-2.5 h-2.5 rounded-full ${isComplete ? accent.dot : "bg-gray-500 animate-pulse"}`}></span>
          <h3 className={`text-lg font-bold ${accent.header}`}>{name}</h3>
        </div>
        {!isComplete && (
          <span className="text-xs font-medium text-gray-400 bg-surface-800 px-2 py-1 rounded-full border border-white/5 animate-pulse">
            {data.status}
          </span>
        )}
      </div>

      {/* Answer */}
      <div className="mb-4 flex-1">
        <p className="text-xs text-gray-500 uppercase tracking-wider mb-2">Answer</p>
        <div className="h-48 overflow-y-auto bg-surface-900/50 rounded-lg p-3 border border-surface-700 relative">
          <p className="text-gray-300 text-sm leading-relaxed font-mono whitespace-pre-wrap">
            {data.answer || (data.status === "Pending" ? "Waiting for query..." : "")}
            {!isComplete && data.status === "Generating..." && (
              <span className={`inline-block w-2 h-4 ml-1 align-middle ${accent.dot} animate-pulse`}></span>
            )}
          </p>
        </div>
      </div>

      {/* Divider */}
      <div className="border-t border-surface-600 my-4"></div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-2 gap-3 text-sm">
        <div className="metric-box">
          <p className="text-gray-400 text-xs mb-1">Prompt Tokens</p>
          <p className="text-gray-100 font-mono font-medium">
            {isComplete ? m.prompt_tokens?.toLocaleString() : "-"}
          </p>
        </div>
        <div className="metric-box">
          <p className="text-gray-400 text-xs mb-1">Completion Tokens</p>
          <p className="text-gray-100 font-mono font-medium">
            {isComplete ? m.completion_tokens?.toLocaleString() : "-"}
          </p>
        </div>
        <div className={`metric-box col-span-2 border border-white/10 ${!isComplete ? 'bg-surface-800 animate-pulse' : 'bg-gradient-to-r from-surface-800 to-surface-700'}`}>
          <div className="flex justify-between items-end">
            <div>
              <p className="text-gray-300 text-xs mb-1">{!isComplete ? "Streaming Tokens" : "Total Tokens"}</p>
              <p className="text-white text-2xl font-bold font-mono tracking-tight">
                {!isComplete 
                  ? data.streamingTokens?.toLocaleString() || "0" 
                  : m.total_tokens?.toLocaleString()}
              </p>
            </div>
            {!isComplete && (
              <div className="text-xs text-blue-400 font-mono mb-1">Live</div>
            )}
          </div>
        </div>
        <div className="metric-box">
          <p className="text-gray-400 text-xs mb-1">Latency</p>
          <p className="text-gray-100 font-mono font-medium">
            {isComplete && m.latency_ms ? `${m.latency_ms.toFixed(0)}ms` : "-"}
          </p>
        </div>
        <div className="metric-box">
          <p className="text-gray-400 text-xs mb-1">Cost</p>
          <p className="text-gray-100 font-mono font-medium">
            {isComplete && m.cost_usd ? `$${m.cost_usd.toFixed(8)}` : "-"}
          </p>
        </div>
      </div>

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
