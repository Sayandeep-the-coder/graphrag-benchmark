import React, { useState } from 'react';
import { 
  Database, 
  RefreshCw, 
  Play, 
  CheckCircle2, 
  AlertCircle, 
  ShieldAlert,
  Terminal,
  Cpu,
  Layers,
  ChevronRight,
  Zap,
  Share2,
  PlusCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const IngestionManager = ({ onIngestStarted }) => {
  const [ingestStatus, setIngestStatus] = useState({
    rag: 'idle',
    graphrag: 'idle',
    collection: 'idle'
  });
  const [lastMessage, setLastMessage] = useState('');

  const triggerIngest = async (type) => {
    setIngestStatus(prev => ({ ...prev, [type]: 'running' }));
    try {
      const response = await fetch(`http://localhost:8080/ingest/${type}`, {
        method: 'POST'
      });
      const data = await response.json();
      setIngestStatus(prev => ({ ...prev, [type]: 'started' }));
      setLastMessage(`SUCCESS: ${data.message}`);
      if (onIngestStarted) onIngestStarted(type, data.message);
    } catch (err) {
      setIngestStatus(prev => ({ ...prev, [type]: 'error' }));
      setLastMessage(`ERROR: Failed to connect to backend for ${type} ingestion.`);
    }
  };

  const strategies = [
    {
      id: 'rag',
      title: 'Pinecone Vector Ingest',
      description: 'Chunking clinical PDFs and WHO guidelines into semantic vectors.',
      icon: Database,
      color: 'text-accent-info',
      bgColor: 'bg-accent-info/10',
      borderColor: 'border-accent-info/20'
    },
    {
      id: 'graphrag',
      title: 'TigerGraph Knowledge Extraction',
      description: 'Schema-aware extraction of drugs, diseases, and adverse events into GSQL nodes.',
      icon: Cpu,
      color: 'text-accent-neon',
      bgColor: 'bg-accent-neon/10',
      borderColor: 'border-accent-neon/20'
    }
  ];

  return (
    <div className="max-w-5xl mx-auto space-y-8 p-8">
      {/* Header */}
      <div className="flex items-center gap-4 mb-10">
        <div className="w-12 h-12 rounded-xl bg-accent-neon/10 flex items-center justify-center border border-accent-neon/20 shadow-[0_0_20px_rgba(0,255,163,0.1)]">
          <Database className="w-6 h-6 text-accent-neon" />
        </div>
        <div>
          <h2 className="text-xl font-black text-white uppercase italic tracking-tighter">Knowledge_Ingestion_Engine</h2>
          <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">Orchestrating multi-modal data pipelines</p>
        </div>
      </div>

      {/* Hero Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card-premium p-6 group">
          <div className="flex items-center justify-between mb-4">
             <Layers size={18} className="text-accent-info" />
             <span className="text-[8px] font-mono text-gray-600">PIPELINE_01</span>
          </div>
          <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2">Clinical Context</h3>
          <p className="text-2xl font-black text-white font-mono italic">342<span className="text-[10px] ml-1 text-gray-600">RECORDS</span></p>
        </div>
        <div className="card-premium p-6 group">
          <div className="flex items-center justify-between mb-4">
             <Share2 size={18} className="text-accent-neon" />
             <span className="text-[8px] font-mono text-gray-600">PIPELINE_02</span>
          </div>
          <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2">Graph Vertices</h3>
          <p className="text-2xl font-black text-white font-mono italic">1,208<span className="text-[10px] ml-1 text-gray-600">NODES</span></p>
        </div>
        <div className="card-premium p-6 group border-accent-warning/30">
          <div className="flex items-center justify-between mb-4">
             <ShieldAlert size={18} className="text-accent-warning" />
             <span className="text-[8px] font-mono text-gray-600">SECURITY</span>
          </div>
          <h3 className="text-[10px] font-black uppercase tracking-[0.2em] text-gray-400 mb-2">PII Filter</h3>
          <p className="text-2xl font-black text-accent-warning font-mono italic">ACTIVE<span className="text-[10px] ml-1 text-gray-600">W/ MASKING</span></p>
        </div>
      </div>

      {/* Main Content Split */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mt-12">
        <div className="lg:col-span-2 space-y-6">
          <div className="flex items-center justify-between px-2">
            <span className="text-[10px] font-black text-gray-600 uppercase tracking-widest flex items-center gap-2">
              <Zap size={12} className="text-accent-neon" />
              Available_Workflows
            </span>
            <span className="text-[8px] font-mono text-gray-800">TOTAL_STRATEGIES: 02</span>
          </div>

          <div className="space-y-4">
            {strategies.map((s) => (
              <motion.div 
                key={s.id}
                whileHover={{ x: 4 }}
                className="bg-black/40 border border-white/5 rounded-2xl p-6 relative group overflow-hidden"
              >
                <div className={`absolute top-0 right-0 w-32 h-32 ${s.bgColor} blur-[60px] opacity-20 -mr-16 -mt-16 group-hover:opacity-40 transition-opacity`}></div>
                
                <div className="flex items-start gap-6 relative z-10">
                  <div className={`w-14 h-14 rounded-2xl ${s.bgColor} ${s.borderColor} border flex items-center justify-center shrink-0`}>
                    <s.icon className={`w-7 h-7 ${s.color}`} />
                  </div>
                  <div className="flex-1">
                    <h4 className="text-sm font-black text-white uppercase tracking-tighter italic mb-1">{s.title}</h4>
                    <p className="text-[11px] text-gray-500 font-medium leading-relaxed max-w-md">
                      {s.description}
                    </p>
                    
                    <div className="mt-6 flex items-center gap-4">
                      <button 
                        onClick={() => triggerIngest(s.id)}
                        disabled={ingestStatus[s.id] === 'running'}
                        className={`flex items-center gap-2 px-6 py-2.5 rounded-xl font-black uppercase tracking-widest text-[9px] transition-all ${
                          ingestStatus[s.id] === 'running' 
                          ? 'bg-gray-800 text-gray-500 cursor-not-allowed'
                          : 'bg-white text-black hover:bg-accent-neon hover:shadow-[0_0_15px_rgba(0,255,163,0.4)]'
                        }`}
                      >
                        {ingestStatus[s.id] === 'running' ? (
                          <RefreshCw className="w-3 h-3 animate-spin" />
                        ) : (
                          <Play className="w-3 h-3 fill-current" />
                        )}
                        {ingestStatus[s.id] === 'running' ? 'Processing...' : 'Initialize Pipeline'}
                      </button>
                      
                      {ingestStatus[s.id] === 'started' && (
                        <div className="flex items-center gap-2 text-accent-neon text-[9px] font-bold uppercase tracking-widest animate-pulse">
                          <CheckCircle2 size={12} />
                          Ingest_Started
                        </div>
                      )}
                      
                      {ingestStatus[s.id] === 'error' && (
                        <div className="flex items-center gap-2 text-accent-warning text-[9px] font-bold uppercase tracking-widest">
                          <AlertCircle size={12} />
                          Backend_Offline
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <div className="bg-black/20 border border-dashed border-white/10 rounded-2xl p-8 flex flex-col items-center justify-center gap-4 group hover:border-accent-neon/30 transition-colors">
             <div className="w-12 h-12 rounded-full border border-white/10 flex items-center justify-center text-gray-700 group-hover:text-accent-neon transition-colors">
                <Terminal size={20} />
             </div>
             <div className="text-center">
                <h5 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em]">Custom_Ingest_Payload</h5>
                <p className="text-[11px] text-gray-600 mt-1">Drag and drop clinical reports (JSON/TXT/PDF) to extend KB</p>
             </div>
          </div>
        </div>

        {/* Sidebar Info */}
        <div className="space-y-6">
           <div className="bg-[#151515] rounded-2xl p-6 border border-white/5 relative overflow-hidden">
              <div className="absolute top-0 right-0 p-4 opacity-5">
                 <ShieldAlert size={80} />
              </div>
              <h4 className="text-[10px] font-black text-accent-warning uppercase tracking-[0.2em] mb-4 flex items-center gap-2">
                 <AlertCircle size={12} />
                 Safety_Protocol_v4
              </h4>
              <ul className="space-y-4">
                 {[
                   'Automated PII anonymization',
                   'Cross-guideline contradiction check',
                   'Source provenance tracking',
                   'FDA/WHO priority weighting'
                 ].map((p, i) => (
                   <li key={i} className="flex items-start gap-3">
                      <div className="mt-1 w-1 h-1 rounded-full bg-accent-warning shrink-0"></div>
                      <span className="text-[10px] text-gray-400 font-medium leading-tight">{p}</span>
                   </li>
                 ))}
              </ul>
           </div>

           <div className="bg-accent-neon/5 rounded-2xl p-6 border border-accent-neon/10">
              <h4 className="text-[10px] font-black text-accent-neon uppercase tracking-[0.2em] mb-3">Pipeline_Monitor</h4>
              <div className="space-y-4">
                <div className="space-y-1">
                   <div className="flex justify-between text-[8px] font-mono text-gray-600 uppercase">
                      <span>Worker_Thread_Alpha</span>
                      <span>98% Load</span>
                   </div>
                   <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: '98%' }}
                        className="h-full bg-accent-neon shadow-[0_0_10px_rgba(0,255,163,0.5)]"
                      ></motion.div>
                   </div>
                </div>
                <div className="space-y-1">
                   <div className="flex justify-between text-[8px] font-mono text-gray-600 uppercase">
                      <span>Worker_Thread_Beta</span>
                      <span>42% Load</span>
                   </div>
                   <div className="h-1 bg-white/5 rounded-full overflow-hidden">
                      <motion.div 
                        initial={{ width: 0 }}
                        animate={{ width: '42%' }}
                        className="h-full bg-accent-info shadow-[0_0_10px_rgba(0,209,255,0.5)]"
                      ></motion.div>
                   </div>
                </div>
              </div>
           </div>

           <AnimatePresence>
             {lastMessage && (
               <motion.div
                 initial={{ opacity: 0, y: 10 }}
                 animate={{ opacity: 1, y: 0 }}
                 exit={{ opacity: 0 }}
                 className="p-4 rounded-xl bg-black border border-white/10 shadow-2xl"
               >
                 <div className="flex items-center justify-between mb-2">
                    <span className="text-[8px] font-mono text-gray-600 uppercase tracking-widest italic">System_Notification</span>
                    <button onClick={() => setLastMessage('')} className="text-gray-700 hover:text-white transition-colors">
                       <PlusCircle size={10} className="rotate-45" />
                    </button>
                 </div>
                 <p className="text-[10px] font-mono text-accent-neon leading-tight">
                    {lastMessage}
                 </p>
               </motion.div>
             )}
           </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default IngestionManager;
