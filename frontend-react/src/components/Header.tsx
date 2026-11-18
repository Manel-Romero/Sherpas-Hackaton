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
    if (sc < 40) return { label: 'Vulnerable', dot: 'bg-[#a17a6d]', text: 'text-[#a17a6d]' };
    if (sc < 70) return { label: 'Consolidación', dot: 'bg-[#9c9485]', text: 'text-[#9c9485]' };
    return { label: 'Resiliente', dot: 'bg-[#6e8c7b]', text: 'text-[#6e8c7b]' };
  };

  const status = getScoreBadge(score);

  return (
    <header className="sticky top-0 z-40 w-full liquid-glass px-4 lg:px-8 py-2.5 transition-colors duration-300">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-3">
        
        {/* Brand */}
        <div className="flex items-center gap-3">
          <div 
            className="flex items-center justify-center w-8 h-8 rounded-xl bg-black/[0.025] dark:bg-white/[0.06] border border-black/[0.06] dark:border-white/10 shadow-sm text-slate-800 dark:text-slate-200"
            title="Sherpas Wealth Living Plan"
          >
            <Compass className="w-4 h-4 text-[#526e5e] dark:text-[#8ba898]" />
          </div>

          <div className="flex items-center gap-2">
            <span className="text-sm font-semibold tracking-tight text-slate-900 dark:text-[#f8fafc] font-display">
              Sherpas <span className="text-[#526e5e] dark:text-[#8ba898] font-normal">Wealth</span>
            </span>
            <span className="hidden sm:inline-flex px-2 py-0.5 text-[10px] font-medium tracking-wide rounded-full bg-black/[0.03] dark:bg-white/[0.05] text-slate-600 dark:text-slate-400 border border-black/[0.04] dark:border-white/[0.06]">
              Living Plan
            </span>
          </div>
        </div>

        {/* Center: Minimalist Case Selector */}
        <div className="flex items-center gap-1.5">
          <div className="relative">
            <select
              value={activeCaseId}
              onChange={(e) => onSelectCase(e.target.value)}
              className="appearance-none bg-black/[0.025] dark:bg-white/[0.05] hover:bg-black/[0.05] dark:hover:bg-white/[0.08] text-slate-800 dark:text-slate-200 text-xs font-medium pl-3 pr-7 py-1.5 rounded-full border border-black/[0.06] dark:border-white/10 focus:outline-none focus:border-[#526e5e] dark:focus:border-[#8ba898] cursor-pointer transition-all"
            >
              {cases.map((c) => (
                <option key={c.id} value={c.id} className="bg-white dark:bg-[#121620] text-slate-800 dark:text-[#f8fafc]">
                  {c.title} &bull; Score {c.score}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          <button
            onClick={onToggleInsights}
            title="Ver dossier confidencial y diagnóstico"
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-black/[0.025] dark:bg-white/[0.05] hover:bg-black/[0.05] dark:hover:bg-white/[0.08] rounded-full border border-black/[0.06] dark:border-white/10 transition-colors cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
            <span className="hidden sm:inline">Dossier</span>
          </button>

          <button
            onClick={onOpenTutorial}
            title="Abrir tutorial interactivo del plan"
            className="flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-black/[0.025] dark:bg-white/[0.05] hover:bg-black/[0.05] dark:hover:bg-white/[0.08] rounded-full border border-black/[0.06] dark:border-white/10 transition-colors cursor-pointer"
          >
            <HelpCircle className="w-3.5 h-3.5 text-[#526e5e] dark:text-[#8ba898]" />
            <span className="hidden sm:inline">Tutorial</span>
          </button>
        </div>

        {/* Right: Score, Sound, Theme Toggle & Recalculate */}
        <div className="flex items-center gap-2">
          {/* Sound FX Toggle */}
          <button
            onClick={onToggleSound}
            title={soundEnabled ? 'Silenciar efectos sonoros' : 'Activar efectos sonoros'}
            aria-label="Alternar audio"
            className="p-1.5 rounded-full text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-black/[0.025] dark:bg-white/[0.05] hover:bg-black/[0.05] dark:hover:bg-white/[0.08] border border-black/[0.05] dark:border-white/10 transition-all cursor-pointer"
          >
            {soundEnabled ? (
              <Volume2 className="w-4 h-4 text-[#526e5e] dark:text-[#8ba898]" />
            ) : (
              <VolumeX className="w-4 h-4 text-slate-400" />
            )}
          </button>

          {/* Minimalist Health Score */}
          <div 
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium bg-black/[0.025] dark:bg-white/[0.05] border border-black/[0.05] dark:border-white/10"
            title={`Salud Financiera: ${status.label}`}
          >
            <span className={`w-2 h-2 rounded-full ${status.dot} animate-pulse`} />
            <span className="font-mono font-semibold text-slate-800 dark:text-slate-200">{score}</span>
            <span className="text-[10px] text-slate-400 hidden md:inline">/100</span>
          </div>

          {/* Theme Toggle Button */}
          <button
            onClick={onToggleTheme}
            title={theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro'}
            aria-label="Alternar tema claro/oscuro"
            className="p-1.5 rounded-full text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-black/[0.025] dark:bg-white/[0.05] hover:bg-black/[0.05] dark:hover:bg-white/[0.08] border border-black/[0.05] dark:border-white/10 transition-all cursor-pointer"
          >
            {theme === 'dark' ? (
              <Sun className="w-4 h-4 text-[#9c9485] transition-transform hover:rotate-45" />
            ) : (
              <Moon className="w-4 h-4 text-[#526e5e] transition-transform hover:-rotate-12" />
            )}
          </button>

          {/* Recalculate Button */}
          <button
            onClick={onResetPlan}
            disabled={isInitializing}
            className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] rounded-full shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer shrink-0"
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
