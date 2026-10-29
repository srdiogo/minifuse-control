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
Signal meters use separate `meters_updated` events, target at most 20 Hz and
clear after 500 ms without fresh data. They never update configuration revisions
or cancel an edit. Each source has a peak bar; the master has L/R mix bars. The
scale is −96 to 0 dBFS; zero magnitude is silence. Numeric peak values are
available in accessible descriptions and hover tips. The bars use the native
palette. Mix meters are post-master and pre-routing, so direct USB playback can
bypass the displayed mix. Meter data is never synthesized from fader positions. Input
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

## Hardware integration observation

On 29 October 2026, a real Qt client connected to the hardware-backed service
and rendered all eight source bars plus stereo master bars for an output mix.
The Analog 1 bar received a nonzero native peak; meter updates left configuration
revision unchanged. The visible Wayland application opened without runtime-log
errors. This complements the 19 offline GUI tests under Basic and Fusion.
Calibration and coverage limits are recorded in the core
[meter report](https://github.com/srdiogo/mf-cli/blob/936962fcef9320fbf0e0991bd095d9c6c9370dc4/docs/mf4/meters.md).


## Mixer presentation

The standalone application shares the panel's channel-strip hierarchy without
requiring Omarchy or Quickshell. All three destinations use the same aligned
pan, mute/solo, configured-gain and signal-meter rows, with a separate master.
The source bank fills the available width and scrolls horizontally when needed;
the master stays beside it. Membership controls live in the **Mix sources…**
popup. Routes remain visible beside the destination heading.

Windows below 740 logical pixels in height use compact spacing and channel
headers. At the minimum 840 × 640 window size the gain tracks and numeric entries
remain visible. A fixed status footer prevents operation messages, pending
verification and recovery actions from moving the mixer during a gesture.

Mute, solo and input modes use confirmed state for their accent text, border and
underline. Keyboard focus has its own border treatment and does not imply an
active switch. Numeric gain fields accept a number, optionally followed by
`dB`, on Enter; `-inf` and `−∞` represent silence. The separate silence action
remains available. Gain readouts follow confirmed updates after editing or
cancelling; live meter samples never change configured gain.

Custom control surfaces use the current Qt palette, including the platform
accent, and inherit the system font family. Theme changes require no hardware
request. Presets and device settings use the same surfaces and spacing; preset
comparison and explicit Apply behavior remain unchanged.
