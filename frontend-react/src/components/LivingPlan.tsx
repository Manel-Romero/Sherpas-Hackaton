import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Target, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle2, 
  Clock, 
  ChevronDown, 
  ChevronUp, 
  Sparkles, 
  Sliders, 
  ShieldCheck, 
  Home, 
  Plane, 
  Coins, 
  Flame, 
  RefreshCw, 
  ArrowRight, 
  Check, 
  Calendar,
  Layers,
  ArrowUpRight,
  Shield,
  Zap,
  Info
} from 'lucide-react';
import { KanbanCard, KanbanState } from '../types';
import { audioService } from '../services/audioService';

export interface FinancialGoal {
  id: string;
  title: string;
  targetAmount: number;
  currentAmount: number;
  targetDate: string;
  category: 'purchase' | 'retirement' | 'lifestyle' | 'emergency';
  priority: 'Alta' | 'Estratégica' | 'Moderada';
  status: 'active' | 'completed' | 'paused';
  notes?: string;
}

export interface StrategicRecommendation {
  id: string;
  title: string;
  impact: string;
  impactType: 'savings' | 'score' | 'debt' | 'protection';
  effort: 'Bajo' | 'Medio' | 'Alto';
  category: 'debt' | 'insurance' | 'investment' | 'savings';
  rationale: string;
  mitigation: string;
  steps: string[];
  status: 'todo' | 'in_process' | 'done';
}

export interface ScenarioAdjustment {
  id: string;
  name: string;
  description: string;
  type: 'inflation' | 'market' | 'retirement' | 'property';
  impactProbability: number; // e.g. -12%
  monthlyCashflowDelta: number; // -$450
  netWorth12mDelta: number; // -$14,000
  mitigationPlan: string;
}

export interface LivingPlanProps {
  caseId?: string;
  kanban?: KanbanState;
  onArrangeCard?: (cardId: string, toStatus: 'todo' | 'in_process' | 'done', toIndex?: number) => Promise<void>;
  onAddCard?: (card: Partial<KanbanCard>) => Promise<void>;
  onDeleteCard?: (cardId: string) => Promise<void>;
  onConsultTask?: (taskTitle: string, taskImpact?: string) => void;
  onSimulateScenario?: (scenarioName: string) => void;
}

// Case presets for Goals
const CASE_GOALS: Record<string, FinancialGoal[]> = {
  'michael-carter': [
    {
      id: 'g-home',
      title: 'Entrada para Vivienda Austin ($550k)',
      targetAmount: 113300,
      currentAmount: 30000,
      targetDate: 'Jun 2027',
      category: 'purchase',
      priority: 'Alta',
      status: 'active',
      notes: 'Requiere $113.3k de entrada más $9.4k de gastos de escrituración.'
    },
    {
      id: 'g-retire',
      title: 'Jubilación Temprana a los 58 Años',
      targetAmount: 1535000,
      currentAmount: 172000,
      targetDate: 'Abr 2047',
      category: 'retirement',
      priority: 'Estratégica',
      status: 'active',
      notes: 'Objetivo de draw mensual sostenible sin agotar fondo a los 85.'
    },
    {
      id: 'g-vacation',
      title: 'Fondo Anual de Vacaciones & Bienestar',
      targetAmount: 3500,
      currentAmount: 3500,
      targetDate: 'Ene 2027',
      category: 'lifestyle',
      priority: 'Moderada',
      status: 'completed',
      notes: 'Provisionado al 100% en cuenta separada sin tocar el ahorro de vivienda.'
    },
    {
      id: 'g-emergency',
      title: 'Fondo de Emergencia Blindado (6 Meses)',
      targetAmount: 55836,
      currentAmount: 30000,
      targetDate: 'Dic 2026',
      category: 'emergency',
      priority: 'Alta',
      status: 'active',
      notes: 'Faltan $25,836 para el óptimo de 6 meses de gastos fijos.'
    }
  ],
  'timothy-melanie-weah': [
    {
      id: 'g-debt-zero',
      title: 'Erradicación de Deuda de Consumo ($18k)',
      targetAmount: 18000,
      currentAmount: 5000,
      targetDate: 'Mar 2027',
      category: 'emergency',
      priority: 'Alta',
      status: 'active'
    },
    {
      id: 'g-529-college',
      title: 'Plan Universitario 529 Liam & Josh',
      targetAmount: 120000,
      currentAmount: 18000,
      targetDate: 'Sep 2035',
      category: 'lifestyle',
      priority: 'Estratégica',
      status: 'active'
    }
  ],
  'daniel-emily-johnson': [
    {
      id: 'g-life-shield',
      title: 'Cobertura de Seguro de Vida $1.6M',
      targetAmount: 1600000,
      currentAmount: 250000,
      targetDate: 'Ene 2027',
      category: 'emergency',
      priority: 'Alta',
      status: 'active'
    },
    {
      id: 'g-emergency-6m',
      title: 'Reserva Familiar 6 Meses de Gasto',
      targetAmount: 46800,
      currentAmount: 21840,
      targetDate: 'Oct 2027',
      category: 'emergency',
      priority: 'Alta',
      status: 'active'
    }
  ],
  'samantha-lewis': [
    {
      id: 'g-miami-prop',
      title: 'Adquisición Inmobiliaria Miami 2030',
      targetAmount: 180000,
      currentAmount: 85000,
      targetDate: 'Ene 2030',
      category: 'purchase',
      priority: 'Alta',
      status: 'active'
    },
    {
      id: 'g-trust-fund',
      title: 'Estructuración Fideicomiso Sucesorio',
      targetAmount: 500000,
      currentAmount: 120000,
      targetDate: 'Nov 2028',
      category: 'retirement',
      priority: 'Estratégica',
      status: 'active'
    }
  ]
};

