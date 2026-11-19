import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Plus, 
  Trash2, 
  CheckCircle2, 
  Circle, 
  Clock, 
  Sparkles, 
  Calendar, 
  ArrowRight, 
  ArrowLeft,
  X,
  Check,
  TrendingUp
} from 'lucide-react';
import { KanbanCard, KanbanState } from '../types';
import { audioService } from '../services/audioService';

interface KanbanBoardProps {
  kanban: KanbanState;
  onArrangeCard: (cardId: string, toStatus: 'todo' | 'in_process' | 'done', toIndex?: number) => Promise<void>;
  onAddCard: (card: Partial<KanbanCard>) => Promise<void>;
  onDeleteCard: (cardId: string) => Promise<void>;
  onConsultTask?: (taskTitle: string, taskImpact?: string) => void;
  isLoading?: boolean;
}

const CATEGORY_CONFIG: Record<string, { 
  label: string; 
  color: string; 
  bg: string; 
  border: string; 
  icon: string;
  badgeClass: string;
}> = {
  debt: { 
    label: 'Deuda', 
    color: '#bfa08f', 
    bg: 'rgba(191, 160, 143, 0.14)', 
    border: 'rgba(191, 160, 143, 0.22)', 
    icon: '💳',
    badgeClass: 'bg-[#875f52]/10 dark:bg-[#bfa08f]/20 text-[#875f52] dark:text-[#f5e5df] border-[#875f52]/20 dark:border-[#bfa08f]/30'
  },
  savings: { 
    label: 'Ahorro', 
    color: '#8ba898', 
    bg: 'rgba(139, 168, 152, 0.14)', 
    border: 'rgba(139, 168, 152, 0.22)', 
    icon: '🌱',
    badgeClass: 'bg-[#526e5e]/10 dark:bg-[#8ba898]/20 text-[#3e5648] dark:text-[#d7ebe1] border-[#526e5e]/20 dark:border-[#8ba898]/30'
  },
  investment: { 
    label: 'Inversión', 
    color: '#90acc4', 
    bg: 'rgba(144, 172, 196, 0.14)', 
    border: 'rgba(144, 172, 196, 0.22)', 
    icon: '📈',
    badgeClass: 'bg-[#4a6b82]/10 dark:bg-[#90acc4]/20 text-[#324a5c] dark:text-[#dceaf5] border-[#4a6b82]/20 dark:border-[#90acc4]/30'
  },
  insurance: { 
    label: 'Seguros', 
    color: '#aba59a', 
    bg: 'rgba(171, 165, 154, 0.14)', 
    border: 'rgba(171, 165, 154, 0.22)', 
    icon: '🛡️',
    badgeClass: 'bg-[#6d665b]/10 dark:bg-[#aba59a]/20 text-[#4d4840] dark:text-[#f0ece5] border-[#6d665b]/20 dark:border-[#aba59a]/30'
  },
  lifestyle: { 
    label: 'Presupuesto', 
    color: '#a79dae', 
    bg: 'rgba(167, 157, 174, 0.14)', 
    border: 'rgba(167, 157, 174, 0.22)', 
    icon: '🏡',
    badgeClass: 'bg-[#695d70]/10 dark:bg-[#a79dae]/20 text-[#4c4252] dark:text-[#eee8f2] border-[#695d70]/20 dark:border-[#a79dae]/30'
  },
  immediate: { 
    label: 'Prioritaria', 
    color: '#b38a7c', 
    bg: 'rgba(179, 138, 124, 0.14)', 
    border: 'rgba(179, 138, 124, 0.22)', 
    icon: '⚡',
    badgeClass: 'bg-[#875f52]/10 dark:bg-[#b38a7c]/20 text-[#875f52] dark:text-[#f9e9e4] border-[#875f52]/20 dark:border-[#b38a7c]/30'
  },
  prioritaria: { 
    label: 'Prioritaria', 
    color: '#b38a7c', 
    bg: 'rgba(179, 138, 124, 0.14)', 
    border: 'rgba(179, 138, 124, 0.22)', 
    icon: '⚡',
    badgeClass: 'bg-[#875f52]/10 dark:bg-[#b38a7c]/20 text-[#875f52] dark:text-[#f9e9e4] border-[#875f52]/20 dark:border-[#b38a7c]/30'
  },
  goal: { 
    label: 'Objetivo Maestro', 
    color: '#b0a89a', 
    bg: 'rgba(176, 168, 154, 0.14)', 
    border: 'rgba(176, 168, 154, 0.22)', 
    icon: '🎯',
    badgeClass: 'bg-[#736a5c]/10 dark:bg-[#b0a89a]/20 text-[#50493e] dark:text-[#f2eee9] border-[#736a5c]/20 dark:border-[#b0a89a]/30'
  },
  general: { 
    label: 'General', 
    color: '#94a3b8', 
    bg: 'rgba(148, 163, 184, 0.14)', 
    border: 'rgba(148, 163, 184, 0.2)', 
    icon: '📌',
    badgeClass: 'bg-slate-500/10 dark:bg-slate-400/20 text-slate-700 dark:text-slate-200 border-slate-500/20 dark:border-slate-400/30'
  },
};

