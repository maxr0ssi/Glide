import './styles/glide-demo.css';

export { GlideDemo } from './components/GlideDemo';
export { useGlide } from './hooks/useGlide';
export type {
  GlideDemoProps,
} from './components/GlideDemo';
export type {
  GateState,
  Landmark,
  BBox,
  HandDet,
  PoseFlags,
} from './core/types';
export type {
  AppConfig,
  TouchProofConfig,
  KinematicsConfig,
} from './core/config';
export type {
  TouchProofSignals,
} from './gestures/touchproof-signals';
export type {
  GestureState,
  VelocityUpdate,
} from './gestures/velocity-controller';
export type {
  Vec2D,
} from './gestures/velocity-tracker';
