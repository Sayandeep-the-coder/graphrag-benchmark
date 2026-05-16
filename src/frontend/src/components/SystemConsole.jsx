import { useState, useEffect, useRef } from "react";

/**
 * SystemConsole — A terminal-like component to display live evaluation events.
 * 
 * Props:
 *  events: Array<{ timestamp: string, message: string, level: "info" | "success" | "warning" }>
 */
export default function SystemConsole({ events = [], onClear }) {
  const consoleEndRef = useRef(null);

  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [events]);

  return (
    <div className="bg-surface-900 border border-white/5 rounded-xl overflow-hidden flex flex-col h-40 shadow-inner shadow-black/40">
      <div className="bg-surface-800 px-4 py-2 flex items-center justify-between border-b border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-accent-neon shadow-[0_0_8px_rgba(0,255,163,0.5)]"></div>
          <span className="text-[10px] font-black text-gray-400 uppercase tracking-widest">Live System Console</span>
        </div>
        <div className="flex items-center gap-4">
          {onClear && (
            <button 
              onClick={onClear}
              className="text-[9px] font-black uppercase text-gray-600 hover:text-white transition-colors"
            >
              Clear
            </button>
          )}
          <span className="text-[10px] font-mono text-gray-600">STITCH_OS v2.4.0</span>
        </div>
      </div>
      <div className="flex-1 overflow-y-auto p-4 font-mono text-[11px] leading-relaxed custom-scrollbar">
        {events.length === 0 ? (
          <div className="text-gray-700 italic">Waiting for process initiation...</div>
        ) : (
          events.map((ev, i) => (
            <div key={i} className="mb-1 flex gap-3 group">
              <span className="text-gray-600 shrink-0 select-none">[{ev.timestamp}]</span>
              <span className={`
                ${ev.level === "success" ? "text-accent-neon" : ""}
                ${ev.level === "warning" ? "text-accent-warning" : ""}
                ${ev.level === "info" ? "text-accent-info" : ""}
                ${!ev.level ? "text-gray-400" : ""}
              `}>
                <span className="mr-2 text-gray-500 opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                {ev.message}
              </span>
            </div>
          ))
        )}
        <div ref={consoleEndRef} />
      </div>
    </div>
  );
}
