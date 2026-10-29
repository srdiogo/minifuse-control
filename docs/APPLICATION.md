# Application architecture and UX specification

Status: planned implementation. This document describes the complete product
architecture rather than an installable mock or a disposable prototype.

## Structure

```text
src/minifuse_control/
  app.py                   Qt application lifecycle and single instance
  client/                  bounded socket adapter and version negotiation
  models/                  confirmed state, capabilities and operation status
  presentation/            view models; no USB selectors
  desktop/                 separately packageable activation policy/agent
qml/
  Main.qml
  pages/                   Mixer, Routing, Presets, Device/Diagnostics
  components/              ChannelStrip, MasterStrip, RoutePicker, status views
assets/                    owned icon and desktop entry sources
tests/                     offscreen UI, contract and session tests
packaging/                 future packaging and optional user-session units
```

Keep socket I/O event-driven (`QLocalSocket` or a bounded worker adapter).
Model updates enter Qt through signals on the GUI thread. No hardware access,
journal sync, blocking socket operation or command subprocess runs in a slider
callback. The adapter translates wire DTOs into view models; QML never computes
USB selectors or implements gain quantization.

## Primary workspace

Provide separate out12, out34 and loopback mix views with a stable master area.
Each supported source strip shows its name, configured gain/pan and mute/solo.
Present analog mono/USB pair membership only where advertised by capabilities.
Use horizontal scrolling at narrow widths without hiding the master/route.
Include precise numeric entry and a clear −infinity representation.

Show the selected route next to the corresponding mix. If USB direct or
another output route bypasses that mix, explain that the mix faders do not
control the currently selected destination. Keep host/PipeWire volume distinct
from these hardware mix controls; do not label both as the same volume.

Presets provide Save As, Inspect, Compare, Restore Preview and explicit Apply.
Snapshots preserve the existing schema. Display unsupported/omitted restore
differences, selected mix scope and source-removal mute/solo side effects before
confirmation. Importing a file is read-only until the user applies a plan.
Save/export files exclusively and show a usable filename on errors.

Device/Diagnostics shows model, connection, service/API compatibility,
capability limitations and operation references. Keep raw technical details
behind an optional diagnostics disclosure; normal control flows use clear
messages with recovery actions.

## Interaction and state model

| State | UI behavior |
|---|---|
| Service unavailable | Explain connection/start action; device writes disabled |
| API incompatible | Explain required component update; no fallback to terminal parsing |
| No device | Keep app usable for offline preset inspection |
| Unsupported/ambiguous device | Explain limitation; do not choose a unit implicitly |
| Ready | Render confirmed state and enable advertised operations |
| Editing | Show local preview separately; no device write during initial-release drag |
| Applying | Queue one explicit commit, show progress; prevent conflicting edits |
| Verified | Replace preview with confirmed result; show success briefly |
| Stale state/device | Discard invalid plan; refresh and let the user reapply deliberately |
| Failure/uncertain outcome | Show rollback/journal outcome; block further writes pending fresh state |
| Reconnected | Obtain fresh baseline; never apply pending edits from the old connection |

Mute/solo clicks and route/membership changes are explicit commits. Faders
commit on release; numeric edits commit on Enter or intentional focus departure
according to one documented rule. Escape, closing, switching away or device
removal discards uncommitted edits. Programmatic model refresh must not emit a
write. A service event cannot overwrite an active local edit silently; flag a
conflict and refresh/resolve it before applying.

A timeout is not proof of failure or permission to repeat a write. Query the
operation identity, surface an indeterminate result if necessary and refresh.
Do not manufacture success because a button changed color.

## Capabilities and truthful indicators

The first release uses only the mapped MF4 control subset. MF1/MF2 discovery
must not expose an MF4 mixer; legacy CLI availability can be explained.
Hide or explain unavailable functions rather than sending guessed selectors.

INST/+48 V indicators require reliable backend readback, not remembered last
commands. Shared phantom power must be presented as shared where supported.
Meters remain unavailable until a calibrated source is implemented. Input
trims are read-only as established by the current backend. No mix-copy or
unsupported mono/stereo conversion is implied by visual stereo grouping.

Use distinct labels for local preview, host preset saved and device readback
verified. Never claim the device has saved to flash based on those states.

## Visual design and accessibility

Use English source strings and translation-ready labels. Start with a clear,
independent visual identity and the useful mixer organization of the reference
application. Do not copy proprietary assets or require an Arturia logo.

Support keyboard focus/activation, readable labels and values, accessible names
for mute/solo/pan/faders, numeric editing, contrast beyond color-only state,
HiDPI/fractional scaling and reduced-motion preferences. Test both light/dark
palettes. Theme changes must not reset model state or trigger operations.
Generic QML controls can later share design tokens with the plugin; host-only
Omarchy imports remain in the plugin repository.
