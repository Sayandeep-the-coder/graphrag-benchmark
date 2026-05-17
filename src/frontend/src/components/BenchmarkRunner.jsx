import React, { useState, useEffect } from 'react';
import {
  Play,
  Terminal,
  Settings2,
  Activity,
  CheckCircle2,
  Timer,
  FileJson,
  Zap,
  BarChart3,
  Cpu,
  RefreshCw,
  AlertCircle,
  History,
  TrendingUp,
  ExternalLink
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import SystemConsole from './SystemConsole';
import MetricsTable from './MetricsTable';

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

const BenchmarkRunner = () => {
  const [isRunning, setIsRunning] = useState(false);
  const [isLite, setIsLite] = useState(true);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(0);
  const [currentTask, setCurrentTask] = useState('Standby');
  const [latestMetrics, setLatestMetrics] = useState(null);
  const [reports, setReports] = useState([]);
  const [showReports, setShowReports] = useState(false);
  const [loadingReports, setLoadingReports] = useState(false);

  // Connect to SSE for logs
  useEffect(() => {
    let eventSource;
    if (isRunning) {
      eventSource = new EventSource('http://localhost:8080/system/logs');
      eventSource.onmessage = (event) => {
        const log = JSON.parse(event.data);
        setLogs(prev => [...prev, log].slice(-100)); // Keep last 100 logs

        // Simple heuristic to update progress based on log messages
        if (log.message.includes('Starting Benchmark')) setProgress(5);
        if (log.message.includes('Accuracy evaluation')) setProgress(90);
        if (log.message.includes('Benchmark Complete')) {
          setProgress(100);
          setIsRunning(false);
          setCurrentTask('Completed');
          fetchSummary();
        }

        // Extract query progress if available: [1/5]
        const match = log.message.match(/\[(\d+)\/(\d+)\]/);
        if (match) {
          const current = parseInt(match[1]);
          const total = parseInt(match[2]);
          setProgress(Math.floor((current / total) * 80) + 5);
          setCurrentTask(`Processing Query ${current}/${total}`);
        }
      };

      eventSource.onerror = () => {
        eventSource.close();
      };
    }

    return () => {
      if (eventSource) eventSource.close();
    };
  }, [isRunning]);

  const fetchSummary = async () => {
    try {
      const res = await fetch(`${API_URL}/metrics/summary`);
      const data = await res.json();
      if (data.total_reports > 0) {
        setLatestMetrics(data);
      }
    } catch (err) {
      console.error("Failed to fetch metrics summary:", err);
    }
  };

  const fetchReports = async () => {
    setLoadingReports(true);
    try {
      const res = await fetch(`${API_URL}/metrics/summary`);
      const data = await res.json();
      setReports(data.reports || []); // Need to check if backend returns a list
      setShowReports(true);
    } catch (err) {
      console.error("Failed to fetch reports:", err);
    } finally {
      setLoadingReports(false);
    }
  };

  useEffect(() => {
    fetchSummary();
  }, []);

  const startBenchmark = async () => {
    setLogs([]);
    setProgress(0);
    setIsRunning(true);
    setCurrentTask('Initializing...');

    try {
      await fetch(`${API_URL}/benchmark/run?light=${isLite}`, {
        method: 'POST'
      });
    } catch (err) {
      setIsRunning(false);
      setCurrentTask('Connection Failed');
      setLogs(prev => [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        message: 'ERROR: Could not connect to benchmark engine.',
        level: 'warning'
      }]);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-8 space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-accent-info/10 flex items-center justify-center border border-accent-info/20 shadow-[0_0_20px_rgba(0,209,255,0.1)]">
            <BarChart3 className="w-6 h-6 text-accent-info" />
          </div>
          <div>
            <h2 className="text-xl font-black text-white uppercase italic tracking-tighter italic">Evaluation_Control_Center</h2>
            <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Stress testing multi-pipeline inference architectures</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className={`px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-widest flex items-center gap-2 ${isRunning ? 'bg-accent-neon/20 text-accent-neon' : 'bg-gray-800 text-gray-500'}`}>
            <div className={`w-1.5 h-1.5 rounded-full ${isRunning ? 'bg-accent-neon animate-pulse' : 'bg-gray-600'}`}></div>
            {isRunning ? 'Engine_Active' : 'Engine_Idle'}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Control Panel */}
        <div className="space-y-6">
          <div className="card-premium p-6">
            <h3 className="text-[10px] font-black text-gray-400 uppercase tracking-widest mb-6 flex items-center gap-2">
              <Settings2 size={12} className="text-accent-info" />
              Benchmark_Parameters
            </h3>

            <div className="space-y-4">
              <div
                onClick={() => !isRunning && setIsLite(true)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${isLite ? 'bg-accent-info/10 border-accent-info/30 ring-1 ring-accent-info/20' : 'bg-black/20 border-white/5 grayscale opacity-60'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black text-white uppercase tracking-tight">Lite Mode</span>
                  <Zap size={14} className={isLite ? 'text-accent-info' : 'text-gray-600'} />
                </div>
                <p className="text-[10px] text-gray-500 leading-tight">5 strategic queries covering all clinical categories. 2-minute runtime.</p>
              </div>

              <div
                onClick={() => !isRunning && setIsLite(false)}
                className={`p-4 rounded-xl border cursor-pointer transition-all ${!isLite ? 'bg-accent-warning/10 border-accent-warning/30 ring-1 ring-accent-warning/20' : 'bg-black/20 border-white/5 grayscale opacity-60'}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-black text-white uppercase tracking-tight">Full Stress Test</span>
                  <Activity size={14} className={!isLite ? 'text-accent-warning' : 'text-gray-600'} />
                </div>
                <p className="text-[10px] text-gray-500 leading-tight">100-question clinical suite. Includes accuracy scoring. 15-minute runtime.</p>
              </div>
            </div>

            <button
              onClick={startBenchmark}
              disabled={isRunning}
              className={`w-full mt-8 flex items-center justify-center gap-3 py-4 rounded-xl font-black uppercase tracking-[0.2em] text-xs transition-all ${isRunning
                  ? 'bg-gray-800 text-gray-600 cursor-not-allowed'
                  : 'bg-white text-black hover:bg-accent-info hover:shadow-[0_0_25px_rgba(0,209,255,0.4)] active:scale-95'
                }`}
            >
              {isRunning ? (
                <>
                  <RefreshCw size={16} className="animate-spin" />
                  Running_Suite...
                </>
              ) : (
                <>
                  <Play size={16} className="fill-current" />
                  Execute_Benchmark
                </>
              )}
            </button>
          </div>

          {latestMetrics && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="card-premium p-6 bg-accent-info/5 border-accent-info/20"
            >
              <h3 className="text-[10px] font-black text-accent-info uppercase tracking-widest mb-4 flex items-center gap-2">
                <TrendingUp size={12} />
                Latest_Run_Performance
              </h3>
              <div className="space-y-4">
                <div className="flex justify-between items-end border-b border-white/5 pb-2">
                  <span className="text-[10px] text-gray-500 uppercase font-bold">Accuracy</span>
                  <span className="text-xl font-black text-white italic">
                    {latestMetrics.accuracy?.graphrag?.judge_pass_rate ? `${(latestMetrics.accuracy.graphrag.judge_pass_rate * 100).toFixed(0)}%` : 'N/A'}
                  </span>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="block text-[8px] text-gray-600 uppercase font-black tracking-widest mb-1">Tokens</span>
                    <span className="text-xs font-mono text-gray-300">{(latestMetrics.summary?.graphrag?.total_tokens || 0).toLocaleString()}</span>
                  </div>
                  <div>
                    <span className="block text-[8px] text-gray-600 uppercase font-black tracking-widest mb-1">Latency</span>
                    <span className="text-xs font-mono text-gray-300">{Math.round(latestMetrics.summary?.graphrag?.latency_ms || 0)}ms</span>
                  </div>
                </div>
              </div>
            </motion.div>
          )}

          <div className="card-premium p-6 bg-accent-neon/5 border-accent-neon/10">
            <h3 className="text-[10px] font-black text-accent-neon uppercase tracking-widest mb-4 flex items-center gap-2">
              <Activity size={12} />
              Realtime_Progress
            </h3>

            <div className="space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-mono text-gray-400 uppercase tracking-tighter">
                  <span>{currentTask}</span>
                  <span>{progress}%</span>
                </div>
                <div className="h-2 bg-black/40 rounded-full overflow-hidden p-0.5 border border-white/5">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${progress}%` }}
                    className="h-full bg-gradient-to-r from-accent-info to-accent-neon rounded-full shadow-[0_0_15px_rgba(0,255,163,0.3)]"
                  ></motion.div>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                  <span className="block text-[8px] text-gray-600 uppercase font-black tracking-widest mb-1">Target</span>
                  <span className="text-xs font-mono text-white">{isLite ? 'LITE_05' : 'FULL_100'}</span>
                </div>
                <div className="bg-black/40 p-3 rounded-lg border border-white/5">
                  <span className="block text-[8px] text-gray-600 uppercase font-black tracking-widest mb-1">Status</span>
                  <span className={`text-xs font-mono ${isRunning ? 'text-accent-neon' : 'text-accent-info'}`}>
                    {isRunning ? 'ACTIVE' : 'READY'}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Console / Output */}
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest flex items-center gap-2">
              <Terminal size={12} className="text-accent-neon" />
              Live_Standard_Output
            </span>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-neon shadow-[0_0_5px_rgba(0,255,163,0.5)]"></div>
                <span className="text-[8px] font-mono text-gray-600">STDOUT</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-1.5 h-1.5 rounded-full bg-accent-warning"></div>
                <span className="text-[8px] font-mono text-gray-600">STDERR</span>
              </div>
            </div>
          </div>

          <div className="h-[500px]">
            <SystemConsole events={logs} onClear={() => setLogs([])} />
          </div>

          <div className="bg-black/20 border border-white/5 rounded-2xl p-6 flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center">
                <FileJson className="text-gray-500 w-5 h-5" />
              </div>
              <div>
                <h4 className="text-[10px] font-black text-white uppercase tracking-widest">Artifact_Generation</h4>
                <p className="text-[10px] text-gray-600">Evaluation reports are automatically persisted to ./results</p>
              </div>
            </div>
            <button
              onClick={fetchReports}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 border border-white/10 rounded-lg text-[9px] font-black uppercase text-gray-400 hover:text-white transition-all flex items-center gap-2"
            >
              {loadingReports ? <RefreshCw size={12} className="animate-spin" /> : <History size={12} />}
              Browse_Reports
            </button>
          </div>

          <AnimatePresence>
            {latestMetrics && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="mt-8"
              >
                <MetricsTable metrics={latestMetrics.summary} />
              </motion.div>
            )}
          </AnimatePresence>
          <AnimatePresence>
            {showReports && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 z-50 flex items-center justify-center p-6 bg-black/80 backdrop-blur-sm"
              >
                <motion.div
                  initial={{ scale: 0.95, y: 20 }}
                  animate={{ scale: 1, y: 0 }}
                  exit={{ scale: 0.95, y: 20 }}
                  className="w-full max-w-4xl max-h-[80vh] bg-[#0c0c0e] border border-white/10 rounded-2xl shadow-2xl flex flex-col overflow-hidden"
                >
                  <div className="flex items-center justify-between p-6 border-b border-white/5">
                    <div className="flex items-center gap-3">
                      <History className="text-accent-info" size={20} />
                      <h3 className="text-sm font-black text-white uppercase tracking-widest">Benchmark_History</h3>
                    </div>
                    <button
                      onClick={() => setShowReports(false)}
                      className="p-2 hover:bg-white/5 rounded-lg text-gray-500 hover:text-white transition-colors"
                    >
                      <RefreshCw size={18} className="rotate-45" />
                    </button>
                  </div>

                  <div className="flex-1 overflow-y-auto p-6 space-y-4 custom-scrollbar">
                    {reports.length === 0 ? (
                      <div className="text-center py-20 text-gray-600 font-mono text-xs uppercase tracking-widest">
                        No historical data found in ./results
                      </div>
                    ) : (
                      reports.map((report, idx) => (
                        <div
                          key={idx}
                          className="p-4 bg-white/5 border border-white/5 rounded-xl hover:border-white/20 transition-all group cursor-pointer"
                          onClick={() => {
                            setLatestMetrics(report);
                            setShowReports(false);
                          }}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-4">
                              <div className="w-10 h-10 rounded-lg bg-black/40 flex items-center justify-center text-accent-info font-mono text-xs">
                                {idx + 1}
                              </div>
                              <div>
                                <h4 className="text-xs font-black text-white uppercase">{report.filename}</h4>
                                <p className="text-[10px] text-gray-500 font-mono">{report.timestamp}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-8">
                              <div className="text-right">
                                <span className="block text-[8px] text-gray-600 uppercase font-black">Tokens</span>
                                <span className="text-xs font-mono text-gray-300">{(report.summary?.graphrag?.total_tokens || 0).toLocaleString()}</span>
                              </div>
                              <div className="text-right">
                                <span className="block text-[8px] text-gray-600 uppercase font-black">Accuracy</span>
                                <span className="text-xs font-mono text-accent-neon">
                                  {report.accuracy?.graphrag?.judge_pass_rate ? `${(report.accuracy.graphrag.judge_pass_rate * 100).toFixed(0)}%` : '-%'}
                                </span>
                              </div>
                              <ExternalLink size={14} className="text-gray-700 group-hover:text-white transition-colors" />
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </motion.div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default BenchmarkRunner;
