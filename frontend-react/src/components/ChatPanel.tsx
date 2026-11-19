import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  Send,
  Sparkles,
  Bot,
  User,
  Zap,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Square,
  Headphones,
  Copy,
  Check,
  FileText,
  ArrowDown,
  Layers,
  ChevronRight,
  TrendingUp
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';
import { ChatMessage, DynamicChart } from '../types';
import { audioService } from '../services/audioService';
import { HandoverModal } from './HandoverModal';
import { SimulationChart } from './SimulationChart';

export interface ChatPanelProps {
  messages: ChatMessage[];
  activeCaseId: string;
  onSendMessage: (text: string) => Promise<void>;
  isStreaming: boolean;
  streamingDelta: string;
  activeTool: string | null;
  onOpenHandover?: () => void;
  className?: string;
}

const CASE_QUICK_CHIPS: Record<string, { tag: string; label: string; prompt: string }[]> = {
  'michael-carter': [
    {
      tag: 'VIVIENDA',
      label: 'Casa 2027 ($113k) vs Retiro 58 años',
      prompt: 'Quiero comprar una casa de $550.000 en 2027 dando $113.300 de entrada, pero también quiero jubilarme a los 58 años. ¿Puedo hacer ambas cosas o cómo debo secuenciarlas?'
    },
    {
      tag: 'DEUDA',
      label: 'Plan Choque Amex 24.9% ($3,500)',
      prompt: 'Tengo $3.500 en la tarjeta Amex Platinum al 24.9% TAE. ¿Cómo debo amortizarla en la tabla y qué impacto tendrá en mi flujo libre?'
    },
    {
      tag: 'MONTE CARLO',
      label: 'Simulación Estocástica de Patrimonio',
      prompt: 'Ejecuta una simulación Monte Carlo de mi patrimonio a 25 años mostrando percentiles P10, P50 y P90 y probabilidad de éxito de retiro.'
    },
    {
      tag: 'IMPREVISTO',
      label: 'Absorber imprevisto tesorería ($2,000)',
      prompt: 'He tenido un accidente imprevisto y he tenido que desembolsar 2.000 $. Ajusta mi tabla para absorber el gasto y dime cómo afecta a mi plan.'
    }
  ],
  'timothy-melanie-weah': [
    {
      tag: 'LIQUIDEZ',
      label: 'Paradoja $150k en cuenta vs Deuda 18%',
      prompt: 'Tenemos $150.000 en efectivo en cuenta y a la vez una tarjeta de $18.000 al 18% TAE. ¿Por qué es un error financiero mantener esto y cómo lo resolvemos?'
    },
    {
      tag: '529',
      label: 'Fondo universidad Liam y Josh',
      prompt: '¿Cómo estructuramos un fondo 529 para la universidad de Liam (6) y Josh (3) sin comprometer nuestra liquidez?'
    },
    {
      tag: 'CARTERA',
      label: 'Rebalanceo de Cartera Conyugal',
      prompt: 'Nuestra cartera tiene demasiado efectivo improductivo. ¿Cómo conciliar mi tolerancia al riesgo con la prudencia de Melanie?'
    },
    {
      tag: 'PRESUPUESTO',
      label: 'Comparativa de Presupuesto Familiar',
      prompt: 'Muéstrame un gráfico comparativo con la distribución de nuestros ingresos y gastos mensuales.'
    }
  ],
  'daniel-emily-johnson': [
    {
      tag: 'SEGURO',
      label: 'Brecha Seguro de Vida ($1.6M)',
      prompt: 'Tenemos $250k de cobertura de vida y Sherpas recomienda $1.6M para proteger a Oliver y Sophia. ¿Por qué es tan urgente y cómo lo estructuramos?'
    },
    {
      tag: 'DEUDA',
      label: 'Liquidar Tarjeta 24.9% TAE',
      prompt: 'Nuestra tarjeta de crédito al 24.9% TAE drena nuestros ahorros. Diseña un plan de choque para amortizarla en la tabla.'
    },
    {
      tag: 'UNIVERSIDAD',
      label: 'Universidad vs 401(k)',
      prompt: '¿Qué debemos priorizar: fondear la universidad de los niños o elevar nuestras aportaciones al 401(k)?'
    },
    {
      tag: 'SCORE',
      label: 'Diagnóstico y Cuello de Botella',
      prompt: 'Analiza nuestro score de salud financiera y explícame cuál es nuestro cuello de botella principal según nuestro informe.'
    }
  ],
  'samantha-lewis': [
    {
      tag: 'DEPLECIÓN',
      label: 'Precipicio invisible a los 73 años',
      prompt: 'Tengo un score alto de 82, pero he visto que mis fondos se agotan a los 73 años. ¿Por qué ocurre y qué medidas debemos tomar hoy?'
    },
    {
      tag: 'FISCAL',
      label: 'Optimización HSA + Backdoor Roth',
      prompt: '¿Cómo puedo aprovechar mi nivel de ingresos para maximizar las ventajas fiscales del HSA y el Backdoor Roth IRA?'
    },
    {
      tag: 'VIVIENDA',
      label: 'Compra vivienda 2030 ($180k)',
      prompt: 'Planifico comprar vivienda en 2030 con $180k de entrada mientras pago la universidad de mis hijos. Simula si es viable.'
    },
    {
      tag: 'ASIGNACIÓN',
      label: 'Asignación Actual vs Objetivo Sherpas',
      prompt: 'Muéstrame un gráfico comparativo con mi distribución de inversiones actual y la recomendada por Sherpas.'
    }
  ]
};

