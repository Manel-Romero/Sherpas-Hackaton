import React from 'react';
import { 
  ChevronDown,
  RotateCcw,
  Compass,
  Sun,
  Moon
} from 'lucide-react';
import { CaseSummary } from '../types';

interface HeaderProps {
  cases: CaseSummary[];
  activeCaseId: string;
  onSelectCase: (caseId: string) => void;
  onResetPlan: () => Promise<void>;
  onToggleInsights?: () => void;
  isInitializing: boolean;
  theme: 'light' | 'dark';
  onToggleTheme: () => void;
  onOpenTutorial?: () => void;
  soundEnabled?: boolean;
  onToggleSound?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  cases,
  activeCaseId,
  onSelectCase,
  onResetPlan,
  isInitializing,
  theme,
  onToggleTheme
}) => {
  const activeCase = cases.find(c => c.id === activeCaseId) || cases[0];
  const score = activeCase?.score ?? 0;

  const getScoreBadge = (sc: number) => {
    if (sc < 40) return { label: 'Vulnerable', dot: 'bg-rose-500' };
    if (sc < 70) return { label: 'Consolidación', dot: 'bg-amber-500' };
    return { label: 'Resiliente', dot: 'bg-emerald-500' };
  };

  const status = getScoreBadge(score);

  return (
    <header className="sticky top-0 z-40 w-full backdrop-blur-xl bg-white/70 dark:bg-[#070b09]/80 border-b border-zinc-200/70 dark:border-white/[0.06] px-4 lg:px-8 py-2.5 transition-colors duration-300">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        
        {/* Brand */}
        <div className="flex items-center gap-2.5">
          <div 
            className="flex items-center justify-center w-8 h-8 rounded-xl bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400"
            title="Sherpas Wealth"
          >
            <Compass className="w-4 h-4" />
          </div>

          <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-[#f8fafc]">
            Sherpas <span className="text-slate-400 dark:text-zinc-500 font-normal">Wealth</span>
          </span>
        </div>

        {/* Center: Clean Case Persona Selector */}
        <div className="flex items-center">
          <div className="relative">
            <select
              value={activeCaseId}
              onChange={(e) => onSelectCase(e.target.value)}
              className="appearance-none bg-black/[0.03] dark:bg-white/[0.05] hover:bg-black/[0.05] dark:hover:bg-white/[0.08] text-slate-800 dark:text-zinc-200 text-xs font-medium pl-3 pr-7 py-1.5 rounded-full border border-zinc-200/70 dark:border-white/[0.08] focus:outline-none focus:border-emerald-500/50 cursor-pointer transition-colors"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id} className="bg-white dark:bg-[#0d120e] text-slate-800 dark:text-[#f8fafc]">
                  {c.title}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3 h-3 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>
        </div>

        {/* Right: Score, Theme & Recalculate */}
        <div className="flex items-center gap-2">
          {/* Health Score Pill */}
          <div 
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-black/[0.03] dark:bg-white/[0.05] border border-zinc-200/70 dark:border-white/[0.06]"
            title={`Salud Financiera: ${status.label}`}
          >
            <span className={`w-1.5 h-1.5 rounded-full ${status.dot}`} />
            <span className="font-semibold text-slate-800 dark:text-zinc-200">{score}</span>
            <span className="text-[10px] text-slate-400 dark:text-zinc-500 font-mono">/100</span>
          </div>

          {/* Theme Toggle */}
          <button
            onClick={onToggleTheme}
            title={theme === 'dark' ? 'Modo claro' : 'Modo oscuro'}
            aria-label="Alternar tema"
            className="p-1.5 rounded-full text-slate-500 dark:text-zinc-400 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-zinc-400 hover:text-amber-400 transition-colors" />
            ) : (
              <Moon className="w-4 h-4 text-slate-600 hover:text-slate-900 transition-colors" />
            )}
          </button>

          {/* Recalculate Button */}
          <button
            onClick={onResetPlan}
            disabled={isInitializing}
            title="Recalcular proyecciones"
            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-emerald-600/90 hover:bg-emerald-600 dark:bg-emerald-600/80 dark:hover:bg-emerald-500 rounded-full shadow-xs transition-colors active:scale-[0.98] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0"
          >
            <RotateCcw className={`w-3 h-3 ${isInitializing ? 'animate-spin' : ''}`} />
            <span className="hidden sm:inline">{isInitializing ? 'Calculando...' : 'Recalcular'}</span>
          </button>
        </div>

      </div>
    </header>
  );
};

export default Header;
