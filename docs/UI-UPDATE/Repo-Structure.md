## Repository structure (proposed backend/frontend split)

This document proposes a cleaner split between the Python backend and a design-first HUD frontend, with minimal coupling via a localhost WebSocket. It also maps current files into the new structure and indicates new directories/files to introduce.

### High-level
- Backend (Python): gesture/perception/scroll, config, and a WS publisher
- Frontend (HUD): macOS host window + web UI (HTML/CSS/JS) consuming WS events
- Dev-only previews stay isolated from runtime code

### Top-level layout (proposed)
```
Glide/
├── README.md
├── LICENSE
├── CHANGELOG.md
├── main.py
├── models/
│   ├── hand_landmarker.task
│   └── gesture_recognizer.task
├── configs/
│   └── defaults.yaml                 # moved from glide/io/defaults.yaml
├── glide/                            # Python backend (package)
│   ├── app/
│   │   └── main.py
│   ├── core/
│   │   ├── config_models.py
│   │   ├── contracts.py
│   │   └── types.py
│   ├── engine/
│   │   └── pipeline.py
│   ├── features/
│   │   ├── alignment.py
│   │   ├── kinematics.py
│   │   └── poses.py
│   ├── gestures/
│   │   ├── touchproof.py
│   │   ├── velocity_controller.py
│   │   └── velocity_tracker.py
│   ├── io/
│   │   ├── config.py                  # (can later read from configs/)
│   │   └── defaults.yaml              # (kept temporarily for compatibility; see Migration)
│   ├── perception/
│   │   ├── camera.py
│   │   ├── hands.py
│   │   └── roi.py
│   └── runtime/
│       ├── actions/
│       │   ├── config.py
│       │   ├── continuous_scroll.py
│       │   └── velocity_dispatcher.py
│       ├── hud/
│       │   └── legacy_tk_hud.py       # moved from glide/runtime/ui/scroll_hud.py
│       └── ipc/
│           └── ws.py                   # NEW: lightweight WS broadcaster (localhost)
├── apps/
│   └── hud-macos/                      # NEW: Swift menubar app (NSPanel + WKWebView)
│       ├── Sources/
│       └── Resources/
│           └── www/                    # built web HUD assets copied here at release time
├── web/
│   └── hud/                            # NEW: Design-first HUD (HTML/CSS/JS; Vite/React or vanilla)
│       ├── index.html
│       ├── src/
│       │   ├── main.tsx (or .ts)
│       │   ├── hud.css
│       │   └── ws-client.ts
│       ├── vite.config.ts
│       └── package.json
├── dev/
│   └── preview/
│       └── overlay.py                  # moved from glide/ui/overlay.py (debug-only)
├── tests/
│   └── test_pyobjc_scroll.py
└── docs/
    ├── ARCHITECTURE.md
    ├── Scrolling.md
    ├── VelocityScrolling.md
    ├── Api.md
    ├── DEPENDENCIES.md
    ├── TouchProof.md
    └── personal-notes/
        (unchanged)
```

### File migration map (current → proposed)

| Current path | New path | Notes |
| --- | --- | --- |
| `glide/ui/overlay.py` | `dev/preview/overlay.py` | Debug-only OpenCV preview overlay, not part of runtime |
| `glide/runtime/ui/scroll_hud.py` | `glide/runtime/hud/legacy_tk_hud.py` | Kept for reference; superseded by macOS WKWebView HUD |
| `glide/io/defaults.yaml` | `configs/defaults.yaml` | Canonical config location; keep old path temporarily for compatibility |
| `glide/io/config.py` | `glide/io/config.py` | Stays; later update to read from `configs/` |
| `glide/runtime/actions/continuous_scroll.py` | same | Native macOS scroll (PyObjC Quartz) |
| `glide/runtime/actions/velocity_dispatcher.py` | same | Dispatches scroll gesture lifecycle |
| `glide/runtime/actions/config.py` | same | Runtime scroll config (dataclass) |
| `glide/core/config_models.py` | same | Pydantic config schema |
| `glide/features/*` | same | Kinematics, poses, etc. |
| `glide/gestures/*` | same | TouchProof and velocity tracking |
| `glide/perception/*` | same | Camera and hands |
| `glide/engine/pipeline.py` | same | Engine loop |
| `tests/test_pyobjc_scroll.py` | same | Tests |
| `docs/*` | same | Documentation |
| `models/*` | same | Model assets |

### New files and directories to add

- `glide/runtime/ipc/ws.py` (Python)
  - Local-only WebSocket broadcaster
  - API: `publish_scroll(vy: float, speed_0_1: float)`, `publish_hide()`
  - Throttle to 30–60 Hz, drop when no clients, optional random session token

- `apps/hud-macos/` (Swift)
  - Menubar/agent app hosting a non-activating `NSPanel` with `NSVisualEffectView`
  - Embeds `WKWebView` that loads `web/hud` build output from `Resources/www`
  - Auto-reconnects to WS; pointer-events disabled; always-on-top; joins all spaces

- `web/hud/` (Web)
  - HUD UI in HTML/CSS/JS (or React)
  - Consumes WS events and updates CSS variables/DOM for direction/speed
  - Dev via Vite (hot reload); production build copied into `apps/hud-macos/Resources/www`

- `dev/preview/overlay.py` (Python)
  - OpenCV visualization for internal debugging only

### Backend ↔ Frontend contract (WS)

Minimal event stream over `ws://127.0.0.1:<port>/hud`:
```json
{"type":"scroll","vy":-240.5,"speed":0.62}
{"type":"hide"}
```
Optional messages:
```json
{"type":"config","position":"bottom-right","opacity":0.85}
{"type":"heartbeat","t":1735945512345}
```

### Migration notes

1) Phase 1 (non-breaking):
   - Introduce `configs/` with `defaults.yaml` duplicated; keep legacy `glide/io/defaults.yaml` path working
   - Add `glide/runtime/ipc/ws.py` and start broadcasting events
   - Build `apps/hud-macos` (WKWebView) to consume `web/hud`
   - Move HUD POC to `glide/runtime/hud/legacy_tk_hud.py`; keep disabled by default

2) Phase 2 (cleanup):
   - Switch all config reads to `configs/defaults.yaml`
   - Remove duplicated legacy config file in `glide/io/`
   - Optionally remove `legacy_tk_hud.py` after full migration

### Rationale

- Clear separation of concerns: backend publishes events; frontend renders them
- Minimal, event-only interface: low latency, no REST API needed
- Design velocity: CSS/JS iterate rapidly without touching backend code
- Native feel: NSPanel + NSVisualEffectView + WKWebView for glass/vibrancy


