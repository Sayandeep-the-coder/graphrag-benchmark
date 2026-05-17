import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, ChevronDown, ListPlus, X, Database } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function EvaluationSidepanel({ onSelect, isOpen, onClose }) {
  const [questions, setQuestions] = useState([]);
  const [grouped, setGrouped] = useState({});
  const [loading, setLoading] = useState(true);
  const [expandedCategories, setExpandedCategories] = useState({});

  useEffect(() => {
    if (isOpen && questions.length === 0) {
      fetch(`${API_URL}/benchmark/questions`)
        .then(res => res.json())
        .then(data => {
          setQuestions(data);
          const groups = data.reduce((acc, q) => {
            const cat = q.category || "GENERAL";
            if (!acc[cat]) acc[cat] = [];
            acc[cat].push(q);
            return acc;
          }, {});
          setGrouped(groups);
          // Expand first category by default
          if (Object.keys(groups).length > 0) {
            setExpandedCategories({ [Object.keys(groups)[0]]: true });
          }
          setLoading(false);
        })
        .catch(err => {
          console.error("Failed to load benchmark questions:", err);
          setLoading(false);
        });
    }
  }, [isOpen, questions.length]);

  const toggleCategory = (cat) => {
    setExpandedCategories(prev => ({
      ...prev,
      [cat]: !prev[cat]
    }));
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />
          
          {/* Sidepanel */}
          <motion.div
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ type: "spring", bounce: 0, duration: 0.4 }}
            className="fixed right-0 top-0 bottom-0 w-[400px] bg-[#111111] border-l border-white/10 z-50 flex flex-col shadow-2xl"
          >
            <div className="p-6 border-b border-white/5 flex items-center justify-between bg-black/20">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-accent-neon/10 flex items-center justify-center border border-accent-neon/20">
                  <ListPlus className="w-4 h-4 text-accent-neon" />
                </div>
                <div>
                  <h2 className="text-sm font-black text-white uppercase tracking-wider">Evaluation Suite</h2>
                  <p className="text-[10px] text-gray-500 font-bold uppercase tracking-widest mt-1">
                    {questions.length} Questions Loaded
                  </p>
                </div>
              </div>
              <button 
                onClick={onClose}
                className="w-8 h-8 flex items-center justify-center rounded-full bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
              >
                <X size={16} />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
              {loading ? (
                <div className="text-center text-[10px] text-gray-500 font-mono py-10 uppercase tracking-widest animate-pulse">
                  Loading Questions...
                </div>
              ) : (
                Object.entries(grouped).map(([category, qList]) => (
                  <div key={category} className="bg-black/40 rounded-xl border border-white/5 overflow-hidden">
                    <button
                      onClick={() => toggleCategory(category)}
                      className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {expandedCategories[category] ? (
                          <ChevronDown size={14} className="text-accent-neon" />
                        ) : (
                          <ChevronRight size={14} className="text-gray-500" />
                        )}
                        <span className="text-[11px] font-black text-white uppercase tracking-widest">{category}</span>
                      </div>
                      <span className="text-[10px] font-mono text-gray-500">{qList.length}</span>
                    </button>
                    
                    <AnimatePresence>
                      {expandedCategories[category] && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          exit={{ height: 0, opacity: 0 }}
                          className="overflow-hidden border-t border-white/5"
                        >
                          <div className="p-2 space-y-1 bg-black/20">
                            {qList.map((item, idx) => (
                              <button
                                key={idx}
                                onClick={() => {
                                  onSelect(item.question, item.correct_answer);
                                  onClose();
                                }}
                                className="w-full text-left p-3 rounded-lg hover:bg-accent-neon/10 border border-transparent hover:border-accent-neon/20 transition-all group"
                              >
                                <p className="text-xs text-gray-300 font-medium group-hover:text-white leading-relaxed line-clamp-2">
                                  {item.question}
                                </p>
                                {item.correct_answer && (
                                  <div className="mt-2 flex items-center gap-1.5 text-[9px] font-mono text-accent-info uppercase tracking-wider">
                                    <Database size={10} />
                                    <span>Has Ground Truth</span>
                                  </div>
                                )}
                              </button>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
