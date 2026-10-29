# Contributing

This repository owns the Qt application and optional desktop activation policy.
Use [mf-service](https://github.com/srdiogo/mf-service) for API and coordination
changes, and [mf-core](https://github.com/srdiogo/mf-cli) for device protocol work.
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
