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
The local research's header-counter candidate is not a validated Linux input
event. Confirm its actual host-visible signal and precise meaning before
advertising button support. Preserve the native long-press Sleep behavior.

Acceptance must cover short release once, repeated reads, repeated presses,
counter wrap, initial nonzero baseline, reconnect, service/agent restart,
long press and missing target. No startup or duplicate event may produce a
spurious launch. Do not modify firmware, scan unknown controls or discard
unknown header fields from transaction checks to implement this feature.
