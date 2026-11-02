"""Exercise the Qt-free activation agent through its real socket protocol."""

import json
from pathlib import Path
import socket
import tempfile
import threading
import unittest
from unittest.mock import Mock, patch

from minifuse_control import desktop
from minifuse_control.preferences import Preferences


class DesktopProtocolTests(unittest.TestCase):
    def exchange(self, messages, *, capability=True):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            device = {
                "device_id": "mf4",
                "generation": "connection-1",
                "capabilities": {"control_panel_button": capability},
            }
            requests, errors, launched = [], [], []
            preferences = Preferences(root / "desktop.json")
            preferences.data["activation_target"] = "application"
            preferences.save()
            with socket.socket(socket.AF_UNIX) as listener:
                listener.bind(str(root / "control.sock"))
                listener.listen(1)
                listener.settimeout(3)

                def serve():
                    try:
                        stream, _ = listener.accept()
                        with stream, stream.makefile("rb") as reader:
                            for result in (
                                {"epoch": "epoch-1", "client_token": "agent-token"},
                                {"devices": [device]},
                                {"seq": 0, "devices": [device]},
                            ):
                                request = json.loads(reader.readline())
                                requests.append(request)
                                stream.sendall(
                                    json.dumps(
                                        {
                                            "api": 1,
                                            "id": request["id"],
                                            "result": result,
                                        }
                                    ).encode()
                                    + b"\n"
                                )
                            for message in messages:
                                stream.sendall(json.dumps(message).encode() + b"\n")
                    except Exception as error:
                        errors.append(error)

                worker = threading.Thread(target=serve)
                worker.start()
                try:
                    with (
                        patch.object(
                            desktop, "socket_path", return_value=root / "control.sock"
                        ),
                        patch.object(desktop, "Preferences", return_value=preferences),
                    ):
                        try:
                            desktop.session(
                                desktop.ActivationPolicy(launched.append),
                                Preferences(root / "agent.json"),
                            )
                        except (ConnectionError, ValueError) as error:
                            errors.append(error)
                finally:
                    worker.join(timeout=4)
                self.assertFalse(worker.is_alive())
            return requests, errors, launched

    @staticmethod
    def event(sequence, event_id, **overrides):
        return {
            "epoch": "epoch-1",
            "seq": sequence,
            "event": "control_panel_requested",
            "data": {
                "device_id": "mf4",
                "generation": "connection-1",
                "event_id": event_id,
            },
            **overrides,
        }

    def test_initial_baseline_never_launches_and_capability_controls_subscription(self):
        for supported in (False, True):
            with self.subTest(supported=supported):
                requests, errors, launched = self.exchange([], capability=supported)
                self.assertEqual(launched, [])
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0], ConnectionError)
                self.assertEqual(
                    "control_panel_requested" in requests[-1]["params"]["events"],
                    supported,
                )

    def test_unique_events_launch_once_duplicate_event_ids_do_not(self):
        _, errors, launched = self.exchange(
            [
                self.event(1, "press-9"),
                self.event(2, "press-9"),
                self.event(3, "press-0"),
            ]
        )
        self.assertEqual(launched, ["application", "application"])
        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], ConnectionError)

    def test_epoch_or_sequence_gap_requires_a_new_baseline_before_launch(self):
        for event in (self.event(2, "gap"), self.event(1, "restart", epoch="new")):
            with self.subTest(event=event):
                _, errors, launched = self.exchange([event])
                self.assertEqual(launched, [])
                self.assertEqual(len(errors), 1)
                self.assertIsInstance(errors[0], ValueError)

    def test_capability_loss_renegotiates_without_launching(self):
        _, errors, launched = self.exchange(
            [
                {
                    "epoch": "epoch-1",
                    "seq": 1,
                    "event": "capabilities_changed",
                    "data": {},
                }
            ]
        )
        self.assertEqual(launched, [])
        self.assertEqual(errors, [])


class DesktopLaunchTests(unittest.TestCase):
    def test_systemd_session_launch_uses_a_separate_unit_and_fixed_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "systemd").mkdir()
            with socket.socket(socket.AF_UNIX) as manager:
                manager.bind(str(root / "systemd/private"))
                with (
                    patch.dict(desktop.os.environ, {"XDG_RUNTIME_DIR": str(root)}),
                    patch.object(
                        desktop.shutil,
                        "which",
                        side_effect=lambda name: {
                            "systemd-run": "/usr/bin/systemd-run",
                            "minifuse-control": "/opt/minifuse/bin/minifuse-control",
                        }.get(name),
                    ),
                    patch.object(desktop.subprocess, "run") as launch,
                    patch.object(desktop.subprocess, "Popen") as direct,
                ):
                    desktop.launch_target("application")
                direct.assert_not_called()
                command = launch.call_args.args[0]
                self.assertEqual(command[0], "/usr/bin/systemd-run")
                self.assertIn("--user", command)
                self.assertIn("--service-type=exec", command)
                self.assertEqual(
                    command[-2:], ["--", "/opt/minifuse/bin/minifuse-control"]
                )
                self.assertTrue(launch.call_args.kwargs["check"])

    def test_without_a_session_manager_the_direct_launcher_remains_available(self):
        process = Mock()
        process.wait.return_value = 0
        with (
            patch.dict(desktop.os.environ, {"XDG_RUNTIME_DIR": ""}),
            patch.object(desktop.shutil, "which", return_value=None),
            patch.object(desktop.subprocess, "Popen", return_value=process) as launch,
            patch.object(desktop.subprocess, "run") as managed,
        ):
            desktop.launch_target("application")
        managed.assert_not_called()
        self.assertEqual(launch.call_args.args[0], ["minifuse-control"])
        self.assertTrue(launch.call_args.kwargs["start_new_session"])

    def test_failed_launch_is_reported_once_without_retrying_a_duplicate_event(self):
        launch = Mock(side_effect=OSError("target unavailable"))
        notify = Mock()
        policy = desktop.ActivationPolicy(launch, notify)
        devices = [
            {
                "device_id": "mf4",
                "generation": "connection-1",
                "capabilities": {"control_panel_button": True},
            }
        ]
        event = DesktopProtocolTests.event(1, "failed-launch")
        self.assertTrue(policy.handle(event, devices, "application"))
        self.assertFalse(policy.handle(event, devices, "application"))
        launch.assert_called_once_with("application")
        notify.assert_called_once()
