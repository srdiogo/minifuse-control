"""One in-flight sample and one replaceable desired value per user gesture."""

import time
from PySide6.QtCore import QObject, QTimer, Signal


class LiveControl(QObject):
    admitted = Signal(str)
    completed = Signal(dict)
    failed = Signal(dict)

    def __init__(self, client, parameters, parent=None):
        super().__init__(parent)
        self.client, self.parameters = client, parameters
        self.identifier = None
        self.latest = None
        self.sequence = 0
        self.in_flight = False
        self.ending = False
        self.stopped = False
        self.cancelled = False
        self.last_sent = 0.0
        self.throttle = QTimer(self)
        self.throttle.setSingleShot(True)
        self.throttle.timeout.connect(self._pump)
        self.deadline = QTimer(self)
        self.deadline.setSingleShot(True)
        self.deadline.timeout.connect(self._timeout)

    def start(self):
        self.client.request("begin_control", self.parameters, self._begun)

    def move(self, value, finish):
        if self.stopped or self.ending:
            return
        self.latest = (value, bool(finish))
        self.ending = bool(finish)
        self._pump()

    def _begun(self, result, error):
        if self.stopped:
            return
        if error:
            self._fail(error)
            return
        self.identifier = result["operation_id"]
        self.admitted.emit(self.identifier)
        if result["status"] != "pending":
            self.settled(result)
        elif self.cancelled:
            self._cancel()
        else:
            self._pump()

    def _pump(self):
        if (
            self.stopped
            or self.cancelled
            or not self.identifier
            or self.in_flight
            or self.latest is None
        ):
            return
        remaining = 0.08 - (time.monotonic() - self.last_sent)
        if remaining > 0:
            self.throttle.start(max(1, int(remaining * 1000) + 1))
            return
        value, finish = self.latest
        self.latest = None
        self.sequence += 1
        self.in_flight = True
        self.last_sent = time.monotonic()
        self.deadline.start(10000)
        self.client.request(
            "update_control",
            {
                "operation_id": self.identifier,
                "sequence": self.sequence,
                "value": value,
                "finish": finish,
            },
            self._accepted,
        )

    def _accepted(self, _, error):
        if error and not self.stopped:
            self._fail(error)

    def settled(self, record):
        if self.stopped or record.get("operation_id") != self.identifier:
            return
        if record.get("status") != "pending":
            self.stop()
            self.completed.emit(record)
            return
        if record.get("sample_sequence") != self.sequence:
            self._fail(
                {
                    "code": "outcome_unknown",
                    "message": "Control confirmation sequence changed; review current settings",
                }
            )
            return
        self.deadline.stop()
        self.in_flight = False
        self._pump()

    def cancel(self):
        self.cancelled = True
        self.latest = None
        self.throttle.stop()
        if self.identifier and not self.stopped:
            self._cancel()

    def _cancel(self):
        self.deadline.start(10000)
        self.client.request(
            "cancel_control",
            {"operation_id": self.identifier},
            lambda result, error: self._fail(error) if error else self.settled(result),
        )

    def stop(self):
        self.stopped = True
        self.latest = None
        self.throttle.stop()
        self.deadline.stop()

    def _timeout(self):
        self._fail(
            {
                "code": "outcome_unknown",
                "message": "Control verification timed out; no movement will be replayed",
            }
        )

    def _fail(self, error):
        self.stop()
        self.failed.emit(error)
