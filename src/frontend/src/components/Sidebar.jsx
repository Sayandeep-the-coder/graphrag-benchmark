import React from 'react';
import { 
  LayoutDashboard, 
  Terminal, 
  Share2, 
  Bell, 
  Cpu, 
  Database,
  PlusCircle,
  Activity
} from 'lucide-react';
import { motion } from 'framer-motion';

const Sidebar = ({ activeTab, setActiveTab }) => {
  const navItems = [
    { id: 'dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { id: 'ingestion', label: 'Data Ingestion', icon: Database },
    { id: 'benchmark', label: 'Run Benchmark', icon: Activity },
    { id: 'evaluations', label: 'System Logs', icon: Terminal },
    { id: 'knowledge', label: 'Knowledge Map', icon: Share2 },
  ];

  return (
    <aside className="fixed left-0 top-0 h-screen w-64 bg-[#0D0D0D] border-r border-white/5 flex flex-col z-50">
      <div className="p-8">
        <div className="flex items-center gap-3 mb-10 group cursor-pointer">
          <motion.div 
            whileHover={{ scale: 1.1, rotate: 5 }}
            className="w-10 h-10 rounded-xl bg-accent-neon flex items-center justify-center text-surface-900"
          >
            <Activity size={20} strokeWidth={3} />
          </motion.div>
          <div className="flex flex-col">
            <h1 className="text-sm font-black text-white tracking-tighter uppercase italic leading-none">
              GraphRAG
            </h1>
            <span className="text-[8px] text-accent-neon font-bold tracking-[0.2em] uppercase mt-1">Core_Engine_v2</span>
          </div>
        </div>

        <nav className="space-y-1">
          {navItems.map((item) => (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`sidebar-link w-full text-left group relative overflow-hidden ${activeTab === item.id ? 'active' : ''}`}
            >
              {activeTab === item.id && (
                <motion.div 
                  layoutId="activeTab"
                  className="absolute left-0 top-0 w-1 h-full bg-accent-neon"
                />
              )}
              <item.icon size={16} className={`${activeTab === item.id ? 'text-accent-neon' : 'text-gray-500'} group-hover:text-white transition-colors`} />
              <span className="text-[10px] font-bold uppercase tracking-widest">{item.label}</span>
            </button>
          ))}
        </nav>

        {/* Workspace Metadata */}
        <div className="mt-12 space-y-4">
          <p className="text-[8px] text-gray-600 font-black uppercase tracking-[0.2em] px-4">Active_Workspace</p>
          <div className="px-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Database size={10} className="text-accent-info" />
                <span className="text-[9px] text-gray-500 font-mono">medical-rag</span>
              </div>
              <span className="text-[8px] text-gray-700 font-mono uppercase">Master</span>
            </div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Cpu size={10} className="text-accent-warning" />
                <span className="text-[9px] text-gray-500 font-mono">LLM_CLUSTER</span>
              </div>
              <span className="text-[8px] text-accent-neon font-mono uppercase">Ready</span>
            </div>
          </div>
        </div>
      </div>

      <div className="mt-auto p-8">
        <motion.button 
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => window.location.reload()}
          className="w-full py-3 bg-accent-neon/10 hover:bg-accent-neon/20 text-accent-neon text-[10px] font-black uppercase tracking-widest rounded-lg transition-all border border-accent-neon/30 flex items-center justify-center gap-2"
        >
          <PlusCircle size={14} />
          New Benchmark
        </motion.button>
      </div>
    </aside>
  );
};

export default Sidebar;
