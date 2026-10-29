#!/usr/bin/env python3
"""Install the built wheel without Qt, inspect resources and remove it cleanly."""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile
import venv
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wheel", type=Path)
    args = parser.parse_args()
    wheel = args.wheel.resolve()
    with zipfile.ZipFile(wheel) as archive:
        names = archive.namelist()
        for suffix in (
            "qml/Main.qml",
            "qml/InputControls.qml",
            "qml/SignalMeter.qml",
            "assets/minifuse-control.svg",
        ):
            assert "minifuse_control/" + suffix in names
        metadata = archive.read(
            next(n for n in names if n.endswith(".dist-info/METADATA"))
        ).decode()
        assert 'extra == "gui"' in metadata and "PySide6==6.11.2" in metadata
    with tempfile.TemporaryDirectory(prefix="minifuse-wheel-") as folder:
        root = Path(folder)
        environment = root / "environment with spaces"
        venv.EnvBuilder(with_pip=True).create(environment)
        python = environment / "bin/python"
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        subprocess.run(
            [
                str(python),
                "-m",
                "pip",
                "install",
                "--no-index",
                "--no-deps",
                str(wheel),
            ],
            env=env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                "import importlib.util; assert importlib.util.find_spec('PySide6') is None; "
                "from minifuse_control import desktop; "
                "from importlib.resources import files; "
                "assert (files('minifuse_control') / 'qml/SignalMeter.qml').is_file()",
            ],
            env=env,
            check=True,
        )
        for command in ("minifuse-control", "minifuse-desktop-agent"):
            subprocess.run(
                [str(environment / "bin" / command), "--help"],
                env=env,
                check=True,
                capture_output=True,
            )
        subprocess.run(
            [str(python), "-m", "pip", "uninstall", "-y", "minifuse-control"],
            env=env,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                str(python),
                "-I",
                "-c",
                "import importlib.util; assert importlib.util.find_spec('minifuse_control') is None",
            ],
            env=env,
            check=True,
        )
        assert not (environment / "bin/minifuse-control").exists()
        assert not (environment / "bin/minifuse-desktop-agent").exists()
    subprocess.run(
        [
            "desktop-file-validate",
            str(ROOT / "packaging/io.github.srdiogo.MiniFuseControl.desktop"),
        ],
        check=True,
    )
    print(
        "Wheel resources, Qt-free agent, installed entrypoints and removal passed; no startup was enabled."
    )


if __name__ == "__main__":
    main()
