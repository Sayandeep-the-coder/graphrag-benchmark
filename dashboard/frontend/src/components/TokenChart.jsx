/**
 * TokenChart — Bar chart comparing total tokens across all 3 pipelines.
 *
 * Props:
 *   data: [
 *     { name: "LLM-Only", total_tokens: number },
 *     { name: "Basic RAG", total_tokens: number },
 *     { name: "GraphRAG", total_tokens: number },
 *   ]
 */
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

const COLORS = ["#ef4444", "#f59e0b", "#22c55e"]; // red, yellow, green

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-surface-700 border border-surface-600 rounded-lg px-4 py-2 shadow-xl">
      <p className="text-gray-300 text-sm font-medium">{payload[0].payload.name}</p>
      <p className="text-white text-lg font-bold font-mono">
        {payload[0].value.toLocaleString()} tokens
      </p>
    </div>
  );
};

export default function TokenChart({ data }) {
  if (!data) return null;

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-gray-200 mb-4">
        🔢 Token Usage Comparison
      </h3>
      <ResponsiveContainer width="100%" height={250}>
        <BarChart data={data} barCategoryGap="25%">
          <XAxis
            dataKey="name"
            tick={{ fill: "#9ca3af", fontSize: 13 }}
            axisLine={{ stroke: "#374151" }}
            tickLine={false}
          />
          <YAxis
            tick={{ fill: "#9ca3af", fontSize: 12 }}
            axisLine={{ stroke: "#374151" }}
            tickLine={false}
            tickFormatter={(v) => v.toLocaleString()}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: "rgba(255,255,255,0.04)" }} />
          <Bar dataKey="total_tokens" radius={[8, 8, 0, 0]} maxBarSize={80}>
            {data.map((_, index) => (
              <Cell key={index} fill={COLORS[index]} fillOpacity={0.85} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
