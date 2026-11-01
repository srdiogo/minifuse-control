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

Basic-model pages have no MF4 faders, routes, meters or preset restore.
Initialization-mode pages have no audio controls. Input/output gain knobs remain
physical controls. MF2 OTG routing is not inferred from another model.

The Omarchy panel is a separate frontend with read-only input indicators.
No firmware, effects or device-storage operations are added.

Synthetic presentation fixtures are in `tests/contract/model-profiles-v1.json`;
the backend compares the same fixture to its implemented model catalog.
Run `python -m unittest discover -s tests -v` and QML linting with the GUI extra.
See the backend's [hardware checklist](https://github.com/srdiogo/minifuse-backend/blob/feature/model-controls/docs/models/TESTING.md)
for read-only capture and deliberate switch acceptance.
