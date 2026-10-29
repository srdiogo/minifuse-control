# Installation and removal

## Application or agent

Use a dedicated virtual environment or a distribution package. Python 3.12–3.14
is supported; the GUI extra pins PySide6 6.11.2. A compatible installed service
is required for device state/control. See `contract.lock.json` for the tested
service source revision and fixture hash.

```sh
python3 -m venv ~/.local/share/minifuse-control/venv
~/.local/share/minifuse-control/venv/bin/pip install '.[gui]'
~/.local/share/minifuse-control/venv/bin/minifuse-control
```

For the agent alone, install `.` without the `gui` extra. `--help`/`--version`
do not require a running service or hardware. The GUI's explicit Start service
button only invokes the existing `mf-service.service` user unit; it does not
install a unit, enable startup or request administrator access.

The desktop-entry template in `packaging/` uses `Exec=minifuse-control`. For a
virtual environment, copy it to the user's applications directory and set Exec
to that environment's absolute executable path. Install the owned SVG from
`src/minifuse_control/assets/minifuse-control.svg` as
`io.github.srdiogo.MiniFuseControl.svg` in an hicolor scalable apps directory.
A distribution package may install these under its normal prefix. No copied
proprietary icon is required.

## Optional desktop activation

The agent default is disabled; current backend button capability is unavailable.
An activation preference does not enable unsupported events. Once the backend
evidence gate passes, a user can select one target and separately opt into
session startup. The user-unit template uses `/usr/bin/minifuse-desktop-agent`;
a local virtual environment needs a user override with its absolute ExecStart.
Only then install/enable the reviewed user unit for the graphical session.
Installing the application or plugin alone does not start the agent.

The agent uses fixed argument vectors for `minifuse-control`, `omarchy-shell`
and `notify-send`. Ensure the selected executable is available in its session
PATH. It cannot run an arbitrary command from preferences or event data.

## Files and troubleshooting

- Service socket: `$XDG_RUNTIME_DIR/mf-service/control.sock`.
- Single-instance GUI endpoint: `$XDG_RUNTIME_DIR/minifuse-control/activate.sock`.
- Preferences and GUI operation reference:
  `$XDG_CONFIG_HOME/minifuse/desktop.json`; agent identity: `agent.json`.
- Host presets/backups belong to the service; removing the GUI does not remove
  them. Retain unresolved operation references until reconciled.

The XDG runtime directory must be owned/private; no shared socket fallback is
used. If controls are unavailable, check service compatibility, module/access,
model capabilities and ambiguity in Device and desktop diagnostics. Reconnects
read a new baseline and never replay unsent fader values or a preset restore.
Wayland may deny window focus; the application remains one instance and can
notify the user instead of forcing compositor focus.

## Removal

Stop/disable the optional agent unit if enabled, remove only its installed unit,
desktop entry and owned icon, then remove the dedicated environment/package.
Run the user manager's daemon-reload after removing a unit. Preserve presets,
backups, preferences and unresolved operation evidence unless the user explicitly
chooses to delete them. No kernel module, udev rule, audio setting or Omarchy
configuration is changed by the GUI's removal.
