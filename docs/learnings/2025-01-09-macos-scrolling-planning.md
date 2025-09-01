# Learnings — macOS Scrolling Planning

## What surprised us
- CLAUDE.md requires strict process: proposal → design → tasks before any implementation
- The design-architect agent created comprehensive subsystem specs automatically
- PyObjC provides direct access to Quartz Event Services without Swift

## Decisions made (and why)
1. **Monolithic Python app for v1**: Simpler than Swift helper, one process to manage
2. **180° = 400px mapping**: Intuitive for users, roughly half screen scroll
3. **Clockwise = scroll down**: Matches physical wheel metaphor
4. **Minimal HUD**: Non-intrusive feedback without disrupting reading

## Follow-ups
- Investigate split Swift helper for v2 (better security model)
- Consider per-app scroll speed customization
- Add horizontal scrolling support later
- Profile actual latency once implemented

### PATCH SUMMARY
- Mode: Planning
- Changed files:
  - docs/proposals/macos-scrolling.md
  - docs/designs/macos-scrolling/DESIGN.md
  - docs/designs/macos-scrolling/subsystems/scroll-dispatcher.md
  - docs/designs/macos-scrolling/subsystems/quartz-scroll-action.md
  - docs/designs/macos-scrolling/subsystems/scroll-hud.md
  - docs/planning/macos-scrolling/TASKS.md
  - docs/DEPENDENCIES.md
  - docs/learnings/2025-01-09-macos-scrolling-planning.md
- Why: Plan macOS scrolling integration for hands-free document control
- How: Created proposal, comprehensive design, subsystem specs, and task breakdown
- Tests: Defined test strategy in design (unit, integration, architecture)
- Risks & Mitigations: Accessibility permissions, thread safety, performance targets documented