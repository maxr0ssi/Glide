/**
 * ScrollArea — scrollable demo content that responds to Glide gestures.
 */

import React, { useRef, useEffect } from 'react';
import { GestureState } from '../gestures/velocity-controller';
import type { Vec2D } from '../gestures/velocity-tracker';

interface ScrollAreaProps {
  velocity: Vec2D | null;
  gestureState: GestureState;
  isActive: boolean;
  children?: React.ReactNode;
}

const DEFAULT_CONTENT = (
  <>
    <h2>Scroll Demo</h2>
    <p>
      This area responds to your Glide gestures. Pinch your index and middle
      fingers together, then move them up or down to scroll.
    </p>
    {Array.from({ length: 20 }, (_, i) => (
      <div key={i} className="glide-scroll-section">
        <h3>Section {i + 1}</h3>
        <p>
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do
          eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad
          minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip
          ex ea commodo consequat.
        </p>
        <p>
          Duis aute irure dolor in reprehenderit in voluptate velit esse cillum
          dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non
          proident, sunt in culpa qui officia deserunt mollit anim id est
          laborum.
        </p>
      </div>
    ))}
  </>
);

export const ScrollArea: React.FC<ScrollAreaProps> = ({
  velocity,
  gestureState,
  isActive,
  children,
}) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!isActive || gestureState !== GestureState.SCROLLING || !velocity) return;
    if (!scrollRef.current) return;

    // Natural scrolling: drag down → scroll up (negate vy)
    const scrollPixels = -velocity.y * 1400;

    scrollRef.current.scrollBy({ top: scrollPixels / 60 });
  }, [velocity, gestureState, isActive]);

  return (
    <div
      ref={scrollRef}
      className={`glide-scroll-area ${isActive ? 'glide-scroll-area--active' : ''}`}
    >
      {children ?? DEFAULT_CONTENT}
    </div>
  );
};
