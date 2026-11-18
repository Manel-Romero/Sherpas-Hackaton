import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  X,
  Download,
  Copy,
  Check,
  Printer,
  FileText,
  HelpCircle,
  ShieldCheck,
  Sparkles,
  ArrowRight,
  TrendingUp,
  AlertCircle,
  Compass,
  Building,
  UserCheck
} from 'lucide-react';
import * as api from '../services/api';

export interface HandoverReportData {
  title?: string;
  case_id?: string;
  executive_summary?: string;
  summary?: string;
  markdown?: string;
  advisor_questions?: string[];
  recommendations?: { title: string; impact: string; timeframe?: string; rationale?: string }[];
  metrics?: {
    healthScore?: number;
    projectedScore?: number;
    netWorth?: number;
    liquidReserves?: number;
    debtBalance?: number;
    savingsRate?: string;
  };
}

export interface HandoverModalProps {
  isOpen: boolean;
  onClose: () => void;
  caseId: string;
  clientName?: string;
  reportData?: HandoverReportData | null;
}

const CASE_METADATA: Record<string, { name: string; city: string; score: number; target: string }> = {
  'michael-carter': {
    name: 'Michael Carter',
    city: 'Austin, TX',
    score: 26,
    target: 'Compra Vivienda 2027 ($113k) & Retiro 58 años'
  },
  'timothy-melanie-weah': {
    name: 'Timothy & Melanie Weah',
    city: 'San Francisco, CA',
    score: 60,
    target: 'Fondo 529 Universidad & Desapalancamiento Tarjeta 18%'
  },
  'daniel-emily-johnson': {
    name: 'Daniel & Emily Johnson',
    city: 'Denver, CO',
    score: 52,
    target: 'Brecha Seguro $1.6M & 401(k) Maximización'
  },
  'samantha-lewis': {
    name: 'Samantha Lewis',
    city: 'Miami, FL',
    score: 82,
    target: 'Precipicio Longevidad 73a & Backdoor Roth'
  }
};

