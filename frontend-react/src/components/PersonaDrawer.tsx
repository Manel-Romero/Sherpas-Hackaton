import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { 
  X, 
  AlertOctagon, 
  Target, 
  Compass, 
  ShieldAlert,
  HelpCircle,
  FileText,
  Sparkles
} from 'lucide-react';
import { PersonaInsights } from '../types';
import * as api from '../services/api';

interface PersonaDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  insights: PersonaInsights | null;
  isLoading: boolean;
}

export const PersonaDrawer: React.FC<PersonaDrawerProps> = ({
  isOpen,
  onClose,
  insights,
  isLoading
}) => {
  const [activeDrawerTab, setActiveDrawerTab] = useState<'dossier' | 'report'>('dossier');
  const [report, setReport] = useState<any>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);

  useEffect(() => {
    if (isOpen && activeDrawerTab === 'report' && (!report || report.case_id !== insights?.case_id)) {
      if (insights?.case_id) {
        setIsLoadingReport(true);
        api.fetchHandoverReport(insights.case_id)
          .then((data) => setReport(data))
          .catch((e) => console.error("Error cargando informe:", e))
          .finally(() => setIsLoadingReport(false));
      }
    }
  }, [isOpen, activeDrawerTab, insights?.case_id]);

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
            className="fixed inset-0 z-50 bg-black/45 dark:bg-black/75 backdrop-blur-md"
          />

          {/* Slide-over memorandum */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 320 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-lg liquid-glass-elevated shadow-2xl flex flex-col overflow-hidden"
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-black/[0.04] dark:border-white/[0.06] bg-black/[0.015] dark:bg-white/[0.02]">
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-mono uppercase tracking-wider text-[#875f52] dark:text-[#b38a7c] bg-[#875f52]/10 dark:bg-[#b38a7c]/15 px-2 py-0.5 rounded-full border border-[#875f52]/20 dark:border-[#b38a7c]/30">
                    Confidencial &bull; Uso Asesor
                  </span>
                </div>
                <h3 className="text-sm font-bold text-slate-900 dark:text-[#f8fafc] mt-1 font-display">
                  {activeDrawerTab === 'dossier' ? 'Dossier Psico-Financiero' : 'Informe Ejecutivo de Entrega'}
                </h3>
                <p className="text-xs text-slate-500 dark:text-slate-400">{insights?.title || 'Expediente del Cliente'}</p>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 text-slate-400 hover:text-slate-800 dark:text-[#94a3b8] dark:hover:text-[#f8fafc] rounded-lg hover:bg-black/[0.04] dark:hover:bg-white/[0.06] transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Sub-tab switcher */}
            <div className="flex items-center gap-2 px-6 pt-3 pb-2 bg-black/[0.015] dark:bg-white/[0.02] border-b border-black/[0.04] dark:border-white/[0.06]">
              <button
                onClick={() => setActiveDrawerTab('dossier')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                  activeDrawerTab === 'dossier'
                    ? 'bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#f8fafc] border border-[#526e5e]/25 dark:border-[#6e8c7b]/30 shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-[#f8fafc]'
                }`}
              >
                <Target className="w-3.5 h-3.5 text-[#526e5e] dark:text-[#8ba898]" />
                <span>Perfil y Arquetipos</span>
              </button>
              <button
                onClick={() => setActiveDrawerTab('report')}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                  activeDrawerTab === 'report'
                    ? 'bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#f8fafc] border border-[#526e5e]/25 dark:border-[#6e8c7b]/30 shadow-sm'
                    : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-[#f8fafc]'
                }`}
              >
                <FileText className="w-3.5 h-3.5 text-[#526e5e] dark:text-[#8ba898]" />
                <span>Dictamen Ejecutivo Handover</span>
              </button>
            </div>

            {/* Body */}
            <div className="flex-1 overflow-y-auto p-6 space-y-5">
              {activeDrawerTab === 'dossier' ? (
                isLoading || !insights ? (
                  <div className="flex flex-col items-center justify-center h-64 text-slate-400 dark:text-slate-500 space-y-3">
                    <div className="w-6 h-6 border-2 border-[#526e5e] dark:border-[#8ba898] border-t-transparent rounded-full animate-spin" />
                    <p className="text-xs font-mono">Indexando persona.md y analítica...</p>
                  </div>
                ) : (
                  <>
                    {/* Wealth Tier & Life Stage */}
                    <div className="p-4 rounded-2xl liquid-glass-card">
                      <div className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 tracking-wider mb-1 flex items-center gap-1.5 font-display">
                        <Target className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
                        Estrato Patrimonial (Wealth Tier D0)
                      </div>
                      <div className="text-sm font-semibold text-slate-900 dark:text-[#f8fafc]">
                        {insights.wealth_tier}
                      </div>
                    </div>

                    {/* Risk Profile & Decision Style Grid */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-3.5 rounded-2xl liquid-glass-card">
                        <div className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 tracking-wider mb-1 font-display">
                          Orientación al Riesgo
                        </div>
                        <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                          {insights.risk_profile}
                        </div>
                      </div>
                      <div className="p-3.5 rounded-2xl liquid-glass-card">
                        <div className="text-[10px] uppercase font-semibold text-slate-500 dark:text-slate-400 tracking-wider mb-1 font-display">
                          Estilo Decisorio
                        </div>
                        <div className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed font-medium">
                          {insights.decision_style}
                        </div>
                      </div>
                    </div>

                    {/* Primary Tension / Psychological Dilemma */}
                    <div className="p-4 rounded-2xl bg-[#875f52]/10 border border-[#875f52]/20">
                      <div className="text-[10px] uppercase font-semibold text-[#875f52] dark:text-[#b38a7c] tracking-wider mb-1.5 flex items-center gap-1.5 font-display">
                        <AlertOctagon className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
                        Tensión Financiera Central
                      </div>
                      <p className="text-xs text-slate-800 dark:text-[#c4a093] leading-relaxed font-normal">
                        {insights.primary_tension}
                      </p>
                    </div>

                    {/* Motivational Anchor */}
                    <div className="p-4 rounded-2xl liquid-glass-card">
                      <div className="text-[10px] uppercase font-semibold text-[#526e5e] dark:text-[#8ba898] tracking-wider mb-1.5 flex items-center gap-1.5 font-display">
                        <Compass className="w-3.5 h-3.5 text-[#526e5e] dark:text-[#8ba898]" />
                        Ancla Motivacional
                      </div>
                      <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                        {insights.emotional_archetype}
                      </p>
                    </div>

                    {/* Transition Alerts */}
                    {insights.key_alerts && insights.key_alerts.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-[10px] uppercase font-semibold text-[#875f52] dark:text-[#b38a7c] tracking-wider flex items-center gap-1.5 font-display">
                          <ShieldAlert className="w-3.5 h-3.5" />
                          Puntos Críticos Detectados por Sherpas
                        </div>
                        <div className="space-y-2">
                          {insights.key_alerts.map((alert, i) => (
                            <div 
                              key={i} 
                              className="p-3 rounded-xl bg-[#875f52]/10 border border-[#875f52]/20 text-xs text-slate-800 dark:text-[#c4a093] leading-relaxed flex items-start gap-2"
                            >
                              <span className="text-[#875f52] dark:text-[#b38a7c] font-mono shrink-0">&bull;</span>
                              <span>{alert}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="pt-2 border-t border-black/10 dark:border-white/10 text-[11px] text-slate-400 dark:text-slate-500 flex items-center justify-between">
                      <span>Sherpas Living Plan &bull; Asesoría Continua</span>
                      <span className="font-mono">{insights.case_id}</span>
                    </div>
                  </>
                )
              ) : (
                /* Report Tab */
                isLoadingReport ? (
                  <div className="flex flex-col items-center justify-center h-64 text-slate-400 dark:text-slate-500 space-y-3">
                    <div className="w-6 h-6 border-2 border-[#526e5e] dark:border-[#8ba898] border-t-transparent rounded-full animate-spin" />
                    <p className="text-xs font-mono">Generando informe ejecutivo actuarial...</p>
                  </div>
                ) : report ? (
                  <div className="space-y-5">
                    {/* Key Questions for Advisor */}
                    {report.advisor_questions && Array.isArray(report.advisor_questions) && report.advisor_questions.length > 0 && (
                      <div className="space-y-2">
                        <div className="text-[10px] uppercase font-semibold text-[#7d7568] dark:text-[#b0a89a] tracking-wider flex items-center gap-1.5 font-display">
                          <HelpCircle className="w-3.5 h-3.5" />
                          Preguntas Clave para Formular al Cliente en Reunión
                        </div>
                        <div className="space-y-2">
                          {report.advisor_questions.map((q: string, i: number) => (
                            <div key={i} className="p-3 rounded-xl bg-[#7d7568]/10 border border-[#7d7568]/20 text-xs text-slate-800 dark:text-[#b0a89a] leading-relaxed flex items-start gap-2">
                              <span className="text-[#7d7568] dark:text-[#b0a89a] font-bold shrink-0">{i + 1}.</span>
                              <span>{q}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Markdown Report Content */}
                    {report.markdown ? (
                      <div className="p-5 rounded-2xl liquid-glass-card shadow-sm prose prose-sm max-w-none text-slate-800 dark:text-slate-300 leading-relaxed">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {report.markdown}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      /* Fallback to summary */
                      <div className="p-4 rounded-2xl liquid-glass-card">
                        <div className="text-[10px] uppercase font-semibold text-[#526e5e] dark:text-[#8ba898] tracking-wider mb-1 flex items-center gap-1.5 font-display">
                          <Sparkles className="w-3.5 h-3.5" />
                          Resumen Ejecutivo para la Reunión
                        </div>
                        <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                          {report.executive_summary || report.summary || 'Informe generado con éxito para revisión del plan.'}
                        </p>
                      </div>
                    )}

                    <div className="pt-2 border-t border-black/10 dark:border-white/10 text-[11px] text-slate-400 dark:text-slate-500 flex items-center justify-between">
                      <span>Sherpas Living Plan &bull; Handover Memo</span>
                      <span className="font-mono">{insights?.case_id}</span>
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-48 text-slate-400 dark:text-slate-500 text-xs text-center">
                    No se encontró informe para este caso.
                  </div>
                )
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default PersonaDrawer;
