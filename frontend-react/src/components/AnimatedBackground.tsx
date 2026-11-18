import React from 'react';

interface AnimatedBackgroundProps {
  theme: 'light' | 'dark';
}

export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = ({ theme }) => {
  return (
    <div 
      className="fixed inset-0 pointer-events-none overflow-hidden z-0 transition-colors duration-700 bg-[#f2f5f3] dark:bg-[#070b09]"
      aria-hidden="true"
    >
      {/* Container for the large diffuse animated green lights */}
      <div className="relative w-full h-full">
        {/* Large Light 1: Soft Sage Mist (Top-Left) */}
        <div 
          className="absolute -top-[12%] -left-[10%] w-[65vw] min-w-[600px] max-w-[950px] h-[65vw] min-h-[600px] max-h-[950px] rounded-full will-change-transform animate-float-orb-1"
          style={{
            filter: 'blur(100px)',
            WebkitFilter: 'blur(100px)',
            background: theme === 'dark' 
              ? 'radial-gradient(circle at 48% 48%, rgba(52, 120, 88, 0.26) 0%, rgba(35, 80, 60, 0.16) 42%, rgba(20, 50, 38, 0.08) 65%, transparent 80%)'
              : 'radial-gradient(circle at 48% 48%, rgba(82, 135, 105, 0.18) 0%, rgba(110, 160, 130, 0.10) 42%, rgba(140, 180, 155, 0.04) 65%, transparent 80%)'
          }}
        />

        {/* Large Light 2: Muted Olive Forest (Top-Right) */}
        <div 
          className="absolute -top-[10%] -right-[12%] w-[70vw] min-w-[650px] max-w-[1000px] h-[70vw] min-h-[650px] max-h-[1000px] rounded-full will-change-transform animate-float-orb-2"
          style={{
            filter: 'blur(110px)',
            WebkitFilter: 'blur(110px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(45, 105, 75, 0.24) 0%, rgba(30, 75, 52, 0.15) 45%, rgba(15, 45, 32, 0.06) 65%, transparent 80%)'
              : 'radial-gradient(circle at 50% 50%, rgba(95, 145, 115, 0.16) 0%, rgba(125, 168, 140, 0.09) 45%, rgba(150, 185, 165, 0.04) 65%, transparent 80%)'
          }}
        />

        {/* Large Light 3: Tranquil Jade & Eucalyptus (Mid-Left & Center) */}
        <div 
          className="absolute top-[32%] -left-[8%] w-[55vw] min-w-[550px] max-w-[850px] h-[55vw] min-h-[550px] max-h-[850px] rounded-full will-change-transform animate-float-orb-3"
          style={{
            filter: 'blur(95px)',
            WebkitFilter: 'blur(95px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(55, 125, 95, 0.22) 0%, rgba(35, 85, 65, 0.13) 42%, rgba(20, 55, 40, 0.05) 65%, transparent 80%)'
              : 'radial-gradient(circle at 50% 50%, rgba(105, 155, 130, 0.15) 0%, rgba(135, 175, 155, 0.08) 42%, rgba(160, 195, 175, 0.03) 65%, transparent 80%)'
          }}
        />

        {/* Large Light 4: Earthy Amber-Olive Horizon (Bottom-Right) */}
        <div 
          className="absolute -bottom-[15%] right-[2%] w-[70vw] min-w-[650px] max-w-[1050px] h-[70vw] min-h-[650px] max-h-[1050px] rounded-full will-change-transform animate-float-orb-4"
          style={{
            filter: 'blur(115px)',
            WebkitFilter: 'blur(115px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(65, 115, 80, 0.22) 0%, rgba(50, 90, 60, 0.14) 45%, rgba(25, 55, 35, 0.06) 65%, transparent 80%)'
              : 'radial-gradient(circle at 50% 50%, rgba(115, 150, 120, 0.15) 0%, rgba(140, 170, 145, 0.08) 45%, rgba(165, 190, 170, 0.03) 65%, transparent 80%)'
          }}
        />

        {/* Large Light 5: Gentle Ambient Core (Mid-Right / Center Pulse) */}
        <div 
          className="absolute top-[28%] right-[18%] w-[45vw] min-w-[450px] max-w-[700px] h-[45vw] min-h-[450px] max-h-[700px] rounded-full will-change-transform animate-float-orb-5"
          style={{
            filter: 'blur(90px)',
            WebkitFilter: 'blur(90px)',
            background: theme === 'dark'
              ? 'radial-gradient(circle at 50% 50%, rgba(50, 110, 80, 0.18) 0%, rgba(30, 75, 55, 0.10) 45%, transparent 75%)'
              : 'radial-gradient(circle at 50% 50%, rgba(100, 145, 120, 0.12) 0%, rgba(130, 168, 145, 0.06) 45%, transparent 75%)'
          }}
        />
      </div>

      {/* Gentle Ambient Vignette for Depth */}
      <div 
        className="absolute inset-0 pointer-events-none bg-gradient-to-b from-transparent via-transparent to-black/15 dark:to-black/35" 
      />
    </div>
  );
};
