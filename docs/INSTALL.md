# Installation and removal

## Backend prerequisite

Install `minifuse-driver-dkms` and `mf-service` from the
[backend workspace](https://github.com/srdiogo/mf-service), using headers for the
running kernel. Follow its [installation guide](https://github.com/srdiogo/mf-service/blob/main/docs/INSTALL.md)
for explicit driver activation, session access and optional login startup.
`mf-core` is compiled into the service; it is not another process. The CLI is
not required. Run `minifuse-doctor` before troubleshooting the GUI.

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

## Arch distribution preview

The public source repository is <https://github.com/srdiogo/minifuse-control>.
Native package recipes under `packaging/arch/` pin an immutable source commit
and archive checksum. The packages have separate ownership:

- `minifuse-control-common`: shared Python state/framing/preferences modules.
- `minifuse-control`: Qt application, QML, launcher and icon; depends on the
  common package, the compatible service and distribution PySide6 (tested at 6.11.2; the pip extra
  remains pinned to that version).
- `minifuse-desktop-agent`: standard-library activation policy and optional
  user unit; depends on the common package and service, without Qt.

The agent package is optional and current logo-button support remains disabled.
Installing either package does not enable a unit, restore a preset or modify
Omarchy. The module and active-session device permissions remain separate
administrator-managed prerequisites from the mf-service workspace. The
`minifuse-driver-dkms` package contains the transport and udev policy; the
`mf-service` package includes the core library. The CLI is not required. See
[backend setup on a new machine](https://github.com/srdiogo/mf-service/blob/main/docs/INSTALL.md).

Build with `makepkg` as an ordinary user and review the resulting package file
lists before installing through the system package manager. These are preview
recipes, not an AUR release or a claim of clean-machine acceptance. Upgrades
preserve preferences and service-owned presets/journals. Removal through the
package manager removes owned program files; disable an enabled optional agent
unit first and retain user evidence until deliberately archived.

CI also builds a source distribution and a wheel from that source distribution,
installs it into a clean environment without Qt, exercises both help entrypoints
and the agent import, checks resources, then uninstalls it. The wheel is the
portable Python distribution; Linux Qt dependencies and the service/module are
separate. Native package construction is tested on Arch rather than implied by
an Ubuntu-built Python wheel.
