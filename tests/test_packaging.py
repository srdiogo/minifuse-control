"""Bind test packages to reviewed source instead of the older release recipe."""

import hashlib
import importlib.util
import io
from pathlib import Path
import subprocess
import tarfile
import tempfile
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "prepare_arch_package", PROJECT / "tools/prepare_arch_package.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
export = MODULE.export


class SourceKitTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.repo = self.base / "repo"
        self.repo.mkdir()
        self.git("init", "--quiet")
        self.git("config", "user.name", "Package Test")
        self.git("config", "user.email", "package-test@example.invalid")
        (self.repo / "pyproject.toml").write_text(
            '[project]\nname="minifuse-control"\nversion="0.1.0"\n'
        )
        (self.repo / "packaging/arch").mkdir(parents=True)
        (self.repo / "packaging/arch/PKGBUILD").write_bytes(
            (PROJECT / "packaging/arch/PKGBUILD").read_bytes()
        )
        (self.repo / "payload").write_text("reviewed source")
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "Add package fixture")

    def git(self, *args):
        return subprocess.check_output(["git", "-C", str(self.repo), *args])

    def test_export_is_reproducible_and_binds_recipe_to_committed_source(self):
        first = self.base / "first"
        second = self.base / "second"
        profile = export(first, root=self.repo)
        self.assertEqual(profile, export(second, root=self.repo))
        for path in first.iterdir():
            self.assertEqual(path.read_bytes(), (second / path.name).read_bytes())
        for name, expected in profile["files"].items():
            self.assertEqual(
                hashlib.sha256((first / name).read_bytes()).hexdigest(), expected
            )
        archive = next(first.glob("*.tar.gz"))
        with tarfile.open(fileobj=io.BytesIO(archive.read_bytes())) as stream:
            content = stream.extractfile(
                f"minifuse-control-{profile['commit']}/payload"
            ).read()
        self.assertEqual(content, b"reviewed source")
        recipe = (first / "PKGBUILD").read_text()
        self.assertIn(profile["commit"], recipe)
        self.assertNotIn("github.com/srdiogo/minifuse-control/archive/", recipe)
        self.assertIn('source=("minifuse-control-$_commit.tar.gz")', recipe)
        subprocess.run(["bash", "-n", str(first / "PKGBUILD")], check=True)

    def test_dirty_or_untracked_content_cannot_be_silently_omitted(self):
        (self.repo / "private-file").write_text("not reviewed")
        with self.assertRaisesRegex(ValueError, "Commit"):
            export(self.base / "out", root=self.repo)
        (self.repo / "private-file").unlink()
        (self.repo / "payload").write_text("uncommitted change")
        with self.assertRaisesRegex(ValueError, "Commit"):
            export(self.base / "out", root=self.repo)

    def test_existing_output_is_not_overwritten(self):
        destination = self.base / "out"
        destination.mkdir()
        (destination / "keep").write_text("keep")
        with self.assertRaisesRegex(ValueError, "empty"):
            export(destination, root=self.repo)
        self.assertEqual((destination / "keep").read_text(), "keep")