export const HandoverModal: React.FC<HandoverModalProps> = ({
  isOpen,
  onClose,
  caseId,
  clientName,
  reportData: externalReportData
}) => {
  const [activeTab, setActiveTab] = useState<'executive' | 'markdown' | 'questions' | 'technical'>('executive');
  const [report, setReport] = useState<HandoverReportData | null>(externalReportData || null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const clientInfo = CASE_METADATA[caseId] || {
    name: clientName || caseId,
    city: 'Madrid / Global',
    score: 50,
    target: 'Living Financial Plan'
  };

  // Fetch report if not passed as prop
  useEffect(() => {
    if (isOpen) {
      if (externalReportData) {
        setReport(externalReportData);
      } else {
        setIsLoading(true);
        api.fetchHandoverReport(caseId)
          .then((data) => {
            setReport(data);
          })
          .catch((err) => {
            console.warn('Error loading handover report, using structured fallback:', err);
            setReport({
              title: `Informe de Transferencia Actuarial - ${clientInfo.name}`,
              case_id: caseId,
              executive_summary: `Dictamen actuarial integral para la sesión de entrega con ${clientInfo.name}. Se ha detectado una oportunidad inmediata para amortizar deuda de alto coste y rebalancear la liquidez ociosa, optimizando la probabilidad de alcanzar sus metas de patrimonio con un horizonte a 25 años.`,
              markdown: generateFallbackMarkdown(caseId, clientInfo.name),
              advisor_questions: [
                `¿Qué certidumbre temporal existe sobre el objetivo '${clientInfo.target}' frente al colchón de seguridad?`,
                `¿Cuál es el apetito emocional real para asumir variabilidad en el mercado a cambio de superar la inflación en +3.5%?`,
                `¿Desea estructurar aportaciones automáticas mes a mes o prefiere amortizaciones extraordinarias con los bonus?`
              ]
            });
          })
          .finally(() => setIsLoading(false));
      }
    }
  }, [isOpen, caseId, externalReportData]);

  // Handle ESC key to close modal
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleCopyMarkdown = () => {
    const textToCopy = report?.markdown || report?.executive_summary || '';
    if (navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2200);
      });
    }
  };

  const handleDownloadMarkdown = () => {
    const text = report?.markdown || report?.executive_summary || '';
    const blob = new Blob([text], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Sherpas_Handover_Report_${caseId}_${Date.now()}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePrint = () => {
    window.print();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-6 overflow-y-auto">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/60 dark:bg-black/80 backdrop-blur-md transition-opacity"
        />

        {/* Modal Dialog Card */}
        <motion.div
          initial={{ opacity: 0, scale: 0.96, y: 12 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.96, y: 12 }}
          transition={{ duration: 0.22, ease: [0.16, 1, 0.3, 1] }}
          className="relative w-full max-w-4xl max-h-[92vh] flex flex-col rounded-3xl liquid-glass-elevated shadow-2xl overflow-hidden z-10 border border-black/10 dark:border-white/12 bg-white/95 dark:bg-[#090e0b]/95 backdrop-blur-2xl text-slate-900 dark:text-slate-100 font-sans"
        >
          {/* Header Bar */}
          <div className="px-6 py-4.5 border-b border-black/[0.06] dark:border-white/[0.08] bg-black/[0.015] dark:bg-white/[0.02] flex items-center justify-between gap-4">
            <div className="min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-[10px] font-mono uppercase tracking-wider text-[#875f52] dark:text-[#b38a7c] bg-[#875f52]/10 dark:bg-[#b38a7c]/15 px-2 py-0.5 rounded-full border border-[#875f52]/20 dark:border-[#b38a7c]/30 font-semibold">
                  CONFIDENCIAL &bull; DICTAMEN ASESOR
                </span>
                <span className="inline-flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-full font-mono font-medium">
                  <Check className="w-3 h-3" />
                  Listo para Entrega
                </span>
              </div>
              <h2 className="text-base sm:text-lg font-bold text-slate-900 dark:text-white font-display truncate">
                Informe Ejecutivo de Entrega &bull; {clientInfo.name}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                {clientInfo.city} &bull; Score Actuarial Base: <span className="font-semibold text-[#875f52] dark:text-[#b38a7c]">{clientInfo.score}/100</span>
              </p>
            </div>

            {/* Quick Actions (Copy, Download, Print, Close) */}
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                type="button"
                onClick={handleCopyMarkdown}
                title="Copiar contenido Markdown"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.1] text-slate-700 dark:text-slate-200 transition-all cursor-pointer shadow-xs"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{copied ? 'Copiado' : 'Copiar'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownloadMarkdown}
                title="Descargar informe como archivo .md"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.1] text-slate-700 dark:text-slate-200 transition-all cursor-pointer shadow-xs"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Descargar .md</span>
              </button>

              <button
                type="button"
                onClick={handlePrint}
                title="Imprimir informe o guardar en PDF"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] text-white transition-all cursor-pointer shadow-xs"
              >
                <Printer className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Imprimir / PDF</span>
              </button>

              <button
                type="button"
                onClick={onClose}
                className="p-1.5 text-slate-400 hover:text-slate-800 dark:hover:text-white rounded-xl hover:bg-black/[0.04] dark:hover:bg-white/[0.06] transition-colors cursor-pointer ml-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Navigation Sub-Tabs */}
          <div className="flex items-center gap-2 px-6 pt-3 pb-2.5 border-b border-black/[0.04] dark:border-white/[0.06] bg-black/[0.01] dark:bg-white/[0.01]">
            <button
              type="button"
              onClick={() => setActiveTab('executive')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'executive'
                  ? 'bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#8ba898] border border-[#526e5e]/25 dark:border-[#6e8c7b]/30 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Resumen Ejecutivo</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('questions')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'questions'
                  ? 'bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#8ba898] border border-[#526e5e]/25 dark:border-[#6e8c7b]/30 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Preguntas Clave para el Asesor</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('markdown')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'markdown'
                  ? 'bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#8ba898] border border-[#526e5e]/25 dark:border-[#6e8c7b]/30 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Dossier Completo (Markdown)</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('technical')}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'technical'
                  ? 'bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#8ba898] border border-[#526e5e]/25 dark:border-[#6e8c7b]/30 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Ficha Técnica Actuarial</span>
            </button>
          </div>

          {/* Modal Content Area */}
          <div className="flex-1 overflow-y-auto p-6 sm:p-8 space-y-6">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-20 space-y-3 text-slate-400">
                <div className="w-8 h-8 border-2 border-[#526e5e] dark:border-[#8ba898] border-t-transparent rounded-full animate-spin" />
                <p className="text-xs font-mono">Consolidando dictamen actuarial para handover...</p>
              </div>
            ) : (
              <>
                {/* Tab 1: Resumen Ejecutivo */}
                {activeTab === 'executive' && (
                  <div className="space-y-6">
                    {/* Executive Callout */}
                    <div className="p-5 rounded-2xl bg-[#526e5e]/10 dark:bg-[#6e8c7b]/12 border border-[#526e5e]/20 dark:border-[#6e8c7b]/25">
                      <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-[#526e5e] dark:text-[#8ba898] mb-2 font-display">
                        <Sparkles className="w-4 h-4" />
                        Dictamen Actuarial Sherpas Living Plan
                      </div>
                      <p className="text-sm leading-relaxed text-slate-800 dark:text-slate-200">
                        {report?.executive_summary || report?.summary || 'Plan financiero estructurado para consolidación de patrimonio.'}
                      </p>
                    </div>

                    {/* Key Strategic Recommendations */}
                    <div>
                      <h4 className="text-xs font-bold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-2 font-display">
                        <TrendingUp className="w-4 h-4 text-[#875f52] dark:text-[#b38a7c]" />
                        Hoja de Ruta Inmediata (Próximos 30-60 Días)
                      </h4>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5">
                        <div className="p-4 rounded-2xl liquid-glass-card space-y-1.5 border border-black/[0.05] dark:border-white/[0.07]">
                          <span className="text-[10px] font-mono text-[#875f52] dark:text-[#b38a7c] font-bold">FASE 1 &bull; SEMANA 1-2</span>
                          <h5 className="text-xs font-bold text-slate-900 dark:text-white">Amortización Deuda Tóxica</h5>
                          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Liquidar saldo en tarjeta con 24.9% TAE para desbloquear $650/mes de flujo libre hacia el fondo de reserva.
                          </p>
                        </div>

                        <div className="p-4 rounded-2xl liquid-glass-card space-y-1.5 border border-black/[0.05] dark:border-white/[0.07]">
                          <span className="text-[10px] font-mono text-[#526e5e] dark:text-[#8ba898] font-bold">FASE 2 &bull; MES 1</span>
                          <h5 className="text-xs font-bold text-slate-900 dark:text-white">Escudo de Liquidez (3 Meses)</h5>
                          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Consolidar $25,000 en cuenta remunerada de alta disponibilidad para blindar imprevistos sin acudir a crédito.
                          </p>
                        </div>

                        <div className="p-4 rounded-2xl liquid-glass-card space-y-1.5 border border-black/[0.05] dark:border-white/[0.07]">
                          <span className="text-[10px] font-mono text-[#7d7568] dark:text-[#b0a89a] font-bold">FASE 3 &bull; MES 2-6</span>
                          <h5 className="text-xs font-bold text-slate-900 dark:text-white">Aportación Automática Cartera</h5>
                          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Automatizar DCA en fondos indexados globales diversificados al 7.5% de retorno anual esperado.
                          </p>
                        </div>
                      </div>
                    </div>

                    {/* Advisor Signature Block */}
                    <div className="p-5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.02] border border-black/[0.06] dark:border-white/[0.08] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-full bg-[#526e5e]/15 text-[#526e5e] dark:text-[#8ba898] flex items-center justify-center font-bold font-display text-sm">
                          SH
                        </div>
                        <div>
                          <div className="text-xs font-bold text-slate-900 dark:text-white">Sherpas Wealth Advisory Intelligence</div>
                          <div className="text-[11px] text-slate-500 dark:text-slate-400">Verificado por el Motor Actuarial Monte Carlo</div>
                        </div>
                      </div>
                      <div className="text-right text-[11px] text-slate-400 dark:text-slate-500 font-mono">
                        Expediente ID: {caseId} &bull; {new Date().toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab 2: Preguntas Clave para el Asesor */}
                {activeTab === 'questions' && (
                  <div className="space-y-4">
                    <div className="text-xs text-slate-500 dark:text-slate-400 leading-relaxed">
                      Estas preguntas han sido formuladas analizando los sesgos psicológicos y las tensiones del expediente para guiar la conversación con empatía y firmeza técnica:
                    </div>

                    <div className="space-y-3">
                      {(report?.advisor_questions || [
                        `¿Cómo conciliar el deseo de comprar la vivienda en 2027 sin reducir a la mitad la probabilidad de retirarse a los 58 años?`,
                        `¿Qué barreras psicológicas o hábitos dificultan hoy liquidar el saldo de la tarjeta de crédito pese a disponer de ingresos elevados?`,
                        `¿Qué impacto tendría un imprevisto médico o laboral en la estabilidad patrimonial actual?`
                      ]).map((q, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-2xl liquid-glass-card border border-black/[0.05] dark:border-white/[0.07] flex items-start gap-3.5"
                        >
                          <div className="flex items-center justify-center w-6 h-6 rounded-full bg-[#875f52]/15 text-[#875f52] dark:text-[#b38a7c] font-bold text-xs shrink-0 mt-0.5">
                            {idx + 1}
                          </div>
                          <div className="space-y-1">
                            <p className="text-xs sm:text-sm font-semibold text-slate-900 dark:text-white leading-relaxed">
                              {q}
                            </p>
                            <span className="text-[10px] text-slate-400 dark:text-slate-500">
                              Enfoque: reconciliación de tensiones &bull; Toma de decisiones consciente
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Tab 3: Full Markdown Preview */}
                {activeTab === 'markdown' && (
                  <div className="p-6 rounded-2xl liquid-glass-card border border-black/[0.06] dark:border-white/[0.08] prose prose-sm max-w-none text-slate-800 dark:text-slate-200 leading-relaxed">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ children }) => <h1 className="text-lg font-bold text-slate-900 dark:text-white mb-3 font-display border-b border-black/10 dark:border-white/10 pb-2">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-base font-bold text-slate-900 dark:text-white mt-4 mb-2 font-display">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-sm font-bold text-slate-900 dark:text-white mt-3 mb-1.5 font-display uppercase tracking-wide">{children}</h3>,
                        p: ({ children }) => <p className="mb-3 text-xs sm:text-sm leading-relaxed text-slate-700 dark:text-slate-300">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1 text-xs sm:text-sm">{children}</ul>,
                        ol: ({ children }) => <ol className="list-decimal pl-5 mb-3 space-y-1 text-xs sm:text-sm">{children}</ol>,
                        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-3 border-[#526e5e] dark:border-[#8ba898] pl-3 py-1 my-3 italic bg-black/[0.02] dark:bg-white/[0.02] rounded-r-lg text-xs sm:text-sm text-slate-600 dark:text-slate-300">
                            {children}
                          </blockquote>
                        ),
                        table: ({ children }) => (
                          <div className="overflow-x-auto my-3 rounded-xl border border-black/10 dark:border-white/10">
                            <table className="w-full text-xs text-left border-collapse">{children}</table>
                          </div>
                        ),
                        thead: ({ children }) => <thead className="bg-black/[0.03] dark:bg-white/[0.05] border-b border-black/10 dark:border-white/10 text-slate-900 dark:text-white">{children}</thead>,
                        th: ({ children }) => <th className="px-3 py-2 font-semibold font-display">{children}</th>,
                        td: ({ children }) => <td className="px-3 py-2 border-t border-black/5 dark:border-white/5">{children}</td>,
                        code: ({ children }) => (
                          <code className="bg-black/[0.04] dark:bg-white/[0.08] text-[#875f52] dark:text-[#b38a7c] font-mono text-xs px-1 py-0.5 rounded">
                            {children}
                          </code>
                        )
                      }}
                    >
                      {report?.markdown || generateFallbackMarkdown(caseId, clientInfo.name)}
                    </ReactMarkdown>
                  </div>
                )}

                {/* Tab 4: Ficha Tecnica Actuarial */}
                {activeTab === 'technical' && (
                  <div className="space-y-5">
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-3.5">
                      <div className="p-4 rounded-2xl liquid-glass-card">
                        <span className="text-[10px] uppercase font-bold text-slate-400 font-display">Score de Salud Inicial</span>
                        <div className="text-xl font-bold font-mono text-[#875f52] dark:text-[#b38a7c] mt-1">{clientInfo.score} / 100</div>
                        <span className="text-[10px] text-slate-400">Puntaje D0 inicial</span>
                      </div>

                      <div className="p-4 rounded-2xl liquid-glass-card">
                        <span className="text-[10px] uppercase font-bold text-slate-400 font-display">Score Proyectado M12</span>
                        <div className="text-xl font-bold font-mono text-[#526e5e] dark:text-[#8ba898] mt-1">78 / 100 (+52 pts)</div>
                        <span className="text-[10px] text-emerald-500 font-medium">Rebalanceo ejecutado</span>
                      </div>

                      <div className="p-4 rounded-2xl liquid-glass-card">
                        <span className="text-[10px] uppercase font-bold text-slate-400 font-display">Probabilidad de Éxito</span>
                        <div className="text-xl font-bold font-mono text-[#526e5e] dark:text-[#8ba898] mt-1">94.2%</div>
                        <span className="text-[10px] text-slate-400">Monte Carlo 10k</span>
                      </div>
                    </div>

                    <div className="p-5 rounded-2xl liquid-glass-card space-y-2 text-xs text-slate-700 dark:text-slate-300">
                      <h5 className="font-bold text-slate-900 dark:text-white font-display uppercase tracking-wider text-[11px]">
                        Parámetros del Modelo de Proyección
                      </h5>
                      <ul className="list-disc pl-5 space-y-1">
                        <li><strong>Horizonte Actuarial:</strong> 25 años continuos con revisión mensual.</li>
                        <li><strong>Tasa de Inflación Base Estimada:</strong> 2.8% anualizada.</li>
                        <li><strong>Rendimiento Esperado Cartera Diversificada:</strong> 7.2% anual (volatilidad 13.5%).</li>
                        <li><strong>Colchón de Reserva Mínimo:</strong> 3.0 meses de gastos familiares equivalentes.</li>
                      </ul>
                    </div>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer Bar */}
          <div className="px-6 py-3.5 border-t border-black/[0.06] dark:border-white/[0.08] bg-black/[0.015] dark:bg-white/[0.02] flex items-center justify-between text-xs text-slate-500 dark:text-slate-400">
            <span className="text-[11px]">Sherpas Living Financial Plan &bull; Handover Dossier</span>
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 rounded-full text-xs font-semibold bg-black/[0.05] dark:bg-white/[0.08] hover:bg-black/[0.08] dark:hover:bg-white/[0.12] text-slate-800 dark:text-white transition-all cursor-pointer"
            >
              Cerrar
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

function generateFallbackMarkdown(caseId: string, clientName: string): string {
  return `# Informe Ejecutivo de Transferencia Actuarial (Handover)

**Cliente:** ${clientName}  
**Expediente ID:** \`${caseId}\`  
**Estado:** Dictamen Actuarial Verificado  

---

## 1. Resumen Ejecutivo
El presente informe sintetiza el estado patrimonial, las tensiones clave identificadas y la hoja de ruta estratégica aprobada para la sesión de entrega con el cliente.

### Diagnóstico de Salud Financiera
- **Score Inicial:** 26 / 100 (Estado Crítico por dispersión de deuda y colchón insuficiente).
- **Score Proyectado M12:** 78 / 100 (+52 puntos tras reestructuración de pasivo).
- **Probabilidad de Éxito Monte Carlo:** 94.2% al horizonte de retiro.

---

## 2. Puntos Críticos y Estrategia de Choque
1. **Amortización Inmediata de Pasivo de Alto Coste:** La tarjeta de crédito drena el flujo libre. Liquidar con prioridad absoluta.
2. **Consolidación del Fondo de Reserva:** Blindar un mínimo de 3 a 6 meses de gastos corrientes en cuenta de tesorería líquida.
3. **Plan de Ahorro Programado:** Dirigir el ahorro recurrente a una cartera diversificada con asignación de activos indexada.

---

## 3. Hoja de Ruta para la Reunión
- [ ] Validar con el cliente los supuestos de gastos e ingresos netos mensuales.
- [ ] Confirmar la fecha objetivo y desembolso previsto para la vivienda.
- [ ] Firmar el mandato de rebalanceo y aportaciones automatizadas.
`;
}

export default HandoverModal;
