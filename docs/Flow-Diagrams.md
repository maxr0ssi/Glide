## Macro Flow Diagrams

High-level ASCII diagrams of the proposed architecture, using simple characters (| / \ - =).

### 1) System overview
```
                  +-------------------+
                  |     macOS UI      |
                  |  (User perceives) |
                  +---------^---------+
                            |
                     Quartz scroll
                            |
 +--------------------------+---------------------------+
 |                      Python Backend                  |
 |                                                     |
 |  +-----------+     +-----------+     +-----------+  |
 |  | Perception| --> |  Features | --> |  Gestures |  |
 |  | (Camera & |     |(Kinematics|     | (Touch-   |  |
 |  |  Hands)   |     |  etc.)    |     |  Proof)   |  |
 |  +-----+-----+     +-----+-----+     +-----+-----+  |
 |        |                  |                 |        |
 |        v                  v                 v        |
 |                  +-------------------------------+   |
 |                  | Velocity Controller/Tracker   |   |
 |                  +-------------------+-----------+   |
 |                                      |               |
 |                         +------------+------------+  |
 |                         |                         |  |
 |                         v                         v  |
 |           +------------------------+    +---------------------+
 |           | VelocityScroll         |    |  IPC: WS Publisher  |
 |           | Dispatcher             |    |  (localhost only)   |
 |           +-----------+------------+    +----------+----------+
 |                       |                            |
 |                       v                            |
 |           +------------------------+               |
 |           | ContinuousScrollAction |               |
 |           |  (Quartz, phases)      |               |
 |           +-----------+------------+               |
 +-----------------------|----------------------------+               
                         |                                           
                         v                                           
                 posts native scroll                                  
                                                                        
                 +---------------------+      WebSocket       +-------------------+
                 |  HUD macOS App     | <------------------- |    WS (backend)   |
                 | (Native Swift/AppKit)|                     +-------------------+
                 | NSPanel + Core Anim. |
                 +---------------------+
                            |
                            v
                 +---------------------+
                 | Native UI Rendering  |
                 | (Ice aesthetic)      |
                 +---------------------+
```

### 2) Runtime frame → scroll → HUD update (sequence)
```
Camera -> Hands -> Features -> Gestures -> Velocity -> Dispatcher
   |         |         |           |            |           |
   v         v         v           v            v           v
[frame] -> [landmarks] -> [signals] -> [state/vel] -> [dispatch]
                                                       /      \
                                                      /        \
                                              [Quartz]          [WS broadcast]
                                                 |                    |
                                                 v                    v
                                        native scroll event     HUD receives JSON
                                                                   |
                                                                   v
                                                            update native UI
                                                            |           |
                                                            |           +--> Expanded mode: also update camera preview
                                                            +--> Minimized mode: HUD only (no camera)
```

### 3) WebSocket session lifecycle
```
Backend WS (127.0.0.1:PORT)
   |
   +-- on_client_connect(token?):
   |       send {type: "config", ...}
   |
   +-- on_scroll_update(vy, speed):
   |       send {type: "scroll", vy, speed}
   |
   +-- on_idle_timeout:
   |       send {type: "hide"}
   |
   +-- on_touchproof_change(active, hands):
   |       send {type: "touchproof", active, hands}
   |
   +-- on_camera_frame (expanded-only, throttled ~10 FPS):
   |       send {type: "camera", frame: <base64_jpeg>}
   |
   +-- on_disconnect:
           (no-op; drop events)

HUD (Native Swift App)
   |
   +-- connect ws://127.0.0.1:PORT/hud?token=XYZ
   +-- auto-reconnect with backoff  
   +-- update native UI on messages
   +-- two modes:
       - minimized: render arrows + speed bars only
       - expanded: render arrows + speed + camera + touchproof
   +-- handle CMD+CTRL+G hotkey
```

### 4) Module boundaries (textual map)
```
glide/ (backend)
 |-- perception/ -> features/ -> gestures/ -> runtime/actions/
 |                                                   |
 |                                                   +-> continuous_scroll.py (Quartz)
 |                                                   |
 |                                                   +-> velocity_dispatcher.py
 |
 |-- runtime/ipc/ws.py  (WebSocket broadcaster)

apps/
 |-- hud-macos/ (Native Swift app with WebSocket client)

dev/
 |-- preview/overlay.py (debug-only)
```


