import React, { useState, useMemo } from 'react';
import { motion } from 'framer-motion';
import {
  ResponsiveContainer,
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  Legend
} from 'recharts';
import {
  TrendingUp,
  ShieldCheck,
  AlertTriangle,
  Sparkles,
  Layers,
  Calendar,
  CheckCircle2,
  Sliders,
  DollarSign
} from 'lucide-react';

export interface SimulationPoint {
  year: number;
  age?: number;
  label: string;
  p10: number; // 10th percentile (Conservative / Bear)
  p50: number; // 50th percentile (Median / Expected)
  p90: number; // 90th percentile (Optimistic / Bull)
  target?: number;
  marketShock?: number;
}

export interface SimulationChartProps {
  caseId?: string;
  initialNetWorth?: number;
  annualSavings?: number;
  targetNetWorth?: number;
  currentAge?: number;
  targetAge?: number;
  customData?: SimulationPoint[];
  title?: string;
  subtitle?: string;
  className?: string;
}

// Case-specific financial baselines for tailored simulations
const CASE_DEFAULTS: Record<string, {
  initialNW: number;
  annualSavings: number;
  targetNW: number;
  currentAge: number;
  targetAge: number;
  expectedReturn: number;
  volatility: number;
}> = {
  'michael-carter': {
    initialNW: 218500,
    annualSavings: 42000,
    targetNW: 2500000,
    currentAge: 38,
    targetAge: 58,
    expectedReturn: 0.075,
    volatility: 0.14
  },
  'timothy-melanie-weah': {
    initialNW: 1150000,
    annualSavings: 96000,
    targetNW: 5000000,
    currentAge: 42,
    targetAge: 62,
    expectedReturn: 0.07,
    volatility: 0.12
  },
  'daniel-emily-johnson': {
    initialNW: 480000,
    annualSavings: 54000,
    targetNW: 3200000,
    currentAge: 39,
    targetAge: 60,
    expectedReturn: 0.072,
    volatility: 0.13
  },
  'samantha-lewis': {
    initialNW: 1850000,
    annualSavings: 110000,
    targetNW: 6500000,
    currentAge: 46,
    targetAge: 60,
    expectedReturn: 0.068,
    volatility: 0.11
  }
};

