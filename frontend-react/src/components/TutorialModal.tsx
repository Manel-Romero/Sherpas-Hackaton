import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  X, 
  ChevronRight, 
  ChevronLeft, 
  CheckCircle2, 
  Compass, 
  ClipboardCheck, 
  LineChart, 
  Sparkles,
  Mic,
  Volume2,
  FileText
} from 'lucide-react';
import { audioService } from '../services/audioService';

interface TutorialModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStartFirstTask?: () => void;
  onViewInitialStatus?: () => void;
  onExploreFreely?: () => void;
}

const STEPS = [
  {
    icon: Compass,
    iconColor: 'text-[#526e5e] dark:text-[#8ba898]',
    tag: 'INTRODUCCIÓN',
    title: 'Bienvenido a tu Living Plan',
    subtitle: 'Finanzas generativas en tiempo real para tu patrimonio familiar',
    body: (
      <div className="space-y-3 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
        <p>
          En <strong>Sherpas Wealth</strong>, tu plan financiero deja de ser un documento PDF estático de 60 páginas y se convierte en un <strong>sistema vivo e interactivo</strong> que responde a cualquier cambio de tu vida.
        </p>
        <p>
          En este breve recorrido de 1 minuto te mostramos las tres herramientas principales de tu panel y cómo interactuar con tu asesor Co-Pilot.
        </p>
      </div>
    )
  },
  {
    icon: ClipboardCheck,
    iconColor: 'text-[#526e5e] dark:text-[#8ba898]',
    tag: 'PESTAÑA 1',
    title: 'Plan de Acción y Tablero Kanban',
    subtitle: 'De la parálisis por análisis a victorias en 3 minutos',
    body: (
      <div className="space-y-3 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
        <p>
          Un tablero visual estructurado semana a semana con las acciones prioritarias de tu caso:
        </p>
        <ul className="list-disc pl-5 space-y-1 text-xs">
          <li><strong>Arrastra o avanza tarjetas</strong> entre <em>Por Hacer</em>, <em>En Proceso</em> y <em>Completada</em>.</li>
          <li><strong>Haz clic en cualquier tarjeta</strong> para ver el detalle, impacto cuantificado y guía paso a paso.</li>
          <li>Usa <strong>➕ Añadir Acción</strong> para registrar tus propias metas o compromisos.</li>
          <li>Sigue la <strong>barra de progreso</strong> superior que mide tu avance real hacia la resiliencia financiera.</li>
        </ul>
      </div>
    )
  },
  {
    icon: LineChart,
    iconColor: 'text-[#875f52] dark:text-[#b38a7c]',
    tag: 'PESTAÑA 2',
    title: 'Proyección Actuarial y Tabla Dinámica',
    subtitle: 'Visualiza el impacto de cada decisión a 12-36 meses',
    body: (
      <div className="space-y-3 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
        <p>
          Comprueba cómo evolucionan tu patrimonio neto, liquidez y servicio de deuda:
        </p>
        <ul className="list-disc pl-5 space-y-1 text-xs">
          <li><strong>Edita cualquier celda</strong> de la tabla haciendo clic: el gráfico superior se recalcula al instante.</li>
          <li><strong>Añade nuevas columnas o fórmulas</strong> (ej: <code>Ingresos * 0.15</code> para nueva meta de ahorro).</li>
          <li><strong>Proyecta aumentos compuestos</strong> o introduce gastos imprevistos para ver cómo se absorben.</li>
        </ul>
      </div>
    )
  },
  {
    icon: Sparkles,
    iconColor: 'text-[#6e8c7b] dark:text-[#8ba898]',
    tag: 'PESTAÑA 3 & VOZ',
    title: 'Asesor Co-Pilot & Experiencia de Voz',
    subtitle: 'Razonamiento financiero de élite con soporte de voz y dictado',
    body: (
      <div className="space-y-3 text-sm leading-relaxed text-slate-700 dark:text-slate-300">
        <p>
          Tu asesor de Sherpas conoce al detalle tu expediente, tus tensiones vitales y tus objetivos:
        </p>
        <div className="p-3 rounded-xl bg-black/[0.03] dark:bg-white/[0.05] border border-black/[0.06] dark:border-white/10 space-y-2">
          <div className="flex items-center gap-2 text-xs font-semibold text-[#526e5e] dark:text-[#8ba898]">
            <Mic className="w-3.5 h-3.5" />
            <span>Dictado por voz en tiempo real:</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Pulsa el micrófono en el chat para formular consultas complejas hablando con naturalidad.
          </p>
          <div className="flex items-center gap-2 text-xs font-semibold text-[#875f52] dark:text-[#b38a7c] pt-1">
            <Volume2 className="w-3.5 h-3.5" />
            <span>Respuestas audibles:</span>
          </div>
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Pulsa el altavoz en cualquier respuesta para escuchar el diagnóstico de tu asesor con voz natural.
          </p>
        </div>
      </div>
    )
  },
  {
    icon: Sparkles,
    iconColor: 'text-emerald-600 dark:text-emerald-400',
    tag: 'SIGUIENTES PASOS',
    title: '¿Cómo prefieres comenzar?',
    subtitle: 'Elige el punto de partida que mejor se adapte a tu momento actual',
    isActionStep: true,
    body: null
  }
];

