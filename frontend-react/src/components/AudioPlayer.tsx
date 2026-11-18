import React, { useState, useEffect, useRef, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Play, 
  Pause, 
  Volume2, 
  VolumeX, 
  Volume1, 
  X, 
  Headphones, 
  Sparkles,
  RotateCcw,
  Maximize2,
  Minimize2
} from 'lucide-react';
import { audioService } from '../services/audioService';

export interface AudioPlayerProps {
  title?: string;
  subtitle?: string;
  textToSpeak?: string;
  audioUrl?: string;
  isOpen?: boolean;
  onClose?: () => void;
  onPlayStateChange?: (isPlaying: boolean) => void;
}

export const AudioPlayer: React.FC<AudioPlayerProps> = ({
  title = "Resumen Ejecutivo de Asesoría",
  subtitle = "Informe auditado por Sherpas Living Plan",
  textToSpeak,
  audioUrl,
  isOpen = true,
  onClose,
  onPlayStateChange
}) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(0.85);
  const [playbackRate, setPlaybackRate] = useState<number>(1.0);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(48); // default estimated 48s briefing
  const [isCompact, setIsCompact] = useState(false);

  const audioRef = useRef<HTMLAudioElement | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const timerRef = useRef<number | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const [waveHeights, setWaveHeights] = useState<number[]>([12, 18, 28, 16, 22, 34, 20, 14, 26, 38, 18, 24, 12]);

  // Handle play state notification
  useEffect(() => {
    onPlayStateChange?.(isPlaying);
  }, [isPlaying, onPlayStateChange]);

  // Dynamic waveform animation when playing
  useEffect(() => {
    if (!isPlaying) {
      setWaveHeights([8, 10, 14, 10, 12, 16, 12, 8, 14, 16, 10, 12, 8]);
      return;
    }

    let t = 0;
    const updateWave = () => {
      t += 0.15;
      const next = [
        10 + Math.sin(t * 1.8) * 8 + 6,
        14 + Math.sin(t * 2.2 + 1) * 12 + 6,
        22 + Math.sin(t * 1.5 + 2) * 16 + 8,
        12 + Math.sin(t * 2.7 + 3) * 10 + 6,
        18 + Math.sin(t * 1.9 + 4) * 14 + 8,
        28 + Math.sin(t * 2.4 + 5) * 18 + 10,
        16 + Math.sin(t * 1.7 + 6) * 12 + 8,
        12 + Math.sin(t * 2.5 + 7) * 9 + 6,
        20 + Math.sin(t * 2.0 + 8) * 15 + 8,
        26 + Math.sin(t * 1.6 + 9) * 18 + 10,
        14 + Math.sin(t * 2.8 + 10) * 11 + 6,
        18 + Math.sin(t * 2.1 + 11) * 13 + 8,
        10 + Math.sin(t * 1.9 + 12) * 8 + 6,
      ];
      setWaveHeights(next);
      animationFrameRef.current = requestAnimationFrame(updateWave);
    };

    animationFrameRef.current = requestAnimationFrame(updateWave);

    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [isPlaying]);

  // Clean markdown for speech
  const getSpeechText = useCallback(() => {
    if (textToSpeak) {
      return textToSpeak
        .replace(/[*_#`~[\]]/g, '')
        .replace(/https?:\/\/\S+/g, '')
        .replace(/\n+/g, '. ')
        .trim();
    }
    return `Plan financiero vivo sincronizado. Todas las metas y recomendaciones estratégicas han sido recalculadas con el motor actuarial. Puedes revisar las proyecciones y simulaciones en cualquier momento.`;
  }, [textToSpeak]);

  // Start speech synthesis or HTML audio
  const handleTogglePlay = () => {
    audioService.playSound('click');

    if (isPlaying) {
      // Pause
      if (audioRef.current && audioUrl) {
        audioRef.current.pause();
      } else if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.pause();
      }
      setIsPlaying(false);
      if (timerRef.current) clearInterval(timerRef.current);
    } else {
      // Play
      if (audioUrl && audioRef.current) {
        audioRef.current.play().catch(() => {});
        setIsPlaying(true);
      } else if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        if (window.speechSynthesis.paused) {
          window.speechSynthesis.resume();
          setIsPlaying(true);
        } else {
          window.speechSynthesis.cancel();
          const clean = getSpeechText();
          const estDuration = Math.max(15, Math.ceil(clean.split(' ').length / 2.5));
          setDuration(estDuration);

          const utterance = new SpeechSynthesisUtterance(clean);
          utterance.lang = 'es-ES';
          utterance.rate = playbackRate;
          utterance.volume = isMuted ? 0 : volume;

          // Spanish voice
          const voices = window.speechSynthesis.getVoices();
          const spanishVoice = voices.find(v => v.lang.startsWith('es') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Neural') || v.name.includes('Monica') || v.name.includes('Jorge'))) 
            || voices.find(v => v.lang.startsWith('es'));
          if (spanishVoice) utterance.voice = spanishVoice;

          utterance.onstart = () => {
            setIsPlaying(true);
          };
          utterance.onend = () => {
            setIsPlaying(false);
            setCurrentTime(0);
            if (timerRef.current) clearInterval(timerRef.current);
          };
          utterance.onerror = () => {
            setIsPlaying(false);
            if (timerRef.current) clearInterval(timerRef.current);
          };

          utteranceRef.current = utterance;
          window.speechSynthesis.speak(utterance);
          setIsPlaying(true);
        }
      }

      // Progress interval timer
      if (timerRef.current) clearInterval(timerRef.current);
      timerRef.current = window.setInterval(() => {
        setCurrentTime((prev) => {
          if (prev >= duration) {
            setIsPlaying(false);
            if (timerRef.current) clearInterval(timerRef.current);
            return 0;
          }
          return prev + 1;
        });
      }, 1000 / playbackRate);
    }
  };

  const handleRestart = () => {
    audioService.playSound('click');
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    if (audioRef.current) {
      audioRef.current.currentTime = 0;
    }
    setCurrentTime(0);
    setIsPlaying(false);
    if (timerRef.current) clearInterval(timerRef.current);
  };

  const handleToggleSpeed = () => {
    audioService.playSound('click');
    const speeds = [1.0, 1.25, 1.5];
    const nextIdx = (speeds.indexOf(playbackRate) + 1) % speeds.length;
    const nextSpeed = speeds[nextIdx];
    setPlaybackRate(nextSpeed);

    if (audioRef.current) {
      audioRef.current.playbackRate = nextSpeed;
    }
    if (isPlaying) {
      // Re-trigger with new rate seamlessly
      handleRestart();
      setTimeout(handleTogglePlay, 50);
    }
  };

  const handleVolumeChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = parseFloat(e.target.value);
    setVolume(val);
    if (val === 0) {
      setIsMuted(true);
    } else {
      setIsMuted(false);
    }
    if (audioRef.current) {
      audioRef.current.volume = val;
    }
  };

  const handleToggleMute = () => {
    audioService.playSound('click');
    setIsMuted(!isMuted);
    if (audioRef.current) {
      audioRef.current.muted = !isMuted;
    }
  };

  const handleClose = () => {
    audioService.playSound('click');
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
    }
    setIsPlaying(false);
    if (timerRef.current) clearInterval(timerRef.current);
    onClose?.();
  };

  const formatTime = (secs: number) => {
    const m = Math.floor(secs / 60);
    const s = Math.floor(secs % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 24, scale: 0.98 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 24, scale: 0.98 }}
        transition={{ type: "spring", stiffness: 380, damping: 28 }}
        className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-[94%] max-w-xl"
      >
        <div className="relative rounded-2xl bg-white/80 dark:bg-zinc-900/85 backdrop-blur-2xl border border-black/[0.08] dark:border-white/[0.1] shadow-2xl shadow-emerald-950/10 p-3 sm:p-4 text-slate-800 dark:text-slate-100 transition-all">
          
          {audioUrl && (
            <audio
              ref={audioRef}
              src={audioUrl}
              onTimeUpdate={() => audioRef.current && setCurrentTime(audioRef.current.currentTime)}
              onLoadedMetadata={() => audioRef.current && setDuration(audioRef.current.duration)}
              onEnded={() => {
                setIsPlaying(false);
                setCurrentTime(0);
              }}
            />
          )}

          {/* Compact View */}
          {isCompact ? (
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 min-w-0">
                <button
                  onClick={handleTogglePlay}
                  className="w-8 h-8 rounded-full bg-emerald-600 hover:bg-emerald-500 text-white flex items-center justify-center shrink-0 shadow-sm cursor-pointer transition-transform active:scale-95"
                  title={isPlaying ? "Pausar" : "Reproducir"}
                >
                  {isPlaying ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4 ml-0.5" />}
                </button>
                <div className="truncate">
                  <span className="text-xs font-semibold truncate block">{title}</span>
                  <span className="text-[10px] text-slate-500 dark:text-slate-400 font-mono">
                    {formatTime(currentTime)} / {formatTime(duration)}
                  </span>
                </div>
              </div>

              {/* Minimal Waveform */}
              <div className="flex items-center gap-1 h-6 px-2">
                {waveHeights.slice(0, 7).map((h, i) => (
                  <span
                    key={i}
                    style={{ height: `${h * 0.5}px` }}
                    className={`w-0.5 rounded-full transition-all duration-100 ${
                      isPlaying ? 'bg-emerald-500 dark:bg-emerald-400' : 'bg-slate-300 dark:bg-zinc-700'
                    }`}
                  />
                ))}
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                <button
                  onClick={() => setIsCompact(false)}
                  className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-white rounded-lg transition-colors cursor-pointer"
                  title="Expandir"
                >
                  <Maximize2 className="w-3.5 h-3.5" />
                </button>
                <button
                  onClick={handleClose}
                  className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-white rounded-lg transition-colors cursor-pointer"
                  title="Cerrar"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ) : (
            /* Full Minimalist Ergonomic View */
            <div className="space-y-3">
              {/* Top Row: Track Meta & Controls */}
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500/15 to-emerald-600/5 dark:from-emerald-400/20 dark:to-emerald-600/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
                    <Headphones className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                    {isPlaying && (
                      <span className="absolute -top-1 -right-1 w-2.5 h-2.5 rounded-full bg-emerald-500 ring-2 ring-white dark:ring-zinc-900 animate-pulse" />
                    )}
                  </div>
                  <div className="truncate">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-semibold text-slate-900 dark:text-white truncate">
                        {title}
                      </span>
                      <span className="inline-flex items-center gap-0.5 text-[9px] uppercase tracking-wider font-mono text-emerald-700 dark:text-emerald-300 bg-emerald-500/10 px-1.5 py-0.5 rounded-full border border-emerald-500/20">
                        <Sparkles className="w-2.5 h-2.5" /> AI Voice
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-0.5">
                      {subtitle}
                    </p>
                  </div>
                </div>

                <div className="flex items-center gap-1 shrink-0">
                  <button
                    onClick={() => setIsCompact(true)}
                    className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-white rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
                    title="Minimizar a modo barra"
                  >
                    <Minimize2 className="w-3.5 h-3.5" />
                  </button>
                  <button
                    onClick={handleClose}
                    className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-white rounded-lg hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
                    title="Cerrar reproductor"
                  >
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Middle Row: Waveform Visualizer */}
              <div className="h-8 flex items-center justify-center gap-1.5 px-3 py-1 rounded-xl bg-black/[0.02] dark:bg-white/[0.02] border border-black/[0.04] dark:border-white/[0.04]">
                {waveHeights.map((h, i) => (
                  <motion.span
                    key={i}
                    animate={{ height: `${h}px` }}
                    transition={{ type: "spring", stiffness: 300, damping: 20 }}
                    className={`w-1 rounded-full transition-colors duration-150 ${
                      isPlaying 
                        ? 'bg-emerald-600 dark:bg-emerald-400 shadow-[0_0_8px_rgba(16,185,129,0.3)]' 
                        : 'bg-slate-300/80 dark:bg-zinc-700/80'
                    }`}
                  />
                ))}
              </div>

              {/* Linear Progress Bar */}
              <div className="space-y-1">
                <div 
                  className="relative w-full h-1.5 bg-slate-200 dark:bg-zinc-800 rounded-full overflow-hidden cursor-pointer group"
                  onClick={(e) => {
                    const rect = e.currentTarget.getBoundingClientRect();
                    const ratio = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
                    const newTime = ratio * duration;
                    setCurrentTime(newTime);
                    if (audioRef.current) audioRef.current.currentTime = newTime;
                  }}
                >
                  <div
                    className="absolute left-0 top-0 bottom-0 bg-emerald-500 rounded-full transition-all duration-200"
                    style={{ width: `${Math.min(100, (currentTime / (duration || 1)) * 100)}%` }}
                  />
                </div>
                <div className="flex justify-between items-center text-[10px] text-slate-400 dark:text-slate-500 font-mono">
                  <span>{formatTime(currentTime)}</span>
                  <span>{formatTime(duration)}</span>
                </div>
              </div>

              {/* Bottom Controls Ribbon */}
              <div className="flex items-center justify-between pt-1 border-t border-black/[0.04] dark:border-white/[0.05]">
                {/* Left: Playback Rate */}
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={handleToggleSpeed}
                    className="px-2 py-0.5 rounded-md text-[11px] font-mono font-medium text-slate-600 dark:text-slate-300 hover:text-emerald-600 dark:hover:text-emerald-400 bg-black/[0.03] dark:bg-white/[0.05] hover:bg-black/[0.06] dark:hover:bg-white/[0.08] transition-colors cursor-pointer"
                    title="Velocidad de reproducción"
                  >
                    {playbackRate}x
                  </button>
                  <button
                    onClick={handleRestart}
                    className="p-1.5 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 rounded-md transition-colors cursor-pointer"
                    title="Reiniciar reproducción"
                  >
                    <RotateCcw className="w-3.5 h-3.5" />
                  </button>
                </div>

                {/* Center: Play/Pause Big Tactile Button */}
                <button
                  onClick={handleTogglePlay}
                  className="px-5 py-1.5 rounded-full bg-emerald-600 hover:bg-emerald-500 active:scale-95 text-white font-medium text-xs flex items-center gap-1.5 shadow-md shadow-emerald-700/20 transition-all cursor-pointer"
                >
                  {isPlaying ? (
                    <>
                      <Pause className="w-3.5 h-3.5 fill-current" />
                      <span>Pausar</span>
                    </>
                  ) : (
                    <>
                      <Play className="w-3.5 h-3.5 fill-current ml-0.5" />
                      <span>{currentTime > 0 ? 'Continuar' : 'Escuchar'}</span>
                    </>
                  )}
                </button>

                {/* Right: Volume Slider */}
                <div className="flex items-center gap-1.5">
                  <button
                    onClick={handleToggleMute}
                    className="p-1 text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors cursor-pointer"
                    title={isMuted ? "Activar audio" : "Silenciar"}
                  >
                    {isMuted || volume === 0 ? (
                      <VolumeX className="w-4 h-4" />
                    ) : volume < 0.5 ? (
                      <Volume1 className="w-4 h-4" />
                    ) : (
                      <Volume2 className="w-4 h-4" />
                    )}
                  </button>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                    value={isMuted ? 0 : volume}
                    onChange={handleVolumeChange}
                    className="w-16 h-1 bg-slate-200 dark:bg-zinc-700 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    title={`Volumen: ${Math.round((isMuted ? 0 : volume) * 100)}%`}
                  />
                </div>
              </div>

            </div>
          )}
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default AudioPlayer;