// Strategic recommendations
const BASE_RECOMMENDATIONS: Record<string, StrategicRecommendation[]> = {
  'michael-carter': [
    {
      id: 'rec-1',
      title: 'Congelar y Desvincular Tarjeta Amex Platinum (20% TAE)',
      impact: '+$700/año Ahorro',
      impactType: 'savings',
      effort: 'Bajo',
      category: 'debt',
      rationale: 'Es la deuda más cara del expediente y devenga $58/mes en intereses que erosionan el flujo libre.',
      mitigation: 'Eliminarla de Apple Pay para frenar cargos automáticos y programar pago mínimo automático.',
      steps: [
        'Desvincular tarjeta de monederos digitales en menos de 2 minutos.',
        'Activar pago recurrente mínimo de $200 para blindar el score de crédito.',
        'Guardar el plástico físico en un lugar no accesible a diario.'
      ],
      status: 'in_process'
    },
    {
      id: 'rec-2',
      title: 'Contratar Póliza Umbrella de $1,000,000',
      impact: '+5 Pts Health Score',
      impactType: 'score',
      effort: 'Bajo',
      category: 'insurance',
      rationale: 'Con un patrimonio neto de $218.5k y activos acumulados, carecer de escudo de responsabilidad civil expone los ahorros ante litigios.',
      mitigation: 'Añadir $1M de cobertura por ~$25/mes blindando activos líquidos presentes y futuros.',
      steps: [
        'Cotizar ampliación con el emisor actual de seguro del BMW.',
        'Alinear límites subyacentes de auto y vivienda antes de la compra de 2027.'
      ],
      status: 'todo'
    },
    {
      id: 'rec-3',
      title: 'Reasignar Excedente Mensual de $500 a Desendeudamiento Relámpago',
      impact: 'Deuda Cero en Mes 6',
      impactType: 'debt',
      effort: 'Medio',
      category: 'debt',
      rationale: 'El excedente mensual actual se diluye en cuenta. Concentrar $500/mes extingue el saldo completo de $3,500 en seis meses.',
      mitigation: 'Libera $200/mes de cuota obligatoria de forma permanente a partir de julio.',
      steps: [
        'Programar transferencia el día 2 de cada mes posterior al cobro de nómina.',
        'Una vez liquidada, reorientar esos $500 directamente al fondo de entrada de vivienda.'
      ],
      status: 'todo'
    },
    {
      id: 'rec-4',
      title: 'Sustituir Fondo de Bonos High-Yield (JNK) por Vehículo Fiscalmente Eficiente',
      impact: '+$527/año Ahorro Fiscal',
      impactType: 'protection',
      effort: 'Bajo',
      category: 'investment',
      rationale: '$15,000 en bonos de alto rendimiento en cuenta gravable generan cupones tributados al 24% marginal.',
      mitigation: 'Traspasar hacia fondos de tesorería exentos o fondos indexados de acumulación.',
      steps: [
        'Ejecutar venta compensando con posibles minusvalías acumuladas.',
        'Reinvertir en fondo con mayor eficiencia tributaria.'
      ],
      status: 'done'
    }
  ]
};

