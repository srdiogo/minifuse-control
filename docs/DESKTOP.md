# Desktop integration and the Arturia button

## Responsibility

The optional `minifuse-desktop-agent` is the sole activation-policy owner. It
subscribes to validated `control_panel_requested` events and chooses a target
from a user preference: `application`, `omarchy_panel` or `disabled`.
The default is disabled until the backend capability and startup choice are
explicitly enabled. The service/core never choose a window or run a launcher.

The agent belongs to this repository but must be separately packageable without
the full Qt application. Keep its runtime small; use a reviewed fixed adapter
for application/Omarchy invocation, never arbitrary executable text supplied
by the service, snapshot or preference.

## Lifecycle

- GUI launch may start/connect to the service on demand.
- Hardware-button activation with the GUI closed requires the service and
  agent to remain running during the login session. A closed GUI cannot listen.
- Offer opt-in session startup through reviewed packaging. Do not install
  startup entries or start background processes during ordinary builds/tests.
- Enforce one agent per user session. A second instance exits cleanly after
  checking the existing instance; it does not become another event consumer.
- Reconnect by negotiating a fresh baseline/epoch. Discard duplicate/stale
  event IDs; startup/counter baselines must never open a window.

## Application activation

Launch through the application's owned desktop identity or a fixed argument
vector. The application exposes a single-instance activation endpoint. If it
already exists, request presentation of that window; do not spawn another
mixer. A launch/present request never restores a preset or writes a device.

When a systemd user session and `systemd-run` are available, the agent starts
the fixed application executable in a separate transient user unit. Restarting
or stopping the agent therefore does not terminate an open mixer. Without a
session manager it uses the direct detached launcher. A failed managed launch
is reported, not retried through a second launcher. The activation socket owns
its connection deadlines, so completed connections leave no callbacks targeting
deleted sockets.

Wayland/compositor focus policy may deny foregrounding without a valid user
activation context. Respect that decision, keep one instance and use a
notification/focus affordance where appropriate. Do not promise forced focus
or require a Hyprland-specific workaround in the general application.

## Omarchy panel activation

The Omarchy plugin implements an explicit panel entrypoint under its own ID,
`srdiogo.minifuse`. The agent's Omarchy adapter uses the documented shell
summon path with a fixed argument vector. The exact target/manifest contract
must be checked against the supported host release during implementation.

The plugin does not independently act on hardware activation events. It can
subscribe to state and present a panel when asked by the agent or by a normal
bar click. If the selected plugin/shell is unavailable, show one actionable
notification and follow an explicit user-configured fallback; do not open both
targets or silently change the preference.

Package the agent independently so plugin-only users can select the Omarchy
target without needing the full application. Installing the plugin alone does
not implicitly enable login startup or install the service/module.

## Button evidence gate

The official MF4 short/long-press behavior is documented in the
[Arturia manual](https://dl.arturia.net/products/minifuse-4/manual/minifuse-4_Manual_1_0_0_EN.pdf).
Linux events are now validated for normal-mode MiniFuse 4 with USB firmware
descriptor 1.0.1. The backend requires a confirmed counter, establishes a startup
baseline, emits once per observed change and assigns IDs independent of the
counter's 9-to-0 wrap. Other models/firmware remain unavailable. See the backend's
[protocol evidence and limits](https://github.com/srdiogo/minifuse-backend/blob/feature/model-controls/docs/mf4/logo-button.md).

The agent negotiates capability and subscribes to the validated event. It never
launches from an initial read, reconnect or duplicate event ID. Sequence/epoch
gaps force a new baseline. The application still owns single-instance activation;
the service performs no launch or configuration write for a button event.

Native long-press Sleep is unchanged and was not physically tested in this
session. Button support must not be generalized to another model or firmware
without its own evidence. No firmware modification or unknown control scan is
needed for this feature.

## MF4 desktop acceptance, 2 November 2026

On MiniFuse 4 USB firmware descriptor 1.0.1, the operator confirmed launch from
a short press and one window after repeated presses. The backend supplied nine
live events across two sessions. Starting from a nonzero counter produced no
launch. The final application ran in its own systemd user unit; restarting the
agent and presenting the application again preserved the same GUI process.
It was floating on the tested Omarchy session. No device controls were changed
by activation; the backend's complete-state comparison changed only counter
byte 14. Other desktops retain their own focus policy.

The final automated suite passed 45 tests with each Basic and Fusion style.
This includes three presentations through the actual application entrypoint,
idle-connection expiry, bounded agent socket negotiation, duplicate IDs,
sequence/epoch gaps, capability loss, managed/direct launch choice and one
notification for a failed target. Static evidence and physical scope are
recorded in the backend's [button report](https://github.com/srdiogo/minifuse-backend/blob/feature/model-controls/docs/mf4/logo-button.md).
