## HUD Implementation Plan (On-Device)

Scope: Build a design-first, “liquid glass” HUD with a clean backend/frontend split. On-device only for now (no packaging/distribution). Limited QA in Phase 7.

### Phase 1 — Restructure only (no new logic)
- Move files to the new tree per `docs/UI-UPDATE/REPO_STRUCTURE.md`.
- Update imports/paths; keep temporary shims so old paths still work.
- Keep `legacy_tk_hud.py` disabled by default.
- Update docs where paths change.

### Phase 2 — Backend WS streaming (no HUD yet)
- Add `glide/runtime/ipc/ws.py` (localhost WebSocket broadcaster).
- Config surface: `scroll.hud.enabled`, `scroll.hud.ws_port`, optional session token.
- Publish events from `VelocityScrollDispatcher`: `scroll(vy,speed_0_1)` and `hide()`.
- Throttle 30–60 Hz; drop when no clients; reconnect-safe.

### Phase 3 — Web HUD skeleton
- Create `web/hud` (Vite + vanilla/React) with minimal visuals.
- Connect to WS; render direction + speed bars; fade in/out.
- Dev flow: hot reload; env var for WS port.

### Phase 4 — macOS host app (WKWebView)
- Create `apps/hud-macos` (Swift; NSPanel + NSVisualEffectView + WKWebView).
- Non-activating, always-on-top, joins all Spaces, ignores mouse.
- In dev: load Vite server URL; in local prod: load built `Resources/www`.
- Reconnect logic to WS; small menu to quit.

### Phase 5 — Integration polish
- Backend flags: `--no-hud`, `--hud-dev-url` (optional).
- Config: `hud_position`, `hud_opacity`, `hud_fade_duration_ms`.
- Normalize speed mapping/epsilon to reduce WS spam.
- Optional: backend sends `config` on connect.

### Phase 6 — “Liquid glass” visuals - (prerequisite) I will Design this in Figma before we commence
- CSS: blur, vibrancy-friendly layering, subtle motion, reduced flicker.
- Validate light/dark modes; multiple positions/scales.
- Respect reduced motion preferences.

### Phase 7 — Limited on-device QA
- Stability across sleep/wake, display changes, multi-space.
- Perf: CPU impact at 60 Hz WS streaming + HUD render.
- Reconnect behavior; error surfaces (no WS server, token mismatch).

### Out of scope (for now)
- Packaging/signing/notarization builds.
- Telemetry/analytics.
- Multi-user or remote connectivity.

### Risks/Notes
- Keep WS bound to `127.0.0.1`; include a random session token.
- Separate process for HUD avoids UI runloop issues in Python.
- Leave config at legacy path temporarily; remove in cleanup pass.


