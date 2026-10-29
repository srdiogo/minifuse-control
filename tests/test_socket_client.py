import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ["QT_QPA_PLATFORMTHEME"] = ""
from PySide6.QtCore import QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtNetwork import QLocalServer
from PySide6.QtTest import QTest
from minifuse_control.client import Client
from minifuse_control.preferences import Preferences

APP = QGuiApplication.instance() or QGuiApplication([])
ROOT = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((ROOT / "tests/contract/v1.json").read_text())


class SocketClientTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.path = Path(self.directory.name) / "control.sock"
        self.server = QLocalServer()
        self.assertTrue(self.server.listen(str(self.path)), self.server.errorString())
        self.preferences = Preferences(Path(self.directory.name) / "preferences.json")
        self.client = Client(self.preferences)
        self.requests, self.peers, self.events = [], [], []
        self.client.event.connect(self.events.append)
        self.server.newConnection.connect(self.connected)
        self.patching = patch(
            "minifuse_control.client.socket_path", return_value=self.path
        )
        self.patching.start()
        self.mode = "normal"

    def tearDown(self):
        self.client.close()
        for peer in self.peers:
            peer.abort()
        self.server.close()
        self.patching.stop()
        APP.processEvents()
        self.directory.cleanup()

    def wait(self, predicate):
        for _ in range(200):
            APP.processEvents()
            if predicate():
                return
            QTest.qWait(5)
        self.fail("Socket condition was not reached")

    def connected(self):
        peer = self.server.nextPendingConnection()
        self.peers.append(peer)
        buffer = bytearray()

        def read():
            buffer.extend(bytes(peer.readAll()))
            while b"\n" in buffer:
                frame, _, remaining = buffer.partition(b"\n")
                buffer[:] = remaining
                request = json.loads(frame)
                self.requests.append(request)
                if request["method"] == "apply_plan" and self.mode == "disconnect":
                    peer.abort()
                    return
                if request["method"] == "hello":
                    result = copy.deepcopy(FIXTURE["hello"]["result"])
                else:
                    result = {
                        "epoch": "fixture-epoch",
                        "seq": 0,
                        "devices": [],
                        "states": [],
                    }
                response = (
                    json.dumps(
                        {"api": 1, "id": request["id"], "result": result}
                    ).encode()
                    + b"\n"
                )
                if request["method"] == "subscribe":
                    response += b'{"event":"future_event","epoch":"fixture-epoch","seq":1,"data":{}}\n'
                middle = len(response) // 2
                peer.write(response[:middle])
                QTimer.singleShot(
                    0,
                    lambda response=response, middle=middle, peer=peer: peer.write(
                        response[middle:]
                    ),
                )

        peer.readyRead.connect(read)

    def test_fragmented_response_then_event_obeys_baseline_order(self):
        def ready(_):
            self.client.request(
                "subscribe",
                {"events": []},
                lambda result, error: setattr(self.client, "sequence", result["seq"]),
            )

        self.client.ready.connect(ready)
        self.client.connect_service()
        self.wait(lambda: len(self.events) == 1)
        self.assertEqual(self.events[0]["seq"], 1)
        self.assertEqual([r["method"] for r in self.requests], ["hello", "subscribe"])
        self.assertEqual(
            Preferences(self.preferences.path).data["client_token"],
            "fixture-client_token",
        )

    def test_disconnect_during_apply_preserves_unknown_result_without_replay(self):
        failures = []
        self.mode = "disconnect"
        self.client.ready.connect(
            lambda _: self.client.request(
                "apply_plan",
                {"plan_id": "plan", "idempotency_key": "once"},
                lambda result, error: failures.append(error),
            )
        )
        self.client.connect_service()
        self.wait(lambda: bool(failures))
        self.client.reconnect.stop()
        self.assertEqual(failures[0]["code"], "outcome_unknown")
        self.assertEqual(sum(r["method"] == "apply_plan" for r in self.requests), 1)


if __name__ == "__main__":
    unittest.main()
