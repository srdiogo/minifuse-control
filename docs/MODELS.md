# Model-specific layouts

The backend inventory supplies a versioned presentation profile. The application
selects one recognized interface and uses its own input controls and physical I/O
counts. Ambiguous inventories leave controls disabled. Unknown metadata never
grants write access; older backends retain the existing MF4 presentation.

MF1: INST1, +48 V, direct monitor. MF2 and MF2 OTG: INST1, INST2, shared +48 V,
direct mono. These basic controls require an explicitly enabled test backend,
confirmed model-specific state and advertised `input_switches` capability.
They use the existing typed plan/apply workflow and wait for readback.
Hardware validation remains pending separately for all three models.

With `MF_SERVICE_EXPERIMENTAL_LOOPBACK=1`, compatible confirmed firmware and
matching driver capabilities, the runtime profile is `loopback_mixer`. Firmware
families are MF1/MF2 1.5.x and OTG 1.0.x; unknown, old and unreviewed families
remain blocked. The application also requires matching inventory/readback
firmware metadata before allowing mixer changes. Compatibility is not physical
validation. The application never updates firmware.

| Model | Native source strips | Extra routes | Meter readings |
|---|---|---|---|
| MF1 | Analog 1, USB 1–2, USB 3–4 | Loopback enable, record also on USB 1–2, monitor mix | Input 1, loopback L/R |
| MF2 | Analog 1, Analog 2, USB 1–2, USB 3–4 | Same independent flags | Inputs 1/2, loopback L/R |
| MF2 OTG | Analog 1, Analog 2, USB 1–2, USB 5–6 | Same flags; Main → OTG, OTG → monitor, LED source | Inputs 1/2, loopback L/R, OTG L/R |

Each has one native loopback mix, source gain/mute, analog pan and stereo master.
Stereo USB pairs link gain/mute and have no pan or solo. MF4 buses, membership
and route selectors are not reused. There are no individual USB playback peak
samples or inferred OTG-source gain controls. Meter data expires after 500 ms.
The loopback mix meters are not asserted to be physical monitor-output meters;
channel/scale confirmation remains pending.

Faders use the existing continuous-control workflow, with stable delegates across
readback. Routing and mute use typed plans. Input controls wait for authoritative
state, and physical button changes update automatically. Windows SLS software
virtual devices and independent software mixes are outside this native path.

Host presets require `host_snapshots`. They compare and restore only this model's
mapped native mixer/routing fields, preserving input modes, +48 V, direct
monitoring and opaque bytes. Cross-model snapshots are rejected by the backend.
They do not confirm nonvolatile device saving. Initialization pages have no audio
controls. Physical input/output gain knobs remain physical controls.

The Omarchy panel remains a separate frontend; its input indicators are read-only.
The full application handles input changes and presets. No effects or firmware
operations are added. The generated synthetic native fixture is
`tests/contract/loopback-v1.json`; the conservative catalog fixture remains
`tests/contract/model-profiles-v1.json`. Neither contains real-device captures.
Tests cover each model's layout, stable faders, firmware agreement, typed routing,
meter shape and expiry. Follow the backend's
[hardware checklist](https://github.com/srdiogo/minifuse-backend/blob/feature/model-controls/docs/models/TESTING.md)
for read-only capture and deliberate acceptance.

For an Arch test package built from this exact checkout, commit reviewed changes
and run `python tools/prepare_arch_package.py --output dist/arch`. Verify its
`SHA256SUMS`, then run `makepkg --cleanbuild` inside that directory. The export
records the complete commit, generates a checksummed local source archive and
refuses dirty/untracked changes or a nonempty output directory. The normal
published recipe remains pinned to the installation preview; it is not the test
recipe. CI exports the PR head for its Arch build.

The model fixtures are pinned to the backend source revision and file hashes in
[model-contract.lock.json](../model-contract.lock.json).
