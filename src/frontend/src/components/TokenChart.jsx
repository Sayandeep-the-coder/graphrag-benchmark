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

const COLORS = ["#FF8A00", "#00D1FF", "#00FFA3"]; // warning, info, neon

const CustomTooltip = ({ active, payload }) => {
  if (!active || !payload?.length) return null;

  return (
    <div className="bg-surface-900/90 backdrop-blur-xl border border-white/10 rounded-lg px-4 py-3 shadow-2xl">
      <p className="text-[9px] text-gray-500 font-black uppercase tracking-widest mb-1">{payload[0].payload.name}</p>
      <div className="flex items-baseline gap-2">
        <p className="text-white text-xl font-black font-mono tracking-tighter">
          {payload[0].value.toLocaleString()}
        </p>
        <p className="text-[10px] text-gray-600 font-bold uppercase">Tokens</p>
      </div>
    </div>
  );
};

export default function TokenChart({ data }) {
  if (!data) return null;

  return (
    <div className="card bg-surface-800/40 border-white/5 relative overflow-hidden group">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-1.5 h-1.5 bg-accent-warning rounded-full"></div>
        <h3 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">
          Token_Utilization_Benchmark
        </h3>
      </div>

      <div className="h-[250px] w-full relative z-10">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 0, right: 60, top: 0, bottom: 0 }}>
            <XAxis type="number" hide />
            <YAxis
              dataKey="name"
              type="category"
              tick={{ fill: "#E0E0E0", fontSize: 10, fontWeight: 800, fontFamily: "JetBrains Mono" }}
              axisLine={false}
              tickLine={false}
              width={120}
            />
            <Tooltip 
              content={<CustomTooltip />} 
              cursor={{ fill: "rgba(255,255,255,0.03)" }} 
              animationDuration={200}
            />
            <Bar dataKey="total_tokens" radius={[0, 6, 6, 0]} barSize={32}>
              {data.map((_, index) => (
                <Cell 
                  key={index} 
                  fill={COLORS[index]} 
                  fillOpacity={0.8}
                  className="transition-all duration-300 hover:fill-opacity-100"
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Decorative background grid for the chart */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(#fff 1px, transparent 1px)', backgroundSize: '20px 20px' }}></div>
    </div>
  );
}
