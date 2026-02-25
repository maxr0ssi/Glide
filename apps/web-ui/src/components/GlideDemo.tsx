/**
 * GlideDemo — top-level exportable component.
 * Split-view: algorithm visualizer + scrollable demo content.
 */

import React from 'react';
import { useGlide } from '../hooks/useGlide';
import type { AppConfig } from '../core/config';
import { Visualizer } from './Visualizer';
import { ScrollArea } from './ScrollArea';
import { GestureState } from '../gestures/velocity-controller';

export interface GlideDemoProps {
  modelPath?: string;
  config?: Partial<AppConfig>;
  showVisualizer?: boolean;
  scrollContent?: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
}

export const GlideDemo: React.FC<GlideDemoProps> = ({
  modelPath,
  config,
  showVisualizer = true,
  scrollContent,
  className = '',
  style,
}) => {
  const glide = useGlide({ modelPath, config });

  const demoOnly = scrollContent === null;

  return (
    <div className={`glide-demo ${demoOnly ? 'glide-demo--full' : ''} ${className}`} style={style}>
      {showVisualizer && (
        <Visualizer
          videoRef={glide.videoRef}
          canvasRef={glide.canvasRef}
          landmarks={glide.landmarks}
          signals={glide.signals}
          gestureState={glide.gestureState}
          fps={glide.fps}
          isLoading={glide.isLoading}
          error={glide.error}
        />
      )}
      {!demoOnly && (
        <ScrollArea
          velocity={glide.velocity}
          gestureState={glide.gestureState}
          isActive={glide.gestureState === GestureState.SCROLLING}
        >
          {scrollContent}
        </ScrollArea>
      )}
    </div>
  );
};