const CHART_COLORS = [
  '#2563eb', // Royal Sapphire
  '#059669', // Emerald
  '#ea580c', // Terracotta Orange
  '#7c3aed', // Amethyst Violet
  '#0891b2', // Ocean Cyan
  '#e11d48', // Crimson Rose
  '#d97706', // Warm Amber
  '#4f46e5', // Deep Indigo
  '#10b981', // Mint Jade
  '#c026d3', // Fuchsia
  '#0284c7', // Sky Blue
  '#ca8a04', // Goldenrod
  '#9333ea', // Royal Purple
  '#0d9488', // Deep Teal
  '#f43f5e', // Coral
  '#6366f1', // Periwinkle
  '#16a34a', // Leaf Green
  '#b45309'  // Warm Bronze
];

export const ChatPanel: React.FC<ChatPanelProps> = ({
  messages,
  activeCaseId,
  onSendMessage,
  isStreaming,
  streamingDelta,
  activeTool,
  onOpenHandover,
  className = ''
}) => {
  const [inputText, setInputText] = useState('');
  const [isDark, setIsDark] = useState(() =>
    typeof document !== 'undefined' ? document.documentElement.classList.contains('dark') : true
  );

  // Audio & Voice States
  const [autoVoice, setAutoVoice] = useState(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('sherpas_auto_voice') === 'true';
    }
    return false;
  });
  const [soundEnabled, setSoundEnabled] = useState(() => audioService.isSoundEnabled());
  const [playingMessageId, setPlayingMessageId] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);
  const [copiedMessageId, setCopiedMessageId] = useState<string | null>(null);
  const [showScrollBottom, setShowScrollBottom] = useState(false);
  const [isHandoverModalOpen, setIsHandoverModalOpen] = useState(false);

  // Refs
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const speechRecognizerRef = useRef<{ start: () => void; stop: () => void; isSupported: boolean } | null>(null);
  const speechBaseTextRef = useRef('');
  const handledAssistantMsgIdsRef = useRef<Set<string>>(new Set());
  const prevStreamingRef = useRef(isStreaming);

  // Mutation observer for dark mode changes
  useEffect(() => {
    const observer = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'));
    });
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  // Track initial message IDs
  useEffect(() => {
    messages.forEach((m) => {
      if (m.role === 'assistant') {
        handledAssistantMsgIdsRef.current.add(m.id);
      }
    });
  }, []);

  // Audio cleanup on unmount
  useEffect(() => {
    return () => {
      audioService.stopSpeaking();
      if (speechRecognizerRef.current) {
        speechRecognizerRef.current.stop();
      }
    };
  }, []);

  // Detect completion of assistant response for sound & voice playback
  useEffect(() => {
    const wasStreaming = prevStreamingRef.current;
    prevStreamingRef.current = isStreaming;

    if (!isStreaming) {
      const lastMsg = messages[messages.length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && !handledAssistantMsgIdsRef.current.has(lastMsg.id)) {
        handledAssistantMsgIdsRef.current.add(lastMsg.id);
        audioService.playSound('message');

        if (autoVoice) {
          audioService.speak(
            lastMsg.content,
            () => setPlayingMessageId(lastMsg.id),
            () => setPlayingMessageId(null),
            () => setPlayingMessageId(null)
          );
          setPlayingMessageId(lastMsg.id);
        }
      } else if (wasStreaming) {
        audioService.playSound('message');
      }
    }
  }, [messages, isStreaming, autoVoice]);

  // Auto-scroll when messages update or streaming delta changes
  useEffect(() => {
    const container = scrollContainerRef.current;
    if (!container) return;

    // Only auto-scroll if user is already near bottom (within 200px)
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 220;
    if (isNearBottom || isStreaming) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, streamingDelta, activeTool, isStreaming]);

  // Scroll position monitor to toggle "Scroll to bottom" button
  const handleScroll = useCallback(() => {
    const container = scrollContainerRef.current;
    if (!container) return;
    const distanceToBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
    setShowScrollBottom(distanceToBottom > 280);
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    setShowScrollBottom(false);
  };

  // Auto-expanding textarea height adjustments (no layout shift or transition jitter)
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    if (!inputText.trim()) {
      textarea.style.height = '44px';
      return;
    }
    textarea.style.height = 'auto';
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, 44), 160);
    textarea.style.height = `${nextHeight}px`;
  }, [inputText]);

  // Voice Mode Toggle
  const toggleAutoVoice = () => {
    setAutoVoice((prev) => {
      const next = !prev;
      if (typeof window !== 'undefined') {
        localStorage.setItem('sherpas_auto_voice', String(next));
      }
      if (!next && playingMessageId) {
        audioService.stopSpeaking();
        setPlayingMessageId(null);
      }
      audioService.playSound('click');
      return next;
    });
  };

  // Sound FX Toggle
  const toggleSound = () => {
    const next = !soundEnabled;
    audioService.setSoundEnabled(next);
    setSoundEnabled(next);
    if (next) audioService.playSound('click');
  };

  // Text-To-Speech reader
  const handleToggleSpeak = (msgId: string, content: string) => {
    if (isListening) {
      speechRecognizerRef.current?.stop();
      setIsListening(false);
    }

    if (playingMessageId === msgId) {
      audioService.stopSpeaking();
      setPlayingMessageId(null);
      return;
    }

    audioService.stopSpeaking();
    const ok = audioService.speak(
      content,
      () => setPlayingMessageId(msgId),
      () => setPlayingMessageId(null),
      () => setPlayingMessageId(null)
    );

    if (ok) {
      setPlayingMessageId(msgId);
    } else {
      setPlayingMessageId(null);
    }
  };

  // Voice Input (STT) Toggle
  const toggleListening = () => {
    if (isListening) {
      speechRecognizerRef.current?.stop();
      setIsListening(false);
      return;
    }

    audioService.stopSpeaking();
    setPlayingMessageId(null);

    speechBaseTextRef.current = inputText;

    const recognizer = audioService.createSpeechRecognizer(
      (transcript: string, _isFinal: boolean) => {
        const base = speechBaseTextRef.current.trim();
        setInputText(base ? `${base} ${transcript}` : transcript);
      },
      (error: string) => {
        console.warn('Speech recognition warning:', error);
        setIsListening(false);
        speechRecognizerRef.current = null;
      },
      () => {
        setIsListening(false);
        speechRecognizerRef.current = null;
      }
    );

    speechRecognizerRef.current = recognizer;

    if (!recognizer.isSupported) {
      alert('El reconocimiento de voz no está soportado en este navegador.');
      return;
    }

    try {
      recognizer.start();
      setIsListening(true);
      audioService.playSound('click');
    } catch (err) {
      console.error('Failed to start speech recognition:', err);
      setIsListening(false);
    }
  };

  // Copy message text helper
  const handleCopyMessage = (msgId: string, text: string) => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(text).then(() => {
        setCopiedMessageId(msgId);
        setTimeout(() => setCopiedMessageId(null), 2000);
      });
    }
  };

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!inputText.trim() || isStreaming) return;

    if (isListening) {
      speechRecognizerRef.current?.stop();
      setIsListening(false);
    }

    audioService.stopSpeaking();
    setPlayingMessageId(null);

    const txt = inputText.trim();
    setInputText('');
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px';
    }

    audioService.playSound('message');
    await onSendMessage(txt);
  };

  const handleChipClick = async (prompt: string) => {
    if (isStreaming) return;
    if (isListening) {
      speechRecognizerRef.current?.stop();
      setIsListening(false);
    }
    audioService.stopSpeaking();
    setPlayingMessageId(null);
    audioService.playSound('message');
    await onSendMessage(prompt);
  };

  const chips = CASE_QUICK_CHIPS[activeCaseId] || CASE_QUICK_CHIPS['michael-carter'];

  // Helper to render dynamic charts embedded in assistant answers
  const renderDynamicChart = (chart: DynamicChart) => {
    const data = chart.labels.map((lbl, idx) => ({
      name: lbl,
      value: chart.values[idx] || 0
    }));

    const textColor = isDark ? '#f8fafc' : '#0f172a';
    const axisColor = isDark ? '#64748b' : '#94a3b8';
    const tooltipBg = isDark ? 'rgba(15, 18, 25, 0.94)' : 'rgba(255, 255, 255, 0.94)';
    const tooltipBorder = isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.1)';

    const renderTooltip = ({ active, payload }: any) => {
      if (!active || !payload || !payload.length) return null;
      const item = payload[0];
      const name = item.name || item.payload?.name || item.dataKey || 'Variable';
      const val = Number(item.value || 0);
      const color = item.payload?.fill || item.color || item.fill || '#2563eb';
      const isPieOrDonut = chart.type === 'pie' || chart.type === 'donut';
      const total = isPieOrDonut ? data.reduce((sum, d) => sum + (Number(d.value) || 0), 0) : 0;
      const pct = total > 0 ? ((val / total) * 100).toFixed(1) : null;

      return (
        <div
          className="px-3 py-2 rounded-xl liquid-glass shadow-lg border border-black/10 dark:border-white/15 pointer-events-none text-left"
          style={{
            backgroundColor: tooltipBg,
            backdropFilter: 'blur(16px)',
            minWidth: '135px'
          }}
        >
          <div className="flex items-center gap-1.5 mb-1">
            <span
              className="w-2.5 h-2.5 rounded-full inline-block shrink-0 shadow-xs"
              style={{ backgroundColor: color }}
            />
            <span className="text-xs font-semibold text-slate-800 dark:text-slate-100 truncate max-w-[180px]" title={name}>
              {name}
            </span>
          </div>
          <div className="flex items-center justify-between gap-3 font-mono text-xs text-slate-600 dark:text-slate-300">
            <span className="font-semibold text-slate-900 dark:text-white">
              ${val.toLocaleString()}
            </span>
            {pct && (
              <span className="text-[10px] font-sans text-emerald-600 dark:text-emerald-400 bg-emerald-500/10 dark:bg-emerald-400/15 px-1.5 py-0.5 rounded-md font-medium">
                {pct}%
              </span>
            )}
          </div>
        </div>
      );
    };

    return (
      <div className="my-3.5 p-4 rounded-2xl liquid-glass shadow-xs border border-black/[0.05] dark:border-white/[0.08]">
        <div className="text-xs font-semibold text-slate-800 dark:text-slate-100 mb-2.5 flex items-center justify-between font-display">
          <span>{chart.title}</span>
          <span className="text-[10px] font-mono font-medium text-[#875f52] dark:text-[#b38a7c] bg-[#875f52]/10 dark:bg-[#b38a7c]/15 px-2 py-0.5 rounded-full border border-[#875f52]/20 dark:border-[#b38a7c]/30">
            {chart.type.toUpperCase()}
          </span>
        </div>
        <div className="h-52 w-full">
          <ResponsiveContainer width="100%" height="100%">
            {chart.type === 'pie' || chart.type === 'donut' ? (
              <PieChart>
                <Pie
                  data={data}
                  cx="50%"
                  cy="50%"
                  innerRadius={chart.type === 'donut' ? 44 : 0}
                  outerRadius={68}
                  dataKey="value"
                  nameKey="name"
                  paddingAngle={data.length > 1 ? 3 : 0}
                >
                  {data.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={CHART_COLORS[index % CHART_COLORS.length]}
                      stroke={isDark ? 'rgba(15, 23, 42, 0.7)' : 'rgba(255, 255, 255, 0.9)'}
                      strokeWidth={1.5}
                    />
                  ))}
                </Pie>
                <Tooltip content={renderTooltip} />
                <Legend
                  verticalAlign="bottom"
                  align="center"
                  wrapperStyle={{ color: textColor, fontSize: '11px', paddingTop: '8px' }}
                  formatter={(val) => <span style={{ color: textColor, fontSize: '11px', fontWeight: 500 }}>{val}</span>}
                />
              </PieChart>
            ) : chart.type === 'line' ? (
              <LineChart data={data}>
                <XAxis dataKey="name" stroke={axisColor} tick={{ fill: textColor, fontSize: 10 }} tickLine={false} />
                <YAxis stroke={axisColor} tick={{ fill: textColor, fontSize: 10 }} tickLine={false} />
                <Tooltip content={renderTooltip} />
                <Legend
                  wrapperStyle={{ color: textColor, fontSize: '11px', paddingTop: '8px' }}
                  formatter={(val) => <span style={{ color: textColor, fontSize: '11px', fontWeight: 500 }}>{val}</span>}
                />
                <Line type="monotone" dataKey="value" stroke="#2563eb" strokeWidth={2.4} dot={{ r: 3.5, fill: '#3b82f6' }} />
              </LineChart>
            ) : (
              <BarChart data={data}>
                <XAxis dataKey="name" stroke={axisColor} tick={{ fill: textColor, fontSize: 10 }} tickLine={false} />
                <YAxis stroke={axisColor} tick={{ fill: textColor, fontSize: 10 }} tickLine={false} />
                <Tooltip content={renderTooltip} />
                <Legend
                  wrapperStyle={{ color: textColor, fontSize: '11px', paddingTop: '8px' }}
                  formatter={(val) => <span style={{ color: textColor, fontSize: '11px', fontWeight: 500 }}>{val}</span>}
                />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {data.map((_, index) => (
                    <Cell key={`bar-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            )}
          </ResponsiveContainer>
        </div>
      </div>
    );
  };

  // Structured Markdown message renderer
  const renderMarkdownMessage = (content: string) => {
    return (
      <div className="prose prose-sm max-w-none text-slate-800 dark:text-slate-100 leading-relaxed font-normal">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ children }) => <p className="mb-2.5 last:mb-0 leading-relaxed text-sm text-slate-800 dark:text-slate-100">{children}</p>,
            strong: ({ children }) => <strong className="font-semibold text-slate-900 dark:text-white">{children}</strong>,
            em: ({ children }) => <em className="italic text-slate-600 dark:text-slate-300">{children}</em>,
            ul: ({ children }) => <ul className="list-disc pl-5 mb-2.5 space-y-1 text-sm text-slate-800 dark:text-slate-100">{children}</ul>,
            ol: ({ children }) => <ol className="list-decimal pl-5 mb-2.5 space-y-1 text-sm text-slate-800 dark:text-slate-100">{children}</ol>,
            li: ({ children }) => <li className="leading-relaxed">{children}</li>,
            h1: ({ children }) => <h1 className="text-base font-bold text-slate-900 dark:text-white mb-2 font-display">{children}</h1>,
            h2: ({ children }) => <h2 className="text-sm font-bold text-slate-900 dark:text-white mb-2 font-display">{children}</h2>,
            h3: ({ children }) => <h3 className="text-xs font-bold text-slate-900 dark:text-white mb-1.5 font-display tracking-wide uppercase">{children}</h3>,
            blockquote: ({ children }) => (
              <blockquote className="border-l-3 border-[#526e5e] dark:border-[#8ba898] pl-3 py-1 my-2.5 italic text-slate-700 dark:text-slate-200 bg-black/[0.02] dark:bg-white/[0.02] rounded-r-lg">
                {children}
              </blockquote>
            ),
            table: ({ children }) => (
              <div className="overflow-x-auto my-3 rounded-xl border border-black/10 dark:border-white/10">
                <table className="w-full text-xs text-left border-collapse">{children}</table>
              </div>
            ),
            thead: ({ children }) => <thead className="bg-black/[0.03] dark:bg-white/[0.05] border-b border-black/10 dark:border-white/10 text-slate-900 dark:text-white">{children}</thead>,
            th: ({ children }) => <th className="px-3.5 py-2 font-semibold font-display">{children}</th>,
            td: ({ children }) => <td className="px-3.5 py-2 border-t border-black/5 dark:border-white/5 text-slate-700 dark:text-slate-200">{children}</td>,
            code: ({ children, className: codeClass }) => {
              const isInline = !codeClass;
              if (isInline) {
                return (
                  <code className="bg-black/[0.05] dark:bg-white/[0.08] text-[#875f52] dark:text-[#b38a7c] font-mono text-xs px-1.5 py-0.5 rounded border border-black/[0.06] dark:border-white/10">
                    {children}
                  </code>
                );
              }
              return (
                <div className="relative group my-2.5">
                  <pre className="bg-slate-950 text-slate-100 p-3.5 rounded-xl border border-white/10 overflow-x-auto text-xs font-mono leading-relaxed">
                    {children}
                  </pre>
                </div>
              );
            },
            pre: ({ children }) => (
              <pre className="bg-black/[0.04] dark:bg-black/40 p-3 rounded-xl border border-black/10 dark:border-white/10 overflow-x-auto my-2.5 text-xs text-slate-800 dark:text-slate-200">
                {children}
              </pre>
            ),
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noreferrer" className="text-[#526e5e] dark:text-[#8ba898] underline hover:opacity-80 transition-opacity">
                {children}
              </a>
            ),
            hr: () => <hr className="my-3 border-black/10 dark:border-white/10" />
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    );
  };

  return (
    <div className={`relative flex flex-col h-[calc(100vh-210px)] min-h-[560px] rounded-3xl liquid-glass shadow-sm overflow-hidden transition-colors duration-300 ${className}`}>
      
      {/* 1. Ultra-Refined Conversational Header */}
      <div className="px-5 py-3 border-b border-black/[0.04] dark:border-white/[0.06] bg-black/[0.015] dark:bg-white/[0.02] flex items-center justify-between gap-3">
        {/* Left: AI Advisory Mode Badge & Status */}
        <div className="flex items-center gap-2.5 min-w-0">
          <div className="flex items-center justify-center w-7 h-7 rounded-lg bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 shrink-0">
            <Bot className="w-3.5 h-3.5" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-900 dark:text-white">Asesor Sherpas</span>
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" title="Asesor conectado" />
          </div>
        </div>

        {/* Right: Quick Action Controls */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            type="button"
            onClick={() => {
              if (onOpenHandover) {
                onOpenHandover();
              } else {
                setIsHandoverModalOpen(true);
              }
            }}
            title="Ver Informe Ejecutivo"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/[0.08] text-slate-700 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white transition-colors cursor-pointer"
          >
            <FileText className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" />
            <span className="hidden sm:inline">Informe Ejecutivo</span>
          </button>
        </div>
      </div>

      {/* 2. Minimalist Prompt Suggestion Chips */}
      <div className="px-5 py-2.5 border-b border-black/[0.04] dark:border-white/[0.06] bg-black/[0.01] dark:bg-white/[0.01]">
        <div className="text-[10px] font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5 font-display">
          <Sparkles className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
          <span>Consultas Estratégicas Recomendadas:</span>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2">
          {chips.map((chip, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handleChipClick(chip.prompt)}
              disabled={isStreaming}
              className="text-left px-3 py-2 rounded-xl liquid-glass-interactive text-slate-700 hover:text-slate-900 dark:text-slate-300 dark:hover:text-white text-xs font-medium transition-all truncate disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer group shadow-xs border border-black/[0.04] dark:border-white/[0.05]"
            >
              <div className="text-[9px] font-bold text-[#875f52] dark:text-[#b38a7c] uppercase tracking-wider mb-0.5">
                [{chip.tag}]
              </div>
              <div className="truncate text-slate-600 dark:text-slate-400 group-hover:text-slate-900 dark:group-hover:text-white text-[11px]">
                {chip.label}
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* 3. Elegant Message Thread */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-5 sm:p-6 space-y-4 relative"
      >
        {messages.map((m) => {
          const isUser = m.role === 'user';
          const isPlayingThisMessage = playingMessageId === m.id;
          const isCopied = copiedMessageId === m.id;

          return (
            <motion.div
              key={m.id}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className={`flex gap-3 max-w-4xl xl:max-w-5xl 2xl:max-w-6xl ${isUser ? 'ml-auto justify-end' : 'mr-auto justify-start'}`}
            >
              {!isUser && (
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#526e5e]/12 dark:bg-[#8ba898]/15 border border-[#526e5e]/20 dark:border-[#8ba898]/25 text-[#526e5e] dark:text-[#8ba898] shrink-0 mt-0.5">
                  <Bot className="w-4 h-4" />
                </div>
              )}

              <div
                className={`p-4 sm:p-5 rounded-2xl text-sm leading-relaxed ${
                  isUser
                    ? 'bg-[#526e5e] text-white rounded-tr-none shadow-xs font-normal'
                    : 'liquid-glass-card text-slate-800 dark:text-slate-100 rounded-tl-none shadow-xs border border-black/[0.05] dark:border-white/[0.08]'
                }`}
              >
                {isUser ? (
                  <>
                    <div className="whitespace-pre-wrap">{m.content}</div>
                    {m.timestamp && (
                      <div className="text-[10px] text-white/70 font-mono text-right mt-1.5">
                        {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    {renderMarkdownMessage(m.content)}
                    {m.chart && renderDynamicChart(m.chart)}

                    {/* Integrated Monte Carlo simulation chart trigger if message asks for it */}
                    {m.content.toLowerCase().includes('monte carlo') && (
                      <div className="mt-4 pt-3 border-t border-black/[0.06] dark:border-white/[0.08]">
                        <SimulationChart
                          caseId={activeCaseId}
                          title="Simulación Monte Carlo Solicitada"
                          subtitle="Trayectoria probabilística proyectada por el Asesor"
                        />
                      </div>
                    )}

                    {/* Assistant Message Actions (TTS, Copy, Timestamp) */}
                    <div className="flex items-center justify-between gap-2 mt-3 pt-2.5 border-t border-black/[0.06] dark:border-white/[0.08]">
                      <div className="flex items-center gap-2">
                        {/* Audio speaker toggle button */}
                        <button
                          type="button"
                          onClick={() => handleToggleSpeak(m.id, m.content)}
                          title={isPlayingThisMessage ? "Detener lectura de voz" : "Escuchar respuesta en voz alta"}
                          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium transition-all cursor-pointer ${
                            isPlayingThisMessage
                              ? 'bg-[#526e5e] text-white shadow-xs ring-2 ring-[#526e5e]/25 dark:bg-[#6e8c7b]'
                              : 'bg-black/[0.04] dark:bg-white/[0.06] hover:bg-black/[0.08] dark:hover:bg-white/[0.1] text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
                          }`}
                        >
                          {isPlayingThisMessage ? (
                            <>
                              <Square className="w-3 h-3 fill-current" />
                              <span>Detener voz</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-3.5 h-3.5" />
                              <span>Escuchar</span>
                            </>
                          )}
                        </button>

                        {/* Copy button */}
                        <button
                          type="button"
                          onClick={() => handleCopyMessage(m.id, m.content)}
                          title="Copiar respuesta"
                          className="p-1 rounded-lg text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 hover:bg-black/[0.04] dark:hover:bg-white/[0.06] transition-colors cursor-pointer"
                        >
                          {isCopied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
                        </button>

                        {/* Subtle animated audio wave indicator when playing */}
                        {isPlayingThisMessage && (
                          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-[#526e5e]/10 dark:bg-[#8ba898]/15 text-[#526e5e] dark:text-[#8ba898] text-[11px] font-medium border border-[#526e5e]/15 dark:border-[#8ba898]/20">
                            <div className="flex items-end gap-0.5 h-3">
                              <span className="w-0.5 h-2 bg-current rounded-full animate-bounce [animation-delay:-0.3s]" />
                              <span className="w-0.5 h-3 bg-current rounded-full animate-bounce [animation-delay:-0.15s]" />
                              <span className="w-0.5 h-1.5 bg-current rounded-full animate-bounce" />
                              <span className="w-0.5 h-2.5 bg-current rounded-full animate-bounce [animation-delay:-0.2s]" />
                            </div>
                            <span>Reproduciendo...</span>
                          </div>
                        )}
                      </div>

                      {m.timestamp && (
                        <span className="text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                          {new Date(m.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      )}
                    </div>
                  </>
                )}
              </div>

              {isUser && (
                <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#875f52]/15 border border-[#875f52]/25 text-[#875f52] dark:text-[#b38a7c] shrink-0 mt-0.5">
                  <User className="w-4 h-4" />
                </div>
              )}
            </motion.div>
          );
        })}

        {/* 4. Fluid Streaming Response Animation */}
        {isStreaming && (
          <motion.div
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex gap-3 max-w-4xl xl:max-w-5xl 2xl:max-w-6xl mr-auto justify-start"
          >
            <div className="flex items-center justify-center w-8 h-8 rounded-full bg-[#526e5e]/12 dark:bg-[#8ba898]/15 border border-[#526e5e]/20 dark:border-[#8ba898]/25 text-[#526e5e] dark:text-[#8ba898] shrink-0 mt-0.5">
              <Bot className="w-4 h-4" />
            </div>
            <div className="p-4 sm:p-5 rounded-2xl text-sm leading-relaxed liquid-glass-card text-slate-800 dark:text-slate-100 rounded-tl-none shadow-xs border border-black/[0.05] dark:border-white/[0.08] space-y-2">
              {activeTool && (
                <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-[#526e5e]/10 dark:bg-[#6e8c7b]/15 border border-[#526e5e]/20 dark:border-[#6e8c7b]/25 text-[#526e5e] dark:text-[#8ba898] text-xs font-semibold animate-pulse">
                  <Zap className="w-3.5 h-3.5 text-[#875f52] dark:text-[#b38a7c]" />
                  <span>Optimizando plan actuarial con {activeTool}...</span>
                </div>
              )}
              {renderMarkdownMessage(streamingDelta)}
              <span className="inline-block w-1.5 h-4 ml-1 bg-[#526e5e] dark:bg-[#8ba898] animate-pulse align-middle" />
            </div>
          </motion.div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Floating "Scroll to bottom" button */}
      <AnimatePresence>
        {showScrollBottom && (
          <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 10 }}
            onClick={scrollToBottom}
            className="absolute bottom-20 right-6 px-3 py-1.5 rounded-full bg-slate-900/90 text-white dark:bg-white/90 dark:text-slate-900 text-xs font-semibold shadow-lg backdrop-blur-md flex items-center gap-1.5 z-20 cursor-pointer"
          >
            <ArrowDown className="w-3.5 h-3.5" />
            <span>Últimos mensajes</span>
          </motion.button>
        )}
      </AnimatePresence>

      {/* 5. Sleek Text Input Box with smooth auto-expand, clear send button & voice ripple */}
      <form
        onSubmit={handleSubmit}
        className="p-3.5 sm:p-4 bg-white/80 dark:bg-[#070c09]/90 backdrop-blur-xl border-t border-black/[0.06] dark:border-white/[0.08]"
      >
        {/* Active Speech Recognition Banner with gentle ripple & pulsing soundwave */}
        {isListening && (
          <div className="flex items-center justify-between px-3.5 py-2 mb-2.5 rounded-xl bg-red-500/10 dark:bg-red-500/15 border border-red-500/25 text-red-600 dark:text-red-400 text-xs">
            <div className="flex items-center gap-2">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-red-500" />
              </span>
              <span className="font-medium">Escuchando tu consulta actuarial... (Dicta tu mensaje)</span>
            </div>
            <div className="flex items-end gap-1 h-3.5">
              <span className="w-1 h-2 bg-red-500 rounded-full animate-bounce [animation-delay:-0.3s]" />
              <span className="w-1 h-3.5 bg-red-500 rounded-full animate-bounce [animation-delay:-0.15s]" />
              <span className="w-1 h-1.5 bg-red-500 rounded-full animate-bounce" />
              <span className="w-1 h-3 bg-red-500 rounded-full animate-bounce [animation-delay:-0.2s]" />
              <span className="w-1 h-2.5 bg-red-500 rounded-full animate-bounce [animation-delay:-0.1s]" />
            </div>
          </div>
        )}

        <div className="flex items-end gap-2 sm:gap-3">
          {/* Smooth auto-expanding textarea with rock-solid height handling */}
          <div className="flex-1 relative">
            <textarea
              ref={textareaRef}
              rows={1}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit();
                }
              }}
              placeholder={
                isListening
                  ? 'Escuchando tu voz...'
                  : isStreaming
                  ? 'Sherpas Co-Pilot está calculando impacto actuarial...'
                  : 'Formula una consulta, dilema financiero o imprevisto al asesor... (Enter para enviar, Shift+Enter para nueva línea)'
              }
              disabled={isStreaming}
              style={{ minHeight: '44px', maxHeight: '160px' }}
              className="w-full resize-none px-4 sm:px-5 py-2.5 sm:py-3 text-sm bg-black/[0.03] dark:bg-white/[0.06] rounded-xl sm:rounded-2xl border border-black/10 dark:border-white/12 text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20 dark:focus:ring-emerald-400/25 focus:border-emerald-600/50 dark:focus:border-emerald-400/50 transition-colors duration-150 disabled:opacity-50 shadow-inner leading-relaxed block overflow-y-auto"
            />
          </div>

          {/* Voice Input (Speech Recognition / STT) Toggle Button */}
          <button
            type="button"
            onClick={toggleListening}
            disabled={isStreaming}
            title={isListening ? "Detener grabación de voz" : "Dictar consulta por voz"}
            className={`flex items-center justify-center w-10 sm:w-11 h-10 sm:h-11 rounded-xl sm:rounded-2xl transition-all shrink-0 cursor-pointer disabled:opacity-30 disabled:cursor-not-allowed ${
              isListening
                ? 'bg-red-500 text-white shadow-md ring-4 ring-red-500/25 animate-pulse'
                : 'liquid-glass-interactive text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
            }`}
          >
            {isListening ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
          </button>

          {/* Clear Send Button */}
          <button
            type="submit"
            disabled={!inputText.trim() || isStreaming}
            title="Enviar consulta (Enter)"
            className="flex items-center justify-center w-10 sm:w-11 h-10 sm:h-11 bg-emerald-600/90 hover:bg-emerald-600 dark:bg-emerald-600/80 dark:hover:bg-emerald-500 text-white rounded-xl sm:rounded-2xl shadow-xs transition-all disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer shrink-0"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>

      {/* Built-in Handover Modal */}
      <HandoverModal
        isOpen={isHandoverModalOpen}
        onClose={() => setIsHandoverModalOpen(false)}
        caseId={activeCaseId}
      />

    </div>
  );
};

export default ChatPanel;