const COLUMNS: { id: 'todo' | 'in_process' | 'done'; title: string; icon: React.ReactNode }[] = [
  { id: 'todo', title: 'Por Ejecutar', icon: <Circle className="w-4 h-4 text-slate-400" /> },
  { id: 'in_process', title: 'En Curso', icon: <Clock className="w-4 h-4 text-[#9c9485]" /> },
  { id: 'done', title: 'Completado', icon: <CheckCircle2 className="w-4 h-4 text-[#6e8c7b]" /> },
];

/**
 * Returns a clean, single concise impact metric without ugly semicolon soup.
 */
const formatImpactCompact = (impact?: string): string => {
  if (!impact) return '';
  const parts = impact.split(';').map(p => p.trim()).filter(Boolean);
  return parts[0] || impact;
};

/**
 * Renders structured impact in modal view with clean bullet points instead of semicolon clutter.
 */
const renderFormattedImpactDetail = (impact?: string) => {
  if (!impact) return null;
  const parts = impact.split(';').map(p => p.trim()).filter(Boolean);

  if (parts.length <= 1) {
    return (
      <div className="mb-4 p-3 rounded-2xl bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/20 text-emerald-800 dark:text-emerald-300 text-xs sm:text-sm font-medium flex items-center gap-2">
        <Sparkles className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
        <span><strong className="font-semibold">Impacto estimado:</strong> {impact}</span>
      </div>
    );
  }

  return (
    <div className="mb-4 p-3.5 rounded-2xl bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/20 space-y-2">
      <div className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300">
        <Sparkles className="w-3.5 h-3.5" />
        <span>Impacto Estimado</span>
      </div>
      <div className="space-y-1.5 pl-1">
        {parts.map((part, idx) => (
          <div key={idx} className="flex items-start gap-2 text-xs text-slate-700 dark:text-slate-200">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 mt-1.5 shrink-0" />
            <span className="leading-relaxed">{part}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export const KanbanBoard: React.FC<KanbanBoardProps> = ({
  kanban,
  onArrangeCard,
  onAddCard,
  onDeleteCard,
  onConsultTask
}) => {
  const [selectedCard, setSelectedCard] = useState<KanbanCard | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<string>('all');

  // Form state
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState<KanbanCard['category']>('savings');
  const [newImpact, setNewImpact] = useState('');
  const [newWeek, setNewWeek] = useState<number>(1);
  const [newDesc, setNewDesc] = useState('');
  const [newSteps, setNewSteps] = useState('');

  const cards = kanban?.cards || [];
  const totalCards = cards.length;
  const doneCards = cards.filter(c => c.status === 'done').length;
  const inProcessCards = cards.filter(c => c.status === 'in_process').length;
  const todoCards = cards.filter(c => c.status === 'todo').length;
  const percentCompleted = totalCards > 0 ? Math.round((doneCards / totalCards) * 100) : 0;
  const isFullyCompleted = totalCards > 0 && doneCards === totalCards;

  const goalCard = cards.find(c => c.category === 'goal');
  const immediateCard = cards.find(c => c.category === 'immediate' || c.category === 'prioritaria');

  const filteredCards = activeCategoryFilter === 'all' 
    ? cards 
    : cards.filter(c => c.category === activeCategoryFilter);

  // Helper for moving cards with audio feedback
  const handleMoveCard = async (cardId: string, toStatus: 'todo' | 'in_process' | 'done', toIndex?: number) => {
    if (toStatus === 'done') {
      audioService.playSound('task_done');
    } else {
      audioService.playSound('click');
    }
    await onArrangeCard(cardId, toStatus, toIndex);
  };

  const handleCreateCard = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle.trim()) return;

    const stepsArray = newSteps
      .split('\n')
      .map(s => s.trim())
      .filter(s => s.length > 0);

    audioService.playSound('click');

    await onAddCard({
      title: newTitle.trim(),
      category: newCategory,
      impact: newImpact.trim() || undefined,
      week: Number(newWeek) || 1,
      short_description: newDesc.trim() || newTitle.trim(),
      detailed_description: newDesc.trim() || undefined,
      steps: stepsArray.length > 0 ? stepsArray : undefined,
      status: 'todo'
    });

    setNewTitle('');
    setNewImpact('');
    setNewDesc('');
    setNewSteps('');
    setIsAddModalOpen(false);
  };

  const getNextStatus = (current: KanbanCard['status']): KanbanCard['status'] | null => {
    if (current === 'todo') return 'in_process';
    if (current === 'in_process') return 'done';
    return null;
  };

  const getPrevStatus = (current: KanbanCard['status']): KanbanCard['status'] | null => {
    if (current === 'done') return 'in_process';
    if (current === 'in_process') return 'todo';
    return null;
  };

  return (
    <div className="space-y-5">
      {/* Plan Execution Progress Bar (Inspired by Streamlit render_plan_progress) */}
      <div className="p-4 sm:p-5 rounded-3xl liquid-glass shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Left side info */}
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#8ba898] flex items-center justify-center shrink-0 border border-[#526e5e]/20 dark:border-[#6e8c7b]/30">
              <TrendingUp className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400 font-display">
                  Progreso de Ejecución del Plan
                </span>
                <span className="num-tabular text-xs font-bold text-[#526e5e] dark:text-[#8ba898]">
                  {percentCompleted}%
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-800 dark:text-white leading-tight">
                {totalCards > 0 ? (
                  <>
                    <span className="font-bold text-[#526e5e] dark:text-[#8ba898]">{doneCards}</span> de <span className="font-bold">{totalCards}</span> acciones completadas ({percentCompleted}%) · <span className="font-bold text-[#9c9485] dark:text-[#d4cbb8]">{inProcessCards}</span> en curso
                  </>
                ) : (
                  'Sin acciones planificadas'
                )}
              </p>
            </div>
          </div>

          {/* Right side celebratory badge or status pill */}
          <div className="flex items-center gap-2 self-start sm:self-center">
            {isFullyCompleted ? (
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ type: 'spring', stiffness: 400, damping: 20 }}
                className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-gradient-to-r from-emerald-500/20 via-[#6e8c7b]/25 to-emerald-500/20 border border-emerald-500/40 text-emerald-800 dark:text-emerald-300 shadow-sm shadow-emerald-500/10"
              >
                <Sparkles className="w-3.5 h-3.5 text-amber-500 dark:text-amber-400" />
                <span>¡Plan Ejecutado al 100%!</span>
                <span>🎉</span>
              </motion.div>
            ) : (
              <div className="flex items-center gap-2 flex-wrap">
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium bg-black/[0.04] dark:bg-white/[0.06] text-slate-600 dark:text-slate-300 border border-black/5 dark:border-white/5">
                  <Circle className="w-2.5 h-2.5 text-slate-400" />
                  <span>{todoCards} por ejecutar</span>
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#9c9485]/10 dark:bg-[#9c9485]/20 text-[#7a6f5e] dark:text-[#d4cbb8] border border-[#9c9485]/20 dark:border-[#9c9485]/30">
                  <Clock className="w-2.5 h-2.5" />
                  <span>{inProcessCards} en curso</span>
                </span>
                <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-medium bg-[#526e5e]/10 dark:bg-[#6e8c7b]/20 text-[#3d5a48] dark:text-[#a3c7b3] border border-[#526e5e]/20 dark:border-[#6e8c7b]/30">
                  <CheckCircle2 className="w-2.5 h-2.5 text-[#526e5e] dark:text-[#8ba898]" />
                  <span>{doneCards} completadas</span>
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Animated green gradient progress indicator bar */}
        <div className="w-full h-2.5 bg-black/[0.06] dark:bg-white/[0.08] rounded-full overflow-hidden p-0.5 border border-black/[0.04] dark:border-white/[0.06]">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-[#526e5e] via-[#6e8c7b] to-[#8ba898] dark:from-[#526e5e] dark:via-[#6e8c7b] dark:to-[#8ba898] shadow-sm relative overflow-hidden"
            initial={{ width: 0 }}
            animate={{ width: `${percentCompleted}%` }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent w-full" />
          </motion.div>
        </div>
      </div>

      {/* Master Plan & Immediate Action Hero Cards */}
      {(goalCard || immediateCard) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
          {goalCard && (
            <div className="p-4 rounded-3xl liquid-glass shadow-sm">
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="text-[10px] font-semibold text-[#875f52] dark:text-[#d8b4a0] uppercase tracking-wider flex items-center gap-1.5 font-display">
                  <span>🎯</span>
                  <span>Objetivo Maestro del Plan</span>
                </div>
                {onConsultTask && (
                  <button
                    onClick={() => onConsultTask(goalCard.title, goalCard.impact)}
                    className="flex items-center gap-1 text-[11px] font-semibold text-[#875f52] dark:text-[#d8b4a0] hover:underline cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Consultar</span>
                  </button>
                )}
              </div>
              <h4 className="text-sm font-semibold text-slate-800 dark:text-white leading-snug">{goalCard.title}</h4>
              {goalCard.short_description && goalCard.short_description !== goalCard.title && (
                <p className="text-xs text-slate-600 dark:text-slate-300 mt-1 leading-relaxed">{goalCard.short_description}</p>
              )}
            </div>
          )}

          {immediateCard && (
            <div className="p-4 rounded-3xl liquid-glass shadow-sm">
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="text-[10px] font-semibold text-[#526e5e] dark:text-[#8ba898] uppercase tracking-wider flex items-center gap-1.5 font-display">
                  <span>⚡</span>
                  <span>Acción Inmediata para Hoy</span>
                </div>
                {onConsultTask && (
                  <button
                    onClick={() => onConsultTask(immediateCard.title, immediateCard.impact)}
                    className="flex items-center gap-1 text-[11px] font-semibold text-[#526e5e] dark:text-[#8ba898] hover:underline cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Consultar</span>
                  </button>
                )}
              </div>
              <h4 className="text-sm font-semibold text-slate-800 dark:text-white leading-snug">{immediateCard.title}</h4>
              {immediateCard.impact && (
                <span className="inline-block text-[11px] font-semibold text-[#526e5e] dark:text-[#8ba898] mt-1">
                  Impacto: {formatImpactCompact(immediateCard.impact)}
                </span>
              )}
            </div>
          )}
        </div>
      )}

      {/* Top Filter and Add Task Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-1.5 flex-wrap">
          <button
            onClick={() => setActiveCategoryFilter('all')}
            className={`px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer ${
              activeCategoryFilter === 'all'
                ? 'bg-black/10 dark:bg-white/15 text-slate-900 dark:text-white shadow-sm'
                : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            Todas ({cards.length})
          </button>
          {Object.entries(CATEGORY_CONFIG).slice(0, 6).map(([catKey, style]) => {
            const count = cards.filter(c => c.category === catKey).length;
            if (count === 0) return null;
            return (
              <button
                key={catKey}
                onClick={() => setActiveCategoryFilter(catKey)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer border ${
                  activeCategoryFilter === catKey
                    ? `${style.badgeClass} shadow-sm font-bold`
                    : 'bg-black/[0.02] dark:bg-white/[0.04] text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white border-transparent'
                }`}
              >
                <span>{style.icon}</span>
                <span>{style.label}</span>
                <span className="text-[10px] opacity-75 font-mono">({count})</span>
              </button>
            );
          })}
        </div>

        <button
          onClick={() => setIsAddModalOpen(true)}
          className="flex items-center gap-1.5 px-3.5 py-1.5 text-xs font-semibold text-white bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] rounded-full shadow-sm transition-all cursor-pointer shrink-0"
        >
          <Plus className="w-3.5 h-3.5" />
          <span>Nueva Acción</span>
        </button>
      </div>

      {/* 3 Column Kanban Board (Sherpas Layout) */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5 items-start">
        {COLUMNS.map((col) => {
          const colCards = filteredCards.filter((c) => c.status === col.id);

          return (
            <div
              key={col.id}
              className="flex flex-col rounded-3xl liquid-glass p-3.5 shadow-sm min-h-[460px]"
            >
              {/* Header */}
              <div className="flex items-center justify-between px-2.5 py-2 mb-3 border-b border-black/[0.05] dark:border-white/[0.08]">
                <div className="flex items-center gap-2">
                  {col.icon}
                  <span className="text-sm font-semibold text-slate-800 dark:text-white font-display tracking-wide">{col.title}</span>
                </div>
                <span className="px-2 py-0.5 text-xs font-semibold font-mono rounded-full bg-black/[0.04] dark:bg-white/[0.08] text-slate-600 dark:text-slate-300">
                  {colCards.length}
                </span>
              </div>

              {/* Cards List */}
              <div className="space-y-3 flex-1 overflow-y-auto max-h-[calc(100vh-270px)] pr-1">
                {colCards.length === 0 ? (
                  <div className="flex flex-col items-center justify-center h-28 rounded-2xl border border-dashed border-black/10 dark:border-white/10 text-slate-500 dark:text-slate-400 text-xs">
                    Sin acciones en esta etapa
                  </div>
                ) : (
                  colCards.map((card) => {
                    const cfg = CATEGORY_CONFIG[card.category] || CATEGORY_CONFIG.general;
                    const nextSt = getNextStatus(card.status);
                    const prevSt = getPrevStatus(card.status);

                    return (
                      <div
                        key={card.id}
                        onClick={() => setSelectedCard(card)}
                        className="group relative p-3.5 rounded-2xl liquid-glass-card hover:border-[#526e5e]/40 dark:hover:border-[#8ba898]/40 shadow-sm transition-all cursor-pointer"
                      >
                        {/* Top Badges */}
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span 
                              className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-semibold uppercase tracking-wider border ${cfg.badgeClass}`}
                            >
                              <span>{cfg.icon}</span>
                              <span>{cfg.label}</span>
                            </span>
                            {card.week && (
                              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-medium bg-black/[0.04] dark:bg-white/[0.08] text-slate-600 dark:text-slate-300 border border-black/5 dark:border-white/5">
                                <Calendar className="w-2.5 h-2.5 text-slate-500 dark:text-slate-400" />
                                Sem {card.week}
                              </span>
                            )}
                          </div>

                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              onDeleteCard(card.id);
                            }}
                            title="Eliminar tarjeta"
                            className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-rose-500 rounded transition-all cursor-pointer"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>

                        {/* Title */}
                        <h4 className="text-sm font-semibold text-slate-800 dark:text-white leading-snug mb-1 group-hover:text-[#526e5e] dark:group-hover:text-[#8ba898] transition-colors font-display">
                          {card.title}
                        </h4>

                        {/* Short Description */}
                        {card.short_description && card.short_description !== card.title && (
                          <p className="text-xs text-slate-600 dark:text-slate-300 line-clamp-2 leading-relaxed mb-2">
                            {card.short_description}
                          </p>
                        )}

                        {/* Financial Impact Badge */}
                        {card.impact && (
                          <div className="mb-2 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#526e5e]/10 dark:bg-[#6e8c7b]/20 text-[#3d5a48] dark:text-[#a3c7b3] border border-[#526e5e]/20 dark:border-[#6e8c7b]/30">
                            <Sparkles className="w-3 h-3 text-[#526e5e] dark:text-[#8ba898]" />
                            <span>{formatImpactCompact(card.impact)}</span>
                          </div>
                        )}

                        {/* Footer Controls */}
                        <div className="flex items-center justify-between pt-2 border-t border-black/[0.04] dark:border-white/[0.06] mt-1 text-xs">
                          <div>
                            {prevSt && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMoveCard(card.id, prevSt);
                                }}
                                title="Mover a etapa anterior"
                                className="p-1 rounded-full text-slate-500 hover:text-slate-800 dark:text-slate-400 dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
                              >
                                <ArrowLeft className="w-3.5 h-3.5" />
                              </button>
                            )}
                          </div>

                          <div className="flex items-center gap-1.5 text-[11px] text-slate-500 dark:text-slate-400 font-mono">
                            {onConsultTask && (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  onConsultTask(card.title, card.impact);
                                }}
                                title="Consultar al Co-Pilot"
                                className="flex items-center gap-1 px-2 py-0.5 rounded-full text-[#875f52] dark:text-[#d8b4a0] hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
                              >
                                <Sparkles className="w-3 h-3" />
                                <span className="text-[10px]">Consultar</span>
                              </button>
                            )}
                            {card.steps && card.steps.length > 0 ? `${card.steps.length} pasos` : ''}
                          </div>

                          <div>
                            {nextSt ? (
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleMoveCard(card.id, nextSt);
                                }}
                                title="Avanzar etapa"
                                className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold text-[#526e5e] dark:text-[#8ba898] hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
                              >
                                <span>Avanzar</span>
                                <ArrowRight className="w-3 h-3" />
                              </button>
                            ) : (
                              <span className="flex items-center gap-1 text-xs font-semibold text-[#526e5e] dark:text-[#8ba898]">
                                <Check className="w-3.5 h-3.5" /> Hecho
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Task Details Modal */}
      <AnimatePresence>
        {selectedCard && (
          <div
            className="fixed inset-0 z-50 overflow-y-auto bg-black/45 dark:bg-black/75 backdrop-blur-md"
            onClick={() => setSelectedCard(null)}
          >
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.16, ease: 'easeOut' }}
                onClick={(e) => e.stopPropagation()}
                className="relative w-full max-w-lg transform overflow-hidden rounded-3xl liquid-glass-elevated p-6 text-left shadow-2xl transition-all max-h-[88vh] overflow-y-auto"
              >
                {(() => {
                  const selectedConfig = CATEGORY_CONFIG[selectedCard.category] || CATEGORY_CONFIG.general;
                  return (
                    <>
                      <div className="flex items-start justify-between gap-4 mb-4">
                        <div>
                          <span 
                            className={`inline-flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider border mb-2.5 ${selectedConfig.badgeClass}`}
                          >
                            <span>{selectedConfig.icon}</span>
                            <span>{selectedConfig.label}</span>
                          </span>
                          <h3 className="text-lg font-bold text-slate-900 dark:text-white font-display">{selectedCard.title}</h3>
                        </div>
                        <button
                          onClick={() => setSelectedCard(null)}
                          className="p-1.5 text-slate-400 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white rounded-lg hover:bg-black/[0.04] dark:hover:bg-white/10 cursor-pointer"
                        >
                          <X className="w-5 h-5" />
                        </button>
                      </div>

                      {renderFormattedImpactDetail(selectedCard.impact)}

                      {selectedCard.detailed_description && (
                        <div className="mb-5 text-sm text-slate-700 dark:text-slate-200 leading-relaxed liquid-glass-card p-4 rounded-2xl border border-black/5 dark:border-white/10">
                          {selectedCard.detailed_description}
                        </div>
                      )}

                      {selectedCard.steps && selectedCard.steps.length > 0 && (
                        <div className="mb-6 space-y-2">
                          <h5 className="text-xs font-semibold uppercase tracking-wider text-slate-600 dark:text-slate-400">
                            Pasos de ejecución secuencial
                          </h5>
                          <div className="space-y-2">
                            {selectedCard.steps.map((st, i) => (
                              <div key={i} className="flex items-start gap-2.5 p-3 rounded-2xl liquid-glass-card text-xs text-slate-700 dark:text-slate-200 border border-black/5 dark:border-white/10">
                                <span className="flex items-center justify-center w-5 h-5 rounded-full bg-[#526e5e]/15 dark:bg-[#6e8c7b]/25 text-[#526e5e] dark:text-[#8ba898] text-[10px] font-bold shrink-0 mt-0.5">
                                  {i + 1}
                                </span>
                                <span className="leading-relaxed">{st}</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      <div className="flex items-center justify-between pt-4 border-t border-black/[0.06] dark:border-white/10">
                        <button
                          onClick={() => {
                            onDeleteCard(selectedCard.id);
                            setSelectedCard(null);
                          }}
                          className="text-xs font-semibold text-rose-600 hover:text-rose-700 dark:text-rose-400 dark:hover:text-rose-300 cursor-pointer"
                        >
                          Eliminar Acción
                        </button>

                        <div className="flex items-center gap-2">
                          {onConsultTask && (
                            <button
                              onClick={() => {
                                onConsultTask(selectedCard.title, selectedCard.impact);
                                setSelectedCard(null);
                              }}
                              className="px-3.5 py-2 text-xs font-semibold text-[#875f52] dark:text-[#d8b4a0] bg-[#875f52]/10 dark:bg-[#875f52]/20 hover:bg-[#875f52]/20 dark:hover:bg-[#875f52]/30 border border-[#875f52]/20 dark:border-[#875f52]/40 rounded-xl transition-all cursor-pointer flex items-center gap-1.5"
                            >
                              <Sparkles className="w-3.5 h-3.5 text-[#875f52] dark:text-[#d8b4a0]" />
                              <span>Consultar Asesor</span>
                            </button>
                          )}
                          {selectedCard.status !== 'done' && (
                            <button
                              onClick={async () => {
                                await handleMoveCard(selectedCard.id, 'done');
                                setSelectedCard(null);
                              }}
                              className="px-4 py-2 text-xs font-semibold text-white bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] rounded-xl shadow-sm transition-all cursor-pointer"
                            >
                              Marcar Completada
                            </button>
                          )}
                          <button
                            onClick={() => setSelectedCard(null)}
                            className="px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-200 hover:text-slate-900 dark:hover:text-white bg-black/[0.04] dark:bg-white/[0.08] hover:bg-black/10 dark:hover:bg-white/15 rounded-xl transition-all border border-black/5 dark:border-white/10 cursor-pointer"
                          >
                            Cerrar
                          </button>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>

      {/* Add Task Modal */}
      <AnimatePresence>
        {isAddModalOpen && (
          <div
            className="fixed inset-0 z-50 overflow-y-auto bg-black/45 dark:bg-black/75 backdrop-blur-md"
            onClick={() => setIsAddModalOpen(false)}
          >
            <div className="flex min-h-full items-center justify-center p-4 text-center">
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.16, ease: 'easeOut' }}
                onClick={(e) => e.stopPropagation()}
                className="relative w-full max-w-md transform overflow-hidden rounded-3xl liquid-glass-elevated p-6 text-left shadow-2xl transition-all max-h-[88vh] overflow-y-auto"
              >
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-base font-bold text-slate-900 dark:text-white font-display">Añadir Nueva Acción al Plan</h3>
                  <button
                    onClick={() => setIsAddModalOpen(false)}
                    className="p-1.5 text-slate-400 hover:text-slate-800 dark:text-slate-300 dark:hover:text-white rounded-lg hover:bg-black/[0.04] dark:hover:bg-white/10 cursor-pointer"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleCreateCard} className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Título de la acción</label>
                    <input
                      type="text"
                      required
                      value={newTitle}
                      onChange={(e) => setNewTitle(e.target.value)}
                      placeholder="Ej: Amortizar saldo Amex con bonus"
                      className="w-full px-3.5 py-2.5 text-sm bg-black/[0.03] dark:bg-[#0c121d] border border-black/10 dark:border-white/15 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#526e5e]/30 dark:focus:ring-[#6e8c7b]/40 focus:border-[#526e5e] dark:focus:border-[#6e8c7b] transition-all"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Categoría</label>
                      <select
                        value={newCategory}
                        onChange={(e) => setNewCategory(e.target.value as any)}
                        className="w-full px-3.5 py-2.5 text-sm bg-white dark:bg-[#0c121d] border border-black/10 dark:border-white/15 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#526e5e]/30 dark:focus:ring-[#6e8c7b]/40 focus:border-[#526e5e] dark:focus:border-[#6e8c7b]"
                      >
                        <option value="debt" className="bg-white text-slate-900 dark:bg-[#0c121d] dark:text-white">Deuda</option>
                        <option value="savings" className="bg-white text-slate-900 dark:bg-[#0c121d] dark:text-white">Ahorro</option>
                        <option value="investment" className="bg-white text-slate-900 dark:bg-[#0c121d] dark:text-white">Inversión</option>
                        <option value="insurance" className="bg-white text-slate-900 dark:bg-[#0c121d] dark:text-white">Seguros</option>
                        <option value="lifestyle" className="bg-white text-slate-900 dark:bg-[#0c121d] dark:text-white">Presupuesto</option>
                        <option value="immediate" className="bg-white text-slate-900 dark:bg-[#0c121d] dark:text-white">Prioritaria</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Semana Objetivo</label>
                      <input
                        type="number"
                        min="1"
                        max="52"
                        value={newWeek}
                        onChange={(e) => setNewWeek(Number(e.target.value))}
                        className="w-full px-3.5 py-2.5 text-sm bg-black/[0.03] dark:bg-[#0c121d] border border-black/10 dark:border-white/15 rounded-xl text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-[#526e5e]/30 dark:focus:ring-[#6e8c7b]/40 focus:border-[#526e5e] dark:focus:border-[#6e8c7b]"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Impacto financiero estimado</label>
                    <input
                      type="text"
                      value={newImpact}
                      onChange={(e) => setNewImpact(e.target.value)}
                      placeholder="Ej: +$450/mes de flujo libre"
                      className="w-full px-3.5 py-2.5 text-sm bg-black/[0.03] dark:bg-[#0c121d] border border-black/10 dark:border-white/15 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#526e5e]/30 dark:focus:ring-[#6e8c7b]/40 focus:border-[#526e5e] dark:focus:border-[#6e8c7b] transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Descripción</label>
                    <textarea
                      rows={2}
                      value={newDesc}
                      onChange={(e) => setNewDesc(e.target.value)}
                      placeholder="Motivación y detalles estratégicos..."
                      className="w-full px-3.5 py-2.5 text-sm bg-black/[0.03] dark:bg-[#0c121d] border border-black/10 dark:border-white/15 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#526e5e]/30 dark:focus:ring-[#6e8c7b]/40 focus:border-[#526e5e] dark:focus:border-[#6e8c7b] transition-all"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1.5">Pasos secuenciales (uno por línea)</label>
                    <textarea
                      rows={3}
                      value={newSteps}
                      onChange={(e) => setNewSteps(e.target.value)}
                      placeholder="1. Revisar saldo disponible&#10;2. Ejecutar transferencia&#10;3. Confirmar cancelación"
                      className="w-full px-3.5 py-2.5 text-sm bg-black/[0.03] dark:bg-[#0c121d] border border-black/10 dark:border-white/15 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-[#526e5e]/30 dark:focus:ring-[#6e8c7b]/40 focus:border-[#526e5e] dark:focus:border-[#6e8c7b] transition-all"
                    />
                  </div>

                  <div className="flex items-center justify-end gap-2 pt-2">
                    <button
                      type="button"
                      onClick={() => setIsAddModalOpen(false)}
                      className="px-4 py-2 text-xs font-semibold text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white bg-black/[0.04] dark:bg-white/[0.08] hover:bg-black/10 dark:hover:bg-white/15 rounded-xl transition-all border border-black/5 dark:border-white/10 cursor-pointer"
                    >
                      Cancelar
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 text-xs font-semibold text-white bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] rounded-xl shadow-sm transition-all cursor-pointer"
                    >
                      Guardar Acción
                    </button>
                  </div>
                </form>
              </motion.div>
            </div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default KanbanBoard;