export const TutorialModal: React.FC<TutorialModalProps> = ({ 
  isOpen, 
  onClose,
  onStartFirstTask,
  onViewInitialStatus,
  onExploreFreely
}) => {
  const [step, setStep] = useState(0);

  useEffect(() => {
    if (isOpen) {
      setStep(0);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const current = STEPS[step];
  const isFirst = step === 0;
  const isLast = step === STEPS.length - 1;
  const IconComp = current.icon;

  const handleNext = () => {
    audioService.playSound('click');
    if (isLast) {
      if (onExploreFreely) onExploreFreely();
      else onClose();
      setStep(0);
    } else {
      setStep(prev => prev + 1);
    }
  };

  const handlePrev = () => {
    audioService.playSound('click');
    if (!isFirst) {
      setStep(prev => prev - 1);
    }
  };

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="fixed inset-0 bg-black/60 backdrop-blur-md"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 10 }}
          className="relative w-full max-w-lg liquid-glass-elevated rounded-3xl p-6 sm:p-7 shadow-2xl z-10 overflow-hidden"
        >
          {/* Header Close */}
          <button
            onClick={onClose}
            className="absolute top-5 right-5 p-1.5 rounded-full text-slate-400 hover:text-slate-700 dark:hover:text-white bg-black/5 dark:bg-white/5 hover:bg-black/10 dark:hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>

          {/* Step Badge & Progress */}
          <div className="flex items-center justify-between mb-4 pr-8">
            <span className="text-[10px] font-bold uppercase tracking-widest text-[#526e5e] dark:text-[#8ba898] bg-[#526e5e]/10 dark:bg-[#8ba898]/15 px-2.5 py-0.5 rounded-full">
              {current.tag}
            </span>
            <span className="text-xs font-semibold text-slate-400">
              {step + 1} de {STEPS.length}
            </span>
          </div>

          {/* Progress bar */}
          <div className="w-full h-1.5 bg-black/5 dark:bg-white/10 rounded-full mb-6 overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-[#526e5e] to-[#6e8c7b] transition-all duration-300 rounded-full"
              style={{ width: `${((step + 1) / STEPS.length) * 100}%` }}
            />
          </div>

          {/* Icon & Title */}
          <div className="flex items-start gap-3.5 mb-4">
            <div className={`p-3 rounded-2xl bg-black/[0.03] dark:bg-white/[0.06] border border-black/[0.06] dark:border-white/10 shrink-0 ${current.iconColor}`}>
              <IconComp className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900 dark:text-white font-display leading-snug">
                {current.title}
              </h3>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                {current.subtitle}
              </p>
            </div>
          </div>

          {/* Body Content */}
          <div className="min-h-[170px] py-1">
            {current.isActionStep ? (
              <div className="space-y-2.5">
                {/* Option 1: Empezar por la primera tarea */}
                <button
                  onClick={() => {
                    audioService.playSound('click');
                    if (onStartFirstTask) onStartFirstTask();
                    else onClose();
                  }}
                  className="w-full text-left p-3 rounded-2xl bg-black/[0.03] dark:bg-white/[0.05] hover:bg-emerald-500/10 dark:hover:bg-emerald-500/15 border border-black/[0.06] dark:border-white/10 hover:border-emerald-500/30 transition-all flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 shrink-0 group-hover:scale-105 transition-transform">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white group-hover:text-emerald-700 dark:group-hover:text-emerald-300 transition-colors font-display">
                        Empezar por la primera tarea
                      </h4>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                        Abre tu Plan de Acción y comienza a ejecutar la primera prioridad recomendada.
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-emerald-600 dark:group-hover:text-emerald-400 group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                </button>

                {/* Option 2: Consultar mi estado inicial */}
                <button
                  onClick={() => {
                    audioService.playSound('click');
                    if (onViewInitialStatus) onViewInitialStatus();
                    else onClose();
                  }}
                  className="w-full text-left p-3 rounded-2xl bg-black/[0.03] dark:bg-white/[0.05] hover:bg-[#875f52]/10 dark:hover:bg-[#b38a7c]/15 border border-black/[0.06] dark:border-white/10 hover:border-[#875f52]/30 transition-all flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-[#875f52]/15 text-[#875f52] dark:text-[#d8b4a0] shrink-0 group-hover:scale-105 transition-transform">
                      <FileText className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white group-hover:text-[#875f52] dark:group-hover:text-[#d8b4a0] transition-colors font-display">
                        Consultar mi estado inicial
                      </h4>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                        Revisa tu informe ejecutivo con el score actuarial, pilares y brechas de tu expediente.
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-[#875f52] dark:group-hover:text-[#d8b4a0] group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                </button>

                {/* Option 3: Permíteme explorar la app por mi cuenta */}
                <button
                  onClick={() => {
                    audioService.playSound('click');
                    if (onExploreFreely) onExploreFreely();
                    else onClose();
                  }}
                  className="w-full text-left p-3 rounded-2xl bg-black/[0.03] dark:bg-white/[0.05] hover:bg-slate-500/10 dark:hover:bg-slate-400/15 border border-black/[0.06] dark:border-white/10 hover:border-slate-500/30 transition-all flex items-center justify-between group cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-xl bg-slate-500/15 text-slate-700 dark:text-slate-300 shrink-0 group-hover:scale-105 transition-transform">
                      <Compass className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="text-xs sm:text-sm font-bold text-slate-900 dark:text-white group-hover:text-slate-700 dark:group-hover:text-slate-200 transition-colors font-display">
                        Permíteme explorar la app por mi cuenta
                      </h4>
                      <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-0.5">
                        Cierra el tutorial y navega libremente por tus proyecciones, tareas y el asesor Co-Pilot.
                      </p>
                    </div>
                  </div>
                  <ChevronRight className="w-4 h-4 text-slate-400 group-hover:text-slate-700 dark:group-hover:text-slate-300 group-hover:translate-x-0.5 transition-all shrink-0 ml-2" />
                </button>
              </div>
            ) : (
              current.body
            )}
          </div>

          {/* Footer Controls */}
          <div className="flex items-center justify-between pt-5 mt-4 border-t border-black/[0.06] dark:border-white/10">
            <button
              onClick={handlePrev}
              disabled={isFirst}
              className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                isFirst 
                  ? 'opacity-0 pointer-events-none' 
                  : 'text-slate-600 dark:text-slate-300 hover:bg-black/5 dark:hover:bg-white/10 cursor-pointer'
              }`}
            >
              <ChevronLeft className="w-3.5 h-3.5" />
              <span>Anterior</span>
            </button>

            <div className="flex items-center gap-1.5">
              {STEPS.map((_, i) => (
                <span 
                  key={i}
                  className={`w-2 h-2 rounded-full transition-all ${
                    i === step ? 'w-5 bg-[#526e5e] dark:bg-[#8ba898]' : 'bg-black/10 dark:bg-white/20'
                  }`}
                />
              ))}
            </div>

            {isLast ? (
              <button
                onClick={() => {
                  audioService.playSound('click');
                  if (onExploreFreely) onExploreFreely();
                  else onClose();
                }}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold bg-black/[0.05] dark:bg-white/[0.08] hover:bg-black/[0.08] dark:hover:bg-white/[0.12] text-slate-800 dark:text-white transition-all cursor-pointer"
              >
                <span>Explorar por mi cuenta</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold bg-[#526e5e] hover:bg-[#43594c] dark:bg-[#6e8c7b] dark:hover:bg-[#5b7566] text-white shadow-sm transition-all cursor-pointer"
              >
                <span>Siguiente</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            )}
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
