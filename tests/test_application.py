import copy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QPA_PLATFORMTHEME"] = ""
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
os.environ.setdefault("QT_QUICK_BACKEND", "software")

from PySide6.QtCore import QObject, QUrl, Signal
from PySide6.QtGui import QGuiApplication, QPalette, QColor
from PySide6.QtQml import QQmlApplicationEngine, QQmlExpression
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from minifuse_control.controller import Controller
from minifuse_control.desktop import ActivationPolicy
from minifuse_control.preferences import Preferences
from minifuse_control.wire import decode, MAX_FRAME

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/contract/v1.json").read_text())
APP = QGuiApplication.instance() or QGuiApplication([])


class RecordedClient(QObject):
    ready = Signal(dict)
    unavailable = Signal(str)
    event = Signal(dict)

    def __init__(self):
        super().__init__()
        self.requests = []
        self.sequence = None

    def request(self, method, params, callback):
        self.requests.append((method, params, callback))

    def connect_service(self):
        pass


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.preferences = Preferences(Path(self.temp.name) / "preferences.json")
        self.client = RecordedClient()
        self.controller = Controller(self.client, self.preferences)
        self.controller._online = True
        self.controller._live_supported = True
        self.controller._state = copy.deepcopy(FIXTURE["state"]["result"])
        self.controller._device = {
            "device_id": self.controller._state["device_id"],
            "generation": self.controller._state["generation"],
            "connection": "ready",
            "capabilities": self.controller._state["capabilities"],
        }
        self.controller._availability()

    def tearDown(self):
        self.temp.cleanup()

    def test_pinned_contract_and_strict_envelopes(self):
        lock = json.loads((ROOT / "contract.lock.json").read_text())
        self.assertEqual(
            hashlib.sha256((ROOT / lock["fixture"]).read_bytes()).hexdigest(),
            lock["sha256"],
        )
        for name in (
            "hello",
            "state",
            "plan",
            "accepted",
            "finished",
            "error",
            "live_begin",
            "live_accepted",
            "live_updated",
            "live_finished",
        ):
            self.assertEqual(decode(json.dumps(FIXTURE[name]).encode()), FIXTURE[name])
        for invalid in (
            b'{"api":1,"api":1}',
            b'{"api":true,"id":"x","result":{}}',
            b'{"api":1,"id":"x","result":{"n":1e999}}',
            b"x" * MAX_FRAME,
        ):
            with self.assertRaises(ValueError):
                decode(invalid)

    def test_render_refresh_and_theme_send_zero_mutations(self):
        engine = QQmlApplicationEngine()
        engine.setInitialProperties({"controller": self.controller})
        engine.load(QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Main.qml")))
        self.assertTrue(engine.rootObjects())
        window: QQuickWindow = engine.rootObjects()[0]
        QTest.qWait(30)
        self.assertEqual(self.client.requests, [])
        self.controller.changed.emit()
        original = QPalette(APP.palette())
        try:
            for background, foreground, accent in (
                ("#17252e", "#e3f1f8", "#e8a442"),
                ("#f2f5f7", "#17252e", "#254b92"),
            ):
                palette = QPalette(original)
                palette.setColor(QPalette.Window, QColor(background))
                palette.setColor(QPalette.WindowText, QColor(foreground))
                palette.setColor(QPalette.Highlight, QColor(accent))
                APP.setPalette(palette)
                QTest.qWait(10)
                self.assertEqual(window.property("color"), QColor(background))
                for expression, expected in (
                    ("palette.windowText", foreground),
                    ("palette.highlight", accent),
                ):
                    actual, _ = QQmlExpression(
                        engine.rootContext(), window, expression
                    ).evaluate()
                    self.assertEqual(actual, QColor(expected))
                self.assertEqual(self.client.requests, [])
                self.assertFalse(window.grabWindow().isNull())
        finally:
            APP.setPalette(original)
            window.close()
            engine.deleteLater()
            APP.processEvents()

    def test_feedback_never_moves_the_controls_between_gestures(self):
        engine = QQmlApplicationEngine()
        engine.setInitialProperties({"controller": self.controller})
        engine.load(QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Main.qml")))
        window: QQuickWindow = engine.rootObjects()[0]
        QTest.qWait(20)
        tabs = window.findChild(QObject, "workspaceTabs")
        panel = window.findChild(QObject, "feedbackPanel")
        feedback = window.findChild(QObject, "feedbackText")
        master = window.findChild(QObject, "masterControl")
        from PySide6.QtCore import QPointF

        def position():
            point = master.mapToScene(QPointF(0, 0))
            return (tabs.property("y"), point.y(), panel.property("height"))

        baseline = position()
        for message in (
            "Device readback verified",
            "",
            "A long device error requiring review and reconciliation. " * 12,
        ):
            self.controller._message = message
            self.controller.changed.emit()
            QTest.qWait(20)
            self.assertEqual(position(), baseline)
            self.assertTrue(feedback.property("text"))
        self.controller._pending = {"key": "unknown"}
        self.controller._busy = False
        self.controller.changed.emit()
        QTest.qWait(20)
        self.assertEqual(position(), baseline)
        self.assertEqual(self.client.requests, [])
        self.controller._pending = None
        window.close()
        engine.deleteLater()
        APP.processEvents()

    def test_commit_uses_a_plan_and_retains_identity_before_apply(self):
        self.controller.change({"kind": "master", "mix": "out12", "level_db": None})
        method, params, callback = self.client.requests.pop()
        self.assertEqual(method, "plan_changes")
        self.assertIsNone(params["changes"][0]["level_db"])
        self.assertFalse(self.controller.canWrite)
        callback(copy.deepcopy(FIXTURE["plan"]["result"]), None)
        method, params, callback = self.client.requests.pop()
        self.assertEqual(method, "apply_plan")
        stored = Preferences(self.preferences.path).data
        self.assertEqual(stored["pending_operation"]["key"], params["idempotency_key"])
        callback(copy.deepcopy(FIXTURE["accepted"]["result"]), None)
        finished = copy.deepcopy(FIXTURE["finished"]["result"])
        self.controller._event({"event": "operation_finished", "data": finished})
        self.assertNotIn("pending_operation", self.preferences.data)

    def test_unknown_outcome_blocks_new_writes_without_replay(self):
        self.controller._pending = {"key": "uncertain"}
        self.controller._completed(
            {"status": "indeterminate", "device_outcome": "unknown"}
        )
        self.assertFalse(self.controller.canWrite)
        self.assertTrue(self.controller.uncertain)
        self.controller.change({"kind": "master", "mix": "out12", "level_db": -6})
        self.assertEqual(self.client.requests, [])
        self.controller.acknowledge()
        self.assertFalse(self.controller.canWrite)
        self.assertIsNotNone(self.controller._pending)

    def test_restore_inspection_and_expiry_do_not_apply(self):
        self.controller._snapshot = "snapshot-content"
        self.controller.previewRestore("out12")
        method, params, callback = self.client.requests.pop()
        self.assertEqual(method, "plan_restore")
        callback(copy.deepcopy(FIXTURE["plan"]["result"]), None)
        self.assertTrue(self.controller.previewRows)
        self.controller._plan_deadline = 0
        self.controller.applyRestore()
        self.assertEqual(self.client.requests, [])

    def test_qml_level_refresh_preview_and_release_rules(self):
        engine = QQmlApplicationEngine()
        from PySide6.QtQml import QQmlComponent

        component = QQmlComponent(
            engine,
            QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/LevelControl.qml")),
        )
        control = component.createWithInitialProperties(
            {"label": "Test", "confirmed": -6.0, "revision": "r1"}
        )
        self.assertIsNotNone(control, component.errors())
        commits, conflicts = [], []
        control.committed.connect(commits.append)
        control.conflicted.connect(lambda: conflicts.append(True))
        control.setProperty("confirmed", -12.0)
        APP.processEvents()
        self.assertEqual(commits, [])
        control.setProperty("dirty", True)
        control.setProperty("preview", -9.0)
        self.assertEqual(commits, [])
        control.finish(-9.0)
        self.assertEqual(commits, [-9.0])
        control.setProperty("dirty", True)
        control.setProperty("revision", "r2")
        control.finish(-4.0)
        self.assertEqual(commits, [-9.0])
        self.assertEqual(conflicts, [True])
        control.deleteLater()
        engine.deleteLater()
        APP.processEvents()

    def test_live_control_coalesces_while_waiting_and_sends_final_value(self):
        target = {"kind": "master_level", "mix": "out12"}
        self.controller.adjust(target, -20, False)
        method, params, begun = self.client.requests.pop()
        self.assertEqual(method, "begin_control")
        self.assertTrue(self.controller.liveActive)
        self.assertFalse(self.controller.canWrite)
        begun({"operation_id": "live-1", "status": "pending"}, None)
        method, first, accepted = self.client.requests.pop()
        self.assertEqual(
            (method, first["value"], first["finish"]), ("update_control", -20, False)
        )
        accepted({"accepted": True}, None)
        for value in range(-19, -8):
            self.controller.adjust(target, value, False)
        self.controller.adjust(target, -7.25, True)
        self.assertEqual(self.client.requests, [])
        # Own readback updates the visible baseline without causing edit conflicts.
        old_revision = self.controller.editRevision
        state = copy.deepcopy(self.controller._state)
        state.update(revision="own-revision", operation_id="live-1")
        self.controller._event({"event": "state_changed", "data": state})
        self.assertEqual(self.controller.editRevision, old_revision)
        self.controller._event(
            {
                "event": "control_updated",
                "data": {
                    "operation_id": "live-1",
                    "status": "pending",
                    "sample_sequence": 1,
                },
            }
        )
        QTest.qWait(100)
        method, final, accepted = self.client.requests.pop()
        self.assertEqual(
            (method, final["value"], final["finish"], final["sequence"]),
            ("update_control", -7.25, True, 2),
        )
        accepted({"accepted": True}, None)
        self.controller._event(
            {
                "event": "operation_finished",
                "data": {
                    "operation_id": "live-1",
                    "status": "completed",
                    "kind": "live_control",
                    "gesture_end": "finished",
                    "device_outcome": "verified",
                    "journal_status": "finalized",
                },
            }
        )
        self.assertFalse(self.controller.liveActive)
        self.assertNotIn("pending_operation", self.preferences.data)

    def test_real_master_pointer_uses_the_continuous_controller_path(self):
        from PySide6.QtCore import QPoint, QPointF, Qt
        from PySide6.QtQuick import QQuickItem

        engine = QQmlApplicationEngine()
        engine.setInitialProperties({"controller": self.controller})
        engine.load(QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Main.qml")))
        window: QQuickWindow = engine.rootObjects()[0]
        QTest.qWait(20)
        master = window.findChild(QObject, "masterControl")
        slider = master.findChild(QQuickItem, "levelSlider")
        scene = slider.mapToScene(QPointF(slider.width() / 2, slider.height() * 0.7))
        start = QPoint(int(scene.x()), int(scene.y()))
        end = QPoint(start.x(), start.y() - 35)
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, end)
        self.assertEqual(self.client.requests[0][0], "begin_control")
        _, _, begun = self.client.requests.pop(0)
        begun({"operation_id": "pointer", "status": "pending"}, None)
        _, first, accepted = self.client.requests.pop(0)
        self.assertFalse(first["finish"])
        self.assertIsInstance(first["value"], float)
        accepted({"accepted": True}, None)
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
        self.assertEqual(self.client.requests, [])
        self.controller._event(
            {
                "event": "control_updated",
                "data": {
                    "operation_id": "pointer",
                    "status": "pending",
                    "sample_sequence": 1,
                },
            }
        )
        QTest.qWait(100)
        self.assertEqual(self.client.requests[0][0], "update_control")
        self.assertTrue(self.client.requests[0][1]["finish"])
        window.close()
        self.controller._unavailable("Test finished")
        engine.deleteLater()
        APP.processEvents()

    def test_live_disconnect_discards_pending_pointer_values_without_replay(self):
        target = {"kind": "master_level", "mix": "out12"}
        self.controller.adjust(target, -20, False)
        _, _, begun = self.client.requests.pop()
        self.controller.adjust(target, -5, True)
        self.controller._unavailable("Disconnected")
        # Even a late admission callback cannot dispatch the buffered value.
        begun({"operation_id": "late", "status": "pending"}, None)
        QTest.qWait(100)
        self.assertEqual(self.client.requests, [])
        self.assertTrue(self.controller.uncertain)
        self.assertFalse(self.controller.canWrite)

    def test_external_change_cancels_a_live_control_instead_of_overwriting(self):
        self.controller.adjust({"kind": "master_level", "mix": "out12"}, -20, False)
        _, _, begun = self.client.requests.pop()
        begun({"operation_id": "live-2", "status": "pending"}, None)
        self.client.requests.clear()
        changed = copy.deepcopy(self.controller._state)
        changed["revision"] = "external-revision"
        self.controller._event({"event": "state_changed", "data": changed})
        self.assertEqual(self.client.requests[-1][0], "cancel_control")
        self.controller.adjust({"kind": "master_level", "mix": "out12"}, -1, True)
        QTest.qWait(100)
        self.assertEqual([m for m, _, _ in self.client.requests], ["cancel_control"])


class AgentTests(unittest.TestCase):
    def test_one_validated_event_has_one_target_and_baselines_do_not_launch(self):
        launched, notices = [], []
        policy = ActivationPolicy(launched.append, notices.append)
        device = {
            "device_id": "d",
            "generation": "g",
            "capabilities": {"control_panel_button": True},
        }
        event = {
            "epoch": "e",
            "event": "control_panel_requested",
            "data": {
                "device_id": "d",
                "generation": "g",
                "event_id": "once",
                "command": "ignored",
            },
        }
        self.assertFalse(policy.handle(event, [device], "disabled"))
        self.assertTrue(policy.handle(event, [device], "application"))
        self.assertFalse(policy.handle(event, [device], "omarchy_panel"))
        self.assertEqual(launched, ["application"])
        device["generation"] = "new"
        self.assertFalse(
            policy.handle(
                {**event, "data": {**event["data"], "event_id": "new"}},
                [device],
                "application",
            )
        )
        self.assertFalse(
            policy.handle(
                {"event": "state_changed", "data": {}}, [device], "application"
            )
        )
        self.assertEqual(notices, [])


if __name__ == "__main__":
    unittest.main()
