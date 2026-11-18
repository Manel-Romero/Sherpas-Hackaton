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
  Brain, 
  Wallet, 
  Coins, 
  TrendingUp, 
  Download, 
  CheckCircle2, 
  Lock 
} from 'lucide-react';
import { PersonaInsights, TableSummary } from '../types';
import * as api from '../services/api';
import { audioService } from '../services/audioService';

interface PersonaDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  insights: PersonaInsights | null;
  isLoading: boolean;
  summary?: TableSummary | null;
  onConsultTopic?: (topic: string) => void;
}

// Case-specific deep psychological & balance sheet profiles
const CASE_PROFILES: Record<string, {
  netWorth: number;
  liquidAssets: number;
  monthlyBurn: number;
  savingsRate: string;
  riskAlignment: { stated: string; revealed: string; inferred: string; status: 'ALIGNED' | 'DIVERGENT' | 'CAUTION' };
  biases: Array<{ name: string; description: string; impact: string }>;
  tensions: Array<{ title: string; subtitle: string; severity: 'high' | 'medium' }>;
}> = {
  'michael-carter': {
    netWorth: 218500,
    liquidAssets: 30000,
    monthlyBurn: 9306,
    savingsRate: '23.9%',
    riskAlignment: {
      stated: 'Growth (Nivel 4)',
      revealed: '72% Renta Variable / 25% Bonos',
      inferred: 'Agresivo (tolerante a volatilidad)',
      status: 'ALIGNED'
    },
    biases: [
      {
        name: 'Sobrecarga Decisional y Parálisis Analítica',
        description: 'Exige validación técnica exhaustiva previa a cualquier acción, retrasando decisiones de desendeudamiento elemental.',
        impact: 'Costo de demora de ~$700/año en intereses evitables.'
      },
      {
        name: 'Compartimentación Mental (Mental Accounting)',
        description: 'Considera sus RSUs y cuenta de trading como capital intocable mientras mantiene deuda al 20% TAE en rotativo.',
        impact: 'Drenaje neto de rentabilidad financiera.'
      },
      {
        name: 'Sesgo de Optimismo en Horizonte de Retiro',
        description: 'Fija meta de retiro a los 58 años sin provisionar el precipicio de liquidez que generará la compra de vivienda en 2027.',
        impact: 'Déficit actuarial de $1.17M proyectado a los 85 años.'
      }
    ],
    tensions: [
      {
        title: 'Entrada de Casa ($113.3k) vs. Fondo de Emergencia',
        subtitle: 'El desembolso previsto para enero 2027 reducirá la cobertura de liquidez a 0 meses si no se secuencia con meses de antelación.',
        severity: 'high'
      },
      {
        title: 'Retiro Temprano a los 58 vs. Protección por Fallecimiento',
        subtitle: 'Dispone de sólo $180k en seguro de vida frente a una necesidad actuarial calculada de $900k-$1.8M.',
        severity: 'medium'
      }
    ]
  },
  'timothy-melanie-weah': {
    netWorth: 650000,
    liquidAssets: 150000,
    monthlyBurn: 11200,
    savingsRate: '18.5%',
    riskAlignment: {
      stated: 'Moderado',
      revealed: 'Ultraconservador en depósitos a la vista',
      inferred: 'Asimétrico defensivo',
      status: 'DIVERGENT'
    },
    biases: [
      {
        name: 'Aversión Extrema a la Pérdida en Liquidez',
        description: 'Mantienen $150,000 en cuenta corriente al 0.01% TAE como refugio psicológico.',
        impact: 'Pérdida de poder adquisitivo por inflación de ~$6,000/año.'
      },
      {
        name: 'Inercia del Status Quo en Tarjetas',
        description: 'Arrastran $18,000 en tarjetas de crédito devengando intereses mientras tienen fondos líquidos de sobra para liquidarlas.',
        impact: 'Intereses tóxicos de $270/mes completamente innecesarios.'
      }
    ],
    tensions: [
      {
        title: 'Exceso de Efectivo vs. Liquidación de Pasivos Caros',
        subtitle: 'Paradoja de alta liquidez estéril conviviendo con deuda de consumo activa.',
        severity: 'high'
      }
    ]
  },
  'daniel-emily-johnson': {
    netWorth: 310000,
    liquidAssets: 42000,
    monthlyBurn: 7800,
    savingsRate: '21.0%',
    riskAlignment: {
      stated: 'Moderado Familiar',
      revealed: 'Conservador indexado',
      inferred: 'Defensivo protector',
      status: 'ALIGNED'
    },
    biases: [
      {
        name: 'Ilusión de Control Financiero',
        description: 'La disciplina en el presupuesto mensual genera una falsa tranquilidad que opaca la falta de coberturas catastróficas.',
        impact: 'Brecha de seguro de vida de $1,350,000 descubierta.'
      }
    ],
    tensions: [
      {
        title: 'Ahorro Universitario vs. Blindaje Familiar Inmediato',
        subtitle: 'Priorizan fondos para los hijos antes de consolidar el testamento y seguro de vida de los progenitores.',
        severity: 'high'
      }
    ]
  },
  'samantha-lewis': {
    netWorth: 1820000,
    liquidAssets: 220000,
    monthlyBurn: 14500,
    savingsRate: '28.0%',
    riskAlignment: {
      stated: 'Crecimiento Alto',
      revealed: 'Concentración Inmobiliaria',
      inferred: 'Empresarial con sesgo físico',
      status: 'CAUTION'
    },
    biases: [
      {
        name: 'Sesgo de Activo Tangible (Real Estate Bias)',
        description: 'Sobrepondera bienes raíces (58% del patrimonio total) por su visibilidad física sobre mercados líquidos.',
        impact: 'Iliquidez estructural ante contingencias sucesorias.'
      }
    ],
    tensions: [
      {
        title: 'Riesgo de Longevidad post-72 vs. Tasa de Retiro Actual',
        subtitle: 'Ritmo de desinversión acelerado que compromete el capital en el último tercio de vida.',
        severity: 'high'
      }
    ]
  }
};

