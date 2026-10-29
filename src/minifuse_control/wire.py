"""Bounded API envelopes shared by the Qt client and the non-Qt agent."""

import json
import math
import os
from pathlib import Path

MAX_FRAME = 256 * 1024


def socket_path() -> Path:
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", ""))
    if not runtime.is_absolute():
        raise ValueError("XDG_RUNTIME_DIR must name the user runtime directory")
    stat = runtime.stat()
    if stat.st_uid != os.geteuid() or stat.st_mode & 0o077:
        raise ValueError("Invalid runtime directory ownership or permissions")
    return runtime / "mf-service/control.sock"


def unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def decode(frame: bytes) -> dict:
    if len(frame) + 1 > MAX_FRAME:
        raise ValueError("Service frame exceeds its limit")

    def invalid(value):
        raise ValueError(f"Nonfinite number: {value}")

    def finite(value):
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("Nonfinite number")
        return number

    message = json.loads(
        frame.decode("utf-8"),
        object_pairs_hook=unique,
        parse_constant=invalid,
        parse_float=finite,
    )
    if not isinstance(message, dict):
        raise ValueError("Service envelope must be an object")
    if "event" in message:
        if (
            not isinstance(message["event"], str)
            or not isinstance(message.get("epoch"), str)
            or type(message.get("seq")) is not int
            or not isinstance(message.get("data"), dict)
        ):
            raise ValueError("Invalid event envelope")
    elif (
        type(message.get("api")) is not int
        or message.get("api") != 1
        or not isinstance(message.get("id"), str)
        or ("result" in message) == ("error" in message)
    ):
        raise ValueError("Invalid response envelope")
    if "event" not in message and not isinstance(
        message.get("result", message.get("error")), dict
    ):
        raise ValueError("Response payload must be an object")
    return message


def encode(identifier: str, method: str, params: dict) -> bytes:
    frame = (
        json.dumps(
            {"api": 1, "id": identifier, "method": method, "params": params},
            allow_nan=False,
            separators=(",", ":"),
        ).encode()
        + b"\n"
    )
    if len(frame) > MAX_FRAME:
        raise ValueError("Request exceeds the service frame limit")
    return frame
