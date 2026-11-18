import React from 'react';

export interface BackgroundEffectProps {
  theme?: 'light' | 'dark';
  className?: string;
}

/**
 * BackgroundEffect - Apple / Linear / Stripe grade organic ambient atmosphere.
 * Ultra-subtle, slow, organic ambient glow with diffuse emerald/sage tones
 * (0.03-0.08 opacity, massive 120px+ blur) over deep muted canvas.
 */
export const BackgroundEffect: React.FC<BackgroundEffectProps> = ({ 
  theme = 'dark',
  className = ''
}) => {
  return (
    <div 
      className={`fixed inset-0 pointer-events-none overflow-hidden z-0 transition-colors duration-700 bg-[#f8faf9] dark:bg-[#070908] ${className}`}
      aria-hidden="true"
    >
      {/* Container for slow floating diffuse organic glow orbs */}
      <div className="relative w-full h-full">
        {/* Ambient Glow 1: Ultra-soft deep emerald mist (Top-Left) */}
        <div 
          className="absolute -top-[15%] -left-[10%] w-[68vw] min-w-[620px] max-w-[1100px] h-[68vw] min-h-[620px] max-h-[1100px] rounded-full will-change-transform animate-float-orb-1"
          style={{
            filter: 'blur(140px)',
            WebkitFilter: 'blur(140px)',
            background: theme === 'dark' 
              ? 'radial-gradient(circle at 48% 48%, rgba(16, 185, 129, 0.07) 0%, rgba(5, 150, 105, 0.04) 38%, rgba(6, 78, 59, 0.015) 65%, transparent 78%)'
              : 'radial-gradient(circle at 48% 48%, rgba(16, 185, 129, 0.055) 0%, rgba(110, 160, 130, 0.03) 40%, rgba(140, 180, 155, 0.01) 65%, transparent 78%)'
          }}
        />

        {/* Ambient Glow 2: Subdued sage / olive aura (Top-Right) */}
        <div 
          className="absolute -top-[12%] -right-[12%] w-[72vw] min-w-[650px] max-w-[1150px] h-[72vw] min-h-[650px] max-h-[1150px] rounded-full will-change-transform animate-float-orb-2"
          style={{
            filter: 'blur(150px)',
            WebkitFilter: 'blur(150px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(5, 150, 105, 0.065) 0%, rgba(16, 185, 129, 0.035) 42%, rgba(4, 120, 87, 0.012) 65%, transparent 78%)'
              : 'radial-gradient(circle at 50% 50%, rgba(52, 211, 153, 0.045) 0%, rgba(82, 135, 105, 0.025) 45%, transparent 78%)'
          }}
        />

        {/* Ambient Glow 3: Center-left tranquil diffuse aura */}
        <div 
          className="absolute top-[35%] -left-[8%] w-[58vw] min-w-[550px] max-w-[900px] h-[58vw] min-h-[550px] max-h-[900px] rounded-full will-change-transform animate-float-orb-3"
          style={{
            filter: 'blur(130px)',
            WebkitFilter: 'blur(130px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.05) 0%, rgba(6, 95, 70, 0.025) 45%, transparent 75%)'
              : 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.04) 0%, rgba(110, 160, 130, 0.02) 45%, transparent 75%)'
          }}
        />

        {/* Ambient Glow 4: Lower horizon ambient wash */}
        <div 
          className="absolute -bottom-[18%] right-[5%] w-[75vw] min-w-[680px] max-w-[1200px] h-[75vw] min-h-[680px] max-h-[1200px] rounded-full will-change-transform animate-float-orb-4"
          style={{
            filter: 'blur(160px)',
            WebkitFilter: 'blur(160px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(52, 211, 153, 0.04) 0%, rgba(16, 185, 129, 0.02) 48%, transparent 78%)'
              : 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.035) 0%, rgba(110, 160, 130, 0.018) 48%, transparent 78%)'
          }}
        />

        {/* Ambient Glow 5: Subtle central harmonic pulse */}
        <div 
          className="absolute top-[28%] right-[22%] w-[48vw] min-w-[460px] max-w-[750px] h-[48vw] min-h-[460px] max-h-[750px] rounded-full will-change-transform animate-float-orb-5"
          style={{
            filter: 'blur(120px)',
            WebkitFilter: 'blur(120px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.04) 0%, rgba(5, 150, 105, 0.015) 50%, transparent 75%)'
              : 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.03) 0%, rgba(130, 168, 145, 0.015) 50%, transparent 75%)'
          }}
        />
      </div>

      {/* Discrete subtle ambient vignette for depth without harsh contrast */}
      <div 
        className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-transparent to-black/[0.04] dark:to-black/[0.25]" 
      />
    </div>
  );
};

export default BackgroundEffect;
