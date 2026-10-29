"""Event-driven local socket client. Mutations are never replayed on reconnect."""

import time
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtNetwork import QLocalSocket
from .wire import MAX_FRAME, decode, encode, socket_path


class Client(QObject):
    ready = Signal(dict)
    event = Signal(dict)
    unavailable = Signal(str)

    def __init__(self, preferences, parent=None):
        super().__init__(parent)
        self.preferences = preferences
        self.socket = QLocalSocket(self)
        self.socket.setReadBufferSize(MAX_FRAME)
        self.socket.connected.connect(self._connected)
        self.socket.readyRead.connect(self._read)
        self.socket.disconnected.connect(self._disconnected)
        self.socket.errorOccurred.connect(self._socket_error)
        self.pending = {}
        self.buffer = b""
        self.frame_start = None
        self.epoch = None
        self.sequence = None
        self.counter = 0
        self.stopping = False
        self.reconnect = QTimer(self)
        self.reconnect.setSingleShot(True)
        self.reconnect.timeout.connect(self.connect_service)
        self.timer = QTimer(self)
        self.timer.setInterval(200)
        self.timer.timeout.connect(self._deadlines)
        self.timer.start()

    def connect_service(self):
        if self.stopping or self.socket.state() != QLocalSocket.UnconnectedState:
            return
        try:
            self.socket.connectToServer(str(socket_path()))
        except (OSError, ValueError) as error:
            self.unavailable.emit(str(error))
            self.reconnect.start(1500)

    def close(self):
        self.stopping = True
        self.reconnect.stop()
        self.timer.stop()
        self.socket.abort()

    def request(self, method, params, callback):
        if (
            len(self.pending) >= 32
            or self.socket.state() != QLocalSocket.ConnectedState
        ):
            callback(
                None,
                {
                    "code": "device_unavailable",
                    "message": "Service is unavailable or busy",
                },
            )
            return
        self.counter += 1
        identifier = str(self.counter)
        try:
            frame = encode(identifier, method, params)
        except (ValueError, TypeError) as error:
            callback(None, {"code": "invalid_request", "message": str(error)})
            return
        self.pending[identifier] = (method, callback, time.monotonic() + 10)
        if self.socket.write(frame) != len(frame):
            self.socket.abort()

    def _socket_error(self, _):
        self.unavailable.emit(self.socket.errorString())
        if not self.stopping:
            self.reconnect.start(1500)

    def _connected(self):
        params = {"client": "minifuse-control", "supported_api": [1]}
        if token := self.preferences.data.get("client_token"):
            params["client_token"] = token
        self.request("hello", params, self._hello)

    def _hello(self, result, error):
        if error:
            self.unavailable.emit(error.get("message", "Negotiation failed"))
            self.socket.abort()
            return
        if (
            result.get("selected_api") != 1
            or not isinstance(result.get("epoch"), str)
            or not isinstance(result.get("client_token"), str)
        ):
            self._protocol_error("Incompatible service negotiation")
            return
        self.epoch = result["epoch"]
        self.preferences.data["client_token"] = result["client_token"]
        try:
            self.preferences.save()
        except OSError as error:
            self._protocol_error(f"Cannot retain operation identity: {error}")
            return
        self.ready.emit(result)

    def _read(self):
        self.buffer += bytes(self.socket.readAll())
        try:
            while b"\n" in self.buffer:
                frame, self.buffer = self.buffer.split(b"\n", 1)
                self.frame_start = None
                message = decode(frame)
                if "event" in message:
                    if (
                        message["epoch"] != self.epoch
                        or self.sequence is None
                        or message["seq"] != self.sequence + 1
                    ):
                        raise ValueError(
                            "Subscription sequence changed; obtain a fresh baseline"
                        )
                    self.sequence = message["seq"]
                    self.event.emit(message)
                else:
                    pending = self.pending.pop(message["id"], None)
                    if pending is None:
                        raise ValueError("Response has no outstanding request")
                    pending[1](message.get("result"), message.get("error"))
            if len(self.buffer) + 1 > MAX_FRAME:
                raise ValueError("Service frame exceeds its limit")
            if self.buffer and self.frame_start is None:
                self.frame_start = time.monotonic()
        except (ValueError, TypeError, KeyError) as error:
            self._protocol_error(str(error))

    def _deadlines(self):
        now = time.monotonic()
        if self.frame_start is not None and now - self.frame_start > 2:
            self._protocol_error("Service frame deadline expired")
        for identifier, (method, callback, deadline) in list(self.pending.items()):
            if now >= deadline:
                self.pending.pop(identifier, None)
                callback(
                    None,
                    {
                        "code": "outcome_unknown"
                        if method
                        in (
                            "apply_plan",
                            "begin_control",
                            "update_control",
                            "cancel_control",
                        )
                        else "device_unavailable",
                        "message": "Service request timed out; refresh or query its operation",
                    },
                )

    def _protocol_error(self, message):
        self.unavailable.emit(message)
        self.socket.abort()

    def _disconnected(self):
        self.epoch = self.sequence = None
        self.buffer = b""
        self.frame_start = None
        pending, self.pending = self.pending, {}
        for method, callback, _ in pending.values():
            callback(
                None,
                {
                    "code": "outcome_unknown"
                    if method
                    in (
                        "apply_plan",
                        "begin_control",
                        "update_control",
                        "cancel_control",
                    )
                    else "device_unavailable",
                    "message": "Service disconnected; no request will be replayed",
                },
            )
        self.unavailable.emit("Service disconnected")
        if not self.stopping:
            self.reconnect.start(1500)