// Interactive What-If Scenarios
const PRESET_SCENARIOS: ScenarioAdjustment[] = [
  {
    id: 'sc-inflation',
    name: 'Shock Inflacionario Persistente (+3.5%)',
    description: 'Aumento continuo de costes de vida (alquiler, suministros, alimentos) de $450/mes.',
    type: 'inflation',
    impactProbability: -8,
    monthlyCashflowDelta: -450,
    netWorth12mDelta: -10800,
    mitigationPlan: 'Reducir gastos discrecionales en $300 y pausar aportaciones a cuentas no deducibles.'
  },
  {
    id: 'sc-market',
    name: 'Corrección Bursátil Severa (-18%)',
    description: 'Retroceso brusco en renta variable global durante los próximos 12 meses.',
    type: 'market',
    impactProbability: -14,
    monthlyCashflowDelta: 0,
    netWorth12mDelta: -26100,
    mitigationPlan: 'Mantener asignación sin vender; aprovechar DCA automático en fondos indexados con descuento.'
  },
  {
    id: 'sc-retire-55',
    name: 'Jubilación Anticipada Acelerada (55 vs 58 años)',
    description: 'Adelantar 3 años la salida laboral, ampliando el periodo de desinversión a 36 años.',
    type: 'retirement',
    impactProbability: -19,
    monthlyCashflowDelta: -650,
    netWorth12mDelta: -15600,
    mitigationPlan: 'Requiere incrementar la tasa de ahorro del 23.9% al 31.5% antes de 2028.'
  },
  {
    id: 'sc-property',
    name: 'Sobrecosto de Entrada Vivienda (+15% en Austin)',
    description: 'Subida del valor de tasación con entrada necesaria de $130,000 en lugar de $113,300.',
    type: 'property',
    impactProbability: -11,
    monthlyCashflowDelta: -220,
    netWorth12mDelta: -16700,
    mitigationPlan: 'Extender el plazo de compra 5 meses o negociar aportación de vendedor para costes de cierre.'
  }
];

