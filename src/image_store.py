"""Two-tier image storage for Petra Clipboard.

* Volatile session cache: ``$XDG_CACHE_HOME/petra/session_images/<id>/<name>``
  Cleared on startup and exit, and pruned when clips are deleted or exceed
  ``max_images``. Keeps full-resolution images off RAM.
* Persistent pinned storage: ``$XDG_CONFIG_HOME/petra/pinned_images/<id>/<name>``
  Survives restarts and stays backwards-compatible with legacy flat files in
  ``pinned_images/``.

Because every image lives as a real file inside its own per-clip subfolder,
renaming a clip renames the actual file on disk without collisions. On native
installs that path is placed on the clipboard as ``text/uri-list`` +
``x-special/gnome-copied-files``; inside Flatpak the file is exported through
``org.freedesktop.portal.Documents`` so any host or sandboxed app receives the
file with its real filename.
"""

from pathlib import Path
import hashlib
import os
import re
import shutil

from PyQt6.QtCore import QMimeData, QUrl
from PyQt6.QtGui import QImage


VALID_IMAGE_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')
_QT_WRITABLE_EXTS = {'.png', '.jpg', '.jpeg', '.bmp', '.webp'}


def _is_flatpak() -> bool:
    return Path('/.flatpak-info').exists() or bool(os.environ.get('FLATPAK_ID'))


def sanitize_filename(name: str, default_ext: str = '.png') -> str:
    """Return a safe single-segment image filename with a valid extension."""
    raw = str(name or '').strip()
    # Replace path separators and control characters
    raw = raw.replace('/', '_').replace('\\', '_').replace('\x00', '')
    raw = re.sub(r'[\r\n\t]+', ' ', raw).strip(' .')
    if not raw or raw in ('.', '..'):
        raw = 'Imagen'

    lower = raw.lower()
    if not any(lower.endswith(ext) for ext in VALID_IMAGE_EXTS):
        ext = default_ext if default_ext.startswith('.') else f'.{default_ext}'
        if ext.lower() not in VALID_IMAGE_EXTS:
            ext = '.png'
        raw = f"{raw}{ext}"
    return raw


