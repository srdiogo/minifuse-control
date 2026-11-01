# Contributing

This repository owns the Qt application and optional desktop activation policy.
Use the [MiniFuse Backend workspace](https://github.com/srdiogo/minifuse-backend) for API,
coordination and device protocol changes; it contains the shared `mf-core` crate.
Omarchy integration is optional and must not become a standalone-GUI requirement.

Use purpose-based branches and English source, documentation and commit messages.
Keep contributor attribution. Describe user-visible behavior and validation;
distinguish automated checks, physical LED confirmation and measured audio.
Never publish private snapshots, serials or microphone PCM as test evidence.

Run Ruff, both Qt test styles and qmllint as described in README.md. Build the
source distribution and wheel with `python -m build`, then run
`python tools/check_distribution.py dist/minifuse_control-0.1.0-py3-none-any.whl`.
That check installs into a temporary environment without Qt and validates the
agent, entrypoints, bundled resources and removal. It never starts integration.

Keep meter samples separate from configured gains and edits. Unsupported model
features must remain unavailable. Firmware modification, effects, device-storage
writes and automatic restore/startup are outside this application's scope.

## Community reports and distribution work

Use [support guidance](SUPPORT.md) and the issue forms for bugs, installation
help, compatibility reports and feature requests. Share exact versions and the
scope actually tested. Preserve private hardware/user data and existing credits.

Distribution packaging and coordinated previews follow the backend's
[roadmap](https://github.com/srdiogo/minifuse-backend/blob/main/docs/DISTRIBUTION.md)
and [release guide](https://github.com/srdiogo/minifuse-backend/blob/main/docs/RELEASING.md).
Build success alone does not establish support for a new distribution or model.
