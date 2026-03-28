"""
Petra Clipboard – Auto-update module.

Provides version checking against GitHub Releases and downloading /
installing updates for the supported packaging formats (snap, flatpak,
appimage, deb).
"""

import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal


# ---------------------------------------------------------------------------
# APP_VERSION
# ---------------------------------------------------------------------------

def _read_version() -> str:
    """Read version from global-version.txt at the project root."""
    try:
        version_file = Path(__file__).parent.parent / "global-version.txt"
        if version_file.exists():
            return version_file.read_text().strip()
    except Exception:
        pass
    return "0.0.1"


APP_VERSION: str = _read_version()

GITHUB_API_URL = (
    "https://api.github.com/repos/gessendarien/petra-clipboard/releases/latest"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def detect_install_type() -> str:
    """Return 'snap' | 'flatpak' | 'appimage' | 'deb'."""
    if os.environ.get("SNAP") or os.environ.get("SNAP_NAME"):
        return "snap"
    if os.environ.get("FLATPAK_ID") or Path("/.flatpak-info").exists():
        return "flatpak"
    if os.environ.get("APPIMAGE") or ".AppImage" in (sys.executable or ""):
        return "appimage"
    return "deb"


def _github_release_data() -> dict | None:
    """Fetch the latest release JSON from GitHub. Returns *None* on error."""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"Accept": "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return None


def fetch_latest_version() -> str | None:
    """Return the latest release tag (without leading 'v'), or *None*."""
    data = _github_release_data()
    if data and "tag_name" in data:
        tag = data["tag_name"]
        return tag.lstrip("v")
    return None


def fetch_release_asset_url(version: str, extension: str) -> str | None:
    """Return the browser_download_url of the asset ending in *extension*."""
    data = _github_release_data()
    if not data:
        return None
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(extension):
            return asset.get("browser_download_url")
    return None


def _fetch_release_asset_sha256(extension: str) -> str | None:
    """Return the SHA-256 digest published alongside the asset.

    Convention: a companion file ``<asset>.sha256`` contains the hex digest.
    If no such file exists we return *None* (skip verification).
    """
    data = _github_release_data()
    if not data:
        return None
    sha_ext = extension + ".sha256"
    for asset in data.get("assets", []):
        name = asset.get("name", "")
        if name.endswith(sha_ext):
            url = asset.get("browser_download_url")
            if url:
                try:
                    with urllib.request.urlopen(url, timeout=10) as resp:
                        return resp.read().decode().strip().split()[0]
                except Exception:
                    return None
    return None


def is_newer(remote: str, local: str) -> bool:
    """Compare two version strings segment-by-segment."""
    try:
        r = tuple(int(x) for x in remote.split("."))
        l = tuple(int(x) for x in local.split("."))
        return r > l
    except (ValueError, AttributeError):
        return False


# ---------------------------------------------------------------------------
# Download helper with progress
# ---------------------------------------------------------------------------

def _download_with_progress(url: str, dest: str, progress_cb=None) -> bool:
    """Download *url* to *dest*, calling *progress_cb(int 0-100)*.

    Returns True on success.
    """
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 8192
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total > 0:
                        progress_cb(int(downloaded * 100 / total))
            if progress_cb:
                progress_cb(100)
        return True
    except Exception:
        return False


def _verify_sha256(filepath: str, expected: str) -> bool:
    """Return True if the SHA-256 of *filepath* matches *expected*."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest().lower() == expected.lower()


# ---------------------------------------------------------------------------
# QThread workers
# ---------------------------------------------------------------------------

class UpdateChecker(QThread):
    """Background thread that checks for a newer release on GitHub."""

    update_available = pyqtSignal(str)
    no_update = pyqtSignal()

    def run(self):
        install_type = detect_install_type()

        latest = fetch_latest_version()
        if latest and is_newer(latest, APP_VERSION):
            self.update_available.emit(latest)
        else:
            self.no_update.emit()


class UpdateDownloader(QThread):
    """Download and install an update in the background."""

    progress = pyqtSignal(int)       # 0-100
    finished = pyqtSignal(bool, str)  # (success, message)

    def __init__(self, version: str, install_type: str, parent=None):
        super().__init__(parent)
        self.version = version
        self.install_type = install_type

    def run(self):
        try:
            if self.install_type == "flatpak":
                self._update_flatpak()
            elif self.install_type == "appimage":
                self._update_appimage()
            elif self.install_type == "deb":
                self._update_deb()
            else:
                self.finished.emit(False, "Tipo de instalación no soportado")
        except Exception as e:
            self.finished.emit(False, str(e))

    # -- flatpak -----------------------------------------------------------
    def _update_flatpak(self):
        self.progress.emit(10)
        try:
            result = subprocess.run(
                ["flatpak", "update", "-y", "io.github.gessendarien.petra"],
                capture_output=True,
                text=True,
                timeout=300,
            )
            self.progress.emit(100)
            if result.returncode == 0:
                self.finished.emit(True, "Actualización completada")
            else:
                self.finished.emit(False, result.stderr or "Error al actualizar flatpak")
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Tiempo de espera agotado")

    # -- appimage ----------------------------------------------------------
    def _update_appimage(self):
        url = fetch_release_asset_url(self.version, ".AppImage")
        if not url:
            self.finished.emit(False, "No se encontró el asset .AppImage")
            return

        tmp_path = "/tmp/petra-update.AppImage"
        ok = _download_with_progress(url, tmp_path, self.progress.emit)
        if not ok:
            self.finished.emit(False, "Error al descargar el archivo")
            return

        # SHA-256 verification
        expected_sha = _fetch_release_asset_sha256(".AppImage")
        if expected_sha:
            if not _verify_sha256(tmp_path, expected_sha):
                self.finished.emit(False, "Verificación SHA256 fallida")
                return

        dest = os.environ.get("APPIMAGE", sys.executable)
        try:
            # Preserve the user's chosen filename
            dest_path = Path(dest)
            shutil.move(tmp_path, str(dest_path))
            os.chmod(str(dest_path), stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)  # 755
            self.finished.emit(True, "")
        except Exception as e:
            self.finished.emit(False, f"Error al reemplazar AppImage: {e}")

    # -- deb ---------------------------------------------------------------
    def _update_deb(self):
        url = fetch_release_asset_url(self.version, ".deb")
        if not url:
            self.finished.emit(False, "No se encontró el asset .deb")
            return

        tmp_path = "/tmp/petra-update.deb"
        ok = _download_with_progress(url, tmp_path, self.progress.emit)
        if not ok:
            self.finished.emit(False, "Error al descargar el archivo")
            return

        # SHA-256 verification
        expected_sha = _fetch_release_asset_sha256(".deb")
        if expected_sha:
            if not _verify_sha256(tmp_path, expected_sha):
                self.finished.emit(False, "Verificación SHA256 fallida")
                return

        try:
            result = subprocess.run(
                ["pkexec", "dpkg", "-i", tmp_path],
                capture_output=True,
                text=True,
                timeout=120,
            )
            self.progress.emit(100)
            if result.returncode == 0:
                self.finished.emit(True, "")
            elif result.returncode in (126, 127):
                # User cancelled pkexec authentication
                self.finished.emit(False, "cancelled")
            else:
                self.finished.emit(False, result.stderr or "Error al instalar .deb")
        except subprocess.TimeoutExpired:
            self.finished.emit(False, "Tiempo de espera agotado")

