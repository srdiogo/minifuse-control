"""Optional activation policy. No Qt import, USB access or launch from baseline."""

import argparse
from collections import deque
import fcntl
import os
from pathlib import Path
import socket
import struct
import subprocess
import sys
import time
from . import __version__
from .preferences import Preferences
from .wire import MAX_FRAME, decode, encode, socket_path


class ActivationPolicy:
    def __init__(self, launch=None, notify=None):
        self.seen = deque(maxlen=256)
        self.launch = launch or launch_target
        self.notify = notify or notification

    def handle(self, message, devices, target):
        if (
            target not in ("application", "omarchy_panel")
            or message.get("event") != "control_panel_requested"
        ):
            return False
        data = message.get("data", {})
        identity = (message.get("epoch"), data.get("event_id"))
        if (
            not isinstance(identity[1], str)
            or not identity[1]
            or len(identity[1]) > 128
            or identity in self.seen
        ):
            return False
        valid = any(
            d.get("device_id") == data.get("device_id")
            and d.get("generation") == data.get("generation")
            and d.get("capabilities", {}).get("control_panel_button") is True
            for d in devices
        )
        if not valid:
            return False
        self.seen.append(identity)
        try:
            self.launch(target)
        except (OSError, subprocess.SubprocessError) as error:
            self.notify(f"Activation target unavailable: {error}")
        return True


def launch_target(target):
    if target == "application":
        process = subprocess.Popen(
            ["minifuse-control"],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            status = process.wait(timeout=0.25)
            if status:
                raise OSError("MiniFuse Control could not start")
        except subprocess.TimeoutExpired:
            pass
    elif target == "omarchy_panel":
        result = subprocess.run(
            ["omarchy-shell", "shell", "summon", "srdiogo.minifuse", "{}"],
            capture_output=True,
            text=True,
            timeout=3,
            check=True,
        )
        if result.stdout.strip() != "ok":
            raise OSError("Enable the MiniFuse Omarchy plugin first")
    else:
        raise ValueError("Unsupported activation target")


def notification(message):
    try:
        subprocess.run(
            ["notify-send", "MiniFuse Control", message], timeout=3, check=False
        )
    except (OSError, subprocess.SubprocessError):
        print(message, file=sys.stderr)


def session(policy, identity, stop=lambda: False):
    with socket.socket(socket.AF_UNIX) as stream:
        stream.settimeout(2)
        stream.connect(str(socket_path()))
        _, uid, _ = struct.unpack(
            "3i",
            stream.getsockopt(
                socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i")
            ),
        )
        if uid != os.geteuid():
            raise ValueError("Unexpected service owner")
        buffer = bytearray()
        frame_started = None

        def receive():
            nonlocal frame_started
            while b"\n" not in buffer:
                if frame_started is not None and time.monotonic() - frame_started > 2:
                    raise ValueError("Frame deadline expired")
                chunk = stream.recv(min(4096, MAX_FRAME - len(buffer)))
                if not chunk:
                    raise ConnectionError("Service disconnected")
                if not buffer:
                    frame_started = time.monotonic()
                buffer.extend(chunk)
                if len(buffer) >= MAX_FRAME and b"\n" not in buffer:
                    raise ValueError("Oversize service frame")
            frame, _, tail = buffer.partition(b"\n")
            buffer[:] = tail
            frame_started = time.monotonic() if tail else None
            return decode(bytes(frame))

        def request(identifier, method, params):
            stream.sendall(encode(identifier, method, params))
            result = receive()
            if result.get("id") != identifier or "error" in result:
                raise ValueError("Agent request rejected")
            return result["result"]

        params = {"client": "minifuse-desktop-agent", "supported_api": [1]}
        if token := identity.data.get("client_token"):
            params["client_token"] = token
        hello = request("hello", "hello", params)
        identity.data["client_token"] = hello["client_token"]
        identity.save()
        devices = request("devices", "list_devices", {})["devices"]
        events = ["device_added", "device_removed", "capabilities_changed"]
        if any(d.get("capabilities", {}).get("control_panel_button") for d in devices):
            events.append("control_panel_requested")
        baseline = request("subscribe", "subscribe", {"events": events})
        devices, sequence = baseline["devices"], baseline["seq"]
        while not stop():
            preferences = Preferences()
            target = preferences.data.get("activation_target", "disabled")
            if target == "disabled":
                return
            try:
                message = receive()
            except socket.timeout:
                continue
            if (
                message.get("epoch") != hello["epoch"]
                or message.get("seq") != sequence + 1
            ):
                raise ValueError("Agent needs a fresh subscription baseline")
            sequence = message["seq"]
            if message["event"] in (
                "device_added",
                "device_removed",
                "capabilities_changed",
            ):
                # Negotiate capabilities again on the next connection. A
                # baseline/reconnection never becomes an activation event.
                return
            policy.handle(message, devices, target)


def main():
    parser = argparse.ArgumentParser(
        description="Optional MiniFuse desktop activation agent"
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args()
    runtime = socket_path().parent.parent
    lock = os.open(
        runtime / "minifuse-desktop-agent.lock",
        os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW,
        0o600,
    )
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock)
        return 0
    config = Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")
    identity = Preferences(config / "minifuse/agent.json")
    policy = ActivationPolicy()
    try:
        while True:
            if Preferences().data.get("activation_target", "disabled") != "disabled":
                try:
                    session(policy, identity)
                except (OSError, ValueError) as error:
                    print(f"mf-agent: {error}", file=sys.stderr)
            time.sleep(2)
    except KeyboardInterrupt:
        return 0
    finally:
        os.close(lock)


if __name__ == "__main__":
    raise SystemExit(main())