class ImageStore:
    """Manages volatile (session) and persistent (pinned) image files."""

    def __init__(self, config_dir: Path | None = None, cache_dir: Path | None = None,
                 standalone: bool | None = None):
        if config_dir is None:
            config_base = Path(os.environ.get('XDG_CONFIG_HOME', Path.home() / '.config'))
            config_dir = config_base / 'petra'
        if cache_dir is None:
            cache_base = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache'))
            cache_dir = cache_base / 'petra'
        if standalone is None:
            standalone = os.environ.get('PETRA_STANDALONE') == '1'

        self.pinned_dir = Path(config_dir) / 'pinned_images'
        session_name = 'session_images_standalone' if standalone else 'session_images'
        self.session_dir = Path(cache_dir) / session_name

        self.pinned_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.paths: dict[str, Path] = {}
        self._doc_ids: dict[str, str] = {}
        self._exported_paths: set[str] = set()
        self._doc_portal_mount: str | None = None
        self.is_flatpak = _is_flatpak()

        # Always start with a clean volatile session cache
        self.clear_session()

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _dir_key(clip_id: str) -> str:
        return hashlib.sha1(str(clip_id).encode('utf-8')).hexdigest()[:16]

    def _is_in_dir(self, path: Path, base: Path) -> bool:
        try:
            path.resolve().relative_to(base.resolve())
            return True
        except Exception:
            return False

    @staticmethod
    def _save_qimage(qimage: QImage, target: Path) -> Path | None:
        """Save a QImage to target. Falls back to PNG if format isn't writable."""
        target.parent.mkdir(parents=True, exist_ok=True)
        ext = target.suffix.lower()
        if ext in _QT_WRITABLE_EXTS:
            if qimage.save(str(target)):
                return target
        # GIF or save failure: write PNG bytes while keeping a .png file
        png_target = target.with_suffix('.png')
        if qimage.save(str(png_target), 'PNG'):
            return png_target
        return None

    # ── Lifecycle ──────────────────────────────────────────────────

    def save_session_image(self, clip_id: str, qimage: QImage,
                           filename: str = 'Imagen.png') -> Path | None:
        """Persist a non-pinned image in the volatile session cache."""
        clean_name = sanitize_filename(filename)
        slot_dir = self.session_dir / self._dir_key(clip_id)
        if slot_dir.exists():
            shutil.rmtree(slot_dir, ignore_errors=True)
        saved = self._save_qimage(qimage, slot_dir / clean_name)
        if saved:
            self.paths[clip_id] = saved
        return saved

    def register_existing(self, clip_id: str, file_path: Path) -> Path | None:
        """Register an existing pinned image file (new or legacy flat layout)."""
        p = Path(file_path)
        if p.exists():
            self.paths[clip_id] = p
            return p
        return None

    def has_image(self, clip_id: str) -> bool:
        p = self.paths.get(clip_id)
        return p is not None and p.exists()

    def get_path(self, clip_id: str) -> Path | None:
        p = self.paths.get(clip_id)
        if p is not None and p.exists():
            return p
        return None

    def get_relative_pinned_path(self, clip_id: str) -> str | None:
        """Return path relative to pinned_dir for storing in pinned.json."""
        p = self.get_path(clip_id)
        if p is None:
            return None
        try:
            return str(p.resolve().relative_to(self.pinned_dir.resolve()))
        except Exception:
            return None

    def load_image(self, clip_id: str) -> QImage | None:
        """Load full-resolution QImage from disk on demand."""
        p = self.get_path(clip_id)
        if p is None:
            return None
        img = QImage(str(p))
        return None if img.isNull() else img

    def rename(self, clip_id: str, new_name: str) -> str | None:
        """Rename the physical image file on disk and return the final filename."""
        old_path = self.get_path(clip_id)
        if old_path is None:
            return None

        default_ext = old_path.suffix or '.png'
        clean_name = sanitize_filename(new_name, default_ext=default_ext)

        # Determine target subfolder: migrate legacy flat pinned files into a
        # per-clip subfolder so renaming never collides with other clips.
        if self._is_in_dir(old_path, self.pinned_dir):
            target_dir = self.pinned_dir / self._dir_key(clip_id)
        else:
            target_dir = self.session_dir / self._dir_key(clip_id)

        target_dir.mkdir(parents=True, exist_ok=True)
        new_path = target_dir / clean_name

        if old_path.resolve() == new_path.resolve():
            return new_path.name

        try:
            # If extension changed (e.g. .png -> .jpg), re-encode if needed;
            # otherwise an atomic rename/move is instantaneous.
            if old_path.suffix.lower() != new_path.suffix.lower() and new_path.suffix.lower() in _QT_WRITABLE_EXTS:
                img = QImage(str(old_path))
                if not img.isNull() and img.save(str(new_path)):
                    old_path.unlink(missing_ok=True)
                else:
                    shutil.move(str(old_path), str(new_path))
            else:
                shutil.move(str(old_path), str(new_path))

            self.paths[clip_id] = new_path
            # Drop stale document portal entry so next copy exports the new filename
            self._delete_doc_portal_entry(clip_id)
            return new_path.name
        except Exception as e:
            print(f"Error renaming image file {old_path} -> {new_path}: {e}")
            return None

    def set_pinned(self, clip_id: str, pinned: bool, display_name: str | None = None) -> Path | None:
        """Move an image between volatile session cache and persistent pinned dir."""
        old_path = self.get_path(clip_id)
        if old_path is None:
            return None

        dest_base = self.pinned_dir if pinned else self.session_dir
        dest_slot = dest_base / self._dir_key(clip_id)

        filename = sanitize_filename(display_name, default_ext=old_path.suffix or '.png') if display_name else old_path.name
        new_path = dest_slot / filename

        if old_path.resolve() == new_path.resolve():
            return old_path

        try:
            dest_slot.mkdir(parents=True, exist_ok=True)
            shutil.move(str(old_path), str(new_path))
            # Remove now-empty source subfolder (never remove pinned_dir / session_dir itself)
            old_parent = old_path.parent
            if old_parent not in (self.pinned_dir, self.session_dir):
                try:
                    if not any(old_parent.iterdir()):
                        old_parent.rmdir()
                except Exception:
                    pass
            self.paths[clip_id] = new_path
            self._delete_doc_portal_entry(clip_id)
            return new_path
        except Exception as e:
            print(f"Error moving image between session/pinned: {e}")
            return old_path

    def remove(self, clip_id: str):
        """Delete the image file (and its per-clip subfolder) from disk."""
        self._delete_doc_portal_entry(clip_id)
        p = self.paths.pop(clip_id, None)
        if p is None:
            return
        try:
            if p.exists():
                p.unlink()
            parent = p.parent
            if parent not in (self.pinned_dir, self.session_dir) and (
                self._is_in_dir(parent, self.session_dir) or self._is_in_dir(parent, self.pinned_dir)
            ):
                shutil.rmtree(parent, ignore_errors=True)
        except Exception as e:
            print(f"Error removing image {p}: {e}")

    def prune(self, valid_clip_ids: set[str]):
        """Remove any tracked image whose clip_id is no longer in the history."""
        stale = [cid for cid in list(self.paths.keys()) if cid not in valid_clip_ids]
        for cid in stale:
            self.remove(cid)

        # Also remove any stray folders in session_dir
        valid_dir_keys = {self._dir_key(cid) for cid in valid_clip_ids}
        try:
            for entry in self.session_dir.iterdir():
                if entry.name not in valid_dir_keys:
                    if entry.is_dir():
                        shutil.rmtree(entry, ignore_errors=True)
                    else:
                        entry.unlink(missing_ok=True)
        except Exception:
            pass

    def cleanup_orphan_pinned(self, keep_rel_paths: set[str]):
        """Remove pinned files/folders no longer referenced by pinned.json."""
        resolved_keep = set()
        for rel in keep_rel_paths:
            try:
                resolved_keep.add((self.pinned_dir / rel).resolve())
            except Exception:
                pass
        try:
            for entry in self.pinned_dir.iterdir():
                if entry.is_dir():
                    files = [f for f in entry.rglob('*') if f.is_file()]
                    if not any(f.resolve() in resolved_keep for f in files):
                        shutil.rmtree(entry, ignore_errors=True)
                elif entry.is_file():
                    if entry.resolve() not in resolved_keep:
                        entry.unlink(missing_ok=True)
        except Exception as e:
            print(f"Error cleaning orphan pinned images: {e}")

    def clear_session(self):
        """Wipe all volatile session images (called on startup and exit)."""
        for cid in list(self._doc_ids.keys()):
            self._delete_doc_portal_entry(cid)
        try:
            if self.session_dir.exists():
                for entry in self.session_dir.iterdir():
                    if entry.is_dir():
                        shutil.rmtree(entry, ignore_errors=True)
                    else:
                        entry.unlink(missing_ok=True)
            else:
                self.session_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Error clearing session image cache: {e}")

        # Drop session paths from registry while keeping pinned ones
        self.paths = {
            cid: p for cid, p in self.paths.items()
            if self._is_in_dir(p, self.pinned_dir) and p.exists()
        }

    def is_internal_path(self, local_path: str) -> bool:
        """True if local_path belongs to Petra's own storage or was exported by Petra."""
        if not local_path:
            return False
        if local_path in self._exported_paths:
            return True
        try:
            p = Path(local_path).resolve()
            if str(p) in self._exported_paths:
                return True
            if self._is_in_dir(p, self.session_dir) or self._is_in_dir(p, self.pinned_dir):
                return True
        except Exception:
            pass
        return False

    # ── Flatpak Document Portal export ─────────────────────────────

    def _get_doc_portal_mount(self) -> str | None:
        if self._doc_portal_mount:
            return self._doc_portal_mount
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                return None
            msg = QDBusMessage.createMethodCall(
                'org.freedesktop.portal.Documents',
                '/org/freedesktop/portal/documents',
                'org.freedesktop.portal.Documents',
                'GetMountPoint',
            )
            reply = bus.call(msg)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                raw = bytes(reply.arguments()[0]).rstrip(b'\x00').decode('utf-8')
                if raw:
                    self._doc_portal_mount = raw
                    return raw
        except Exception as e:
            print(f"Document portal GetMountPoint failed: {e}")
        return None

    def _export_via_document_portal(self, clip_id: str, local_path: Path) -> Path | None:
        """Export local_path via org.freedesktop.portal.Documents for Flatpak."""
        mount = self._get_doc_portal_mount()
        if not mount:
            return None
        fd = None
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusInterface, QDBusMessage, QDBusUnixFileDescriptor
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                return None
            iface = QDBusInterface(
                'org.freedesktop.portal.Documents',
                '/org/freedesktop/portal/documents',
                'org.freedesktop.portal.Documents',
                bus,
            )
            flags = getattr(os, 'O_PATH', os.O_RDONLY) | getattr(os, 'O_CLOEXEC', 0)
            fd = os.open(str(local_path), flags)
            dbus_fd = QDBusUnixFileDescriptor(fd)
            os.close(fd)
            fd = None

            reply = iface.call('Add', dbus_fd, True, False)
            if reply.type() == QDBusMessage.MessageType.ReplyMessage and reply.arguments():
                doc_id = str(reply.arguments()[0])
                self._doc_ids[clip_id] = doc_id
                return Path(mount) / doc_id / local_path.name
            if reply.errorMessage():
                print(f"Document portal Add error: {reply.errorMessage()}")
        except Exception as e:
            print(f"Document portal export failed: {e}")
        finally:
            if fd is not None:
                try:
                    os.close(fd)
                except Exception:
                    pass
        return None

    def _delete_doc_portal_entry(self, clip_id: str):
        doc_id = self._doc_ids.pop(clip_id, None)
        if not doc_id:
            return
        try:
            from PyQt6.QtDBus import QDBusConnection, QDBusMessage
            bus = QDBusConnection.sessionBus()
            if not bus.isConnected():
                return
            msg = QDBusMessage.createMethodCall(
                'org.freedesktop.portal.Documents',
                '/org/freedesktop/portal/documents',
                'org.freedesktop.portal.Documents',
                'Delete',
            )
            msg.setArguments([doc_id])
            bus.call(msg)
        except Exception:
            pass

    def export_for_clipboard(self, clip_id: str) -> Path | None:
        """Return a file path readable by other applications (portal on Flatpak)."""
        local_path = self.get_path(clip_id)
        if local_path is None:
            return None
        if self.is_flatpak:
            exported = self._export_via_document_portal(clip_id, local_path)
            if exported is not None:
                self._exported_paths.add(str(exported))
                self._exported_paths.add(str(local_path))
                return exported
            return None
        self._exported_paths.add(str(local_path))
        return local_path

    def build_mime_data(self, clip_id: str) -> QMimeData | None:
        """Build QMimeData carrying the real file URI (standard Linux file copy),
        with a safe fallback to raw QImage data if file export is unavailable."""
        mime = QMimeData()
        export_path = self.export_for_clipboard(clip_id)
        if export_path is not None:
            url = QUrl.fromLocalFile(str(export_path))
            mime.setUrls([url])
            # Standard format read by GTK/GNOME/Chromium/Electron apps on Linux
            mime.setData(
                'x-special/gnome-copied-files',
                f'copy\n{url.toString()}'.encode('utf-8'),
            )
            return mime

        # Fallback: raw image bytes
        img = self.load_image(clip_id)
        if img is not None:
            mime.setImageData(img)
            return mime
        return None