export const PersonaDrawer: React.FC<PersonaDrawerProps> = ({
  isOpen,
  onClose,
  insights,
  isLoading,
  summary,
  onConsultTopic
}) => {
  const [activeDrawerTab, setActiveDrawerTab] = useState<'dossier' | 'report'>('dossier');
  const [report, setReport] = useState<any>(null);
  const [isLoadingReport, setIsLoadingReport] = useState(false);
  const [isCopied, setIsCopied] = useState(false);

  const caseId = insights?.case_id || 'michael-carter';
  const profileData = CASE_PROFILES[caseId] || CASE_PROFILES['michael-carter'];

  // Net worth & liquid assets display: prioritize summary props, fallback to case profile
  const netWorthVal = summary?.net_worth ?? profileData.netWorth;
  const liquidAssetsVal = profileData.liquidAssets;
  const monthlyBurnVal = summary?.monthly_expenses ?? profileData.monthlyBurn;

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
  }, [isOpen, activeDrawerTab, insights?.case_id, report]);

  const handleOpenReportTab = () => {
    audioService.playSound('click');
    setActiveDrawerTab('report');
  };

  const handleCopyMarkdown = () => {
    if (report?.markdown) {
      navigator.clipboard.writeText(report.markdown);
      setIsCopied(true);
      audioService.playSound('message');
      setTimeout(() => setIsCopied(false), 2000);
    }
  };

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(val);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop with ultra-smooth blur */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 z-50 bg-black/50 dark:bg-black/75 backdrop-blur-md"
          />

          {/* Slide-over memorandum */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 30, stiffness: 320 }}
            className="fixed right-0 top-0 bottom-0 z-50 w-full max-w-xl bg-white/95 dark:bg-zinc-950/95 backdrop-blur-2xl border-l border-black/[0.08] dark:border-white/[0.08] shadow-2xl flex flex-col overflow-hidden text-slate-800 dark:text-slate-100"
          >
            {/* Header with Advisor Direct Badge & Action */}
            <div className="px-6 py-5 border-b border-black/[0.06] dark:border-white/[0.08] bg-black/[0.015] dark:bg-white/[0.02]">
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="inline-flex items-center gap-1 text-[10px] font-mono uppercase tracking-wider text-emerald-800 dark:text-emerald-300 bg-emerald-500/10 px-2.5 py-0.5 rounded-full border border-emerald-500/20">
                    <Lock className="w-2.5 h-2.5" /> Confidencial &bull; Uso Asesor
                  </span>
                  <span className="text-[10px] font-mono text-slate-400">
                    ID: {insights?.case_id || 'expediente'}
                  </span>
                </div>
                <button
                  onClick={onClose}
                  className="p-1.5 text-slate-400 hover:text-slate-800 dark:hover:text-white rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
                  title="Cerrar expediente"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3 mt-3">
                <div>
                  <h3 className="text-base sm:text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
                    {activeDrawerTab === 'dossier' ? 'Dossier Psico-Financiero Integral' : 'Dictamen Ejecutivo Handover'}
                  </h3>
                  <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                    {insights?.title ? `${insights.title} • ${insights.city || 'Austin, TX'}` : 'Expediente del Cliente'}
                  </p>
                </div>

                {/* Direct Action Button: Generate / View Handover Report */}
                {activeDrawerTab === 'dossier' ? (
                  <button
                    onClick={handleOpenReportTab}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white text-xs font-semibold shadow-sm transition-all cursor-pointer shrink-0"
                  >
                    <FileText className="w-3.5 h-3.5" />
                    <span>Ver Handover Report</span>
                  </button>
                ) : (
                  <button
                    onClick={() => setActiveDrawerTab('dossier')}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-black/5 dark:bg-white/10 hover:bg-black/10 text-slate-700 dark:text-slate-200 text-xs font-medium transition-all cursor-pointer shrink-0"
                  >
                    <Target className="w-3.5 h-3.5" />
                    <span>Volver a Perfil</span>
                  </button>
                )}
              </div>

              {/* Sub-tab Navigation */}
              <div className="flex items-center gap-2 mt-4 pt-3 border-t border-black/[0.04] dark:border-white/[0.06]">
                <button
                  onClick={() => setActiveDrawerTab('dossier')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    activeDrawerTab === 'dossier'
                      ? 'bg-black/5 dark:bg-white/10 text-slate-900 dark:text-white font-semibold'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
                  }`}
                >
                  <Brain className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Perfil & Sesgos Cognitivos</span>
                </button>
                <button
                  onClick={() => setActiveDrawerTab('report')}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all cursor-pointer ${
                    activeDrawerTab === 'report'
                      ? 'bg-black/5 dark:bg-white/10 text-slate-900 dark:text-white font-semibold'
                      : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
                  }`}
                >
                  <FileText className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>Informe para Reunión Asesor</span>
                </button>
              </div>
            </div>

            {/* Scrollable Body Content */}
            <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">
              {activeDrawerTab === 'dossier' ? (
                isLoading || !insights ? (
                  <div className="flex flex-col items-center justify-center h-64 text-slate-400 dark:text-slate-500 space-y-3">
                    <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-xs font-mono">Indexando expediente actuarial y sesgos...</p>
                  </div>
                ) : (
                  <>
                    {/* SECTION 1: Financial Balance Sheet Breakdown */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500 font-mono">
                          Balance y Liquidez
                        </span>
                        <span className="text-[10px] font-mono text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded-md border border-emerald-500/20">
                          {insights.wealth_tier}
                        </span>
                      </div>

                      <div className="grid grid-cols-3 gap-2.5">
                        <div className="p-3.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06]">
                          <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[10px] uppercase font-mono">
                            <Wallet className="w-3 h-3 text-emerald-600 dark:text-emerald-400" />
                            <span>Patrimonio Neto</span>
                          </div>
                          <div className="text-sm sm:text-base font-bold text-slate-900 dark:text-white mt-1">
                            {formatCurrency(netWorthVal)}
                          </div>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                            Activos - Pasivos
                          </div>
                        </div>

                        <div className="p-3.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06]">
                          <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[10px] uppercase font-mono">
                            <Coins className="w-3 h-3 text-amber-500" />
                            <span>Activos Líquidos</span>
                          </div>
                          <div className="text-sm sm:text-base font-bold text-slate-900 dark:text-white mt-1">
                            {formatCurrency(liquidAssetsVal)}
                          </div>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                            {(liquidAssetsVal / (monthlyBurnVal || 1)).toFixed(1)} meses gasto
                          </div>
                        </div>

                        <div className="p-3.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06]">
                          <div className="flex items-center gap-1.5 text-slate-400 dark:text-slate-500 text-[10px] uppercase font-mono">
                            <TrendingUp className="w-3 h-3 text-sky-500" />
                            <span>Tasa de Ahorro</span>
                          </div>
                          <div className="text-sm sm:text-base font-bold text-slate-900 dark:text-white mt-1">
                            {profileData.savingsRate}
                          </div>
                          <div className="text-[10px] text-slate-500 dark:text-slate-400 mt-0.5">
                            Del ingreso bruto
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* SECTION 2: Risk Tolerance Alignment */}
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500 font-mono">
                          Orientación y Tolerancia al Riesgo
                        </span>
                        <span className={`text-[10px] font-mono px-2 py-0.5 rounded-md border ${
                          profileData.riskAlignment.status === 'ALIGNED'
                            ? 'text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 border-emerald-500/20'
                            : 'text-amber-700 dark:text-amber-300 bg-amber-500/10 border-amber-500/20'
                        }`}>
                          {profileData.riskAlignment.status === 'ALIGNED' ? 'Alineado D4' : 'Divergencia Detectada'}
                        </span>
                      </div>

                      <div className="p-4 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06] space-y-3">
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
                          <div>
                            <span className="text-[10px] font-mono text-slate-400 uppercase block">Riesgo Declarado</span>
                            <span className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5 block">
                              {profileData.riskAlignment.stated}
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] font-mono text-slate-400 uppercase block">Riesgo Revelado</span>
                            <span className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5 block">
                              {profileData.riskAlignment.revealed}
                            </span>
                          </div>
                          <div>
                            <span className="text-[10px] font-mono text-slate-400 uppercase block">Riesgo Inferido</span>
                            <span className="font-semibold text-slate-800 dark:text-slate-200 mt-0.5 block">
                              {profileData.riskAlignment.inferred}
                            </span>
                          </div>
                        </div>

                        <div className="pt-2.5 border-t border-black/[0.04] dark:border-white/[0.05] text-[11px] text-slate-500 dark:text-slate-400">
                          <strong className="text-slate-700 dark:text-slate-300">Estilo Decisorio:</strong> {insights.decision_style}
                        </div>
                      </div>
                    </div>

                    {/* SECTION 3: Psychological Biases */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500 font-mono">
                        <Brain className="w-3.5 h-3.5 text-purple-500" />
                        <span>Sesgos Psicológicos y Conductuales</span>
                      </div>

                      <div className="space-y-2.5">
                        {profileData.biases.map((bias, i) => (
                          <div
                            key={i}
                            className="p-3.5 rounded-xl bg-purple-500/[0.03] dark:bg-purple-500/[0.05] border border-purple-500/15 transition-all hover:border-purple-500/25"
                          >
                            <div className="flex items-center justify-between gap-2">
                              <span className="text-xs font-semibold text-purple-900 dark:text-purple-200">
                                {bias.name}
                              </span>
                              <span className="text-[9px] font-mono uppercase text-purple-600 dark:text-purple-300 bg-purple-500/10 px-1.5 py-0.5 rounded">
                                Sesgo D5
                              </span>
                            </div>
                            <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">
                              {bias.description}
                            </p>
                            <div className="mt-2 text-[11px] text-purple-800 dark:text-purple-300/90 font-medium flex items-center gap-1">
                              <span>Repercusión:</span>
                              <span className="font-normal">{bias.impact}</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* SECTION 4: Core Tensions / Psychological Dilemma */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500 font-mono">
                        <AlertOctagon className="w-3.5 h-3.5 text-amber-500" />
                        <span>Tensiones Financieras Centrales</span>
                      </div>

                      <div className="p-4 rounded-xl bg-amber-500/[0.04] dark:bg-amber-500/[0.06] border border-amber-500/20 space-y-3">
                        <div className="text-xs font-semibold text-amber-900 dark:text-amber-200">
                          {insights.primary_tension}
                        </div>
                        {profileData.tensions.map((t, i) => (
                          <div key={i} className="pt-2 border-t border-amber-500/10 text-xs">
                            <span className="font-semibold text-slate-800 dark:text-slate-200 block">{t.title}</span>
                            <p className="text-slate-600 dark:text-slate-400 mt-0.5 leading-relaxed">{t.subtitle}</p>
                          </div>
                        ))}
                      </div>
                    </div>

                    {/* SECTION 5: Motivational Anchor & Alerts */}
                    <div className="space-y-3">
                      <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500 font-mono">
                        <Compass className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                        <span>Ancla Motivacional</span>
                      </div>
                      <div className="p-3.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06] text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                        {insights.emotional_archetype}
                      </div>
                    </div>

                    {/* Key Alerts */}
                    {insights.key_alerts && insights.key_alerts.length > 0 && (
                      <div className="space-y-2.5">
                        <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500 font-mono">
                          <ShieldAlert className="w-3.5 h-3.5 text-rose-500" />
                          <span>Puntos Críticos Detectados</span>
                        </div>
                        <div className="space-y-2">
                          {insights.key_alerts.map((alert, i) => (
                            <div 
                              key={i} 
                              className="p-3 rounded-xl bg-rose-500/[0.03] dark:bg-rose-500/[0.06] border border-rose-500/20 text-xs text-slate-800 dark:text-rose-200 leading-relaxed flex items-start gap-2.5"
                            >
                              <span className="text-rose-500 font-mono text-sm leading-none mt-0.5">&bull;</span>
                              <span>{alert}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )
              ) : (
                /* REPORT TAB */
                isLoadingReport ? (
                  <div className="flex flex-col items-center justify-center h-64 text-slate-400 dark:text-slate-500 space-y-3">
                    <div className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin" />
                    <p className="text-xs font-mono">Generando dictamen ejecutivo actuarial...</p>
                  </div>
                ) : report ? (
                  <div className="space-y-5">
                    {/* Top Actions Ribbon */}
                    <div className="flex items-center justify-between p-3 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06]">
                      <div className="flex items-center gap-2">
                        <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                        <span className="text-xs font-semibold text-slate-800 dark:text-white">
                          Dictamen Listo para Reunión
                        </span>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={handleCopyMarkdown}
                          className="px-2.5 py-1 text-[11px] font-medium text-slate-700 dark:text-slate-200 bg-black/5 dark:bg-white/10 hover:bg-black/10 rounded-lg transition-colors cursor-pointer flex items-center gap-1"
                        >
                          <Download className="w-3 h-3" />
                          <span>{isCopied ? '¡Copiado!' : 'Copiar Dictamen'}</span>
                        </button>
                      </div>
                    </div>

                    {/* Key Questions for Advisor */}
                    {report.advisor_questions && Array.isArray(report.advisor_questions) && report.advisor_questions.length > 0 && (
                      <div className="space-y-2.5">
                        <div className="flex items-center gap-1.5 text-[11px] uppercase tracking-wider font-semibold text-slate-400 dark:text-slate-500 font-mono">
                          <HelpCircle className="w-3.5 h-3.5 text-amber-500" />
                          <span>Preguntas Estratégicas para la Reunión</span>
                        </div>
                        <div className="space-y-2">
                          {report.advisor_questions.map((q: string, i: number) => (
                            <div key={i} className="p-3 rounded-xl bg-amber-500/[0.04] dark:bg-amber-500/[0.06] border border-amber-500/20 text-xs text-slate-800 dark:text-amber-100 leading-relaxed flex items-start gap-2.5">
                              <span className="text-amber-500 font-bold shrink-0">{i + 1}.</span>
                              <span>{q}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Markdown Report Content */}
                    {report.markdown ? (
                      <div className="p-5 rounded-2xl bg-black/[0.015] dark:bg-white/[0.02] border border-black/[0.05] dark:border-white/[0.06] text-xs sm:text-sm text-slate-800 dark:text-slate-200 leading-relaxed prose prose-sm dark:prose-invert max-w-none">
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                          {report.markdown}
                        </ReactMarkdown>
                      </div>
                    ) : (
                      <div className="p-4 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06] text-xs text-slate-700 dark:text-slate-300">
                        {report.executive_summary || report.summary || 'Informe generado con éxito para revisión del plan.'}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-col items-center justify-center h-48 text-slate-400 dark:text-slate-500 text-xs text-center">
                    No se encontró informe previo para este expediente.
                  </div>
                )
              )}
            </div>

            {/* Bottom Status Footer */}
            <div className="px-6 py-3 border-t border-black/[0.06] dark:border-white/[0.08] bg-black/[0.015] dark:bg-white/[0.02] flex items-center justify-between text-[11px] text-slate-400 dark:text-slate-500">
              <span className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Sherpas Continuous Advisory Engine
              </span>
              <span className="font-mono text-[10px]">{caseId}</span>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
};

export default PersonaDrawer;
