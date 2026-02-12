# Proposal: Glide Web UI → Personal Website Integration

## The Idea

Two goals, one project:

1. **Get better at using AI tools** — this entire TypeScript port was built with Claude Code, from planning through 78 passing tests. Practicing the workflow of specifying intent, reviewing output, and iterating on a real codebase.

2. **Add Glide to my personal website** — I built a touch-free gesture control system in Python + Swift. Rather than just describing it on a project card, visitors can *try it themselves* in the browser. What better way to showcase something you've built than letting people use it.

## What Exists

### Glide Web UI (`apps/web-ui/`)

A TypeScript port of Glide's core detection pipeline, packaged as a React library:

- **`useGlide` hook** — full pipeline: camera → MediaPipe → alignment → kinematics → poses → TouchProof → velocity. Returns `{ videoRef, signals, gestureState, landmarks, fps }`.
- **`<GlideDemo />`** — ready-made split-view component (visualizer + scroll area). Works but uses its own styling.
- **All detection runs client-side** — MediaPipe WASM, no server needed. ~25MB model download (browser-cached).

Published to GitHub Packages as `@maxr0ssi/glide-web-ui`.

### Personal Website (`ResumeAI/apps/web/`)

React 18 + Vite + TypeScript + Tailwind. State-based SPA with two views:

- **Proto** (frontpage) — sticky-scroll sections: hero → stats → projects → chat
- **ConversationalCanvas** — RAG-powered chat about my experience

Glide already has a project card in the projects section. Currently it just shows a description and tags.

## Integration Plan

### How It Gets There

```
Glide repo                          ResumeAI repo
─────────                           ──────────────
apps/web-ui/src/  ──build:lib──►  @maxr0ssi/glide-web-ui (GitHub Packages)
                                          │
                                    npm install
                                          │
                                    apps/web/src/
                                    └── components/GlideDemo/
                                        └── uses useGlide hook
```

- **Glide CI** publishes `@maxr0ssi/glide-web-ui` to GitHub Packages on push to `main`
- **ResumeAI** installs it via `.npmrc` with a GitHub token
- No source code duplication — single source of truth in the Glide repo

### How It Looks

The `useGlide` hook is the integration point. Import it, get the raw signals, build a UI that matches the personal site's design system (Tailwind + CSS variables). The pre-built `<GlideDemo />` component is available too but the hook gives full control.

Possible placements on the site:
- **"Try it" button on the Glide project card** → opens a full-screen overlay
- **Dedicated section** in the Proto scroll layout
- **Separate route** (`/glide`)

The right choice depends on how prominent it should be vs. how much it interrupts the existing flow. A project card button → overlay is the least disruptive starting point.

### What Visitors Experience

1. Click "Try Demo" on the Glide project card
2. Browser requests camera access
3. MediaPipe model loads (~25MB, cached after first visit)
4. Live hand tracking appears — pinch index + middle fingers to scroll
5. Signal dashboard shows the detection algorithm in real-time
6. Close overlay to return to the site

### Auth & Deployment

- ResumeAI's deployment (Vercel/Netlify) needs `GITHUB_TOKEN` as an env secret to install from GitHub Packages at build time
- `.npmrc` in ResumeAI configures the `@maxr0ssi` scope to use GitHub's npm registry
- The token only needs `read:packages` scope

## Open Questions

- **UX placement**: Overlay vs. section vs. route — try overlay first, iterate
- **Mobile**: MediaPipe works on mobile browsers but camera position (front-facing, held at arm's length) is very different from laptop webcam. May need different thresholds or a "desktop only" note.
- **Model size**: 25MB first-load could be slow on mobile. Consider lazy-loading only when the user clicks "Try Demo" (the hook's `enabled` prop supports this).
- **MFC tuning**: Optical flow is excluded from the web port. If false positive rate is too high, bump `fusedEnterThreshold` by ~0.05.

## Non-Goals

- No backend changes to either project
- No changes to the Python/Swift Glide pipeline
- Not building a full web app — just an embeddable demo component
