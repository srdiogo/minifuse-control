"""Capability-driven presentation. All hardware semantics remain in mf-core."""

import json
import os
import secrets
import time
from pathlib import Path
from PySide6.QtCore import QObject, Property, Signal, Slot, QUrl, QProcess
from .live import LiveControl


class Controller(QObject):
    changed = Signal()
    discardEdits = Signal()

    def __init__(self, client, preferences, parent=None):
        super().__init__(parent)
        self.client, self.preferences = client, preferences
        self._devices, self._state, self._presets = [], {}, []
        self._status = "Connecting to mf-service…"
        self._message = ""
        self._busy = False
        self._online = False
        self._device = None
        self._preview = {}
        self._snapshot = None
        self._plan_deadline = 0
        self._pending = preferences.data.get("pending_operation")
        self._operation_id = None
        self._start_process = None
        self._last_operation = {}
        self._ack_after_refresh = False
        self._live = None
        self._live_key = ""
        self._live_supported = False
        self._edit_revision = ""
        client.ready.connect(self._ready)
        client.unavailable.connect(self._unavailable)
        client.event.connect(self._event)

    @Property(str, notify=changed)
    def status(self):
        return self._status

    @Property(str, notify=changed)
    def message(self):
        return self._message

    @Property(bool, notify=changed)
    def busy(self):
        return self._busy

    @Property(bool, notify=changed)
    def canWrite(self):
        return bool(
            self._online
            and self._device
            and self._state
            and not self._busy
            and not self._pending
            and self._device.get("capabilities", {}).get("mixer")
        )

    @Property("QVariantMap", notify=changed)
    def inputs(self):
        if not self.capabilities.get("switch_readback"):
            return {}
        return self._state.get("state", {}).get("inputs", {})

    @Property(bool, notify=changed)
    def canWriteInputs(self):
        return bool(self.canWrite and self.capabilities.get("input_switches"))

    @Property(bool, notify=changed)
    def liveActive(self):
        return self._live is not None

    @Property(str, notify=changed)
    def activeControlKey(self):
        return self._live_key

    @Property(str, notify=changed)
    def editRevision(self):
        return self._edit_revision or self.revision

    @Property(bool, notify=changed)
    def online(self):
        return self._online

    @Property(bool, notify=changed)
    def uncertain(self):
        return bool(self._pending and not self._busy)

    @Property("QVariantList", notify=changed)
    def devices(self):
        return self._devices

    @Property("QVariantMap", notify=changed)
    def state(self):
        return self._state

    @Property("QVariantList", notify=changed)
    def mixes(self):
        return self._state.get("state", {}).get("mixes", [])

    @Property("QVariantMap", notify=changed)
    def capabilities(self):
        return self._state.get("capabilities", {})

    @Property("QVariantList", notify=changed)
    def presets(self):
        return self._presets

    @Property("QVariantMap", notify=changed)
    def preview(self):
        return self._preview

    @Property("QVariantList", notify=changed)
    def previewRows(self):
        state = self._preview.get("predicted_state") or self._preview.get(
            "inspection", {}
        ).get("state", {})
        current = self._state.get("state", {}) if self._preview.get("plan_id") else {}
        rows = []

        def display(value, field):
            if value is None:
                return "−∞" if "db" in field else "Undefined"
            if isinstance(value, bool):
                return "On" if value else "Off"
            if isinstance(value, float):
                return f"{value:.3f}"
            return str(value)

        def add(label, field, after, before):
            if current and before == after:
                return
            if (
                current
                and isinstance(before, float)
                and isinstance(after, float)
                and abs(before - after) < 0.000001
            ):
                return
            rows.append(
                {
                    "field": label,
                    "before": display(before, field) if current else "—",
                    "after": display(after, field),
                }
            )

        for mix in state.get("mixes", []):
            previous = next(
                (m for m in current.get("mixes", []) if m["mix"] == mix["mix"]), {}
            )
            for field, label in (("master_db", "Master dB"), ("route", "Route")):
                add(
                    f"{mix['mix']} · {label}",
                    field,
                    mix.get(field),
                    previous.get(field),
                )
            for channel in mix.get("channels", []):
                prior = next(
                    (
                        c
                        for c in previous.get("channels", [])
                        if c["channel"] == channel["channel"]
                    ),
                    {},
                )
                for field, label in (
                    ("derived_level_db", "Level dB"),
                    ("derived_pan", "Pan"),
                    ("mute", "Mute"),
                    ("solo", "Solo"),
                    ("mono_included", "Mono source included"),
                    ("stereo_pair_included", "Stereo pair included"),
                ):
                    add(
                        f"{mix['mix']} · {channel['channel']} · {label}",
                        field,
                        channel.get(field),
                        prior.get(field),
                    )
        return rows

    @Property(str, notify=changed)
    def revision(self):
        return self._state.get("revision", "")

    @Property(str, notify=changed)
    def diagnostics(self):
        return json.dumps(
            {"devices": self._devices, "operation": self._last_operation}, indent=2
        )

    @Property(str, notify=changed)
    def activationTarget(self):
        return self.preferences.data.get("activation_target", "disabled")

    def _failure(self, error):
        self._busy = False
        self._message = error.get("message", "Operation failed")
        self.changed.emit()

    def _identity(self):
        return {key: self._state[key] for key in ("device_id", "generation")}

    def _ready(self, negotiation):
        self._live_supported = "live_controls" in negotiation.get("features", [])
        self._online = True
        self._status = "Connected to mf-service"
        self.client.request(
            "subscribe",
            {
                "events": [
                    "device_added",
                    "device_removed",
                    "capabilities_changed",
                    "state_changed",
                    "operation_started",
                    "operation_finished",
                ]
                + (["control_updated"] if self._live_supported else [])
            },
            self._subscribed,
        )
        self.loadPresets()

    def _subscribed(self, result, error):
        if error:
            self._failure(error)
            return
        self.client.sequence = result["seq"]
        self._devices = result["devices"]
        self._device = next(
            (
                d
                for d in self._devices
                if d.get("connection") == "ready"
                and d.get("capabilities", {}).get("mixer")
            ),
            None,
        )
        self._state = next(
            (
                s
                for s in result["states"]
                if self._device and s["device_id"] == self._device["device_id"]
            ),
            {},
        )
        self._edit_revision = self.revision
        self._availability()
        if self._pending:
            self._query_pending()

    def _availability(self):
        if self._state:
            self._status = "MiniFuse 4 · confirmed device state"
        elif self._devices:
            self._status = "Device controls unavailable"
            self._message = next(
                (
                    d.get("error", {}).get("message", "Unsupported device")
                    for d in self._devices
                    if d.get("error")
                ),
                "Choose a supported, unambiguous device",
            )
        else:
            self._status = "No supported interface connected"
        self.changed.emit()

    def _unavailable(self, reason):
        self._stop_live()
        self._online = False
        self._busy = False
        self._state = {}
        self._device = None
        self._preview = {}
        self._status = "Service unavailable"
        self._message = reason
        self.discardEdits.emit()
        self.changed.emit()

    def _event(self, event):
        name, data = event["event"], event["data"]
        if name == "state_changed":
            if self._device and data["device_id"] == self._device["device_id"]:
                if data.get("generation") != self._state.get("generation"):
                    self.discardEdits.emit()
                    self._preview = {}
                if (
                    self._preview.get("plan_id")
                    and data.get("revision") != self.revision
                ):
                    self._preview = {}
                    self._message = "Restore preview invalidated by a device change. Create a fresh preview."
                own_sample = (
                    self._live and data.get("operation_id") == self._operation_id
                )
                if not own_sample:
                    self._edit_revision = data["revision"]
                    if self._live:
                        self.cancelControl()
                        self.discardEdits.emit()
                self._state = data
                self.changed.emit()
            elif not self._state:
                self.refresh()
        elif name in ("device_added", "device_removed", "capabilities_changed"):
            if name != "device_added":
                self._state = {}
                self._preview = {}
                self.discardEdits.emit()
            self.refresh()
        elif name == "control_updated" and self._live:
            self._live.settled(data)
        elif (
            name == "operation_finished"
            and self._live
            and self._operation_id == data.get("operation_id")
        ):
            self._live.settled(data)
        elif name == "operation_finished" and self._operation_id == data.get(
            "operation_id"
        ):
            self._completed(data)

    @Slot()
    def refresh(self):
        if not self._online:
            self.client.connect_service()
            return
        self._preview = {}
        self.discardEdits.emit()
        self.client.request("list_devices", {}, self._inventory)

    def _inventory(self, result, error):
        if error:
            self._failure(error)
            return
        self._devices = result["devices"]
        ready = [
            d
            for d in self._devices
            if d.get("connection") == "ready" and d.get("capabilities", {}).get("mixer")
        ]
        if len(ready) != 1:
            self._state, self._device = {}, None
            self._availability()
            return
        self._device = ready[0]
        self.client.request(
            "get_state",
            {key: self._device[key] for key in ("device_id", "generation")},
            self._got_state,
        )

    def _got_state(self, result, error):
        if error:
            self._state = {}
            self._failure(error)
            return
        self._state = result
        self._edit_revision = self.revision
        if self._ack_after_refresh:
            self._ack_after_refresh = False
            self._clear_pending()
            self._busy = False
        self._availability()

    @Slot("QVariantMap", "QVariant", bool)
    def adjust(self, target, value, finish):
        target = dict(target)
        key = ":".join(str(target.get(k, "")) for k in ("kind", "mix", "source"))
        if self._live:
            if key == self._live_key:
                self._live.move(value, finish)
            return
        if not self.canWrite:
            return
        if not self._live_supported:
            self._message = (
                "Continuous controls require a service with live_controls support."
            )
            self.changed.emit()
            return
        self._pending = {"key": secrets.token_hex(24), "kind": "live_control"}
        self.preferences.data["pending_operation"] = self._pending
        try:
            self.preferences.save()
        except OSError as error:
            self._pending = None
            self.preferences.data.pop("pending_operation", None)
            self._failure({"message": f"Cannot retain control identity: {error}"})
            return
        self._edit_revision = self.revision
        self._busy = True
        self._live_key = key
        self._message = ""
        self._preview = {}
        self._live = LiveControl(
            self.client,
            {
                **self._identity(),
                "expected_revision": self.revision,
                "target": target,
                "idempotency_key": self._pending["key"],
            },
            self,
        )
        self._live.admitted.connect(self._live_admitted)
        self._live.completed.connect(self._completed)
        self._live.failed.connect(self._live_failed)
        self.changed.emit()
        self._live.move(value, finish)
        self._live.start()

    def _live_admitted(self, identifier):
        self._operation_id = identifier

    def _stop_live(self):
        if self._live:
            self._live.stop()
            self._live.deleteLater()
            self._live = None
        self._live_key = ""

    def _live_failed(self, error):
        self._stop_live()
        self._busy = False
        self.discardEdits.emit()
        self._message = error.get(
            "message", "Control interrupted; review current settings"
        )
        if self._pending and self._online:
            self._query_pending()
        self.changed.emit()

    @Slot()
    def cancelControl(self):
        if self._live:
            self._live.cancel()

    @Slot("QVariantMap")
    def change(self, change):
        if not self.canWrite:
            return
        if change.get("kind") == "input_switch" and not self.canWriteInputs:
            return
        self._busy = True
        self._message = "Preparing verified change…"
        params = {
            **self._identity(),
            "expected_revision": self.revision,
            "changes": [dict(change)],
        }
        self.changed.emit()
        self.client.request("plan_changes", params, self._planned_change)

    @Slot(str, bool)
    def setInputSwitch(self, target, enabled):
        if (
            self.canWriteInputs
            and target in ("inst1", "inst2", "phantom_power")
            and isinstance(self.inputs.get(target), bool)
            and self.inputs[target] != enabled
        ):
            self.change({"kind": "input_switch", "target": target, "enabled": enabled})

    def _planned_change(self, result, error):
        if error:
            self._failure(error)
            self.refresh()
            return
        self._apply(result["plan_id"])

    def _apply(self, plan_id):
        self._pending = {"key": secrets.token_hex(24)}
        self.preferences.data["pending_operation"] = self._pending
        try:
            self.preferences.save()
        except OSError as error:
            self._pending = None
            self.preferences.data.pop("pending_operation", None)
            self._failure({"message": f"Cannot retain operation identity: {error}"})
            return
        self._busy = True
        self._message = "Applying; waiting for device verification…"
        self.changed.emit()
        self.client.request(
            "apply_plan",
            {"plan_id": plan_id, "idempotency_key": self._pending["key"]},
            self._accepted,
        )

    def _accepted(self, result, error):
        if error:
            self._busy = False
            if error.get("code") != "outcome_unknown":
                self._clear_pending()
            self._failure(error)
            self.refresh()
            return
        self._operation_id = result["operation_id"]
        if result["status"] != "pending":
            self._completed(result)

    def _query_pending(self):
        self.client.request(
            "get_operation",
            {"idempotency_key": self._pending["key"]},
            lambda result, error: (
                self._failure(error) if error else self._completed(result)
            ),
        )

    def _completed(self, result):
        if result.get("status") != "pending":
            self._stop_live()
        self._last_operation = result
        self._busy = False
        if result.get("status") == "pending":
            self._operation_id = result["operation_id"]
            self._busy = True
            if result.get("kind") == "live_control" and not self._live:
                self.client.request(
                    "cancel_control",
                    {"operation_id": self._operation_id},
                    lambda record, error: (
                        self._failure(error) if error else self._completed(record)
                    ),
                )
        elif (
            result.get("status") == "indeterminate"
            or result.get("device_outcome") == "unknown"
        ):
            self._message = "Result is uncertain. Refresh and review current settings before applying again."
        else:
            outcome = result.get("device_outcome")
            journal_failed = result.get("journal_status") == "failed"
            if outcome == "verified":
                self._message = (
                    "Device readback verified; journal finalization failed. Retain the operation reference."
                    if journal_failed
                    else "Device readback verified"
                )
            elif result.get("rollback_verified"):
                self._message = (
                    "Change failed; the original state was restored and verified."
                )
            else:
                self._message = (result.get("error") or {}).get(
                    "message", "Change failed; refresh current settings"
                )
            if result.get("gesture_end") not in (None, "finished"):
                self._message = f"Control ended ({result['gesture_end']}). Confirmed changes are retained; the final pointer value may not have been applied."
            self._clear_pending()
            self.refresh()
        self.changed.emit()

    def _clear_pending(self):
        self._pending = None
        self._operation_id = None
        self.preferences.data.pop("pending_operation", None)
        try:
            self.preferences.save()
        except OSError as error:
            self._message = f"Could not finalize local operation reference: {error}"

    @Slot()
    def acknowledge(self):
        if self._pending and not self._busy:
            self._ack_after_refresh = True
            self._busy = True
            self.refresh()

    @Slot()
    def editConflict(self):
        self._message = (
            "Device state changed while editing. The local edit was discarded."
        )
        self.changed.emit()

    @Slot()
    def loadPresets(self):
        self.client.request("list_presets", {}, self._listed_presets)

    def _listed_presets(self, result, error):
        if not error:
            self._presets = result["presets"]
            self.changed.emit()

    @Slot(str)
    def savePreset(self, name):
        if not self._state or self._busy:
            return
        self.client.request(
            "capture_snapshot",
            self._identity(),
            lambda result, error: (
                self._failure(error)
                if error
                else self.client.request(
                    "save_preset",
                    {"name": name, "snapshot": result["snapshot"]},
                    self._saved_preset,
                )
            ),
        )

    def _saved_preset(self, result, error):
        if error:
            self._failure(error)
        else:
            self._message = f"Host preset saved: {result['name']}"
            self.loadPresets()
            self.changed.emit()

    @Slot(str)
    def inspectPreset(self, identifier):
        self.client.request(
            "load_preset",
            {"preset_id": identifier},
            lambda result, error: (
                self._failure(error) if error else self._inspect(result["snapshot"])
            ),
        )

    @Slot(QUrl)
    def importSnapshot(self, url):
        try:
            if not url.isLocalFile():
                raise ValueError("Choose a local snapshot file")
            with Path(url.toLocalFile()).open("rb") as stream:
                content = stream.read(65537)
            if len(content) > 65536:
                raise ValueError("Snapshot exceeds 64 KiB")
            self._inspect(content.decode("utf-8"))
        except (OSError, ValueError) as error:
            self._failure({"message": str(error)})

    def _inspect(self, content):
        self._preview = {}
        self._snapshot = content
        self.client.request("inspect_snapshot", {"snapshot": content}, self._inspected)

    def _inspected(self, result, error):
        if error:
            self._snapshot = None
            self._failure(error)
        else:
            self._preview = {"inspection": result}
            self.changed.emit()

    @Slot(str)
    def previewRestore(self, mix=""):
        if not self.canWrite or not self._snapshot:
            return
        params = {
            **self._identity(),
            "revision": self.revision,
            "snapshot": self._snapshot,
        }
        if mix:
            params["mix"] = mix
        self.client.request("plan_restore", params, self._restore_plan)

    def _restore_plan(self, result, error):
        if error:
            self._failure(error)
        else:
            self._preview = result
            self._plan_deadline = time.monotonic() + result["expires_in_ms"] / 1000
            self.changed.emit()

    @Slot()
    def applyRestore(self):
        if not self.canWrite or not self._preview.get("plan_id"):
            return
        if time.monotonic() >= self._plan_deadline:
            self._failure(
                {"message": "Restore preview expired. Create a fresh preview."}
            )
            self._preview = {}
            return
        identifier = self._preview["plan_id"]
        self._preview = {}
        self._apply(identifier)

    @Slot(QUrl)
    def exportSnapshot(self, url):
        if self._snapshot is None:
            return
        try:
            if not url.isLocalFile():
                raise ValueError("Choose a local destination")
            fd = os.open(url.toLocalFile(), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w") as stream:
                stream.write(self._snapshot)
                stream.flush()
                os.fsync(stream.fileno())
            parent = os.open(
                Path(url.toLocalFile()).parent, os.O_RDONLY | os.O_DIRECTORY
            )
            try:
                os.fsync(parent)
            finally:
                os.close(parent)
            self._message = "Host snapshot exported"
            self.changed.emit()
        except (OSError, ValueError) as error:
            self._failure({"message": str(error)})

    @Slot(str)
    def setActivationTarget(self, target):
        if target not in ("disabled", "application", "omarchy_panel"):
            return
        self.preferences.data["activation_target"] = target
        try:
            self.preferences.save()
        except OSError as error:
            self._failure({"message": str(error)})
        self.changed.emit()

    @Slot()
    def startService(self):
        if self._start_process is not None:
            return
        process = QProcess(self)
        self._start_process = process
        process.finished.connect(self._service_started)
        process.errorOccurred.connect(lambda _: self._service_start_error(process))
        process.start("systemctl", ["--user", "start", "mf-service.service"])

    def _service_start_error(self, process):
        self._start_process = None
        self._failure({"message": process.errorString()})
        process.deleteLater()

    def _service_started(self, code, _):
        if code:
            self._failure(
                {
                    "message": "Could not start the installed user service. Run mf-service in a terminal or review the unit installation."
                }
            )
        self._start_process = None
        self.client.connect_service()
