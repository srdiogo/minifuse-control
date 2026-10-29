# Implementation and validation

## Delivery sequence

1. Pin a service contract revision and supported Qt/PySide6 versions. Define
   typed client/view models and contract tests before wiring controls.
2. Implement service availability, capability-driven device selection and
   offline preset inspection, then the three full mixer views.
3. Implement pending-edit/commit workflows, routes, membership and verified
   outcomes. Reuse the existing MiniFuse CC interaction scenarios.
4. Add preset comparison/restore preview, explicit Apply and content export.
5. Complete accessible keyboard use, scalable layouts and theme behavior.
6. Implement single-instance application activation and the separate agent.
7. Validate final builds with the real service and hardware; package the app
   and optional integration separately.

There is currently no executable or dependency manifest because implementation
has not begun. Do not ship a fake device backend as normal application behavior.
Deterministic simulated services are test fixtures only.

## Automated gates

- Run canonical protocol fixtures, including unsupported API, fragmented
  messages, errors, stale generation/revision and operation-status recovery.
- Offscreen Qt tests prove that setting/refreshing controls does not commit;
  dragging previews only and release commits once with the final value.
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
Meters, complete MF1/MF2 control and native device-save confirmation are not
release claims without their own implementation and validation.

Document dependencies, service/API compatibility, package installation/update/
removal, optional startup and troubleshooting. The application must not install
or replace kernel modules, udev rules or host audio routing on launch.
