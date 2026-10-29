# Application architecture and UX specification

Status: implemented development architecture. Hardware, Wayland and packaging
release acceptance remain open.

## Structure

```text
src/minifuse_control/
  app.py                   application lifecycle and single instance
  client.py                bounded QLocalSocket adapter and negotiation
  controller.py            confirmed state, capabilities, plans and outcomes
  live.py                  one in-flight sample plus one latest desired value
  preferences.py           private durable identity and preferences
  desktop.py               standard-library activation policy/agent
  qml/                     mixer strips, presets, device/diagnostics
  assets/                  owned icon
tests/                     offscreen pointer, contract and local socket tests
packaging/                 desktop entry and optional agent user unit
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
Include precise numeric entry and a clear −infinity representation. Source and
master strips share fixed header/footer regions and the same central control
geometry, including scrollbar space. Captions, dB values, track endpoints and
numeric entries align across strips. Fader values keep one numeric format;
operation feedback belongs in the status area. A short window scrolls the
mixer vertically rather than compressing controls below their usable height.

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
| Editing | Render local motion immediately; submit bounded, verified intermediate values |
| Applying | One sample in flight plus one replaceable latest value; prevent conflicting controls |
| Verified | Replace preview with confirmed result; show success briefly |
| Stale state/device | Discard invalid plan; refresh and let the user reapply deliberately |
| Failure/uncertain outcome | Show rollback/journal outcome; block further writes pending fresh state |
| Reconnected | Obtain fresh baseline; never apply pending edits from the old connection |

The application automatically reads state on connection and follows service
events. Manual refresh belongs in diagnostics. Mute/solo clicks and
route/membership changes are deliberate immediate commits. Faders/pan submit
while moving, initially at most once per 80 ms and only after the prior sample
settles. Release retains the latest value and sends a final sample. This is a
scheduling bound, not a measured hardware latency promise.

Numeric levels commit on Enter; Escape and focus loss discard numeric edits.
Escape/closing/switching mix stops the current gesture without undoing already
confirmed changes or applying unsent motion. Programmatic refresh, layout and
theme changes never emit writes. Own verified state events update the baseline
without resetting the active pointer preview; an external change ends the old
gesture. Other mutations remain disabled until settlement/reconciliation.

A timeout is not proof of failure or permission to repeat a write. Query the
operation identity, surface an indeterminate result if necessary and refresh.
Do not manufacture success because a button changed color.

## Capabilities and truthful indicators

The first release uses only the mapped MF4 control subset. MF1/MF2 discovery
must not expose an MF4 mixer; legacy CLI availability can be explained.
Hide or explain unavailable functions rather than sending guessed selectors.

MF4 INST1, INST2 and shared +48 V indicators use authoritative `state.inputs`
readback on connection and state events. The UI displays On/Off text as well as
highlighting, with accessible checkbox state. A click submits a discrete typed
plan/apply action; the indicator changes only after confirmed device state.
Writes require `input_switches`; an older module retains read-only indicators.
Phantom power is labelled as shared by inputs 1–2 and is excluded from mixer
preset restoration. No automatic input-mode or power restoration is performed.
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
Keep feedback in a fixed-height status area so changing operation messages
never moves an active control. Long messages remain readable by scrolling.
The normal application inherits the session Qt style/platform theme and palette,
including selection colors; it does not force a test style or fixed accent.
Explicit headless test settings are confined to tests and CI.

Generic QML controls can later share design tokens with the plugin; host-only
Omarchy imports remain in the plugin repository.
