import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QPA_PLATFORMTHEME"] = ""
os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Basic")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
from PySide6.QtCore import QObject, QPoint, QPointF, QUrl, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest

APP = QGuiApplication.instance() or QGuiApplication([])
ROOT = Path(__file__).resolve().parents[1]


class InteractionTests(unittest.TestCase):
    def test_pointer_gesture_sends_live_values_and_preserves_final_release(self):
        engine = QQmlEngine()
        component = QQmlComponent(engine)
        component.setData(
            b"""import QtQuick
import QtQuick.Window
Window {
    visible: true; width: 200; height: 480
    LevelControl { objectName: "testControl"; label: "Test"; confirmed: -12; revision: "initial"; anchors.fill: parent }
}""",
            QUrl.fromLocalFile(str(ROOT / "src/minifuse_control/qml/Interaction.qml")),
        )
        window: QQuickWindow = component.create()
        self.assertIsNotNone(window, component.errors())
        QTest.qWait(20)
        control = window.findChild(QObject, "testControl")
        slider = window.findChild(QQuickItem, "levelSlider")
        commits, conflicts = [], []
        control.adjusted.connect(lambda value, finish: commits.append((value, finish)))
        control.conflicted.connect(lambda: conflicts.append(True))
        point = slider.mapToScene(QPointF(slider.width() / 2, slider.height() * 0.7))
        start = QPoint(int(point.x()), int(point.y()))
        end = QPoint(start.x(), start.y() - 45)
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, end)
        self.assertTrue(commits)
        self.assertTrue(all(not finish for _, finish in commits))
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
        self.assertTrue(commits[-1][1])
        control.reset()
        QTest.mousePress(window, Qt.LeftButton, Qt.NoModifier, start)
        QTest.mouseMove(window, end)
        before_conflict = len(commits)
        control.setProperty("revision", "external-change")
        QTest.mouseRelease(window, Qt.LeftButton, Qt.NoModifier, end)
        self.assertEqual(len(commits), before_conflict)
        self.assertEqual(conflicts, [True])
        window.close()
        window.deleteLater()
        engine.deleteLater()
        APP.processEvents()

    def test_second_process_activates_the_existing_application(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runtime = root / "runtime"
            runtime.mkdir(mode=0o700)
            environment = dict(
                os.environ,
                PYTHONPATH=str(ROOT / "src"),
                XDG_RUNTIME_DIR=str(runtime),
                XDG_CONFIG_HOME=str(root / "config"),
                XDG_STATE_HOME=str(root / "state"),
                XDG_DATA_HOME=str(root / "data"),
            )
            command = [sys.executable, "-m", "minifuse_control.app"]
            first = subprocess.Popen(
                command, env=environment, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
            try:
                for _ in range(200):
                    if first.poll() is not None:
                        self.fail(first.communicate()[1].decode())
                    if (runtime / "minifuse-control/activate.sock").exists():
                        break
                    time.sleep(0.01)
                second = subprocess.run(
                    command, env=environment, capture_output=True, timeout=4
                )
                self.assertEqual(second.returncode, 0, second.stderr.decode())
                self.assertIsNone(first.poll())
            finally:
                first.terminate()
                first.communicate(timeout=4)


if __name__ == "__main__":
    unittest.main()
