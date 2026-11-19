import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ClipboardCheck, 
  LineChart, 
  Sparkles,
  ShieldCheck,
  CheckCircle2
} from 'lucide-react';
import {
  CaseSummary,
  PersonaInsights,
  KanbanState,
  KanbanCard,
  TableState,
  TableSummary,
  ChatMessage
} from './types';
import * as api from './services/api';
import { Header } from './components/Header';
import { PersonaDrawer } from './components/PersonaDrawer';
import { KanbanBoard } from './components/KanbanBoard';
import { ProjectionTable } from './components/ProjectionTable';
import { ChatCoPilot } from './components/ChatCoPilot';
import { ToastContainer, ToastMessage } from './components/Toast';
import { AnimatedBackground } from './components/AnimatedBackground';
import { TutorialModal } from './components/TutorialModal';
import { HandoverModal } from './components/HandoverModal';
import { audioService } from './services/audioService';

export const App: React.FC = () => {
  // Theme state with local persistence
  const [theme, setTheme] = useState<'light' | 'dark'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sherpas_theme');
      if (saved === 'light' || saved === 'dark') return saved;
      return window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return 'dark';
  });

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      localStorage.setItem('sherpas_theme', next);
      if (next === 'dark') {
        document.documentElement.classList.add('dark');
        document.documentElement.classList.remove('light');
      } else {
        document.documentElement.classList.remove('dark');
        document.documentElement.classList.add('light');
      }
      return next;
    });
  }, []);

  useEffect(() => {
    if (theme === 'dark') {
      document.documentElement.classList.add('dark');
      document.documentElement.classList.remove('light');
    } else {
      document.documentElement.classList.remove('dark');
      document.documentElement.classList.add('light');
    }
  }, [theme]);

  // Tab & Case state with persistence to prevent loss on reload
  const [activeTab, setActiveTab] = useState<'kanban' | 'table' | 'chat'>(() => {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('sherpas_active_tab');
      if (saved === 'kanban' || saved === 'table' || saved === 'chat') return saved;
    }
    return 'kanban';
  });

  // Audio, Tutorial & Handover states
  const [soundEnabled, setSoundEnabled] = useState<boolean>(() => audioService.isSoundEnabled());
  const [isTutorialOpen, setIsTutorialOpen] = useState(false);
  const [isHandoverOpen, setIsHandoverOpen] = useState(false);
  const [autoOpenCardId, setAutoOpenCardId] = useState<string | null>(null);

  const handleToggleSound = useCallback(() => {
    setSoundEnabled((prev) => {
      const next = !prev;
      audioService.setSoundEnabled(next);
      if (next) {
        audioService.playSound('message');
      }
      return next;
    });
  }, []);

  const handleSelectTab = (tab: 'kanban' | 'table' | 'chat') => {
    audioService.playSound('click');
    setActiveTab(tab);
    localStorage.setItem('sherpas_active_tab', tab);
  };

  // Case & session state
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [activeCaseId, setActiveCaseId] = useState<string>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('sherpas_active_case') || 'michael-carter';
    }
    return 'michael-carter';
  });

  const handleSelectCase = (caseId: string) => {
    audioService.playSound('click');
    setActiveCaseId(caseId);
    localStorage.setItem('sherpas_active_case', caseId);
  };

  const [sessionId, setSessionId] = useState<string>(() => `sess_${activeCaseId}_${Date.now()}`);

  // Data states
  const [kanban, setKanban] = useState<KanbanState>({ case_id: 'michael-carter', version: 0, statuses: {}, cards: [] });
  const [table, setTable] = useState<TableState>({ case_id: 'michael-carter', version: 0, columns: [], rows: [] });
  const [tableSummary, setTableSummary] = useState<TableSummary | null>(null);
  const [personaInsights, setPersonaInsights] = useState<PersonaInsights | null>(null);

  // UI state
  const [isInitializing, setIsInitializing] = useState(false);
  const [isInsightsOpen, setIsInsightsOpen] = useState(false);
  const [isLoadingInsights, setIsLoadingInsights] = useState(false);
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [proactivePrompt, setProactivePrompt] = useState<{ title: string; prompt: string; type: 'task' | 'column' } | null>(null);

  // Chat streaming state
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingDelta, setStreamingDelta] = useState('');
  const [activeTool, setActiveTool] = useState<string | null>(null);

  const kanbanVersionRef = useRef<number>(0);
  const tableVersionRef = useRef<number>(0);

  const addToast = (text: string, type: 'success' | 'error' | 'info' = 'info') => {
    const id = `${Date.now()}_${Math.random()}`;
    setToasts((prev) => [...prev, { id, text, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const handleStartFirstTask = useCallback(() => {
    audioService.playSound('click');
    setIsTutorialOpen(false);
    handleSelectTab('kanban');
    const firstTodo = kanban.cards.find(c => c.status === 'todo') || kanban.cards[0];
    if (firstTodo) {
      setAutoOpenCardId(firstTodo.id);
    }
  }, [kanban.cards]);

  const handleViewInitialStatus = useCallback(() => {
    audioService.playSound('click');
    setIsTutorialOpen(false);
    setIsHandoverOpen(true);
  }, []);

  const handleExploreFreely = useCallback(() => {
    audioService.playSound('click');
    setIsTutorialOpen(false);
    addToast('¡Navegación libre! Explora tu Living Plan a tu propio ritmo.', 'info');
  }, []);

  // Keyboard navigation for tabs (1, 2, 3)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return;
      if (e.key === '1') handleSelectTab('kanban');
      if (e.key === '2') handleSelectTab('table');
      if (e.key === '3') handleSelectTab('chat');
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Initial load of cases
  useEffect(() => {
    api.fetchCases().then((cList) => {
      setCases(cList);
    });
  }, []);

  const loadCaseData = useCallback(async (caseId: string) => {
    try {
      const [kData, tData, sData] = await Promise.all([
        api.fetchKanban(caseId),
        api.fetchTable(caseId),
        api.fetchTableSummary(caseId)
      ]);

      setKanban(kData);
      kanbanVersionRef.current = kData.version;

      setTable(tData);
      tableVersionRef.current = tData.version;

      setTableSummary(sData);
    } catch (e) {
      console.error('Error cargando datos del caso:', e);
    }
  }, []);

  useEffect(() => {
    loadCaseData(activeCaseId);
    setSessionId(`sess_${activeCaseId}_${Date.now()}`);

    setMessages([
      {
        id: 'welcome_memo',
        role: 'assistant',
        content: `**Expediente actuarial sincronizado.**\n\nPuedes examinar las acciones prioritarias en el **Plan de Accion**, auditar la proyeccion patrimonial reactiva o plantear consultas y simulaciones What-If a traves de este asesor.`
      }
    ]);
  }, [activeCaseId, loadCaseData]);

  const handleToggleInsights = async () => {
    if (!isInsightsOpen && (!personaInsights || personaInsights.case_id !== activeCaseId)) {
      setIsLoadingInsights(true);
      try {
        const ins = await api.fetchPersonaInsights(activeCaseId);
        setPersonaInsights(ins);
      } catch (e) {
        addToast('No se pudieron obtener insights del perfil', 'error');
      } finally {
        setIsLoadingInsights(false);
      }
    }
    setIsInsightsOpen(!isInsightsOpen);
  };

  const handleResetPlan = async () => {
    setIsInitializing(true);
    try {
      const res = await api.initCasePlan(activeCaseId, sessionId);
      await loadCaseData(activeCaseId);
      const headline = res.master_plan?.headline || 'Plan maestro generado con exito';
      addToast(headline, 'success');

      setMessages((prev) => [
        ...prev,
        {
          id: `init_${Date.now()}`,
          role: 'assistant',
          content: `### Dictamen de Plan Maestro Actualizado\n\n**${headline}**\n\n- **Accion Inmediata:** ${res.master_plan?.immediate_action?.title || 'Revisar backlog de tareas'}.\n- **Impacto Proyectado:** ${res.master_plan?.immediate_action?.impact || 'Consolidacion financiera'}.`
        }
      ]);
    } catch (e: any) {
      addToast(e.message || 'Error inicializando plan', 'error');
    } finally {
      setIsInitializing(false);
    }
  };

  const handleArrangeCard = async (cardId: string, toStatus: 'todo' | 'in_process' | 'done', toIndex: number = 0) => {
    try {
      const res = await api.arrangeCard(activeCaseId, cardId, toStatus, toIndex);
      setKanban((prev) => ({ ...prev, cards: res.cards, version: res.version }));
      kanbanVersionRef.current = res.version;
      addToast('Estado de accion actualizado', 'success');
    } catch (e: any) {
      addToast(e.message || 'Error moviendo tarjeta', 'error');
    }
  };

  const handleAddCard = async (cardData: Partial<KanbanCard>) => {
    try {
      const res = await api.addKanbanCard(activeCaseId, cardData);
      await loadCaseData(activeCaseId);
      addToast('Nueva accion registrada en el roadmap', 'success');
      setProactivePrompt({
        title: cardData.title || 'Nueva accion',
        prompt: `He anadido la tarea '${cardData.title}' (impacto: ${cardData.impact || 'no especificado'}). ¿Como me recomiendas abordarla y que impacto financiero proyectas en mi plan?`,
        type: 'task'
      });
    } catch (e: any) {
      addToast(e.message || 'Error anadiendo tarea', 'error');
    }
  };

  const handleDeleteCard = async (cardId: string) => {
    try {
      await api.deleteKanbanCard(activeCaseId, cardId);
      setKanban((prev) => ({
        ...prev,
        cards: prev.cards.filter((c) => c.id !== cardId)
      }));
      addToast('Accion eliminada', 'info');
    } catch (e: any) {
      addToast(e.message || 'Error eliminando tarea', 'error');
    }
  };

  const handleUpdateCell = async (date: string, column: string, value: number | string) => {
    try {
      const res = await api.updateTableCell(activeCaseId, date, column, value);
      setTable((prev) => ({ ...prev, rows: res.rows, version: res.version }));
      tableVersionRef.current = res.version;
      const sData = await api.fetchTableSummary(activeCaseId);
      setTableSummary(sData);
      addToast(`Celda ${date} [${column}] actualizada`, 'success');
    } catch (e: any) {
      addToast(e.message || 'Error actualizando celda', 'error');
    }
  };

  const handleAddColumn = async (name: string, defaultValue: number) => {
    try {
      const res = await api.addTableColumn(activeCaseId, name, defaultValue);
      await loadCaseData(activeCaseId);
      addToast(`Columna '${name}' incorporada al modelo`, 'success');
      setProactivePrompt({
        title: name,
        prompt: `He anadido la columna '${name}' al modelo actuarial con valor base de $${defaultValue}. ¿Como me recomiendas proyectarla e integrarla en mi plan?`,
        type: 'column'
      });
    } catch (e: any) {
      addToast(e.message || 'Error anadiendo columna', 'error');
    }
  };

  const handleAddNextMonth = async () => {
    try {
      const res = await api.addNextMonth(activeCaseId);
      await loadCaseData(activeCaseId);
      addToast(`Proyeccion extendida al mes ${res.new_month || 'siguiente'}`, 'success');
    } catch (e: any) {
      addToast(e.message || 'Error extendiendo proyeccion', 'error');
    }
  };

  const handleConsultTask = (title: string, impact?: string) => {
    setActiveTab('chat');
    const prompt = `Quiero profundizar sobre la tarea '${title}'${impact ? ` (impacto estimado: ${impact})` : ''}. Explicame con detalle cual es la mejor estrategia para completarla y como repercute en mis metas financieras.`;
    handleSendMessage(prompt);
  };

  const handleConsultColumn = (colName: string) => {
    setActiveTab('chat');
    const prompt = `Explicame como repercute la partida '${colName}' en mi flujo de caja y balance, y como optimizarla en mi plan de proyeccion actuarial.`;
    handleSendMessage(prompt);
  };

  const handleDeleteColumn = async (colName: string) => {
    try {
      await api.deleteTableColumn(activeCaseId, colName);
      await loadCaseData(activeCaseId);
      addToast(`Columna '${colName}' eliminada`, 'info');
    } catch (e: any) {
      addToast(e.message || 'Error borrando columna', 'error');
    }
  };

  const handleSendMessage = async (text: string) => {
    if (!text.trim() || isStreaming) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: Date.now()
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsStreaming(true);
    setStreamingDelta('');
    setActiveTool(null);

    let fullReply = '';
    let receivedChart: any = null;
    let anyChangesApplied = false;
    let appliedSummary = '';

    const historyPayload = messages.map((m) => ({
      role: m.role,
      content: m.content
    }));

    await api.streamChat(
      activeCaseId,
      sessionId,
      text,
      historyPayload,
      (event) => {
        if (event.type === 'token' || event.type === 'delta') {
          const delta = event.content || event.delta || '';
          fullReply += delta;
          setStreamingDelta(fullReply);
        } else if (event.type === 'tool_start') {
          setActiveTool(event.tool || 'herramienta');
        } else if (event.type === 'tool_end') {
          setActiveTool(null);
          if (event.modified) {
            anyChangesApplied = true;
            if (event.diff) appliedSummary = event.diff;
          }
        } else if (event.type === 'state') {
          if (event.full_reply && !fullReply) {
            fullReply = event.full_reply;
            setStreamingDelta(fullReply);
          }
          if (event.chart_to_render) {
            receivedChart = event.chart_to_render;
          }
          if (event.changes_applied) {
            anyChangesApplied = true;
            if (event.applied_summary) appliedSummary = event.applied_summary;
          }
        } else if (event.type === 'error') {
          addToast(event.detail || 'Error en el servidor', 'error');
        }
      },
      (err) => {
        setIsStreaming(false);
        setActiveTool(null);
        addToast(err.message || 'Error en comunicacion con Co-Pilot', 'error');
      },
      async () => {
        setIsStreaming(false);
        setActiveTool(null);
        setStreamingDelta('');

        if (fullReply) {
          const assistantMsg: ChatMessage = {
            id: `assistant_${Date.now()}`,
            role: 'assistant',
            content: fullReply,
            chart: receivedChart,
            timestamp: Date.now()
          };
          setMessages((prev) => [...prev, assistantMsg]);
        }

        if (anyChangesApplied) {
          addToast(`Sincronizacion completada: ${appliedSummary || 'Modelo y roadmap actualizados'}`, 'success');
          await loadCaseData(activeCaseId);
        }
      }
    );
  };

  // Background version polling
  useEffect(() => {
    const interval = setInterval(async () => {
      if (isStreaming) return;
      try {
        const [kRes, tRes] = await Promise.all([
          api.fetchKanban(activeCaseId),
          api.fetchTable(activeCaseId)
        ]);

        if (kRes.version !== kanbanVersionRef.current) {
          setKanban(kRes);
          kanbanVersionRef.current = kRes.version;
          addToast('Tablero sincronizado externamente', 'info');
        }

        if (tRes.version !== tableVersionRef.current) {
          setTable(tRes);
          tableVersionRef.current = tRes.version;
          const sData = await api.fetchTableSummary(activeCaseId);
          setTableSummary(sData);
          addToast('Proyeccion actualizada externamente', 'info');
        }
      } catch (e) {
        // Ignorar fallos de sondeo
      }
    }, 4500);

    return () => clearInterval(interval);
  }, [activeCaseId, isStreaming]);

  return (
    <div className="min-h-screen bg-transparent text-slate-900 dark:text-slate-100 flex flex-col font-sans selection:bg-emerald-500/20 relative overflow-x-hidden transition-colors duration-300">
      
      {/* Animated Diffuse Green Lights (Large Ambient Organic Auroras) */}
      <AnimatedBackground theme={theme} />

      <div className="relative z-10 flex flex-col min-h-screen">
        {/* Top Command Bar */}
        <Header
          cases={cases}
          activeCaseId={activeCaseId}
          onSelectCase={handleSelectCase}
          onResetPlan={handleResetPlan}
          onToggleInsights={handleToggleInsights}
          isInitializing={isInitializing}
          theme={theme}
          onToggleTheme={toggleTheme}
          onOpenTutorial={() => setIsTutorialOpen(true)}
          soundEnabled={soundEnabled}
          onToggleSound={handleToggleSound}
        />

        {/* Main Workspace */}
        <main className="flex-1 w-full max-w-[1920px] mx-auto px-4 sm:px-6 lg:px-8 xl:px-12 py-5 flex flex-col">
          
          {/* Minimalist Floating Glass Navigation */}
          <div className="flex items-center justify-start mb-5">
            <div className="flex items-center p-1 rounded-full liquid-glass gap-1 shadow-sm">
              <button
                onClick={() => handleSelectTab('kanban')}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs transition-all cursor-pointer ${
                  activeTab === 'kanban' 
                    ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white shadow-sm font-semibold' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-medium'
                }`}
              >
                <ClipboardCheck className="w-3.5 h-3.5 text-[#526e5e] dark:text-[#8ba898]" />
                <span>Plan de Acción</span>
              </button>

              <button
                onClick={() => handleSelectTab('table')}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs transition-all cursor-pointer ${
                  activeTab === 'table' 
                    ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white shadow-sm font-semibold' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-medium'
                }`}
              >
                <LineChart className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
                <span>Proyección Actuarial</span>
              </button>

              <button
                onClick={() => handleSelectTab('chat')}
                className={`flex items-center gap-1.5 px-4 py-1.5 rounded-full text-xs transition-all cursor-pointer ${
                  activeTab === 'chat' 
                    ? 'bg-black/10 dark:bg-white/12 text-slate-900 dark:text-white shadow-sm font-semibold' 
                    : 'text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white font-medium'
                }`}
              >
                <Sparkles className="w-3.5 h-3.5 text-[#7d7568] dark:text-[#b0a89a]" />
                <span>Asesor Co-Pilot</span>
              </button>
            </div>
          </div>

          {/* Minimalist Proactive Co-Pilot Banner */}
          <AnimatePresence>
            {proactivePrompt && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -6 }}
                className="mb-4 px-4 py-3 rounded-2xl liquid-glass shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
              >
                <div className="flex items-center gap-2 text-xs text-slate-700 dark:text-slate-300">
                  <Sparkles className="w-4 h-4 text-[#526e5e] dark:text-[#8ba898] shrink-0" />
                  <span>
                    Has añadido {proactivePrompt.type === 'task' ? 'la acción' : 'la partida'} <strong className="font-semibold text-slate-900 dark:text-white">'{proactivePrompt.title}'</strong>. ¿Deseas consultar al asesor para analizar su impacto?
                  </span>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <button
                    onClick={() => {
                      const p = proactivePrompt.prompt;
                      setProactivePrompt(null);
                      handleSelectTab('chat');
                      handleSendMessage(p);
                    }}
                    className="px-3.5 py-1.5 text-xs font-semibold text-white bg-[#526e5e] hover:bg-[#445b4d] dark:bg-[#6e8c7b] dark:hover:bg-[#5c7768] rounded-full shadow-sm transition-all cursor-pointer flex items-center gap-1.5"
                  >
                    <Sparkles className="w-3 h-3" />
                    <span>Consultar Asesor</span>
                  </button>
                  <button
                    onClick={() => setProactivePrompt(null)}
                    className="px-2.5 py-1.5 text-xs font-medium text-slate-400 hover:text-slate-700 dark:hover:text-white transition-colors cursor-pointer"
                  >
                    Descartar
                  </button>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

        {/* View Content */}
        <div className="flex-1">
          {activeTab === 'kanban' && (
            <KanbanBoard
              kanban={kanban}
              onArrangeCard={handleArrangeCard}
              onAddCard={handleAddCard}
              onDeleteCard={handleDeleteCard}
              onConsultTask={handleConsultTask}
              autoOpenCardId={autoOpenCardId}
              onClearAutoOpenCard={() => setAutoOpenCardId(null)}
            />
          )}

          {activeTab === 'table' && (
            <ProjectionTable
              table={table}
              summary={tableSummary}
              onUpdateCell={handleUpdateCell}
              onAddColumn={handleAddColumn}
              onDeleteColumn={handleDeleteColumn}
              onAddNextMonth={handleAddNextMonth}
              onConsultColumn={handleConsultColumn}
            />
          )}

          {activeTab === 'chat' && (
            <ChatCoPilot
              messages={messages}
              activeCaseId={activeCaseId}
              onSendMessage={handleSendMessage}
              isStreaming={isStreaming}
              streamingDelta={streamingDelta}
              activeTool={activeTool}
            />
          )}
        </div>

      </main>

      {/* Psycho-Financial Dossier Slide-Over */}
      <PersonaDrawer
        isOpen={isInsightsOpen}
        onClose={() => setIsInsightsOpen(false)}
        insights={personaInsights}
        isLoading={isLoadingInsights}
      />

      {/* Interactive Onboarding Tutorial */}
      <TutorialModal
        isOpen={isTutorialOpen}
        onClose={() => setIsTutorialOpen(false)}
        onStartFirstTask={handleStartFirstTask}
        onViewInitialStatus={handleViewInitialStatus}
        onExploreFreely={handleExploreFreely}
      />

      {/* Executive Initial State & Handover Modal */}
      <HandoverModal
        isOpen={isHandoverOpen}
        onClose={() => setIsHandoverOpen(false)}
        caseId={activeCaseId}
        clientName={cases.find(c => c.id === activeCaseId)?.title || activeCaseId}
      />

      {/* Floating Notifications */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      </div>
    </div>
  );
};

export default App;
