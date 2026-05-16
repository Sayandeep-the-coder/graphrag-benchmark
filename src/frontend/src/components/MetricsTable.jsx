/**
 * MetricsTable — Side-by-side comparison of metrics across all 3 pipelines.
 *
 * Props:
 *   metrics: { llm_only: {...}, basic_rag: {...}, graphrag: {...} }
 *     Each object contains: total_tokens, latency_ms, cost_usd
 */
export default function MetricsTable({ metrics }) {
  if (!metrics) return null;

  const { llm_only, basic_rag, graphrag } = metrics;

  const rows = [
    {
      label: "Total Tokens",
      values: [
        llm_only.total_tokens,
        basic_rag.total_tokens,
        graphrag?.total_tokens,
      ],
      format: (v) => (v != null ? v.toLocaleString() : "-"),
    },
    {
      label: "Latency",
      values: [
        llm_only.latency_ms,
        basic_rag.latency_ms,
        graphrag?.latency_ms,
      ],
      format: (v) => (v != null ? `${v.toFixed(0)}ms` : "-"),
    },
    {
      label: "Cost",
      values: [
        llm_only.cost_usd,
        basic_rag.cost_usd,
        graphrag?.cost_usd,
      ],
      format: (v) => (v != null ? `$${v.toFixed(8)}` : "-"),
    },
  ];

  return (
    <div className="card bg-surface-800/40 border-white/5 relative overflow-hidden">
      {/* Decorative background element */}
      <div className="absolute top-0 right-0 p-4 opacity-5 pointer-events-none">
        <svg width="120" height="120" viewBox="0 0 100 100">
          <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="0.5" />
          <path d="M50 10 L50 90 M10 50 L90 50" stroke="currentColor" strokeWidth="0.5" />
        </svg>
      </div>

      <div className="flex items-center gap-3 mb-6">
        <div className="w-1.5 h-1.5 bg-accent-info rounded-full"></div>
        <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">
          Comparative_Analysis_Matrix
        </h3>
      </div>

      <div className="overflow-x-auto custom-scrollbar border border-white/5 rounded-xl">
        <table className="w-full border-collapse">
          <thead>
            <tr className="border-b-2 border-white/10">
              <th className="text-left py-4 px-6 text-[9px] font-black text-gray-500 uppercase tracking-widest bg-black/40 border-r border-white/5">
                Metric_Parameter
              </th>
              <th className="text-right py-4 px-6 text-[9px] font-black text-accent-warning uppercase tracking-widest bg-black/20 border-r border-white/5">
                LLM_ONLY
              </th>
              <th className="text-right py-4 px-6 text-[9px] font-black text-accent-info uppercase tracking-widest bg-black/40 border-r border-white/5">
                BASIC_RAG
              </th>
              <th className="text-right py-4 px-6 text-[9px] font-black text-accent-neon uppercase tracking-widest bg-black/20">
                GRAPHRAG_CORE
              </th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => {
              const numericValues = row.values.filter((v) => v != null);
              const minVal = numericValues.length > 0 ? Math.min(...numericValues) : null;
              
              return (
                <tr
                  key={row.label}
                  className="border-b border-white/5 hover:bg-white/[0.02] transition-colors group"
                >
                  <td className="py-5 px-6 text-[11px] font-bold text-gray-400 group-hover:text-white uppercase tracking-wider transition-colors bg-black/20 border-r border-white/5">
                    {row.label.replace(" ", "_")}
                  </td>
                  {row.values.map((val, i) => {
                    const isMin = val != null && val === minVal;
                    return (
                      <td
                        key={i}
                        className={`text-right py-5 px-6 font-mono text-xs transition-all border-r border-white/5 last:border-r-0 ${
                          isMin
                            ? "text-accent-neon font-black drop-shadow-[0_0_8px_rgba(0,255,163,0.3)] bg-accent-neon/5"
                            : "text-gray-500"
                        } ${i % 2 === 0 ? 'bg-black/10' : 'bg-black/5'}`}
                      >
                        {isMin && <span className="mr-2 text-[8px] animate-pulse">●</span>}
                        {row.format(val)}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
      <div className="mt-4 flex items-center justify-end gap-4 text-[9px] font-bold text-gray-600 uppercase tracking-widest">
        <div className="flex items-center gap-1.5">
          <div className="w-1.5 h-1.5 bg-accent-neon rounded-full"></div>
          Best Performance
        </div>
      </div>
    </div>
  );
}