export const LivingPlan: React.FC<LivingPlanProps> = ({
  caseId = 'michael-carter',
  kanban,
  onArrangeCard,
  onAddCard,
  onDeleteCard,
  onConsultTask,
  onSimulateScenario
}) => {
  const [activeFilter, setActiveFilter] = useState<'all' | 'goals' | 'recommendations' | 'scenarios'>('all');
  const [expandedRecId, setExpandedRecId] = useState<string | null>(null);
  const [selectedScenarios, setSelectedScenarios] = useState<string[]>([]);
  const [goals, setGoals] = useState<FinancialGoal[]>(() => CASE_GOALS[caseId] || CASE_GOALS['michael-carter']);
  const [recommendations, setRecommendations] = useState<StrategicRecommendation[]>(
    () => BASE_RECOMMENDATIONS[caseId] || BASE_RECOMMENDATIONS['michael-carter']
  );

  // Sync goals when case changes
  React.useEffect(() => {
    setGoals(CASE_GOALS[caseId] || CASE_GOALS['michael-carter']);
    setRecommendations(BASE_RECOMMENDATIONS[caseId] || BASE_RECOMMENDATIONS['michael-carter']);
  }, [caseId]);

  // Handle goal inline status toggle
  const handleToggleGoalStatus = (goalId: string) => {
    audioService.playSound('click');
    setGoals((prev) =>
      prev.map((g) => {
        if (g.id !== goalId) return g;
        const nextStatus = g.status === 'active' ? 'completed' : g.status === 'completed' ? 'paused' : 'active';
        if (nextStatus === 'completed') audioService.playSound('task_done');
        return { ...g, status: nextStatus };
      })
    );
  };

  // Handle recommendation inline status toggle
  const handleToggleRecStatus = async (recId: string) => {
    audioService.playSound('click');
    setRecommendations((prev) =>
      prev.map((r) => {
        if (r.id !== recId) return r;
        const nextStatus = r.status === 'todo' ? 'in_process' : r.status === 'in_process' ? 'done' : 'todo';
        if (nextStatus === 'done') audioService.playSound('task_done');
        return { ...r, status: nextStatus };
      })
    );

    // If an onArrangeCard handler is provided and cards exist, attempt syncing
    if (onArrangeCard && kanban?.cards) {
      const matchCard = kanban.cards.find(c => c.id === recId || c.title.toLowerCase().includes(recId));
      if (matchCard) {
        const nextStatus = matchCard.status === 'todo' ? 'in_process' : matchCard.status === 'in_process' ? 'done' : 'todo';
        await onArrangeCard(matchCard.id, nextStatus);
      }
    }
  };

  // Handle scenario toggle
  const handleToggleScenario = (scId: string) => {
    audioService.playSound('click');
    setSelectedScenarios((prev) =>
      prev.includes(scId) ? prev.filter((id) => id !== scId) : [...prev, scId]
    );
  };

  // Compute live scenario impact
  const scenarioImpact = useMemo(() => {
    if (selectedScenarios.length === 0) {
      return {
        probDelta: 0,
        cashflowDelta: 0,
        netWorthDelta: 0,
        activeCount: 0
      };
    }
    const active = PRESET_SCENARIOS.filter((s) => selectedScenarios.includes(s.id));
    return {
      probDelta: active.reduce((acc, s) => acc + s.impactProbability, 0),
      cashflowDelta: active.reduce((acc, s) => acc + s.monthlyCashflowDelta, 0),
      netWorthDelta: active.reduce((acc, s) => acc + s.netWorth12mDelta, 0),
      activeCount: active.length
    };
  }, [selectedScenarios]);

  const baseProbability = 82;
  const currentProbability = Math.max(15, Math.min(99, baseProbability + scenarioImpact.probDelta));

  const formatCurrency = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      maximumFractionDigits: 0
    }).format(val);
  };

  // SVG Progress Ring helper
  const renderProgressRing = (percentage: number, strokeColor: string = '#10b981') => {
    const radius = 22;
    const circumference = 2 * Math.PI * radius;
    const strokeDashoffset = circumference - (Math.min(100, Math.max(0, percentage)) / 100) * circumference;

    return (
      <div className="relative w-14 h-14 flex items-center justify-center shrink-0">
        <svg className="w-14 h-14 -rotate-90" viewBox="0 0 54 54">
          <circle
            cx="27"
            cy="27"
            r={radius}
            className="stroke-black/[0.06] dark:stroke-white/[0.08]"
            strokeWidth="4"
            fill="transparent"
          />
          <circle
            cx="27"
            cy="27"
            r={radius}
            stroke={strokeColor}
            strokeWidth="4"
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            fill="transparent"
            className="transition-all duration-700 ease-out"
          />
        </svg>
        <span className="absolute text-[11px] font-mono font-bold text-slate-800 dark:text-slate-100">
          {Math.round(percentage)}%
        </span>
      </div>
    );
  };

  return (
    <div className="w-full space-y-6 pb-12">
      {/* Top Strategic Overview Ribbon */}
      <div className="p-5 sm:p-6 rounded-2xl bg-white/70 dark:bg-zinc-900/60 backdrop-blur-xl border border-black/[0.06] dark:border-white/[0.08] shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          
          <div className="flex items-start sm:items-center gap-4">
            {renderProgressRing(currentProbability, currentProbability >= 70 ? '#10b981' : currentProbability >= 50 ? '#f59e0b' : '#ef4444')}
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs uppercase font-mono tracking-wider font-semibold text-emerald-800 dark:text-emerald-300 bg-emerald-500/10 px-2 py-0.5 rounded-full border border-emerald-500/20">
                  Living Financial Plan &bull; Activo
                </span>
                {scenarioImpact.activeCount > 0 && (
                  <span className="text-[11px] font-mono text-amber-700 dark:text-amber-300 bg-amber-500/10 px-2 py-0.5 rounded-full border border-amber-500/20 animate-pulse">
                    {scenarioImpact.activeCount} Escenarios Simulados
                  </span>
                )}
              </div>
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-slate-900 dark:text-white mt-1">
                Probabilidad de Éxito Patrimonial: {currentProbability}%
              </h2>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Simulación Monte Carlo (1,000 iteraciones actuariales) ajustada a las metas y contingencias del cliente.
              </p>
            </div>
          </div>

          {/* Quick Metrics Cards */}
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
            <div className="px-3.5 py-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06]">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Metas en Curso</span>
              <span className="text-sm font-bold text-slate-900 dark:text-white mt-0.5 block">
                {goals.filter(g => g.status === 'active').length} de {goals.length}
              </span>
            </div>
            <div className="px-3.5 py-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06]">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Acciones Pendientes</span>
              <span className="text-sm font-bold text-slate-900 dark:text-white mt-0.5 block">
                {recommendations.filter(r => r.status !== 'done').length} prioritarias
              </span>
            </div>
            <div className="col-span-2 sm:col-span-1 px-3.5 py-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.06]">
              <span className="text-[10px] font-mono uppercase text-slate-400 block">Impacto Escenarios</span>
              <span className={`text-sm font-bold mt-0.5 block font-mono ${
                scenarioImpact.probDelta < 0 ? 'text-rose-500' : 'text-slate-900 dark:text-white'
              }`}>
                {scenarioImpact.probDelta !== 0 ? `${scenarioImpact.probDelta}%` : 'Base Estable'}
              </span>
            </div>
          </div>

        </div>

        {/* Navigation & Filter Ribbon */}
        <div className="flex items-center justify-between gap-3 mt-6 pt-4 border-t border-black/[0.04] dark:border-white/[0.06]">
          <div className="flex items-center gap-1.5 overflow-x-auto py-0.5">
            <button
              onClick={() => { audioService.playSound('click'); setActiveFilter('all'); }}
              className={`px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer whitespace-nowrap ${
                activeFilter === 'all'
                  ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white font-semibold shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
              }`}
            >
              Todos los Elementos
            </button>
            <button
              onClick={() => { audioService.playSound('click'); setActiveFilter('goals'); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer whitespace-nowrap ${
                activeFilter === 'goals'
                  ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white font-semibold shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
              }`}
            >
              <Target className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
              <span>Metas Financieras ({goals.length})</span>
            </button>
            <button
              onClick={() => { audioService.playSound('click'); setActiveFilter('recommendations'); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer whitespace-nowrap ${
                activeFilter === 'recommendations'
                  ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white font-semibold shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
              }`}
            >
              <Zap className="w-3.5 h-3.5 text-amber-500" />
              <span>Recomendaciones Estratégicas ({recommendations.length})</span>
            </button>
            <button
              onClick={() => { audioService.playSound('click'); setActiveFilter('scenarios'); }}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium transition-all cursor-pointer whitespace-nowrap ${
                activeFilter === 'scenarios'
                  ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white font-semibold shadow-sm'
                  : 'text-slate-500 dark:text-slate-400 hover:text-slate-800 dark:hover:text-white'
              }`}
            >
              <Sliders className="w-3.5 h-3.5 text-sky-500" />
              <span>Banco de Escenarios ({PRESET_SCENARIOS.length})</span>
            </button>
          </div>

          {selectedScenarios.length > 0 && (
            <button
              onClick={() => {
                audioService.playSound('click');
                setSelectedScenarios([]);
              }}
              className="text-xs text-slate-400 hover:text-rose-500 font-medium transition-colors cursor-pointer flex items-center gap-1 shrink-0"
              title="Restablecer simulación a línea base"
            >
              <RefreshCw className="w-3 h-3" />
              <span className="hidden sm:inline">Restablecer</span>
            </button>
          )}
        </div>
      </div>

      {/* SECTION 1: Financial Goals Cards */}
      {(activeFilter === 'all' || activeFilter === 'goals') && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Target className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
              <h3 className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white uppercase font-mono">
                Metas Financieras del Cliente
              </h3>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Seguimiento Actuarial en Tiempo Real
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {goals.map((goal) => {
              const pct = Math.min(100, Math.round((goal.currentAmount / (goal.targetAmount || 1)) * 100));
              const isDone = goal.status === 'completed' || pct >= 100;

              return (
                <div
                  key={goal.id}
                  className={`p-5 rounded-2xl bg-white/70 dark:bg-zinc-900/60 backdrop-blur-xl border transition-all ${
                    isDone 
                      ? 'border-emerald-500/30 dark:border-emerald-500/20' 
                      : 'border-black/[0.06] dark:border-white/[0.08] hover:border-black/15 dark:hover:border-white/15'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        <span className="text-[10px] font-mono uppercase tracking-wider px-2 py-0.5 rounded-full bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.05] dark:border-white/[0.08] text-slate-600 dark:text-slate-400 flex items-center gap-1">
                          <Calendar className="w-3 h-3 text-slate-400" />
                          <span>{goal.targetDate}</span>
                        </span>
                        <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${
                          goal.priority === 'Alta'
                            ? 'text-rose-700 dark:text-rose-300 bg-rose-500/10 border-rose-500/20'
                            : 'text-sky-700 dark:text-sky-300 bg-sky-500/10 border-sky-500/20'
                        }`}>
                          {goal.priority}
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-white mt-2 truncate">
                        {goal.title}
                      </h4>
                    </div>

                    {/* Inline Status Toggle Button */}
                    <button
                      onClick={() => handleToggleGoalStatus(goal.id)}
                      className={`px-2.5 py-1 rounded-lg text-[11px] font-medium transition-all cursor-pointer flex items-center gap-1.5 shrink-0 ${
                        isDone
                          ? 'bg-emerald-500/15 text-emerald-800 dark:text-emerald-300 border border-emerald-500/25'
                          : goal.status === 'paused'
                          ? 'bg-amber-500/15 text-amber-800 dark:text-amber-300 border border-amber-500/25'
                          : 'bg-black/5 dark:bg-white/5 text-slate-600 dark:text-slate-300 hover:bg-black/10'
                      }`}
                      title="Alternar estado de la meta"
                    >
                      {isDone ? (
                        <>
                          <CheckCircle2 className="w-3.5 h-3.5" />
                          <span>Completada</span>
                        </>
                      ) : goal.status === 'paused' ? (
                        <>
                          <Clock className="w-3.5 h-3.5" />
                          <span>Pausada</span>
                        </>
                      ) : (
                        <>
                          <TrendingUp className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
                          <span>En Progreso</span>
                        </>
                      )}
                    </button>
                  </div>

                  {/* Sleek Linear Progress Bar */}
                  <div className="mt-4 space-y-1.5">
                    <div className="flex justify-between items-baseline text-xs font-mono">
                      <span className="font-semibold text-slate-900 dark:text-white">
                        {formatCurrency(goal.currentAmount)}
                      </span>
                      <span className="text-slate-400">
                        Meta: {formatCurrency(goal.targetAmount)} ({pct}%)
                      </span>
                    </div>

                    <div className="relative w-full h-2 rounded-full bg-slate-100 dark:bg-zinc-800/80 overflow-hidden">
                      <motion.div
                        className={`h-full rounded-full transition-all duration-500 ${
                          isDone 
                            ? 'bg-emerald-500' 
                            : pct > 50 
                            ? 'bg-gradient-to-r from-emerald-600 to-emerald-400' 
                            : 'bg-gradient-to-r from-slate-400 to-emerald-500'
                        }`}
                        initial={{ width: 0 }}
                        animate={{ width: `${pct}%` }}
                      />
                    </div>
                  </div>

                  {goal.notes && (
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-3 pt-2.5 border-t border-black/[0.04] dark:border-white/[0.05] leading-relaxed">
                      {goal.notes}
                    </p>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SECTION 2: Strategic Recommendations */}
      {(activeFilter === 'all' || activeFilter === 'recommendations') && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-amber-500" />
              <h3 className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white uppercase font-mono">
                Recomendaciones Estratégicas de Alto Impacto
              </h3>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Dictaminadas por el Motor Actuarial
            </span>
          </div>

          <div className="space-y-3">
            {recommendations.map((rec) => {
              const isExpanded = expandedRecId === rec.id;
              const isCompleted = rec.status === 'done';

              return (
                <div
                  key={rec.id}
                  className={`rounded-2xl bg-white/70 dark:bg-zinc-900/60 backdrop-blur-xl border transition-all overflow-hidden ${
                    isCompleted
                      ? 'border-emerald-500/25 bg-emerald-500/[0.015]'
                      : 'border-black/[0.06] dark:border-white/[0.08] hover:border-black/15 dark:hover:border-white/15'
                  }`}
                >
                  <div className="p-4 sm:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 flex-wrap">
                        {/* High-Signal Impact Badge */}
                        <span className={`inline-flex items-center gap-1 text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full border ${
                          rec.impactType === 'savings'
                            ? 'text-emerald-800 dark:text-emerald-300 bg-emerald-500/10 border-emerald-500/25'
                            : rec.impactType === 'score'
                            ? 'text-purple-800 dark:text-purple-300 bg-purple-500/10 border-purple-500/25'
                            : rec.impactType === 'debt'
                            ? 'text-sky-800 dark:text-sky-300 bg-sky-500/10 border-sky-500/25'
                            : 'text-amber-800 dark:text-amber-300 bg-amber-500/10 border-amber-500/25'
                        }`}>
                          <Sparkles className="w-3 h-3" />
                          <span>{rec.impact}</span>
                        </span>

                        <span className="text-[10px] font-mono uppercase text-slate-500 px-2 py-0.5 rounded-md bg-black/[0.02] dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06]">
                          Esfuerzo: {rec.effort}
                        </span>
                      </div>

                      <h4 className={`text-sm font-semibold mt-2 ${
                        isCompleted ? 'line-through text-slate-400 dark:text-slate-500' : 'text-slate-900 dark:text-white'
                      }`}>
                        {rec.title}
                      </h4>
                    </div>

                    {/* Tactile Action Buttons */}
                    <div className="flex items-center gap-2 shrink-0">
                      {/* Rationale Expander Toggle */}
                      <button
                        onClick={() => {
                          audioService.playSound('click');
                          setExpandedRecId(isExpanded ? null : rec.id);
                        }}
                        className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer flex items-center gap-1 text-xs font-medium"
                        title={isExpanded ? "Ocultar fundamentación" : "Ver fundamentación técnica"}
                      >
                        <span className="hidden sm:inline">Fundamentación</span>
                        {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                      </button>

                      {/* Consult Advisor Button */}
                      {onConsultTask && (
                        <button
                          onClick={() => {
                            audioService.playSound('click');
                            onConsultTask(rec.title, rec.impact);
                          }}
                          className="px-3 py-1.5 rounded-xl bg-black/5 dark:bg-white/5 hover:bg-black/10 dark:hover:bg-white/10 text-slate-700 dark:text-slate-200 text-xs font-medium transition-all cursor-pointer flex items-center gap-1"
                          title="Profundizar en Asesor Co-Pilot"
                        >
                          <ArrowUpRight className="w-3 h-3 text-emerald-500" />
                          <span>Consultar</span>
                        </button>
                      )}

                      {/* Status Toggle Action */}
                      <button
                        onClick={() => handleToggleRecStatus(rec.id)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all cursor-pointer flex items-center gap-1.5 active:scale-95 shadow-sm ${
                          isCompleted
                            ? 'bg-emerald-600 text-white hover:bg-emerald-500'
                            : rec.status === 'in_process'
                            ? 'bg-amber-500/20 text-amber-800 dark:text-amber-200 border border-amber-500/30'
                            : 'bg-black/5 dark:bg-white/10 text-slate-800 dark:text-slate-200 hover:bg-black/10'
                        }`}
                      >
                        {isCompleted ? (
                          <>
                            <Check className="w-3.5 h-3.5" />
                            <span>Ejecutada</span>
                          </>
                        ) : rec.status === 'in_process' ? (
                          <>
                            <Clock className="w-3.5 h-3.5" />
                            <span>En Proceso</span>
                          </>
                        ) : (
                          <>
                            <span>Marcar Lista</span>
                          </>
                        )}
                      </button>
                    </div>
                  </div>

                  {/* Smooth Accordion Rationale Expander */}
                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.2 }}
                        className="px-4 sm:px-5 pb-5 pt-1 border-t border-black/[0.04] dark:border-white/[0.06] bg-black/[0.01] dark:bg-white/[0.01]"
                      >
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-3">
                          <div className="space-y-1">
                            <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block">
                              Por Qué lo Recomienda Sherpas
                            </span>
                            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                              {rec.rationale}
                            </p>
                          </div>
                          <div className="space-y-1">
                            <span className="text-[10px] font-mono uppercase text-emerald-600 dark:text-emerald-400 font-semibold block">
                              Riesgo Mitigado / Retorno
                            </span>
                            <p className="text-xs text-slate-700 dark:text-slate-300 leading-relaxed">
                              {rec.mitigation}
                            </p>
                          </div>
                        </div>

                        {rec.steps && rec.steps.length > 0 && (
                          <div className="mt-4 pt-3 border-t border-black/[0.04] dark:border-white/[0.05]">
                            <span className="text-[10px] font-mono uppercase text-slate-400 font-semibold block mb-2">
                              Paso a Paso de Ejecución
                            </span>
                            <div className="space-y-1.5">
                              {rec.steps.map((st, idx) => (
                                <div key={idx} className="flex items-start gap-2 text-xs text-slate-600 dark:text-slate-300">
                                  <span className="w-4 h-4 rounded-full bg-black/5 dark:bg-white/10 text-slate-600 dark:text-slate-300 text-[10px] font-mono flex items-center justify-center shrink-0 mt-0.5">
                                    {idx + 1}
                                  </span>
                                  <span>{st}</span>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SECTION 3: Interactive Scenarios Bench */}
      {(activeFilter === 'all' || activeFilter === 'scenarios') && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Sliders className="w-4 h-4 text-sky-500" />
              <h3 className="text-sm font-semibold tracking-tight text-slate-900 dark:text-white uppercase font-mono">
                Simulador de Escenarios What-If
              </h3>
            </div>
            <span className="text-[11px] text-slate-400 font-mono">
              Comprueba la Resiliencia de tu Patrimonio
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {PRESET_SCENARIOS.map((sc) => {
              const isSelected = selectedScenarios.includes(sc.id);

              return (
                <div
                  key={sc.id}
                  onClick={() => handleToggleScenario(sc.id)}
                  className={`p-5 rounded-2xl backdrop-blur-xl border transition-all cursor-pointer relative overflow-hidden ${
                    isSelected
                      ? 'bg-sky-500/[0.06] dark:bg-sky-500/[0.08] border-sky-500/40 shadow-sm'
                      : 'bg-white/70 dark:bg-zinc-900/60 border-black/[0.06] dark:border-white/[0.08] hover:border-black/15 dark:hover:border-white/15'
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className={`text-[10px] font-mono uppercase px-2 py-0.5 rounded-full border ${
                          isSelected
                            ? 'text-sky-800 dark:text-sky-300 bg-sky-500/15 border-sky-500/30 font-bold'
                            : 'text-slate-500 bg-black/[0.02] dark:bg-white/[0.04] border-black/[0.04] dark:border-white/[0.06]'
                        }`}>
                          {sc.type}
                        </span>
                        <span className="text-[10px] font-mono text-rose-500 font-bold">
                          {sc.impactProbability}% Prob. Éxito
                        </span>
                      </div>
                      <h4 className="text-sm font-semibold text-slate-900 dark:text-white mt-1.5">
                        {sc.name}
                      </h4>
                      <p className="text-xs text-slate-600 dark:text-slate-400 mt-1 leading-relaxed">
                        {sc.description}
                      </p>
                    </div>

                    {/* Toggle Switch */}
                    <div
                      className={`w-10 h-6 rounded-full p-1 transition-colors duration-200 ease-in-out shrink-0 mt-1 ${
                        isSelected ? 'bg-sky-500' : 'bg-slate-200 dark:bg-zinc-700'
                      }`}
                    >
                      <div
                        className={`w-4 h-4 rounded-full bg-white shadow-sm transform transition-transform duration-200 ease-in-out ${
                          isSelected ? 'translate-x-4' : 'translate-x-0'
                        }`}
                      />
                    </div>
                  </div>

                  {/* Impact Highlights */}
                  <div className="mt-4 pt-3 border-t border-black/[0.04] dark:border-white/[0.06] flex items-center justify-between text-xs font-mono">
                    <span className="text-slate-500">Flujo Mensual:</span>
                    <span className={`font-semibold ${sc.monthlyCashflowDelta < 0 ? 'text-rose-500' : 'text-slate-700 dark:text-slate-300'}`}>
                      {sc.monthlyCashflowDelta < 0 ? `-$${Math.abs(sc.monthlyCashflowDelta)}/mes` : 'Sin variación'}
                    </span>
                  </div>

                  {isSelected && (
                    <div className="mt-3 p-2.5 rounded-xl bg-sky-500/10 border border-sky-500/20 text-[11px] text-sky-950 dark:text-sky-200 leading-relaxed">
                      <strong className="block text-sky-900 dark:text-sky-300 mb-0.5">Estrategia Preventiva:</strong>
                      {sc.mitigationPlan}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default LivingPlan;
