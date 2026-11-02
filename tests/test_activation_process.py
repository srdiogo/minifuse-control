"""Single-instance presentation through the actual application entrypoint."""

import os
from pathlib import Path
import subprocess
import socket
import sys
import tempfile
import time
import unittest


class ActivationProcessTests(unittest.TestCase):
    def test_repeated_presentation_keeps_one_process_and_releases_socket_timers(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            tools = root / "bin"
            tools.mkdir()
            notification = tools / "notify-send"
            notification.write_text("#!/bin/sh\nexit 0\n")
            notification.chmod(0o700)
            environment = {
                **os.environ,
                "XDG_RUNTIME_DIR": str(root),
                "XDG_CONFIG_HOME": str(root / "config"),
                "XDG_DATA_HOME": str(root / "data"),
                "XDG_STATE_HOME": str(root / "state"),
                "QT_QPA_PLATFORM": "offscreen",
                "QT_QPA_PLATFORMTHEME": "",
                "QT_QUICK_BACKEND": "software",
                "PATH": str(tools) + os.pathsep + os.environ.get("PATH", ""),
            }
            command = [sys.executable, "-m", "minifuse_control.app"]
            with (root / "stderr.log").open("w+") as log:
                process = subprocess.Popen(
                    command,
                    env=environment,
                    stdout=subprocess.DEVNULL,
                    stderr=log,
                )
                try:
                    endpoint = root / "minifuse-control/activate.sock"
                    deadline = time.monotonic() + 5
                    while not endpoint.exists() and time.monotonic() < deadline:
                        self.assertIsNone(process.poll())
                        time.sleep(0.02)
                    self.assertTrue(endpoint.exists())
                    for _ in range(3):
                        presented = subprocess.run(
                            command, env=environment, capture_output=True, timeout=5
                        )
                        self.assertEqual(presented.returncode, 0, presented.stderr)
                        self.assertIsNone(process.poll())
                    # Completed peers have been deleted when their former
                    # one-second deadlines expire. No callback may target them.
                    with socket.socket(socket.AF_UNIX) as idle:
                        idle.settimeout(3)
                        idle.connect(str(endpoint))
                        self.assertEqual(idle.recv(1), b"")
                    time.sleep(0.2)
                    self.assertIsNone(process.poll())
                    log.flush()
                    log.seek(0)
                    diagnostics = log.read()
                    self.assertNotIn("No Wrapper found", diagnostics)
                    self.assertNotIn("Internal C++ object", diagnostics)
                    self.assertNotIn("Traceback (most recent call last)", diagnostics)
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait(timeout=5)
