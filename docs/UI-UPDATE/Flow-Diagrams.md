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
                 | (NSPanel + WebView)|                      +-------------------+
                 +----------+----------+
                            |
                            v
                 +---------------------+
                 |  Web HUD (JS/CSS)   |
                 |  (renders glass UI) |
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
                                                             update DOM/CSS
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
   +-- on_disconnect:
           (no-op; drop events)

HUD (WKWebView)
   |
   +-- connect ws://127.0.0.1:PORT/hud?token=XYZ
   +-- auto-reconnect with backoff
   +-- update UI on messages
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
 |-- hud-macos/ (Swift, NSPanel + WKWebView host)

web/
 |-- hud/ (HTML/CSS/JS; connects to WS)

dev/
 |-- preview/overlay.py (debug-only)
```


