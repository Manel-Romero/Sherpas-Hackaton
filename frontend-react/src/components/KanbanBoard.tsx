import React, { useState, useEffect } from 'react';
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
  TrendingUp,
  Target
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
  autoOpenCardId?: string | null;
  onClearAutoOpenCard?: () => void;
}

const CATEGORY_CONFIG: Record<string, { 
  label: string; 
  color: string; 
  bg: string; 
  border: string; 
  badgeClass: string;
}> = {
  debt: { 
    label: 'Deuda', 
    color: '#c97a63', 
    bg: 'rgba(201, 122, 99, 0.12)', 
    border: 'rgba(201, 122, 99, 0.25)', 
    badgeClass: 'bg-[#c97a63]/10 dark:bg-[#c97a63]/20 text-[#c97a63] dark:text-[#f5d7cf] border-[#c97a63]/25'
  },
  savings: { 
    label: 'Ahorro', 
    color: '#059669', 
    bg: 'rgba(5, 150, 105, 0.12)', 
    border: 'rgba(5, 150, 105, 0.25)', 
    badgeClass: 'bg-[#059669]/10 dark:bg-[#059669]/20 text-[#059669] dark:text-[#a7f3d0] border-[#059669]/25'
  },
  investment: { 
    label: 'Inversión', 
    color: '#2563eb', 
    bg: 'rgba(37, 99, 235, 0.12)', 
    border: 'rgba(37, 99, 235, 0.25)', 
    badgeClass: 'bg-[#2563eb]/10 dark:bg-[#2563eb]/20 text-[#2563eb] dark:text-[#bfdbfe] border-[#2563eb]/25'
  },
  insurance: { 
    label: 'Seguros', 
    color: '#7c3aed', 
    bg: 'rgba(124, 58, 237, 0.12)', 
    border: 'rgba(124, 58, 237, 0.25)', 
    badgeClass: 'bg-[#7c3aed]/10 dark:bg-[#7c3aed]/20 text-[#7c3aed] dark:text-[#ddd6fe] border-[#7c3aed]/25'
  },
  lifestyle: { 
    label: 'Presupuesto', 
    color: '#0891b2', 
    bg: 'rgba(8, 145, 178, 0.12)', 
    border: 'rgba(8, 145, 178, 0.25)', 
    badgeClass: 'bg-[#0891b2]/10 dark:bg-[#0891b2]/20 text-[#0891b2] dark:text-[#a5f3fc] border-[#0891b2]/25'
  },
  immediate: { 
    label: 'Prioritaria', 
    color: '#ea580c', 
    bg: 'rgba(234, 88, 12, 0.12)', 
    border: 'rgba(234, 88, 12, 0.25)', 
    badgeClass: 'bg-[#ea580c]/10 dark:bg-[#ea580c]/20 text-[#ea580c] dark:text-[#fed7aa] border-[#ea580c]/25'
  },
  prioritaria: { 
    label: 'Prioritaria', 
    color: '#ea580c', 
    bg: 'rgba(234, 88, 12, 0.12)', 
    border: 'rgba(234, 88, 12, 0.25)', 
    badgeClass: 'bg-[#ea580c]/10 dark:bg-[#ea580c]/20 text-[#ea580c] dark:text-[#fed7aa] border-[#ea580c]/25'
  },
  goal: { 
    label: 'Objetivo Maestro', 
    color: '#d97706', 
    bg: 'rgba(217, 119, 6, 0.12)', 
    border: 'rgba(217, 119, 6, 0.25)', 
    badgeClass: 'bg-[#d97706]/10 dark:bg-[#d97706]/20 text-[#d97706] dark:text-[#fde68a] border-[#d97706]/25'
  },
  general: { 
    label: 'General', 
    color: '#64748b', 
    bg: 'rgba(100, 116, 139, 0.12)', 
    border: 'rgba(100, 116, 139, 0.25)', 
    badgeClass: 'bg-slate-500/10 dark:bg-slate-400/20 text-slate-700 dark:text-slate-200 border-slate-500/20'
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
  onConsultTask,
  autoOpenCardId,
  onClearAutoOpenCard
}) => {
  const [selectedCard, setSelectedCard] = useState<KanbanCard | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [activeCategoryFilter, setActiveCategoryFilter] = useState<string>('all');

  const cards = kanban?.cards || [];

  // Auto-open requested card (e.g. from tutorial "Empezar por la primera tarea")
  useEffect(() => {
    if (autoOpenCardId && cards.length > 0) {
      const target = cards.find(c => c.id === autoOpenCardId) || cards.find(c => c.status === 'todo') || cards[0];
      if (target) {
        setSelectedCard(target);
        onClearAutoOpenCard?.();
      }
    }
  }, [autoOpenCardId, cards, onClearAutoOpenCard]);

  // Form state
  const [newTitle, setNewTitle] = useState('');
  const [newCategory, setNewCategory] = useState<KanbanCard['category']>('savings');
  const [newImpact, setNewImpact] = useState('');
  const [newWeek, setNewWeek] = useState<number>(1);
  const [newDesc, setNewDesc] = useState('');
  const [newSteps, setNewSteps] = useState('');

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
      {/* Plan Execution Progress Bar */}
      <div className="p-4 sm:p-5 rounded-3xl liquid-glass shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          {/* Left side info */}
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-2xl bg-[#526e5e]/15 dark:bg-[#6e8c7b]/20 text-[#526e5e] dark:text-[#8ba898] flex items-center justify-center shrink-0 border border-[#526e5e]/20 dark:border-[#6e8c7b]/30">
              <TrendingUp className="w-4 h-4" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 dark:text-slate-400 font-display">
                  Progreso del Plan
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-800 dark:text-white leading-tight mt-0.5">
                {totalCards > 0 ? (
                  <>
                    <span className="font-bold text-[#526e5e] dark:text-[#8ba898]">{doneCards}</span> / {totalCards} ({percentCompleted}%)
                  </>
                ) : (
                  'Sin acciones'
                )}
              </p>
            </div>
          </div>

          {/* Right side celebratory badge */}
          <div className="flex items-center gap-2 self-start sm:self-center">
            {isFullyCompleted && (
              <motion.div
                initial={{ scale: 0.9, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-emerald-500/15 border border-emerald-500/30 text-emerald-800 dark:text-emerald-300"
              >
                <CheckCircle2 className="w-3.5 h-3.5" />
                <span>100% completado</span>
              </motion.div>
            )}
          </div>
        </div>

        {/* Animated green gradient progress indicator bar */}
        <div className="w-full h-2 bg-black/[0.06] dark:bg-white/[0.08] rounded-full overflow-hidden p-0.5 border border-black/[0.04] dark:border-white/[0.06]">
          <motion.div
            className="h-full rounded-full bg-gradient-to-r from-[#526e5e] via-[#6e8c7b] to-[#8ba898] shadow-sm relative overflow-hidden"
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
            <div 
              style={{ borderColor: '#d9770635', boxShadow: '0 0 14px #d9770612' }}
              className="p-4 rounded-3xl liquid-glass shadow-xs border"
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="text-[10px] font-semibold text-amber-700 dark:text-amber-300 uppercase tracking-wider flex items-center gap-1.5 font-display">
                  <Target className="w-3.5 h-3.5 text-amber-600 dark:text-amber-400" />
                  <span>Objetivo Maestro del Plan</span>
                </div>
                {onConsultTask && (
                  <button
                    onClick={() => onConsultTask(goalCard.title, goalCard.impact)}
                    className="flex items-center gap-1 text-[11px] font-semibold text-amber-700 dark:text-amber-300 hover:underline cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Consultar</span>
                  </button>
                )}
              </div>
              <h4 className="text-sm font-semibold text-slate-800 dark:text-white leading-snug">{goalCard.title}</h4>
            </div>
          )}

          {immediateCard && (
            <div 
              style={{ borderColor: '#ea580c35', boxShadow: '0 0 14px #ea580c12' }}
              className="p-4 rounded-3xl liquid-glass shadow-xs border"
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="text-[10px] font-semibold text-orange-700 dark:text-orange-300 uppercase tracking-wider flex items-center gap-1.5 font-display">
                  <Sparkles className="w-3.5 h-3.5 text-orange-600 dark:text-orange-400" />
                  <span>Acción Inmediata para Hoy</span>
                </div>
                {onConsultTask && (
                  <button
                    onClick={() => onConsultTask(immediateCard.title, immediateCard.impact)}
                    className="flex items-center gap-1 text-[11px] font-semibold text-orange-700 dark:text-orange-300 hover:underline cursor-pointer"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Consultar</span>
                  </button>
                )}
              </div>
              <h4 className="text-sm font-semibold text-slate-800 dark:text-white leading-snug">{immediateCard.title}</h4>
              {immediateCard.impact && (
                <span className="inline-block text-[11px] font-semibold text-orange-700 dark:text-orange-300 mt-1">
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
          {Object.entries(CATEGORY_CONFIG).slice(0, 7).map(([catKey, style]) => {
            const count = cards.filter(c => c.category === catKey).length;
            if (count === 0) return null;
            return (
              <button
                key={catKey}
                onClick={() => setActiveCategoryFilter(catKey)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer border ${
                  activeCategoryFilter === catKey
                    ? 'bg-black/10 dark:bg-white/15 text-slate-900 dark:text-white border-black/15 dark:border-white/20 shadow-sm'
                    : 'bg-black/[0.02] dark:bg-white/[0.04] text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white border-transparent'
                }`}
              >
                <span 
                  className="w-2 h-2 rounded-full shrink-0 shadow-xs" 
                  style={{ backgroundColor: style.color }} 
                />
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
                        style={{
                          borderColor: `${cfg.color}35`,
                          boxShadow: `0 0 14px ${cfg.color}12`,
                        }}
                        className="group relative p-3.5 rounded-2xl liquid-glass-card border hover:border-[#526e5e]/50 dark:hover:border-[#8ba898]/50 shadow-xs transition-all cursor-pointer"
                      >
                        {/* Top Indicator */}
                        <div className="flex items-center justify-between gap-2 mb-2">
                          <div className="flex items-center gap-2">
                            <span 
                              className="w-2 h-2 rounded-full shrink-0 shadow-xs" 
                              style={{ backgroundColor: cfg.color }} 
                              title={cfg.label}
                            />
                            <span className="text-[11px] font-medium text-slate-500 dark:text-slate-400">
                              {cfg.label}
                            </span>
                            {card.week && (
                              <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                                · Sem {card.week}
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
                        <h4 className="text-sm font-semibold text-slate-800 dark:text-white leading-snug mb-2 group-hover:text-[#526e5e] dark:group-hover:text-[#8ba898] transition-colors font-display">
                          {card.title}
                        </h4>

                        {/* Financial Impact Badge */}
                        {card.impact && (
                          <div className="mb-2.5 inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#526e5e]/10 dark:bg-[#6e8c7b]/20 text-[#3d5a48] dark:text-[#a3c7b3] border border-[#526e5e]/20 dark:border-[#6e8c7b]/30">
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
                          <div 
                            className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-medium border mb-2.5" 
                            style={{ borderColor: `${selectedConfig.color}40`, backgroundColor: `${selectedConfig.color}15` }}
                          >
                            <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: selectedConfig.color }} />
                            <span style={{ color: selectedConfig.color }} className="font-semibold">{selectedConfig.label}</span>
                          </div>
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
