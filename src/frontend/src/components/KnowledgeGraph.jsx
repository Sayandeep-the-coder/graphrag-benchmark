import React, { useState } from 'react';
import { motion } from 'framer-motion';

const KnowledgeGraph = ({ nodes = [], links = [] }) => {
  const [hoveredNode, setHoveredNode] = useState(null);

  // Default data if none provided
  const displayNodes = nodes.length > 0 ? nodes : [
    { id: 'Patient', x: 200, y: 200, type: 'Entity' },
    { id: 'Disease', x: 400, y: 150, type: 'Concept' },
    { id: 'Treatment', x: 350, y: 350, type: 'Action' },
    { id: 'Symptom', x: 100, y: 300, type: 'Observation' },
    { id: 'Medication', x: 500, y: 300, type: 'Entity' },
    { id: 'Lab_Result', x: 150, y: 100, type: 'Data' },
  ];

  const displayLinks = links.length > 0 ? links : [
    { source: 'Patient', target: 'Symptom' },
    { source: 'Patient', target: 'Lab_Result' },
    { source: 'Disease', target: 'Symptom' },
    { source: 'Disease', target: 'Treatment' },
    { source: 'Treatment', target: 'Medication' },
    { source: 'Patient', target: 'Medication' },
  ];

  const getAccentColor = (type) => {
    switch (type) {
      case 'Entity': return '#00FFA3'; // Neon Green
      case 'Concept': return '#00D1FF'; // Info Blue
      case 'Action': return '#FFB800'; // Warning Yellow
      default: return '#FF4D4D'; // Coral Red
    }
  };

  return (
    <div className="w-full h-full relative overflow-hidden bg-black/40 rounded-xl border border-white/5 bg-grid">
      <svg className="w-full h-full" viewBox="0 0 600 500">
        <defs>
          <filter id="glow">
            <feGaussianBlur stdDeviation="2.5" result="coloredBlur"/>
            <feMerge>
              <feMergeNode in="coloredBlur"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>
          </filter>
        </defs>

        {/* Links */}
        {displayLinks.map((link, i) => {
          const s = displayNodes.find(n => n.id === link.source);
          const t = displayNodes.find(n => n.id === link.target);
          if (!s || !t) return null;
          
          return (
            <line
              key={i}
              x1={s.x} y1={s.y} x2={t.x} y2={t.y}
              stroke="white"
              strokeOpacity="0.1"
              strokeWidth="1"
            />
          );
        })}

        {/* Nodes */}
        {displayNodes.map((node) => (
          <motion.g
            key={node.id}
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            whileHover={{ scale: 1.2 }}
            onMouseEnter={() => setHoveredNode(node)}
            onMouseLeave={() => setHoveredNode(null)}
            className="cursor-pointer"
          >
            <circle
              cx={node.x}
              cy={node.y}
              r="6"
              fill={getAccentColor(node.type)}
              filter="url(#glow)"
              className="transition-all duration-300"
            />
            <text
              x={node.x + 12}
              y={node.y + 4}
              fill="white"
              fillOpacity="0.5"
              className="text-[10px] font-mono pointer-events-none uppercase tracking-widest"
            >
              {node.id}
            </text>
          </motion.g>
        ))}
      </svg>

      {/* Node Info Overlay */}
      {hoveredNode && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="absolute bottom-6 left-6 p-4 glass rounded-lg border-accent-neon/20 min-w-[200px]"
        >
          <p className="text-[8px] text-accent-neon font-black uppercase tracking-[0.2em] mb-1">Node_Analysis</p>
          <p className="text-sm font-bold text-white mb-2">{hoveredNode.id}</p>
          <div className="flex items-center gap-2">
            <span className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">Type:</span>
            <span className="badge-premium" style={{ color: getAccentColor(hoveredNode.type), borderColor: `${getAccentColor(hoveredNode.type)}20` }}>
              {hoveredNode.type}
            </span>
          </div>
        </motion.div>
      )}

      {/* Legend */}
      <div className="absolute top-6 right-6 flex flex-col gap-2">
        {['Entity', 'Concept', 'Action', 'Observation'].map(type => (
          <div key={type} className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full" style={{ backgroundColor: getAccentColor(type) }}></div>
            <span className="text-[9px] text-gray-500 font-bold uppercase tracking-widest">{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KnowledgeGraph;
