# Implementation and validation

## Delivery sequence

1. Pin a service contract revision and supported Qt/PySide6 versions. Define
   typed client/view models and contract tests before wiring controls.
2. Implement service availability, capability-driven device selection and
   offline preset inspection, then the three full mixer views.
3. Implement continuous-control workflows, routes, membership and verified
   outcomes. Reuse the existing MiniFuse CC interaction scenarios.
4. Add preset comparison/restore preview, explicit Apply and content export.
5. Complete accessible keyboard use, scalable layouts and theme behavior.
6. Implement single-instance application activation and the separate agent.
7. Validate final builds with the real service and hardware; package the app
   and optional integration separately.

The application, standard-library agent, Python packaging metadata, desktop
entry, optional unit and CI definition are implemented. Do not ship a fake device backend as normal application behavior.
Deterministic simulated services are test fixtures only.

## Automated gates

- Run canonical protocol fixtures, including unsupported API, fragmented
  messages, errors, stale generation/revision and operation-status recovery.
- Offscreen Qt tests prove that setting/refreshing controls does not commit;
  dragging sends intermediate values through one bounded gesture and release
  preserves the latest final value without a backlog.
- Mute/solo changes preserve gains; membership shows pair/mute/solo effects;
  route warnings follow confirmed capability/state, not tab selection.
- Unknown/silent levels are distinct from 0 dB. Unsupported models/topologies
  expose no active control path.
- Preset import/show/cancel never writes. Apply uses the displayed current
  plan; expired/stale plans require a fresh deliberate action.
- Disconnect, close and selection changes discard pending edits. Service
  failure blocks writes and surfaces structured recovery, not automatic retry.
- A verified device result with journal failure is rendered accurately.
- One desktop agent handles each event once. A repeated invocation activates
  one application instance; neither GUI nor plugin duplicates button policy.

## Manual/session gates

Test the supported Wayland environment, fractional scaling, small/large
displays, keyboard-only use, contrast and reduced motion. Verify that launch
works without Omarchy and that a denied focus request does not create duplicate
windows. Test absent service, unavailable module/access and no/multiple devices.

For hardware checks, use the final revision and service build, record original
full state/switches, begin with muted sources and controlled levels, and restore
the complete baseline after the session. Distinguish digital loopback tests,
human listening and visual LED confirmation. No microphone audio or private
snapshots enter public fixtures.

## Release acceptance

The complete mapped MF4 feature set, preset workflows, error/reconnect states,
accessibility and normal launcher must pass before application release.
Optional button support remains disabled until its evidence gate passes.
MF4 meters have calibrated readback with documented coverage. Complete MF1/MF2
control and native device-save confirmation remain unavailable.

Document dependencies, service/API compatibility, package installation/update/
removal, optional startup and troubleshooting. The application must not install
or replace kernel modules, udev rules or host audio routing on launch.

## Current software coverage

The test suite covers real pointer movement, offscreen construction/rendering,
refresh/theme updates without writes, coalescing during delayed confirmation,
final release, external-change cancellation, disconnect without replay,
plan/apply identity persistence, indeterminate outcomes, preset preview expiry,
strict framing and a real QLocalSocket peer. A separate-process test verifies
single-instance activation. Agent tests cover validated capability/generation,
one target, deduplication and no activation from baselines.

Local validation uses Python 3.14.7, PySide6 6.11.2 and Qt 6.11.2. CI tests
Python 3.12/3.14 with Basic and Fusion styles. Hosted results must be checked
on the published source revision. No
production service/module, session startup or global desktop setting is changed
by these tests. The hardware-backed service, input LEDs and live Qt meter path have bounded
validation on one MF4; see APPLICATION.md and the service validation report.
Clean-machine installation, other rates and broader desktop acceptance remain
open.

The wheel and source distribution build locally. A temporary clean virtual
environment installs/removes the wheel, verifies bundled QML/icon resources and
imports/runs the agent help without PySide6. This is package construction
coverage, not a clean-machine GUI or graphical-session acceptance claim.


The mixer presentation refresh adds offscreen checks for fully visible master
tracks and numeric entries at the minimum window size, mute/solo styling while
pointer or keyboard focus remains on the button, and numeric readback updates
after editing/reset. Existing alignment, continuous-gesture, switch capability,
theme-without-mutation and recovery tests also cover the new layout. Light and
dark palette renders are reviewed separately from hardware-backed validation.
