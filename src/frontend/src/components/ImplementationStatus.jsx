import { CheckCircle2, GitBranch, ShieldAlert, Target } from "lucide-react";

const CATEGORY_LABELS = {
  TEMPORAL: "Temporal",
  CONTRADICTION: "Contradiction",
  MULTIHOP: "Multi-hop",
  COUNTERFACTUAL: "Counterfactual",
  CROSS_ENTITY: "Cross-entity",
};

export default function ImplementationStatus({ status }) {
  if (!status) return null;

  const categories = status.benchmark?.categories || {};
  const pipelines = status.pipelines || [];
  const features = status.graph_features || [];
  const artifacts = Object.values(status.artifacts || {});
  const presentArtifacts = artifacts.filter((item) => item.present).length;

  return (
    <section className="grid grid-cols-1 xl:grid-cols-[1.2fr_0.8fr] gap-6">
      <div className="card-premium p-6">
        <div className="flex items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-accent-neon/10 border border-accent-neon/20 flex items-center justify-center">
              <Target className="w-4 h-4 text-accent-neon" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-black uppercase tracking-[0.2em]">Implemented_Strategy</p>
              <h2 className="text-sm text-white font-black uppercase tracking-widest mt-1">Clinical GraphRAG Build</h2>
            </div>
          </div>
          <div className="text-right">
            <p className="text-2xl font-black font-mono text-accent-neon">{status.benchmark?.total_questions || 0}</p>
            <p className="text-[8px] text-gray-500 font-black uppercase tracking-widest">Benchmark_Questions</p>
          </div>
        </div>

        <p className="text-[12px] text-gray-400 leading-relaxed font-mono mb-6">
          {status.thesis}
        </p>

        <div className="grid grid-cols-2 md:grid-cols-5 gap-2 mb-6">
          {Object.entries(categories).map(([category, count]) => (
            <div key={category} className="metric-box !p-3 bg-black/30">
              <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-1">
                {CATEGORY_LABELS[category] || category}
              </p>
              <p className="text-lg font-black font-mono text-white">{count}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {pipelines.map((pipeline) => (
            <div key={pipeline.name} className="rounded-lg border border-white/5 bg-black/25 p-4">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="w-4 h-4 text-accent-neon" />
                <p className="text-[10px] text-white font-black uppercase tracking-widest">{pipeline.name}</p>
              </div>
              <p className="text-[10px] text-gray-500 leading-relaxed font-mono">{pipeline.role}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="card-premium p-6">
        <div className="flex items-center justify-between mb-5">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-accent-warning/10 border border-accent-warning/20 flex items-center justify-center">
              <ShieldAlert className="w-4 h-4 text-accent-warning" />
            </div>
            <div>
              <p className="text-[9px] text-gray-500 font-black uppercase tracking-[0.2em]">Demo_Signals</p>
              <h2 className="text-sm text-white font-black uppercase tracking-widest mt-1">
                {status.benchmark?.named_finding}
              </h2>
            </div>
          </div>
          <div className="text-right">
            <p className="text-sm font-black font-mono text-accent-info">
              {presentArtifacts}/{artifacts.length}
            </p>
            <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest">Artifacts</p>
          </div>
        </div>

        <div className="space-y-3">
          {features.slice(0, 5).map((feature) => (
            <div key={feature} className="flex items-start gap-3">
              <GitBranch className="w-3.5 h-3.5 text-accent-neon mt-0.5 shrink-0" />
              <p className="text-[11px] text-gray-400 font-mono leading-relaxed">{feature}</p>
            </div>
          ))}
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          <div className="metric-box !p-3 bg-black/30">
            <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-1">LLM_Judge_Target</p>
            <p className="text-lg font-black font-mono text-accent-neon">
              {Math.round((status.benchmark?.target_accuracy?.llm_judge || 0) * 100)}%
            </p>
          </div>
          <div className="metric-box !p-3 bg-black/30">
            <p className="text-[8px] text-gray-600 font-black uppercase tracking-widest mb-1">BERTScore_Target</p>
            <p className="text-lg font-black font-mono text-accent-info">
              {(status.benchmark?.target_accuracy?.bertscore || 0).toFixed(2)}
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
