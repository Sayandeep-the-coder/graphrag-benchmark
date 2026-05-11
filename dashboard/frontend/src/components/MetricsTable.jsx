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
    <div className="card overflow-hidden">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">
        📊 Metrics Comparison
      </h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-surface-600">
              <th className="text-left py-3 px-4 text-gray-400 font-medium sticky left-0 bg-surface-800">
                Metric
              </th>
              <th className="text-right py-3 px-4 text-red-400 font-medium">
                LLM-Only
              </th>
              <th className="text-right py-3 px-4 text-yellow-400 font-medium">
                Basic RAG
              </th>
              <th className="text-right py-3 px-4 text-green-400 font-medium">
                GraphRAG
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
                  className="border-b border-surface-700 hover:bg-surface-700/50 transition-colors"
                >
                  <td className="py-3 px-4 text-gray-300 font-medium sticky left-0 bg-surface-800">
                    {row.label}
                  </td>
                  {row.values.map((val, i) => (
                    <td
                      key={i}
                      className={`text-right py-3 px-4 font-mono ${
                        val != null && val === minVal
                          ? "text-green-400 font-bold"
                          : "text-gray-400"
                      }`}
                    >
                      {row.format(val)}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
