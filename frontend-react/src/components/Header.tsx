import React from 'react';
import { 
  ChevronDown,
  RotateCcw,
  FileText,
  Compass,
  Sun,
  Moon,
  HelpCircle,
  Volume2,
  VolumeX
} from 'lucide-react';
import { CaseSummary } from '../types';

interface HeaderProps {
  cases: CaseSummary[];
  activeCaseId: string;
  onSelectCase: (caseId: string) => void;
  onResetPlan: () => Promise<void>;
  onToggleInsights: () => void;
  isInitializing: boolean;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onOpenTutorial: () => void;
  soundEnabled: boolean;
  onToggleSound: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  cases,
  activeCaseId,
  onSelectCase,
  onResetPlan,
  onToggleInsights,
  isInitializing,
  theme,
  onToggleTheme,
  onOpenTutorial,
  soundEnabled,
  onToggleSound
}) => {
  const activeCase = cases.find(c => c.id === activeCaseId) || cases[0];
  const score = activeCase?.score ?? 0;

  const getScoreBadge = (sc: number) => {
    if (sc < 40) return { label: 'Vulnerable', dot: 'bg-rose-500', text: 'text-rose-500 dark:text-rose-400' };
    if (sc < 70) return { label: 'Consolidación', dot: 'bg-amber-500', text: 'text-amber-500 dark:text-amber-400' };
    return { label: 'Resiliente', dot: 'bg-emerald-500', text: 'text-emerald-500 dark:text-emerald-400' };
  };

  const status = getScoreBadge(score);

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-white/60 dark:bg-slate-900/40 border-b border-zinc-200/80 dark:border-white/[0.08] px-4 lg:px-8 py-2.5 transition-colors duration-300">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        
        {/* Brand & Micro-Indicator */}
        <div className="flex items-center gap-3">
          <div 
            className="relative flex items-center justify-center w-8 h-8 rounded-xl bg-emerald-500/[0.08] dark:bg-emerald-500/[0.12] border border-emerald-500/20 shadow-sm text-emerald-600 dark:text-emerald-400 transition-transform duration-200 hover:scale-[1.03]"
            title="Sherpas Wealth - Living Financial Plan"
          >
            <Compass className="w-4 h-4" />
            {/* Ambient Micro-indicator dot */}
            <span className="absolute -top-0.5 -right-0.5 flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-60" />
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500" />
            </span>
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-[#f8fafc] font-display">
              Sherpas <span className="text-slate-400 dark:text-zinc-400 font-light">Wealth</span>
            </span>
            <span className="hidden sm:inline-flex items-center gap-1 px-2 py-0.5 text-[10px] font-mono tracking-wider uppercase rounded-full bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border border-emerald-500/20">
              Living Plan
            </span>
          </div>
        </div>

        {/* Center: Minimalist Client Persona Selector & Tools */}
        <div className="flex items-center gap-1.5">
          <div className="relative">
            <select
              value={activeCaseId}
              onChange={(e) => onSelectCase(e.target.value)}
              className="appearance-none bg-black/[0.03] dark:bg-white/[0.05] hover:bg-black/[0.05] dark:hover:bg-white/[0.08] text-slate-800 dark:text-zinc-200 text-xs font-medium pl-3 pr-7 py-1.5 rounded-full border border-zinc-200/80 dark:border-white/[0.08] focus:outline-none focus:border-emerald-500/50 cursor-pointer transition-all duration-200"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id} className="bg-white dark:bg-[#0d120e] text-slate-800 dark:text-[#f8fafc]">
                  {c.title} &bull; Score {c.score}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          <button
            onClick={onToggleInsights}
            title="Ver dossier confidencial y diagnóstico"
            className="glass-button flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-700 dark:text-zinc-300 hover:text-slate-900 dark:hover:text-white rounded-full transition-all duration-200 cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="hidden sm:inline">Dossier</span>
          </button>

          <button
            onClick={onOpenTutorial}
            title="Abrir tutorial interactivo del plan"
            className="glass-button flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-700 dark:text-zinc-300 hover:text-slate-900 dark:hover:text-white rounded-full transition-all duration-200 cursor-pointer"
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-500 dark:text-zinc-400" />
            <span className="hidden sm:inline">Tutorial</span>
          </button>
        </div>

        {/* Right: Audio Indicator, Score Pill, Theme Toggle & Recalculate */}
        <div className="flex items-center gap-2">
          {/* Audio Status Indicator */}
          <button
            onClick={onToggleSound}
            title={soundEnabled ? 'Silenciar efectos sonoros' : 'Activar efectos sonoros'}
            aria-label="Alternar audio"
            className="glass-button p-1.5 rounded-full relative text-slate-600 dark:text-zinc-300 hover:text-slate-900 dark:hover:text-white transition-all duration-200 cursor-pointer"
          >
            {soundEnabled ? (
              <>
                <Volume2 className="w-4 h-4 text-emerald-500 dark:text-emerald-400" />
                <span className="absolute bottom-1 right-1 w-1 h-1 rounded-full bg-emerald-500 animate-pulse" />
              </>
            ) : (
              <VolumeX className="w-4 h-4 text-zinc-400" />
            )}
          </button>

          {/* Minimalist Health Score */}
          <div 
            className="glass-card flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border border-zinc-200/80 dark:border-white/[0.08]"
            title={`Salud Financiera: ${status.label}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${status.dot} animate-pulse`} />
            <span className="num-tabular font-semibold text-slate-800 dark:text-zinc-200">{score}</span>
            <span className="text-[10px] text-slate-400 dark:text-zinc-500 hidden md:inline font-mono">/100</span>
          </div>

          {/* Discrete Theme Toggle Button */}
          <button
            onClick={onToggleTheme}
            title={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
            aria-label="Alternar tema claro/oscuro"
            className="glass-button p-1.5 rounded-full text-slate-600 dark:text-zinc-300 hover:text-slate-900 dark:hover:text-white transition-all duration-200 cursor-pointer"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-zinc-300 hover:text-amber-400 transition-colors" />
            ) : (
              <Moon className="w-4 h-4 text-emerald-700 hover:text-emerald-800 transition-colors" />
            )}
          </button>

          {/* Recalculate Button */}
          <button
            onClick={onResetPlan}
            disabled={isInitializing}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-medium text-white bg-emerald-600 hover:bg-emerald-500 dark:bg-emerald-600/90 dark:hover:bg-emerald-500 rounded-full shadow-sm transition-all duration-200 active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0"
          >
            <RotateCcw className={`w-3.5 h-3.5 ${isInitializing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{isInitializing ? 'Calculando...' : 'Recalcular'}</span>
          </button>
        </div>

      </div>
    </header>
  );
};

export default Header;
