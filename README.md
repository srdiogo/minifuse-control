# MiniFuse Control for Linux

Planned standalone Qt Quick application and optional desktop activation agent
for the MiniFuse Linux control platform.

**Project status: documented design, not an implemented application.** No GUI,
agent, launcher or autostart is installed by this repository. Implementation
milestones M4/M5 depend on the extracted `mf-core` and `mf-service` described in
the `mf-cli` platform plan (`docs/platform/DELIVERY.md`).

## Product

A full mixer and routing application for the established MiniFuse 4 controls,
with host snapshots/presets, verified operation feedback and explicit model
capabilities. It runs independently of Omarchy. The Omarchy plugin is another
client of the same service, not an application dependency.

Use Qt 6, Qt Quick/QML and a small PySide6 adapter for the local API. Reuse the
existing MiniFuse CC application's interaction design and test scenarios.
Replace its independent Python transport/protocol implementation with the
service; do not copy it into this project.

## Documents

- [Application architecture and UX](docs/APPLICATION.md)
- [Desktop agent and physical-button activation](docs/DESKTOP.md)
- [Implementation and validation](docs/IMPLEMENTATION.md)

The canonical wire contract is `mf-service/docs/IPC.md`. Pin the matching spec
revision and execute its contract fixtures; this repository does not define a
second API. The current draft targets API major 1, which is not yet frozen.

## Repository boundary

The application owns presentation, pending local edits, preferences and
explicit snapshot import/export. The service owns device state/plans and
execution. The core owns device semantics and verification. The optional
desktop agent owns the choice to activate the application or Omarchy panel.

No firmware/effects/device-storage writer, arbitrary USB command, global audio
configuration change or undocumented model support belongs here. Signal meters
and reliable switch indicators remain unavailable until the backend advertises
validated capabilities. A stored gain value is not a live signal level.

## Packaging intent

Publish the application and desktop integration as separable components so a
plugin-only user can run the activation agent without installing the full GUI.
Ship a desktop entry, icon and optional reviewed user-session startup files.
Use existing device access through the service; the GUI does not run as root.

New project-owned material is [MIT licensed](LICENSE). Existing design/research
comes from srdiogo's MiniFuse CC work and the `mf-cli` evidence record, which
credits upstream contributors. This is an independent community project.
