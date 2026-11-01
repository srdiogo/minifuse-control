"""Synthetic model layouts and control gates; these are not device captures."""

import copy
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


if __name__ == "__main__":
    unittest.main()
