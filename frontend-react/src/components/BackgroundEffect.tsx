import React from 'react';

export interface BackgroundEffectProps {
  theme?: 'light' | 'dark';
  className?: string;
}

/**
 * BackgroundEffect - Ambient organic diffuse green lights (auroras).
 * Visibly diffuse, soft emerald / sage orbs floating slowly behind the glass panels.
 * Balanced to be clearly visible and elegant without being harsh or neon.
 */
export const BackgroundEffect: React.FC<BackgroundEffectProps> = ({ 
  theme = 'dark',
  className = ''
}) => {
  const isDark = theme === 'dark';

  return (
    <div 
      className={`fixed inset-0 pointer-events-none overflow-hidden z-0 transition-colors duration-700 ${
        isDark ? 'bg-[#070b09]' : 'bg-[#f4f7f5]'
      } ${className}`}
      aria-hidden="true"
    >
      {/* Container for slow floating diffuse organic glow orbs */}
      <div className="relative w-full h-full">
        {/* Ambient Glow 1: Visible, soft diffuse emerald light (Top-Left) */}
        <div 
          className="absolute -top-[10%] -left-[8%] w-[65vw] min-w-[550px] max-w-[950px] h-[65vw] min-h-[550px] max-h-[950px] rounded-full will-change-transform animate-float-orb-1"
          style={{
            filter: 'blur(90px)',
            WebkitFilter: 'blur(90px)',
            background: isDark
              ? 'radial-gradient(circle at 45% 45%, rgba(16, 185, 129, 0.24) 0%, rgba(5, 150, 105, 0.15) 42%, rgba(6, 78, 59, 0.06) 68%, transparent 80%)'
              : 'radial-gradient(circle at 45% 45%, rgba(16, 185, 129, 0.16) 0%, rgba(110, 180, 140, 0.09) 45%, rgba(140, 200, 165, 0.03) 70%, transparent 82%)'
          }}
        />

        {/* Ambient Glow 2: Large diffuse jade aura (Top-Right) */}
        <div 
          className="absolute -top-[12%] -right-[10%] w-[68vw] min-w-[580px] max-w-[1000px] h-[68vw] min-h-[580px] max-h-[1000px] rounded-full will-change-transform animate-float-orb-2"
          style={{
            filter: 'blur(95px)',
            WebkitFilter: 'blur(95px)',
            background: isDark
              ? 'radial-gradient(circle at 50% 50%, rgba(5, 150, 105, 0.22) 0%, rgba(16, 185, 129, 0.13) 45%, rgba(4, 120, 87, 0.05) 70%, transparent 82%)'
              : 'radial-gradient(circle at 50% 50%, rgba(52, 211, 153, 0.15) 0%, rgba(82, 160, 120, 0.08) 45%, transparent 80%)'
          }}
        />

        {/* Ambient Glow 3: Center-left tranquil diffuse aura */}
        <div 
          className="absolute top-[32%] -left-[10%] w-[55vw] min-w-[480px] max-w-[850px] h-[55vw] min-h-[480px] max-h-[850px] rounded-full will-change-transform animate-float-orb-3"
          style={{
            filter: 'blur(85px)',
            WebkitFilter: 'blur(85px)',
            background: isDark
              ? 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.18) 0%, rgba(6, 95, 70, 0.10) 48%, transparent 78%)'
              : 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.12) 0%, rgba(110, 180, 145, 0.06) 48%, transparent 78%)'
          }}
        />

        {/* Ambient Glow 4: Bottom-right wide ambient wash */}
        <div 
          className="absolute -bottom-[15%] right-[2%] w-[70vw] min-w-[600px] max-w-[1050px] h-[70vw] min-h-[600px] max-h-[1050px] rounded-full will-change-transform animate-float-orb-4"
          style={{
            filter: 'blur(100px)',
            WebkitFilter: 'blur(100px)',
            background: isDark
              ? 'radial-gradient(circle at 50% 50%, rgba(52, 211, 153, 0.19) 0%, rgba(16, 185, 129, 0.11) 48%, rgba(6, 78, 59, 0.04) 70%, transparent 82%)'
              : 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.13) 0%, rgba(110, 175, 140, 0.06) 48%, transparent 80%)'
          }}
        />

        {/* Ambient Glow 5: Subtle central floating accent */}
        <div 
          className="absolute top-[25%] right-[20%] w-[45vw] min-w-[420px] max-w-[700px] h-[45vw] min-h-[420px] max-h-[700px] rounded-full will-change-transform animate-float-orb-5"
          style={{
            filter: 'blur(80px)',
            WebkitFilter: 'blur(80px)',
            background: isDark
              ? 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.16) 0%, rgba(5, 150, 105, 0.08) 50%, transparent 78%)'
              : 'radial-gradient(circle at 50% 50%, rgba(16, 185, 129, 0.10) 0%, rgba(130, 180, 155, 0.05) 50%, transparent 78%)'
          }}
        />
      </div>

      {/* Discrete subtle ambient vignette for depth */}
      <div 
        className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-transparent to-black/[0.15] dark:to-black/[0.4]" 
      />
    </div>
  );
};

export default BackgroundEffect;
