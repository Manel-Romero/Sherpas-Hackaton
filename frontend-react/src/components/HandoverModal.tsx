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
  Sparkles,
  TrendingUp,
  Target
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
  const [activeTab, setActiveTab] = useState<'summary' | 'questions' | 'document'>('summary');
  const [report, setReport] = useState<HandoverReportData | null>(externalReportData || null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copied, setCopied] = useState<boolean>(false);

  const clientInfo = CASE_METADATA[caseId] || {
    name: clientName || caseId,
    city: 'Cliente Sherpas',
    score: 50,
    target: 'Plan Financiero'
  };

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
          .catch(() => {
            setReport({
              title: `Informe Ejecutivo - ${clientInfo.name}`,
              case_id: caseId,
              executive_summary: `Plan patrimonial estructurado para ${clientInfo.name}. Se identifican oportunidades directas de reestructuración de liquidez y reducción de deuda, protegiendo las metas clave a largo plazo.`,
              markdown: generateFallbackMarkdown(caseId, clientInfo.name),
              advisor_questions: [
                `¿Qué flexibilidad temporal existe respecto al objetivo principal ('${clientInfo.target}') ante variaciones de mercado?`,
                `¿Cuál es el umbral de tolerancia a la volatilidad a cambio de una rentabilidad real neta superior a la inflación?`,
                `¿Se prefieren aportaciones periódicas fijas o amortizaciones basadas en incentivos extraordinarios?`
              ]
            });
          })
          .finally(() => setIsLoading(false));
      }
    }
  }, [isOpen, caseId, externalReportData]);

  // ESC to close
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  const handleCopy = () => {
    const textToCopy = report?.markdown || report?.executive_summary || '';
    if (navigator.clipboard) {
      navigator.clipboard.writeText(textToCopy).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };

  const handleDownload = () => {
    const text = report?.markdown || report?.executive_summary || '';
    const blob = new Blob([text], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `Informe_${caseId}_${Date.now()}.md`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.97, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.97, y: 10 }}
          transition={{ duration: 0.18, ease: 'easeOut' }}
          className="relative w-full max-w-3xl lg:max-w-4xl xl:max-w-5xl max-h-[90vh] flex flex-col rounded-3xl liquid-glass-elevated shadow-2xl overflow-hidden z-10 border border-black/10 dark:border-white/10 bg-white/95 dark:bg-[#090d0b]/95 backdrop-blur-2xl text-slate-900 dark:text-slate-100 font-sans"
        >
          {/* Minimalist Clean Header */}
          <div className="px-6 py-4 border-b border-black/[0.06] dark:border-white/[0.08] flex items-center justify-between gap-4">
            <div className="min-w-0">
              <h2 className="text-base sm:text-lg font-semibold text-slate-900 dark:text-white truncate">
                Informe Ejecutivo &bull; {clientInfo.name}
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 font-medium">
                {clientInfo.city} &bull; Score {clientInfo.score}/100
              </p>
            </div>

            {/* Quick Actions */}
            <div className="flex items-center gap-1.5 shrink-0">
              <button
                type="button"
                onClick={handleCopy}
                title="Copiar texto"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.1] text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                <span className="hidden sm:inline">{copied ? 'Copiado' : 'Copiar'}</span>
              </button>

              <button
                type="button"
                onClick={handleDownload}
                title="Descargar .md"
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.1] text-slate-700 dark:text-slate-200 transition-colors cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Descargar</span>
              </button>

              <button
                type="button"
                onClick={() => window.print()}
                title="Imprimir"
                className="p-1.5 rounded-full text-slate-500 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
              >
                <Printer className="w-4 h-4" />
              </button>

              <button
                type="button"
                onClick={onClose}
                className="p-1.5 rounded-full text-slate-400 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer ml-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Simple Navigation Tabs */}
          <div className="flex items-center gap-1.5 px-6 pt-3 pb-2.5 border-b border-black/[0.04] dark:border-white/[0.06]">
            <button
              type="button"
              onClick={() => setActiveTab('summary')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                activeTab === 'summary'
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Resumen</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('questions')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                activeTab === 'questions'
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>Preguntas Clave</span>
            </button>

            <button
              type="button"
              onClick={() => setActiveTab('document')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-colors cursor-pointer ${
                activeTab === 'document'
                  ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Documento</span>
            </button>
          </div>

          {/* Modal Content */}
          <div className="flex-1 overflow-y-auto p-6 sm:p-7 space-y-6">
            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-16 space-y-2 text-slate-400">
                <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                <p className="text-xs">Generando informe...</p>
              </div>
            ) : (
              <>
                {/* Tab: Resumen */}
                {activeTab === 'summary' && (
                  <div className="space-y-5">
                    {/* Executive Summary Paragraph */}
                    <div className="p-4 sm:p-5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.06] dark:border-white/[0.06]">
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-emerald-600 dark:text-emerald-400 mb-2">
                        Dictamen Actuarial
                      </h4>
                      <p className="text-sm leading-relaxed text-slate-800 dark:text-slate-200">
                        {report?.executive_summary || report?.summary || 'Plan financiero estructurado para consolidación de patrimonio.'}
                      </p>
                    </div>

                    {/* Immediate Key Priorities */}
                    <div>
                      <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 mb-3 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        Acciones Prioritarias (Próximos 30-60 Días)
                      </h4>

                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06] space-y-1">
                          <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">1. Deuda</span>
                          <h5 className="text-xs font-semibold text-slate-900 dark:text-white">Amortización de Pasivos</h5>
                          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Liquidar crédito de alto coste para liberar flujo de caja recurrente.
                          </p>
                        </div>

                        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06] space-y-1">
                          <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">2. Colchón</span>
                          <h5 className="text-xs font-semibold text-slate-900 dark:text-white">Fondo de Seguridad</h5>
                          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Asegurar 3 a 6 meses de gastos en cuenta remunerada accesible.
                          </p>
                        </div>

                        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06] space-y-1">
                          <span className="text-[10px] font-mono text-emerald-600 dark:text-emerald-400 font-semibold">3. Ahorro</span>
                          <h5 className="text-xs font-semibold text-slate-900 dark:text-white">Aportación Automática</h5>
                          <p className="text-xs text-slate-600 dark:text-slate-400 leading-relaxed">
                            Programar ahorro mensual en cartera diversificada a largo plazo.
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Tab: Preguntas Clave */}
                {activeTab === 'questions' && (
                  <div className="space-y-3">
                    <p className="text-xs text-slate-500 dark:text-slate-400">
                      Puntos recomendados para enfocar la conversación con el cliente:
                    </p>

                    {(report?.advisor_questions || [
                      `¿Cómo equilibrar la compra de vivienda a corto plazo con la meta de jubilación a largo plazo?`,
                      `¿Qué barreras impiden liquidar la deuda de tarjeta a pesar del nivel de ingresos?`,
                      `¿Cuál es el margen de maniobra ante imprevistos médicos o laborales en los próximos 12 meses?`
                    ]).map((q, idx) => (
                      <div
                        key={idx}
                        className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06] flex items-start gap-3"
                      >
                        <span className="flex items-center justify-center w-5 h-5 rounded-full bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold text-xs shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <p className="text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed">
                          {q}
                        </p>
                      </div>
                    ))}
                  </div>
                )}

                {/* Tab: Documento Completo */}
                {activeTab === 'document' && (
                  <div className="p-5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.06] dark:border-white/[0.06] prose prose-sm max-w-none text-slate-800 dark:text-slate-200 leading-relaxed">
                    <ReactMarkdown
                      remarkPlugins={[remarkGfm]}
                      components={{
                        h1: ({ children }) => <h1 className="text-base font-bold text-slate-900 dark:text-white mb-3 border-b border-black/10 dark:border-white/10 pb-2">{children}</h1>,
                        h2: ({ children }) => <h2 className="text-sm font-bold text-slate-900 dark:text-white mt-4 mb-2">{children}</h2>,
                        h3: ({ children }) => <h3 className="text-xs font-bold text-slate-900 dark:text-white mt-3 mb-1 uppercase tracking-wide">{children}</h3>,
                        p: ({ children }) => <p className="mb-2 text-xs sm:text-sm leading-relaxed text-slate-700 dark:text-slate-300">{children}</p>,
                        ul: ({ children }) => <ul className="list-disc pl-5 mb-3 space-y-1 text-xs sm:text-sm">{children}</ul>,
                        li: ({ children }) => <li className="leading-relaxed">{children}</li>,
                        blockquote: ({ children }) => (
                          <blockquote className="border-l-2 border-emerald-500 pl-3 py-1 my-2 italic text-xs text-slate-600 dark:text-slate-400">
                            {children}
                          </blockquote>
                        ),
                        table: ({ children }) => (
                          <div className="overflow-x-auto my-3 rounded-lg border border-black/10 dark:border-white/10">
                            <table className="w-full text-xs text-left border-collapse">{children}</table>
                          </div>
                        ),
                        th: ({ children }) => <th className="px-3 py-1.5 font-semibold bg-black/[0.02] dark:bg-white/[0.04]">{children}</th>,
                        td: ({ children }) => <td className="px-3 py-1.5 border-t border-black/5 dark:border-white/5">{children}</td>
                      }}
                    >
                      {report?.markdown || generateFallbackMarkdown(caseId, clientInfo.name)}
                    </ReactMarkdown>
                  </div>
                )}
              </>
            )}
          </div>

          {/* Clean Footer */}
          <div className="px-6 py-3 border-t border-black/[0.06] dark:border-white/[0.08] flex items-center justify-end">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-1.5 rounded-full text-xs font-medium bg-black/[0.05] dark:bg-white/[0.08] hover:bg-black/[0.08] dark:hover:bg-white/[0.12] text-slate-800 dark:text-white transition-colors cursor-pointer"
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
  return `# Informe Ejecutivo

**Cliente:** ${clientName}  
**Expediente:** \`${caseId}\`  

---

## 1. Resumen Ejecutivo
Plan patrimonial estructurado para optimizar la liquidez y consolidar las metas financieras a largo plazo.

### Diagnóstico
- **Score Inicial:** 26 / 100
- **Score Proyectado M12:** 78 / 100
- **Probabilidad de Éxito:** 94.2%

---

## 2. Hoja de Ruta Prioritaria
1. **Amortización de Pasivos:** Liquidar saldos de tarjeta de alto coste para liberar flujo mensual.
2. **Fondo de Reserva:** Mantener entre 3 y 6 meses de gastos en cuenta de liquidez.
3. **Ahorro Automatizado:** Dirigir excedentes mensuales a cartera diversificada a largo plazo.

---

## 3. Puntos de Diálogo para la Reunión
- Validar supuestos de ingresos y gastos mensuales.
- Confirmar horizonte temporal para la compra de vivienda.
- Establecer calendario de aportaciones periódicas.
`;
}

export default HandoverModal;
