"""Presentation regressions exercised with isolated Qt windows and no device."""

from pathlib import Path
import unittest

import test_application as application
from test_application import APP
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

ROOT = Path(__file__).resolve().parents[1]
QML = ROOT / "src/minifuse_control/qml"


def visual(item, name):
    if item.objectName() == name:
        return item
    for child in item.childItems():
        found = visual(child, name)
        if found is not None:
            return found
    return None


def click(window, item):
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window, Qt.LeftButton, Qt.NoModifier, QPoint(round(point.x()), round(point.y()))
    )


class PresentationTests(unittest.TestCase):
    def test_source_picker_opens_without_writes_and_uses_verified_membership(self):
        fixture = application.ApplicationTests()
        fixture.setUp()
        engine = QQmlApplicationEngine()
        engine.setInitialProperties({"controller": fixture.controller})
        engine.load(QUrl.fromLocalFile(str(QML / "Main.qml")))
        window = engine.rootObjects()[0]
        try:
            QTest.qWait(20)
            click(window, visual(window.contentItem(), "sourcesButton"))
            QTest.qWait(30)
            member = visual(window.contentItem(), "membershipSource-analog1")
            self.assertIsNotNone(member)
            self.assertTrue(member.property("active"))
            self.assertEqual(fixture.client.requests, [])
            click(window, member)
            self.assertTrue(member.property("active"))
            method, params, _ = fixture.client.requests[-1]
            self.assertEqual(method, "plan_changes")
            self.assertEqual(
                params["changes"],
                [
                    {
                        "kind": "membership",
                        "mix": "out12",
                        "source": "analog1",
                        "included": False,
                    }
                ],
            )
        finally:
            window.close()
            engine.deleteLater()
            APP.processEvents()
            fixture.tearDown()

    def test_state_button_keeps_on_and_off_distinct_during_pointer_and_keyboard_focus(
        self,
    ):
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(
            b"""import QtQuick
import QtQuick.Window
Window {
    visible: true; width: 160; height: 100
    StateButton {
        objectName: "stateButton"; text: "M"; description: "Source mute"
        anchors.centerIn: parent
        onClicked: active = !active
    }
}""",
            QUrl.fromLocalFile(str(QML / "StateInteraction.qml")),
        )
        window = component.create()
        self.assertIsNotNone(window, component.errors())
        button = window.findChild(QQuickItem, "stateButton")
        try:
            QTest.qWait(20)
            off_color = button.property("contentItem").property("color")
            for _ in range(2):
                click(window, button)
                QTest.qWait(10)
                self.assertTrue(button.property("active"))
                self.assertTrue(button.property("highlighted"))
                self.assertTrue(button.hasActiveFocus())
                self.assertNotEqual(
                    button.property("contentItem").property("color"), off_color
                )
                click(window, button)
                QTest.qWait(10)
                self.assertFalse(button.property("active"))
                self.assertTrue(button.hasActiveFocus())
                self.assertEqual(
                    button.property("contentItem").property("color"), off_color
                )
            QTest.keyClick(window, Qt.Key_Space)
            self.assertTrue(button.property("active"))
            QTest.keyClick(window, Qt.Key_Space)
            self.assertFalse(button.property("active"))
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            APP.processEvents()

    def test_minimum_window_keeps_master_and_gain_entry_inside_the_viewport(self):
        fixture = application.ApplicationTests()
        fixture.setUp()
        engine = QQmlApplicationEngine()
        engine.setInitialProperties({"controller": fixture.controller})
        engine.load(QUrl.fromLocalFile(str(QML / "Main.qml")))
        window = engine.rootObjects()[0]
        try:
            page = window.findChild(QObject, "mixerPage")
            for size in ((840, 640), (1280, 820), (960, 1056)):
                window.setWidth(size[0])
                window.setHeight(size[1])
                for index in range(3):
                    page.setProperty("selected", index)
                    QTest.qWait(30)
                    viewport = window.findChild(QQuickItem, "stripViewport")
                    top = viewport.mapToScene(QPointF()).y()
                    bottom = top + viewport.height()
                    for name in ("masterControl", "sourceLevel-analog1"):
                        control = visual(window.contentItem(), name)
                        for part in ("levelSlider", "levelEntry"):
                            item = visual(control, part)
                            point = item.mapToScene(QPointF())
                            self.assertGreaterEqual(point.y(), top)
                            self.assertLessEqual(point.y() + item.height(), bottom)
                    master = visual(window.contentItem(), "masterStrip")
                    right = master.mapToScene(QPointF(master.width(), 0)).x()
                    self.assertLessEqual(right, window.width())
            self.assertEqual(fixture.client.requests, [])
        finally:
            window.close()
            engine.deleteLater()
            APP.processEvents()
            fixture.tearDown()

    def test_gain_readout_follows_readback_after_numeric_entry_and_reset(self):
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(
            b"""import QtQuick
import QtQuick.Window
Window {
    visible: true; width: 200; height: 480
    LevelControl {
        objectName: "gain"; label: "Gain"; confirmed: -12
        anchors.fill: parent
    }
}""",
            QUrl.fromLocalFile(str(QML / "GainInteraction.qml")),
        )
        window = component.create()
        self.assertIsNotNone(window, component.errors())
        control = window.findChild(QQuickItem, "gain")
        numeric = window.findChild(QQuickItem, "levelValue")
        commits = []
        control.committed.connect(commits.append)
        try:
            QTest.qWait(20)
            click(window, numeric)
            numeric.setProperty("text", "-24 dB")
            QTest.keyClick(window, Qt.Key_Return)
            self.assertEqual(commits, [-24])
            control.reset()
            control.setProperty("confirmed", -18.5)
            QTest.qWait(10)
            self.assertEqual(numeric.property("text"), "-18.50 dB")
            self.assertEqual(commits, [-24])
            control.setProperty("dirty", True)
            control.setProperty("preview", -30.25)
            QTest.qWait(10)
            self.assertEqual(numeric.property("text"), "-30.25 dB")
            control.reset()
            self.assertEqual(numeric.property("text"), "-18.50 dB")
        finally:
            window.close()
            window.deleteLater()
            engine.deleteLater()
            APP.processEvents()


if __name__ == "__main__":
    unittest.main()
