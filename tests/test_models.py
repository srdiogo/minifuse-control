"""Synthetic model layouts and control gates; these are not device captures."""

import copy
import hashlib
import json
from pathlib import Path
import unittest

import test_application as application
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from test_presentation import visual
from PySide6.QtTest import QTest

ROOT = Path(__file__).resolve().parents[1]
MODELS = json.loads((ROOT / "tests/contract/model-profiles-v1.json").read_text())


class ModelTests(unittest.TestCase):
    def setUp(self):
        self.fixture = application.ApplicationTests()
        self.fixture.setUp()
        self.controller = self.fixture.controller

    def tearDown(self):
        self.fixture.tearDown()

    def select(self, model, enabled=True):
        profile = copy.deepcopy(model["profile"])
        device = dict(
            device_id="synthetic",
            generation="generation",
            model=profile["model"],
            product_id=model["product_id"],
            profile=profile,
            connection="ready" if enabled else "unavailable",
            capabilities=dict(
                mixer=False,
                input_switches=enabled,
                switch_readback=enabled,
                signal_meters=False,
                mixes=[],
            ),
        )
        inputs = {c["target"]: False for c in profile["input_controls"]}
        state = dict(
            device_id="synthetic",
            generation="generation",
            revision="revision",
            capabilities=device["capabilities"],
            state=dict(
                model=profile["model"],
                layout="minifuse-basic-b2-v1",
                inputs=inputs,
                mixes=[],
            ),
        )
        self.controller._devices = [device]
        self.controller._device = device
        self.controller._state = state if enabled else {}
        self.controller._busy = False
        self.controller._availability()

    def test_each_basic_model_renders_its_controls_without_an_mf4_mixer(self):
        lock = json.loads((ROOT / "model-contract.lock.json").read_text())
        for fixture in lock["fixtures"]:
            self.assertEqual(
                hashlib.sha256((ROOT / fixture["path"]).read_bytes()).hexdigest(),
                fixture["sha256"],
            )
        for model in MODELS["devices"]:
            if model["profile"]["id"] == "mf4":
                continue
            normal = model["profile"]["device_mode"] == "control"
            self.select(model, normal)
            engine = QQmlApplicationEngine()
            engine.setInitialProperties({"controller": self.controller})
            engine.load(
                QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Main.qml"))
            )
            self.assertTrue(engine.rootObjects())
            window = engine.rootObjects()[0]
            try:
                window.setWidth(840)
                window.setHeight(640)
                QTest.qWait(20)
                self.assertIsNotNone(window.findChild(QObject, "modelPage"))
                self.assertIsNone(window.findChild(QObject, "mixerPage"))
                self.assertFalse(self.controller.canWrite)
                self.assertEqual(self.controller.canWriteInputs, normal)
                expected = {c["target"] for c in model["profile"]["input_controls"]}
                self.assertEqual(
                    {c["target"] for c in self.controller.inputControls}, expected
                )
                for target in ("inst1", "inst2", "phantom_power", "direct_monitor"):
                    control = visual(window.contentItem(), "inputSwitch-" + target)
                    self.assertEqual(
                        control is not None,
                        target in expected,
                        (model["product_id"], target),
                    )
                self.assertEqual(self.fixture.client.requests, [])
            finally:
                window.close()
                engine.deleteLater()
                application.APP.processEvents()

    def test_basic_switch_uses_a_typed_plan_and_waits_for_readback(self):
        model = MODELS["devices"][0]
        self.select(model)
        self.controller.setInputSwitch("inst2", True)
        self.assertEqual(self.fixture.client.requests, [])
        self.controller.setInputSwitch("direct_monitor", True)
        method, params, _ = self.fixture.client.requests[-1]
        self.assertEqual(method, "plan_changes")
        self.assertEqual(
            params["changes"],
            [dict(kind="input_switch", target="direct_monitor", enabled=True)],
        )
        self.assertFalse(self.controller.inputs["direct_monitor"])
        self.assertFalse(self.controller.canWriteInputs)

    def test_readback_and_explicit_capability_are_both_required(self):
        self.select(MODELS["devices"][1], False)
        self.controller.setInputSwitch("phantom_power", True)
        self.assertFalse(self.controller.canWriteInputs)
        self.assertEqual(self.fixture.client.requests, [])
        self.select(MODELS["devices"][1])
        self.controller._state["capabilities"]["input_switches"] = False
        self.controller.setInputSwitch("inst1", True)
        self.assertEqual(self.fixture.client.requests, [])
        self.controller._devices.append(copy.deepcopy(self.controller._device))
        self.assertIsNone(self.controller._select_device())

    def test_unknown_profile_schema_never_grants_control_access(self):
        self.select(MODELS["devices"][1])
        self.controller._device["profile"]["schema_version"] = 2
        self.assertFalse(self.controller.canWriteInputs)
        self.assertEqual(self.controller.panelLayout, "unsupported")
        self.assertEqual(self.controller.inputControls, [])
        self.controller.setInputSwitch("inst1", True)
        self.assertEqual(self.fixture.client.requests, [])

    def test_changing_from_mf4_presets_selects_the_basic_model_page(self):
        engine = QQmlApplicationEngine()
        engine.setInitialProperties({"controller": self.controller})
        engine.load(QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Main.qml")))
        window = engine.rootObjects()[0]
        try:
            tabs = window.findChild(QObject, "workspaceTabs")
            tabs.setProperty("currentIndex", 1)
            self.select(MODELS["devices"][0])
            QTest.qWait(20)
            self.assertEqual(tabs.property("currentIndex"), 0)
            self.assertIsNotNone(window.findChild(QObject, "modelPage"))
            self.assertIsNone(window.findChild(QObject, "mixerPage"))
            self.assertEqual(self.fixture.client.requests, [])
        finally:
            window.close()
            engine.deleteLater()
            application.APP.processEvents()


NATIVE = json.loads((ROOT / "tests/contract/loopback-v1.json").read_text())["devices"]


class LoopbackTests(unittest.TestCase):
    setUp = ModelTests.setUp
    tearDown = ModelTests.tearDown

    def select_native(self, fixture):
        self.controller._device = copy.deepcopy(fixture["device"])
        self.controller._devices = [self.controller._device]
        self.controller._state = copy.deepcopy(fixture["state"])
        self.controller._busy = False
        self.controller._availability()

    def test_native_pages_keep_model_sources_and_stable_faders_during_readback(self):
        for fixture in NATIVE:
            self.select_native(fixture)
            engine = QQmlApplicationEngine()
            engine.setInitialProperties({"controller": self.controller})
            engine.load(
                QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Main.qml"))
            )
            self.assertTrue(engine.rootObjects())
            window = engine.rootObjects()[0]
            try:
                window.setWidth(1000)
                window.setHeight(900)
                QTest.qWait(30)
                self.assertTrue(self.controller.canWrite)
                self.assertTrue(self.controller.capabilities["host_snapshots"])
                self.assertEqual(
                    [m["mix"] for m in self.controller.mixes], ["loopback"]
                )
                channel = visual(window.contentItem(), "sourceLevel-analog1")
                self.assertIsNotNone(channel)
                stereo = visual(window.contentItem(), "sourcePan-usb12")
                self.assertFalse(stereo.isVisible())
                solo = visual(window.contentItem(), "sourceSolo-analog1")
                self.assertFalse(solo.isVisible())
                otg = visual(window.contentItem(), "mainToOtg")
                self.assertEqual(
                    otg.isVisible(), self.controller.modelProfile["id"] == "mf2_otg"
                )
                self.controller._state["revision"] = "updated-revision"
                self.controller._state["state"]["mixes"][0]["channels"][0][
                    "derived_level_db"
                ] = -18
                self.controller.changed.emit()
                QTest.qWait(10)
                self.assertIs(
                    visual(window.contentItem(), "sourceLevel-analog1"), channel
                )
                self.assertEqual(channel.property("confirmed"), -18)
                self.assertEqual(self.fixture.client.requests, [])
                self.assertFalse(window.grabWindow().isNull())
            finally:
                window.close()
                engine.deleteLater()
                application.APP.processEvents()

    def test_native_routing_waits_for_readback_and_firmware_mismatch_blocks_writes(
        self,
    ):
        self.select_native(NATIVE[0])
        self.controller.change(dict(kind="loopback_routing", monitor=True))
        method, params, _ = self.fixture.client.requests[-1]
        self.assertEqual(method, "plan_changes")
        self.assertEqual(
            params["changes"], [dict(kind="loopback_routing", monitor=True)]
        )
        self.assertFalse(self.controller.loopbackRouting["monitor"])
        for modify in (
            lambda d: d.pop("firmware"),
            lambda d: d["firmware"].update(loopback_compatible=False),
            lambda d: d["firmware"].update(raw_bcd=0x151),
        ):
            self.select_native(NATIVE[1])
            modify(self.controller._device)
            self.assertFalse(self.controller.canWrite)
            self.assertTrue(self.controller.canWriteInputs)

    def test_native_master_stays_enabled_during_its_pending_live_gesture(self):
        self.select_native(NATIVE[0])
        engine = QQmlApplicationEngine()
        engine.setInitialProperties({"controller": self.controller})
        engine.load(QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Main.qml")))
        window = engine.rootObjects()[0]
        try:
            QTest.qWait(20)
            master = visual(window.contentItem(), "loopbackMasterLevel")
            self.controller.adjust(
                {"kind": "master_level", "mix": "loopback"}, -18, False
            )
            QTest.qWait(10)
            self.assertTrue(self.controller.liveActive)
            self.assertFalse(self.controller.canWrite)
            self.assertTrue(master.isEnabled())
            self.assertEqual(self.fixture.client.requests[-1][0], "begin_control")
        finally:
            window.close()
            engine.deleteLater()
            application.APP.processEvents()

    def test_native_restore_preview_includes_stereo_side_and_routing_changes(self):
        self.select_native(NATIVE[1])
        predicted = copy.deepcopy(self.controller._state["state"])
        predicted["mixes"][0]["channels"][2]["db_right"] = -24
        predicted["mixes"][0]["channels"][2]["mute_mixed"] = True
        predicted["loopback"]["monitor"] = True
        self.controller._preview = {
            "plan_id": "synthetic-plan",
            "predicted_state": predicted,
        }
        fields = {row["field"] for row in self.controller.previewRows}
        self.assertEqual(
            fields,
            {
                "loopback · monitor",
                "loopback · usb12 · Right dB",
                "loopback · usb12 · Mixed mute",
            },
        )

    def test_native_meter_shapes_expiry_and_model_isolation(self):
        for fixture in NATIVE:
            self.select_native(fixture)
            self.controller._got_meters(fixture["meters"])
            self.assertEqual(
                self.controller.meters["inputs_dbfs"], fixture["meters"]["inputs_dbfs"]
            )
            for field, value in (
                ("loopback_dbfs", [0]),
                ("inputs_dbfs", [True]),
                (
                    "otg_dbfs",
                    [0, 0] if fixture["device"]["profile"]["id"] != "mf2_otg" else None,
                ),
            ):
                malformed = copy.deepcopy(fixture["meters"])
                malformed[field] = value
                self.controller._got_meters(malformed)
                self.assertEqual(self.controller.meters, {})
            self.controller._got_meters(fixture["meters"])
            QTest.qWait(550)
            self.assertEqual(self.controller.meters, {})


if __name__ == "__main__":
    unittest.main()