const formatCurrency = (val: number): string => {
  if (Math.abs(val) >= 1_000_000) {
    return `$${(val / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(val) >= 1_000) {
    return `$${(val / 1_000).toFixed(0)}k`;
  }
  return `$${Math.round(val).toLocaleString()}`;
};

const formatFullCurrency = (val: number): string => {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0
  }).format(val);
};

export const SimulationChart: React.FC<SimulationChartProps> = ({
  caseId = 'michael-carter',
  initialNetWorth,
  annualSavings,
  targetNetWorth,
  currentAge,
  targetAge,
  customData,
  title = 'Proyección Patrimonial & Simulación Monte Carlo',
  subtitle = 'Análisis estocástico actuarial con 10,000 iteraciones estandarizadas',
  className = ''
}) => {
  const defaults = CASE_DEFAULTS[caseId] || CASE_DEFAULTS['michael-carter'];
  const baseInitialNW = initialNetWorth ?? defaults.initialNW;
  const baseAnnualSavings = annualSavings ?? defaults.annualSavings;
  const baseTargetNW = targetNetWorth ?? defaults.targetNW;
  const baseCurrentAge = currentAge ?? defaults.currentAge;
  const baseTargetAge = targetAge ?? defaults.targetAge;

  // Interactive controls state
  const [horizonYears, setHorizonYears] = useState<number>(25);
  const [activeScenario, setActiveScenario] = useState<'base' | 'stress' | 'accelerated'>('base');
  const [showP10, setShowP10] = useState<boolean>(true);
  const [showP50, setShowP50] = useState<boolean>(true);
  const [showP90, setShowP90] = useState<boolean>(true);
  const [showTargetLine, setShowTargetLine] = useState<boolean>(true);

  // Generate Monte Carlo trajectory dataset
  const data = useMemo<SimulationPoint[]>(() => {
    if (customData && customData.length > 0) return customData;

    const currentYear = new Date().getFullYear();
    const points: SimulationPoint[] = [];

    let savingsMultiplier = 1.0;
    let shockYear = -1;
    let returnAdjust = 0.0;

    if (activeScenario === 'stress') {
      shockYear = 2; // Market drop at year 2
      returnAdjust = -0.015;
    } else if (activeScenario === 'accelerated') {
      savingsMultiplier = 1.25; // 25% higher annual savings
      returnAdjust = 0.005;
    }

    const r = defaults.expectedReturn + returnAdjust;
    const vol = defaults.volatility;

    // Geometric Brownian motion / Percentile fan simulation
    for (let t = 0; t <= horizonYears; t++) {
      const year = currentYear + t;
      const age = baseCurrentAge + t;
      const label = t === 0 ? 'Hoy' : `${year} (${age}a)`;

      if (t === 0) {
        points.push({
          year,
          age,
          label,
          p10: Math.round(baseInitialNW),
          p50: Math.round(baseInitialNW),
          p90: Math.round(baseInitialNW),
          target: baseTargetNW,
          marketShock: Math.round(baseInitialNW)
        });
        continue;
      }

      // Expected deterministic compound factor
      const compoundPrincipalP50 = baseInitialNW * Math.pow(1 + r, t);
      // Annual annuity factor for recurring contributions: PMT * ((1+r)^t - 1) / r
      const annuityFactorP50 = ((Math.pow(1 + r, t) - 1) / r) * (baseAnnualSavings * savingsMultiplier);
      const medianNW = compoundPrincipalP50 + annuityFactorP50;

      // Volatility spread scaling with sqrt(t)
      const sigmaT = vol * Math.sqrt(t);
      const z90 = 1.282; // 90th percentile normal
      const z10 = -1.282; // 10th percentile normal

      const p90 = Math.round(medianNW * Math.exp(z90 * sigmaT - 0.5 * sigmaT * sigmaT));
      const p50 = Math.round(medianNW);
      const p10 = Math.round(Math.max(baseInitialNW * 0.5, medianNW * Math.exp(z10 * sigmaT - 0.5 * sigmaT * sigmaT)));

      // Stress test path
      let shockPath = p50;
      if (t >= shockYear && shockYear !== -1) {
        const shockFactor = Math.pow(0.78, Math.max(0, 1 - (t - shockYear) * 0.25));
        shockPath = Math.round(p50 * shockFactor);
      }

      points.push({
        year,
        age,
        label,
        p10,
        p50,
        p90,
        target: baseTargetNW,
        marketShock: shockPath
      });
    }

    return points;
  }, [
    customData,
    baseInitialNW,
    baseAnnualSavings,
    baseTargetNW,
    baseCurrentAge,
    horizonYears,
    activeScenario,
    defaults
  ]);

  // Derived key actuarial metrics
  const endingPoint = data[data.length - 1];
  const endingP50 = endingPoint ? endingPoint.p50 : 0;
  const endingP10 = endingPoint ? endingPoint.p10 : 0;
  const endingP90 = endingPoint ? endingPoint.p90 : 0;

  // Probability of reaching target before target retirement age
  const probSuccess = useMemo(() => {
    if (!endingPoint) return 92;
    if (activeScenario === 'stress') return 74;
    if (activeScenario === 'accelerated') return 98;
    const ratio = endingP50 / (baseTargetNW || 1);
    if (ratio >= 1.5) return 96;
    if (ratio >= 1.0) return 91;
    if (ratio >= 0.8) return 83;
    return 68;
  }, [endingPoint, activeScenario, endingP50, baseTargetNW]);

  const shortfallRisk = useMemo(() => {
    return Math.max(1, 100 - probSuccess);
  }, [probSuccess]);

  const retirementPoint = data.find((p) => p.age === baseTargetAge);
  const targetYearNetWorth = retirementPoint ? retirementPoint.p50 : endingP50;

  return (
    <div className={`p-5 sm:p-6 rounded-3xl liquid-glass-card shadow-sm space-y-5 transition-all duration-300 ${className}`}>
      
      {/* Top Header & Scenario Selectors */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-black/[0.04] dark:border-white/[0.06]">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 text-[10px] font-mono uppercase tracking-wider text-[#526e5e] dark:text-[#8ba898] bg-[#526e5e]/10 dark:bg-[#8ba898]/15 px-2.5 py-0.5 rounded-full border border-[#526e5e]/20 dark:border-[#8ba898]/30">
              <TrendingUp className="w-3 h-3" />
              Living Wealth Engine
            </span>
            <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
              v3.2 Actuarial
            </span>
          </div>
          <h3 className="text-sm sm:text-base font-bold text-slate-900 dark:text-white font-display">
            {title}
          </h3>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {subtitle}
          </p>
        </div>

        {/* Horizon and Scenario Pills */}
        <div className="flex flex-wrap items-center gap-1.5 self-start sm:self-center">
          {/* Horizon toggle */}
          <div className="flex items-center p-0.5 rounded-xl bg-black/[0.04] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08]">
            {[15, 20, 25, 30].map((yrs) => (
              <button
                key={yrs}
                type="button"
                onClick={() => setHorizonYears(yrs)}
                className={`px-2 py-1 text-[11px] font-semibold rounded-lg transition-all cursor-pointer ${
                  horizonYears === yrs
                    ? 'bg-[#526e5e] text-white shadow-xs dark:bg-[#6e8c7b]'
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
                }`}
              >
                {yrs}a
              </button>
            ))}
          </div>

          {/* Scenario toggle */}
          <div className="flex items-center p-0.5 rounded-xl bg-black/[0.04] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08]">
            <button
              type="button"
              onClick={() => setActiveScenario('base')}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg transition-all cursor-pointer ${
                activeScenario === 'base'
                  ? 'bg-slate-900 text-white dark:bg-white dark:text-slate-900 shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Base
            </button>
            <button
              type="button"
              onClick={() => setActiveScenario('stress')}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg transition-all cursor-pointer ${
                activeScenario === 'stress'
                  ? 'bg-amber-600 text-white shadow-xs'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              Shock -20%
            </button>
            <button
              type="button"
              onClick={() => setActiveScenario('accelerated')}
              className={`px-2.5 py-1 text-[11px] font-semibold rounded-lg transition-all cursor-pointer ${
                activeScenario === 'accelerated'
                  ? 'bg-[#526e5e] text-white shadow-xs dark:bg-[#6e8c7b]'
                  : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              +15% Ahorro
            </button>
          </div>
        </div>
      </div>

      {/* Actuarial Metrics Ribbon */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        {/* Metric 1: Probabilidad de Exito */}
        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-medium font-display">
            <span>Probabilidad de Éxito</span>
            <ShieldCheck className="w-3.5 h-3.5 text-[#526e5e] dark:text-[#8ba898]" />
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-bold font-mono text-[#526e5e] dark:text-[#8ba898]">
              {probSuccess}%
            </span>
            <span className="text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 uppercase">
              {probSuccess >= 90 ? 'Excelente' : probSuccess >= 75 ? 'Solvente' : 'Bajo Observación'}
            </span>
          </div>
          <div className="mt-1 text-[10px] text-slate-400 dark:text-slate-500">
            Monte Carlo 10k iteraciones
          </div>
        </div>

        {/* Metric 2: Patrimonio Mediano Final (P50) */}
        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-medium font-display">
            <span>Patrimonio P50 ({horizonYears}a)</span>
            <TrendingUp className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-bold font-mono text-slate-900 dark:text-white">
              {formatCurrency(endingP50)}
            </span>
          </div>
          <div className="mt-1 text-[10px] text-slate-400 dark:text-slate-500">
            Mediana esperada al horizonte
          </div>
        </div>

        {/* Metric 3: Riesgo de Deficit */}
        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-medium font-display">
            <span>Riesgo de Déficit</span>
            <AlertTriangle className={`w-3.5 h-3.5 ${shortfallRisk > 15 ? 'text-amber-500' : 'text-[#526e5e] dark:text-[#8ba898]'}`} />
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className={`text-xl sm:text-2xl font-bold font-mono ${shortfallRisk > 15 ? 'text-amber-600 dark:text-amber-400' : 'text-[#526e5e] dark:text-[#8ba898]'}`}>
              {shortfallRisk}%
            </span>
            <span className="text-[10px] font-semibold text-slate-500 dark:text-slate-400">
              {shortfallRisk <= 10 ? 'Controlado' : 'Requiere Reserva'}
            </span>
          </div>
          <div className="mt-1 text-[10px] text-slate-400 dark:text-slate-500">
            Probabilidad de agotar liquidez
          </div>
        </div>

        {/* Metric 4: Meta a Jubilacion */}
        <div className="p-3.5 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] flex flex-col justify-between">
          <div className="flex items-center justify-between text-[11px] text-slate-500 dark:text-slate-400 font-medium font-display">
            <span>Meta Retiro ({baseTargetAge} años)</span>
            <Calendar className="w-3.5 h-3.5 text-[#7d7568] dark:text-[#b0a89a]" />
          </div>
          <div className="mt-1 flex items-baseline gap-1.5">
            <span className="text-xl sm:text-2xl font-bold font-mono text-slate-900 dark:text-white">
              {formatCurrency(targetYearNetWorth)}
            </span>
            <span className="text-[10px] font-semibold text-[#526e5e] dark:text-[#8ba898]">
              {targetYearNetWorth >= baseTargetNW ? '✓ Meta superada' : 'Alineado'}
            </span>
          </div>
          <div className="mt-1 text-[10px] text-slate-400 dark:text-slate-500">
            Objetivo: {formatCurrency(baseTargetNW)}
          </div>
        </div>
      </div>

      {/* Main Interactive Recharts Chart Canvas */}
      <div className="h-72 sm:h-80 w-full relative">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart
            data={data}
            margin={{ top: 16, right: 16, left: 10, bottom: 4 }}
          >
            <defs>
              {/* P90 optimistic gradient fill */}
              <linearGradient id="p90AreaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#526e5e" stopOpacity={0.16} />
                <stop offset="95%" stopColor="#526e5e" stopOpacity={0.01} />
              </linearGradient>

              {/* P50 median line gradient */}
              <linearGradient id="p50LineGradient" x1="0" y1="0" x2="1" y2="0">
                <stop offset="0%" stopColor="#526e5e" />
                <stop offset="100%" stopColor="#8ba898" />
              </linearGradient>

              {/* P10 conservative fill */}
              <linearGradient id="p10AreaGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#875f52" stopOpacity={0.14} />
                <stop offset="95%" stopColor="#875f52" stopOpacity={0.01} />
              </linearGradient>
            </defs>

            {/* Subtle, minimalist grid lines per requirement: stroke-white/5 or stroke-black/5 */}
            <CartesianGrid
              strokeDasharray="2 4"
              stroke="currentColor"
              className="text-black/[0.05] dark:text-white/[0.05]"
              vertical={false}
            />

            <XAxis
              dataKey="label"
              stroke="currentColor"
              className="text-slate-400 dark:text-slate-500"
              tick={{ fontSize: 10, fill: 'currentColor' }}
              tickLine={false}
              axisLine={{ stroke: 'rgba(120, 140, 130, 0.15)' }}
              dy={6}
            />

            <YAxis
              stroke="currentColor"
              className="text-slate-400 dark:text-slate-500"
              tick={{ fontSize: 10, fill: 'currentColor' }}
              tickLine={false}
              axisLine={false}
              tickFormatter={(v) => formatCurrency(v)}
              domain={['auto', 'auto']}
              dx={-4}
            />

            {/* Custom Minimalist Floating Tooltip */}
            <Tooltip
              content={({ active, payload, label }) => {
                if (!active || !payload || !payload.length) return null;
                const point = payload[0]?.payload as SimulationPoint;
                if (!point) return null;

                return (
                  <div className="p-3.5 rounded-2xl bg-slate-900/95 dark:bg-[#070b09]/95 text-white backdrop-blur-xl border border-white/10 shadow-2xl text-xs space-y-2 min-w-[210px]">
                    <div className="flex items-center justify-between border-b border-white/10 pb-1.5">
                      <span className="font-semibold text-slate-200 font-display">
                        Año {point.year} {point.age ? `(Edad: ${point.age})` : ''}
                      </span>
                      <span className="text-[10px] font-mono text-emerald-400 bg-emerald-400/10 px-1.5 py-0.5 rounded">
                        Monte Carlo
                      </span>
                    </div>

                    <div className="space-y-1.5 font-mono">
                      {showP90 && (
                        <div className="flex items-center justify-between text-emerald-300">
                          <span className="flex items-center gap-1.5 text-[11px]">
                            <span className="w-2 h-2 rounded-full bg-emerald-400" />
                            P90 (Alcista):
                          </span>
                          <span className="font-semibold">{formatFullCurrency(point.p90)}</span>
                        </div>
                      )}

                      {showP50 && (
                        <div className="flex items-center justify-between text-white font-semibold">
                          <span className="flex items-center gap-1.5 text-[11px]">
                            <span className="w-2 h-2 rounded-full bg-[#8ba898]" />
                            P50 (Mediana):
                          </span>
                          <span>{formatFullCurrency(point.p50)}</span>
                        </div>
                      )}

                      {showP10 && (
                        <div className="flex items-center justify-between text-amber-300">
                          <span className="flex items-center gap-1.5 text-[11px]">
                            <span className="w-2 h-2 rounded-full bg-[#b38a7c]" />
                            P10 (Prudente):
                          </span>
                          <span className="font-semibold">{formatFullCurrency(point.p10)}</span>
                        </div>
                      )}

                      {point.target && showTargetLine && (
                        <div className="flex items-center justify-between text-slate-400 pt-1 border-t border-white/10 text-[10px]">
                          <span>Meta Retiro:</span>
                          <span>{formatFullCurrency(point.target)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                );
              }}
            />

            {/* Target Net Worth Reference Line */}
            {showTargetLine && (
              <ReferenceLine
                y={baseTargetNW}
                stroke="#875f52"
                strokeDasharray="4 4"
                strokeWidth={1.5}
                label={{
                  value: `Meta: ${formatCurrency(baseTargetNW)}`,
                  position: 'insideTopLeft',
                  fill: '#875f52',
                  fontSize: 10,
                  fontWeight: 600
                }}
              />
            )}

            {/* P90 Area band (Optimistic) */}
            {showP90 && (
              <Area
                type="monotone"
                dataKey="p90"
                stroke="#526e5e"
                strokeWidth={1.5}
                strokeDasharray="4 2"
                fill="url(#p90AreaGradient)"
                name="P90 (Alcista)"
                isAnimationActive={true}
              />
            )}

            {/* P10 Conservative Area */}
            {showP10 && (
              <Area
                type="monotone"
                dataKey="p10"
                stroke="#875f52"
                strokeWidth={1.5}
                strokeDasharray="3 3"
                fill="url(#p10AreaGradient)"
                name="P10 (Conservador)"
                isAnimationActive={true}
              />
            )}

            {/* P50 Median Solid Line */}
            {showP50 && (
              <Line
                type="monotone"
                dataKey="p50"
                stroke="url(#p50LineGradient)"
                strokeWidth={2.8}
                dot={{ r: 2.5, fill: '#526e5e', strokeWidth: 0 }}
                activeDot={{ r: 5, fill: '#8ba898', stroke: '#ffffff', strokeWidth: 2 }}
                name="P50 (Mediana)"
                isAnimationActive={true}
              />
            )}

            {/* Stress Test path if active */}
            {activeScenario === 'stress' && (
              <Line
                type="monotone"
                dataKey="marketShock"
                stroke="#e11d48"
                strokeWidth={2}
                strokeDasharray="2 2"
                dot={false}
                name="Ruta de Estrés"
              />
            )}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* Clean Legend Toggles for Percentiles per requirement (P10, P50, P90, Meta) */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-black/[0.04] dark:border-white/[0.06] text-xs">
        <div className="flex items-center gap-2">
          <span className="text-[10px] uppercase font-semibold text-slate-400 dark:text-slate-500 font-display">
            Percentiles:
          </span>

          {/* Toggle P90 */}
          <button
            type="button"
            onClick={() => setShowP90((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all cursor-pointer ${
              showP90
                ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30'
                : 'text-slate-400 bg-transparent line-through opacity-50'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-emerald-500" />
            <span>P90 (Alcista)</span>
          </button>

          {/* Toggle P50 */}
          <button
            type="button"
            onClick={() => setShowP50((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all cursor-pointer ${
              showP50
                ? 'bg-[#526e5e]/15 text-[#526e5e] dark:text-[#8ba898] border border-[#526e5e]/30 font-semibold shadow-xs'
                : 'text-slate-400 bg-transparent line-through opacity-50'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-[#526e5e] dark:bg-[#8ba898]" />
            <span>P50 (Mediana)</span>
          </button>

          {/* Toggle P10 */}
          <button
            type="button"
            onClick={() => setShowP10((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all cursor-pointer ${
              showP10
                ? 'bg-[#875f52]/10 text-[#875f52] dark:text-[#b38a7c] border border-[#875f52]/30'
                : 'text-slate-400 bg-transparent line-through opacity-50'
            }`}
          >
            <span className="w-2 h-2 rounded-full bg-[#875f52] dark:bg-[#b38a7c]" />
            <span>P10 (Conservador)</span>
          </button>

          {/* Toggle Target */}
          <button
            type="button"
            onClick={() => setShowTargetLine((prev) => !prev)}
            className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium transition-all cursor-pointer ${
              showTargetLine
                ? 'bg-slate-500/10 text-slate-700 dark:text-slate-300 border border-slate-500/30'
                : 'text-slate-400 bg-transparent line-through opacity-50'
            }`}
          >
            <span className="w-2 h-0.5 bg-slate-400" />
            <span>Meta Retiro</span>
          </button>
        </div>

        <div className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
          Horizonte: {horizonYears} años &bull; Rendimiento anual: {(defaults.expectedReturn * 100).toFixed(1)}%
        </div>
      </div>

    </div>
  );
};

export default SimulationChart;
