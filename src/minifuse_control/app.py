"""Standalone Qt Quick application with one activation endpoint per user."""

import argparse
import errno
import fcntl
import os
from pathlib import Path
import socket
import stat
import sys
from . import __version__


def main():
    parser = argparse.ArgumentParser(
        description="MiniFuse mixer, routing and host presets"
    )
    parser.add_argument("--version", action="version", version=__version__)
    parser.parse_args()
    try:
        from PySide6.QtCore import QTimer, QUrl, QProcess
        from PySide6.QtGui import QGuiApplication, QIcon
        from PySide6.QtNetwork import QLocalServer
        from PySide6.QtQml import QQmlApplicationEngine
    except ImportError:
        parser.exit(1, "Install the GUI dependencies: pip install '.[gui]'\n")
    from .client import Client
    from .controller import Controller
    from .preferences import Preferences
    from .wire import socket_path

    runtime = socket_path().parent.parent / "minifuse-control"
    runtime.mkdir(mode=0o700, exist_ok=True)
    metadata = runtime.lstat()
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_uid != os.geteuid()
        or metadata.st_mode & 0o077
    ):
        parser.exit(1, "Invalid application runtime directory\n")
    lock = os.open(
        runtime / "instance.lock", os.O_CREAT | os.O_WRONLY | os.O_NOFOLLOW, 0o600
    )
    endpoint = runtime / "activate.sock"
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        try:
            with socket.socket(socket.AF_UNIX) as peer:
                peer.settimeout(1)
                peer.connect(str(endpoint))
                peer.sendall(b"activate\n")
            return 0
        except OSError:
            parser.exit(
                1,
                "The existing application could not be activated; no second window was opened.\n",
            )
        finally:
            os.close(lock)
    if endpoint.exists():
        metadata = endpoint.lstat()
        if not stat.S_ISSOCK(metadata.st_mode) or metadata.st_uid != os.geteuid():
            parser.exit(1, "Refusing to replace an unowned activation endpoint\n")
        with socket.socket(socket.AF_UNIX) as peer:
            try:
                peer.connect(str(endpoint))
            except OSError as error:
                if error.errno != errno.ECONNREFUSED:
                    raise
                endpoint.unlink()
            else:
                parser.exit(1, "A live activation endpoint already exists\n")

    app = QGuiApplication(sys.argv)
    app.setApplicationName("MiniFuse Control")
    app.setDesktopFileName("io.github.srdiogo.MiniFuseControl")
    package = Path(__file__).parent
    app.setWindowIcon(QIcon(str(package / "assets/minifuse-control.svg")))
    preferences = Preferences()
    client = Client(preferences)
    controller = Controller(client, preferences)
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({"controller": controller})
    engine.load(QUrl.fromLocalFile(str(package / "qml/Main.qml")))
    if not engine.rootObjects():
        return 1
    window = engine.rootObjects()[0]
    server = QLocalServer()
    server.setSocketOptions(QLocalServer.UserAccessOption)
    if not server.listen(str(endpoint)):
        parser.exit(1, server.errorString() + "\n")
    peers = []

    def activate():
        window.show()
        window.raise_()
        window.requestActivate()

        def fallback():
            if not window.isActive():
                QProcess.startDetached(
                    "notify-send",
                    [
                        "MiniFuse Control",
                        "Open the existing application from your task switcher.",
                    ],
                )

        QTimer.singleShot(1000, fallback)

    def connected():
        while server.hasPendingConnections():
            peer = server.nextPendingConnection()
            if len(peers) >= 16:
                peer.abort()
                peer.deleteLater()
                continue
            peer.setReadBufferSize(32)
            peers.append(peer)
            received = bytearray()

            def read(peer=peer, received=received):
                received.extend(bytes(peer.readAll()))
                if bytes(received) == b"activate\n":
                    activate()
                    peer.disconnectFromServer()
                elif len(received) >= 32 or b"\n" in received:
                    peer.abort()

            peer.readyRead.connect(read)
            peer.disconnected.connect(
                lambda peer=peer: (peers.remove(peer), peer.deleteLater())
            )
            QTimer.singleShot(1000, peer.disconnectFromServer)

    server.newConnection.connect(connected)
    app.aboutToQuit.connect(client.close)
    app.aboutToQuit.connect(server.close)
    QTimer.singleShot(0, client.connect_service)
    result = app.exec()
    os.close(lock)
    return result


if __name__ == "__main__":
    raise SystemExit(main())
