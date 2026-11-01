# Application development

MiniFuse Control is a Qt Quick frontend for MiniFuse Backend. Device protocol,
verification and coordination belong in the backend workspace. The application
has no Omarchy dependency; its optional activation agent is packaged separately.

## Run from source

Requires Linux and Python 3.12–3.14. The GUI extra pins PySide6 6.11.2. From a
checkout of this repository:

```sh
python3 -m venv .venv
.venv/bin/pip install '.[gui,dev]' build
.venv/bin/minifuse-control
```

Normal control also needs an installed compatible backend and driver. The
application does not install those components on launch. See
[installation](INSTALL.md) and `contract.lock.json` for the tested service
producer and canonical fixture digest.

## Checks

```sh
.venv/bin/ruff check src tests tools --select E4,E7,E9,F
.venv/bin/ruff format --check src tests tools
QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME= QT_QUICK_CONTROLS_STYLE=Basic QT_QUICK_BACKEND=software .venv/bin/python -m unittest discover -s tests -v
QT_QPA_PLATFORM=offscreen QT_QPA_PLATFORMTHEME= QT_QUICK_CONTROLS_STYLE=Fusion QT_QUICK_BACKEND=software .venv/bin/python -m unittest discover -s tests -v
.venv/bin/pyside6-qmllint src/minifuse_control/qml/*.qml
.venv/bin/python -m build
.venv/bin/python tools/check_distribution.py dist/minifuse_control-0.1.0-py3-none-any.whl
```

Tests use deterministic local socket peers and canonical service fixtures;
there is no simulated-device mode in the normal application. Distribution
checks install and remove the wheel in an isolated environment, including the
standard-library agent without Qt. These checks do not enable desktop startup
or establish clean-machine hardware acceptance.

The agent default is disabled and physical-logo events remain unavailable.
Read [application architecture](APPLICATION.md), [desktop policy](DESKTOP.md),
[implementation and validation](IMPLEMENTATION.md) and [contributing](../CONTRIBUTING.md).
Release packaging follows the backend's
[distribution roadmap](https://github.com/srdiogo/minifuse-backend/blob/main/docs/DISTRIBUTION.md)
and [release guide](https://github.com/srdiogo/minifuse-backend/blob/main/docs/RELEASING.md).
