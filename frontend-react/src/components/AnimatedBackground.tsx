import React from 'react';
import { BackgroundEffect, BackgroundEffectProps } from './BackgroundEffect';

export interface AnimatedBackgroundProps extends BackgroundEffectProps {}

/**
 * AnimatedBackground re-exports BackgroundEffect to maintain seamless integration.
 */
export const AnimatedBackground: React.FC<AnimatedBackgroundProps> = (props) => {
  return <BackgroundEffect {...props} />;
};

export default AnimatedBackground;
