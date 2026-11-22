import ctypes
import json
import os
import re
import subprocess
import threading
import uuid
from pathlib import Path

from PyQt6.QtCore import QObject, QSocketNotifier, QTimer, pyqtSignal


def _shortcut_to_xdg_trigger(shortcut_str):
    """Convert 'Super + v' / 'Alt + space' to XDG GlobalShortcuts preferred_trigger."""
    parts = [p.strip() for p in str(shortcut_str).split('+') if p.strip()]
    mapped = []
    for part in parts:
        low = part.lower()
        if low in ('super', 'mod4', 'meta', 'logo'):
            mapped.append('LOGO')
        elif low in ('ctrl', 'control'):
            mapped.append('CTRL')
        elif low == 'alt':
            mapped.append('ALT')
        elif low == 'shift':
            mapped.append('SHIFT')
        else:
            mapped.append(part.lower())
    return '+'.join(mapped)


class _PortalGlobalShortcuts(QObject):
    """Flatpak/Wayland global shortcuts via org.freedesktop.portal.GlobalShortcuts.

    Uses libglib/libgio directly so D-Bus a(sa{sv}) structs are marshalled with
    exact signatures without requiring extra Python packages inside the sandbox.
    """

    activated = pyqtSignal()

    SHORTCUT_ID = "toggle-petra"
    PORTAL_BUS = b"org.freedesktop.portal.Desktop"
    PORTAL_PATH = b"/org/freedesktop/portal/desktop"
    PORTAL_IFACE = b"org.freedesktop.portal.GlobalShortcuts"
    REQUEST_IFACE = b"org.freedesktop.portal.Request"
    SESSION_IFACE = b"org.freedesktop.portal.Session"

    def __init__(self, on_toggle=None):
        super().__init__()
        if on_toggle is not None:
            self.activated.connect(on_toggle)
        self._glib = None
        self._gio = None
        self._conn = None
        self._ctx = None
        self._loop = None
        self._thread = None
        self._session_handle = None
        self._sub_ids = []
        self._callbacks = []
        self._ready_event = threading.Event()
        self._list_event = threading.Event()
        self._already_bound = False
        self._load_libs()

    def _load_libs(self):
        try:
            glib = ctypes.CDLL("libglib-2.0.so.0")
            gio = ctypes.CDLL("libgio-2.0.so.0")
        except OSError:
            return

        glib.g_main_context_new.argtypes = []
        glib.g_main_context_new.restype = ctypes.c_void_p
        glib.g_main_context_push_thread_default.argtypes = [ctypes.c_void_p]
        glib.g_main_context_pop_thread_default.argtypes = [ctypes.c_void_p]
        glib.g_main_context_unref.argtypes = [ctypes.c_void_p]
        glib.g_main_loop_new.argtypes = [ctypes.c_void_p, ctypes.c_int]
        glib.g_main_loop_new.restype = ctypes.c_void_p
        glib.g_main_loop_run.argtypes = [ctypes.c_void_p]
        glib.g_main_loop_quit.argtypes = [ctypes.c_void_p]
        glib.g_main_loop_unref.argtypes = [ctypes.c_void_p]

        glib.g_variant_type_new.argtypes = [ctypes.c_char_p]
        glib.g_variant_type_new.restype = ctypes.c_void_p
        glib.g_variant_type_free.argtypes = [ctypes.c_void_p]
        glib.g_variant_parse.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p,
        ]
        glib.g_variant_parse.restype = ctypes.c_void_p
        glib.g_variant_print.argtypes = [ctypes.c_void_p, ctypes.c_int]
        glib.g_variant_print.restype = ctypes.c_void_p
        glib.g_variant_unref.argtypes = [ctypes.c_void_p]
        glib.g_free.argtypes = [ctypes.c_void_p]
        glib.g_error_free.argtypes = [ctypes.c_void_p]

        gio.g_bus_get_sync.argtypes = [ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p]
        gio.g_bus_get_sync.restype = ctypes.c_void_p
        gio.g_dbus_connection_get_unique_name.argtypes = [ctypes.c_void_p]
        gio.g_dbus_connection_get_unique_name.restype = ctypes.c_char_p
        gio.g_dbus_connection_call_sync.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
            ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_int,
            ctypes.c_int, ctypes.c_void_p, ctypes.c_void_p,
        ]
        gio.g_dbus_connection_call_sync.restype = ctypes.c_void_p
        gio.g_dbus_connection_signal_subscribe.argtypes = [
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p,
            ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_void_p,
            ctypes.c_void_p, ctypes.c_void_p,
        ]
        gio.g_dbus_connection_signal_subscribe.restype = ctypes.c_uint
        gio.g_dbus_connection_signal_unsubscribe.argtypes = [ctypes.c_void_p, ctypes.c_uint]

        self._glib = glib
        self._gio = gio

    def _parse_variant(self, sig_bytes, text_str):
        vtype = self._glib.g_variant_type_new(sig_bytes)
        err = ctypes.c_void_p()
        var = self._glib.g_variant_parse(
            vtype, text_str.encode("utf-8"), None, None, ctypes.byref(err)
        )
        self._glib.g_variant_type_free(vtype)
        if err.value:
            self._glib.g_error_free(err)
        return var

    def _print_variant(self, var_ptr):
        if not var_ptr:
            return ""
        raw_ptr = self._glib.g_variant_print(var_ptr, 0)
        if not raw_ptr:
            return ""
        try:
            return ctypes.string_at(raw_ptr).decode("utf-8", errors="replace")
        finally:
            self._glib.g_free(raw_ptr)

    def _dbus_call(self, path, iface, method, sig_bytes=None, text_str=None, timeout_ms=5000):
        params = self._parse_variant(sig_bytes, text_str) if sig_bytes else None
        err = ctypes.c_void_p()
        res = self._gio.g_dbus_connection_call_sync(
            self._conn,
            self.PORTAL_BUS,
            path,
            iface,
            method,
            params,
            None,
            0,
            timeout_ms,
            None,
            ctypes.byref(err),
        )
        # g_dbus_connection_call_sync consumes floating variant ref; no unref needed on params
        if err.value:
            self._glib.g_error_free(err)
            return None
        return res

    def is_available(self):
        """Return True if org.freedesktop.portal.GlobalShortcuts is exposed by the desktop."""
        if not self._glib or not self._gio:
            return False
        err = ctypes.c_void_p()
        conn = self._gio.g_bus_get_sync(2, None, ctypes.byref(err))  # G_BUS_TYPE_SESSION = 2
        if err.value:
            self._glib.g_error_free(err)
            return False
        if not conn:
            return False
        self._conn = conn
        res = self._dbus_call(
            self.PORTAL_PATH,
            b"org.freedesktop.DBus.Properties",
            b"Get",
            b"(ss)",
            "('org.freedesktop.portal.GlobalShortcuts', 'version')",
            timeout_ms=2000,
        )
        if not res:
            return False
        printed = self._print_variant(res)
        self._glib.g_variant_unref(res)
        return any(ch.isdigit() for ch in printed)

    def start(self, shortcut_str, force_rebind=False):
        """Ensure portal session exists, bind shortcut if needed, and listen for Activated."""
        if not self._conn and not self.is_available():
            return False

        trigger = _shortcut_to_xdg_trigger(shortcut_str)
        if self._session_handle and self._thread and self._thread.is_alive():
            if force_rebind:
                self._bind_shortcut(self._session_handle, trigger)
            return True

        self._ready_event.clear()
        self._list_event.clear()
        self._already_bound = False

        self._thread = threading.Thread(
            target=self._run_loop,
            args=(trigger, force_rebind),
            daemon=True,
        )
        self._thread.start()
        return self._ready_event.wait(timeout=3.0) and bool(self._session_handle)

    def _run_loop(self, trigger, force_rebind):
        ctx = self._glib.g_main_context_new()
        self._ctx = ctx
        self._glib.g_main_context_push_thread_default(ctx)
        loop = self._glib.g_main_loop_new(ctx, 0)
        self._loop = loop

        sig_cb_type = ctypes.CFUNCTYPE(
            None,
            ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p,
            ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p,
        )

        unique = self._gio.g_dbus_connection_get_unique_name(self._conn).decode("utf-8")
        sender = unique.lstrip(":").replace(".", "_")

        def _on_activated(_conn, _sender, _path, _iface, _signal, params, _ud):
            text = self._print_variant(params)
            if f"'{self.SHORTCUT_ID}'" in text:
                self.activated.emit()

        act_cb = sig_cb_type(_on_activated)
        self._callbacks.append(act_cb)
        sub_act = self._gio.g_dbus_connection_signal_subscribe(
            self._conn,
            self.PORTAL_BUS,
            self.PORTAL_IFACE,
            b"Activated",
            self.PORTAL_PATH,
            None,
            0,
            act_cb,
            None,
            None,
        )
        self._sub_ids.append(sub_act)

        # CreateSession
        req_token = f"petra_gs_req_{uuid.uuid4().hex[:10]}"
        sess_token = f"petra_gs_sess_{uuid.uuid4().hex[:10]}"
        req_path = f"/org/freedesktop/portal/desktop/request/{sender}/{req_token}".encode("utf-8")

        def _on_create_resp(_conn, _sender, _path, _iface, _signal, params, _ud):
            text = self._print_variant(params)
            m = re.search(r"'session_handle'\s*:\s*<'([^']+)'>", text)
            if m:
                self._session_handle = m.group(1)
                self._ready_event.set()
                # Check existing bindings before prompting user
                threading.Thread(
                    target=self._check_and_bind,
                    args=(sender, self._session_handle, trigger, force_rebind),
                    daemon=True,
                ).start()
            else:
                self._ready_event.set()

        create_cb = sig_cb_type(_on_create_resp)
        self._callbacks.append(create_cb)
        sub_create = self._gio.g_dbus_connection_signal_subscribe(
            self._conn,
            self.PORTAL_BUS,
            self.REQUEST_IFACE,
            b"Response",
            req_path,
            None,
            0,
            create_cb,
            None,
            None,
        )
        self._sub_ids.append(sub_create)

        res = self._dbus_call(
            self.PORTAL_PATH,
            self.PORTAL_IFACE,
            b"CreateSession",
            b"(a{sv})",
            f"({{'handle_token': <'{req_token}'>, 'session_handle_token': <'{sess_token}'>}})",
        )
        if res:
            self._glib.g_variant_unref(res)
        else:
            self._ready_event.set()

        self._glib.g_main_loop_run(loop)
        self._glib.g_main_context_pop_thread_default(ctx)
        self._glib.g_main_loop_unref(loop)
        self._glib.g_main_context_unref(ctx)

    def _check_and_bind(self, sender, session_handle, trigger, force_rebind):
        if not force_rebind:
            sig_cb_type = ctypes.CFUNCTYPE(
                None,
                ctypes.c_void_p, ctypes.c_char_p, ctypes.c_char_p,
                ctypes.c_char_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p,
            )
            list_token = f"petra_gs_list_{uuid.uuid4().hex[:10]}"
            list_path = f"/org/freedesktop/portal/desktop/request/{sender}/{list_token}".encode("utf-8")

            def _on_list_resp(_conn, _sender, _path, _iface, _signal, params, _ud):
                text = self._print_variant(params)
                self._already_bound = f"'{self.SHORTCUT_ID}'" in text
                self._list_event.set()

            list_cb = sig_cb_type(_on_list_resp)
            self._callbacks.append(list_cb)
            sub_list = self._gio.g_dbus_connection_signal_subscribe(
                self._conn,
                self.PORTAL_BUS,
                self.REQUEST_IFACE,
                b"Response",
                list_path,
                None,
                0,
                list_cb,
                None,
                None,
            )
            self._sub_ids.append(sub_list)
            res = self._dbus_call(
                self.PORTAL_PATH,
                self.PORTAL_IFACE,
                b"ListShortcuts",
                b"(oa{sv})",
                f"(objectpath '{session_handle}', {{'handle_token': <'{list_token}'>}})",
            )
            if res:
                self._glib.g_variant_unref(res)
                self._list_event.wait(timeout=2.0)

        if force_rebind or not self._already_bound:
            self._bind_shortcut(session_handle, trigger)

    def _bind_shortcut(self, session_handle, trigger):
        bind_token = f"petra_gs_bind_{uuid.uuid4().hex[:10]}"
        safe_trigger = trigger.replace("'", "")
        text = (
            f"(objectpath '{session_handle}', "
            f"[('{self.SHORTCUT_ID}', {{'description': <'Show or hide Petra Clipboard'>, "
            f"'preferred_trigger': <'{safe_trigger}'>}})], "
            f"'', {{'handle_token': <'{bind_token}'>}})"
        )
        res = self._dbus_call(
            self.PORTAL_PATH,
            self.PORTAL_IFACE,
            b"BindShortcuts",
            b"(oa(sa{sv})sa{sv})",
            text,
            timeout_ms=10000,
        )
        if res:
            self._glib.g_variant_unref(res)

    def stop(self):
        try:
            if self._conn and self._session_handle:
                res = self._dbus_call(
                    self._session_handle.encode("utf-8"),
                    self.SESSION_IFACE,
                    b"Close",
                    timeout_ms=1000,
                )
                if res:
                    self._glib.g_variant_unref(res)
                self._session_handle = None
            if self._conn:
                for sid in self._sub_ids:
                    self._gio.g_dbus_connection_signal_unsubscribe(self._conn, sid)
                self._sub_ids.clear()
            if self._loop:
                self._glib.g_main_loop_quit(self._loop)
                self._loop = None
        except Exception:
            pass


class _XKeyEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("serial", ctypes.c_ulong),
        ("send_event", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("window", ctypes.c_ulong),
        ("root", ctypes.c_ulong),
        ("subwindow", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("x", ctypes.c_int),
        ("y", ctypes.c_int),
        ("x_root", ctypes.c_int),
        ("y_root", ctypes.c_int),
        ("state", ctypes.c_uint),
        ("keycode", ctypes.c_uint),
        ("same_screen", ctypes.c_int),
    ]


class _XEvent(ctypes.Union):
    _fields_ = [
        ("type", ctypes.c_int),
        ("xkey", _XKeyEvent),
        ("pad", ctypes.c_long * 24),
    ]


class _XErrorEvent(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.c_int),
        ("display", ctypes.c_void_p),
        ("resourceid", ctypes.c_ulong),
        ("serial", ctypes.c_ulong),
        ("error_code", ctypes.c_ubyte),
        ("request_code", ctypes.c_ubyte),
        ("minor_code", ctypes.c_ubyte),
    ]


class _X11GlobalShortcutGrabber(QObject):
    """Sandbox-native X11 global hotkey listener using XGrabKey + QSocketNotifier."""

    SHIFT_MASK = 1 << 0
    LOCK_MASK = 1 << 1
    CONTROL_MASK = 1 << 2
    MOD1_MASK = 1 << 3
    MOD2_MASK = 1 << 4
    MOD4_MASK = 1 << 6
    RELEVANT_MODS = SHIFT_MASK | CONTROL_MASK | MOD1_MASK | MOD4_MASK
    GRAB_MODE_ASYNC = 1
    KEY_PRESS = 2
    BAD_ACCESS = 10

    def __init__(self, on_toggle=None):
        super().__init__()
        self._on_toggle = on_toggle
        self._x11 = None
        self._dpy = None
        self._root = None
        self._notifier = None
        self._keycode = None
        self._mod_mask = 0
        self._grab_error = False
        self._err_cb_ref = None
        self._load_x11()

    def _load_x11(self):
        try:
            x11 = ctypes.CDLL("libX11.so.6")
        except OSError:
            return
        x11.XOpenDisplay.argtypes = [ctypes.c_char_p]
        x11.XOpenDisplay.restype = ctypes.c_void_p
        x11.XDefaultRootWindow.argtypes = [ctypes.c_void_p]
        x11.XDefaultRootWindow.restype = ctypes.c_ulong
        x11.XStringToKeysym.argtypes = [ctypes.c_char_p]
        x11.XStringToKeysym.restype = ctypes.c_ulong
        x11.XKeysymToKeycode.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        x11.XKeysymToKeycode.restype = ctypes.c_uint
        x11.XGrabKey.argtypes = [
            ctypes.c_void_p, ctypes.c_int, ctypes.c_uint,
            ctypes.c_ulong, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        ]
        x11.XGrabKey.restype = ctypes.c_int
        x11.XUngrabKey.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_uint, ctypes.c_ulong]
        x11.XUngrabKey.restype = ctypes.c_int
        x11.XConnectionNumber.argtypes = [ctypes.c_void_p]
        x11.XConnectionNumber.restype = ctypes.c_int
        x11.XPending.argtypes = [ctypes.c_void_p]
        x11.XPending.restype = ctypes.c_int
        x11.XNextEvent.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
        x11.XNextEvent.restype = ctypes.c_int
        x11.XSync.argtypes = [ctypes.c_void_p, ctypes.c_int]
        x11.XCloseDisplay.argtypes = [ctypes.c_void_p]
        x11.XSetErrorHandler.argtypes = [ctypes.c_void_p]
        x11.XSetErrorHandler.restype = ctypes.c_void_p
        self._x11 = x11

    def _parse_shortcut(self, shortcut_str):
        mod_mask = 0
        key_name = None
        for part in [p.strip() for p in str(shortcut_str).split('+') if p.strip()]:
            low = part.lower()
            if low in ('ctrl', 'control'):
                mod_mask |= self.CONTROL_MASK
            elif low == 'alt':
                mod_mask |= self.MOD1_MASK
            elif low == 'shift':
                mod_mask |= self.SHIFT_MASK
            elif low in ('super', 'mod4', 'meta'):
                mod_mask |= self.MOD4_MASK
            else:
                key_name = part
        if not key_name:
            return None, 0
        for candidate in (key_name, key_name.lower(), key_name.upper()):
            ks = self._x11.XStringToKeysym(candidate.encode("utf-8"))
            if ks:
                kc = self._x11.XKeysymToKeycode(self._dpy, ks)
                if kc:
                    return int(kc), mod_mask
        return None, 0

    def _ungrab_current(self):
        if self._dpy and self._keycode is not None:
            for extra in (0, self.LOCK_MASK, self.MOD2_MASK, self.LOCK_MASK | self.MOD2_MASK):
                self._x11.XUngrabKey(self._dpy, self._keycode, self._mod_mask | extra, self._root)
            self._x11.XSync(self._dpy, 0)
            self._keycode = None
            self._mod_mask = 0

    def grab(self, shortcut_str):
        if not self._x11 or not os.environ.get("DISPLAY"):
            return False
        if not self._dpy:
            self._dpy = self._x11.XOpenDisplay(None)
            if not self._dpy:
                return False
            self._root = self._x11.XDefaultRootWindow(self._dpy)

        self._ungrab_current()

        keycode, mod_mask = self._parse_shortcut(shortcut_str)
        if not keycode:
            return False

        self._grab_error = False
        err_handler_type = ctypes.CFUNCTYPE(ctypes.c_int, ctypes.c_void_p, ctypes.POINTER(_XErrorEvent))

        def _on_xerror(_dpy, err_ptr):
            if err_ptr and err_ptr.contents.error_code == self.BAD_ACCESS:
                self._grab_error = True
            return 0

        self._err_cb_ref = err_handler_type(_on_xerror)
        prev_handler = self._x11.XSetErrorHandler(self._err_cb_ref)
        try:
            for extra in (0, self.LOCK_MASK, self.MOD2_MASK, self.LOCK_MASK | self.MOD2_MASK):
                self._x11.XGrabKey(
                    self._dpy,
                    keycode,
                    mod_mask | extra,
                    self._root,
                    0,
                    self.GRAB_MODE_ASYNC,
                    self.GRAB_MODE_ASYNC,
                )
            self._x11.XSync(self._dpy, 0)
        finally:
            self._x11.XSetErrorHandler(prev_handler)

        if self._grab_error:
            for extra in (0, self.LOCK_MASK, self.MOD2_MASK, self.LOCK_MASK | self.MOD2_MASK):
                self._x11.XUngrabKey(self._dpy, keycode, mod_mask | extra, self._root)
            self._x11.XSync(self._dpy, 0)
            return False

        self._keycode = keycode
        self._mod_mask = mod_mask

        if self._notifier is None:
            fd = self._x11.XConnectionNumber(self._dpy)
            self._notifier = QSocketNotifier(fd, QSocketNotifier.Type.Read, self)
            self._notifier.activated.connect(self._on_x11_events)

        return True

    def _on_x11_events(self):
        if not self._dpy:
            return
        ev = _XEvent()
        while self._x11.XPending(self._dpy) > 0:
            self._x11.XNextEvent(self._dpy, ctypes.byref(ev))
            if ev.type == self.KEY_PRESS:
                mods = ev.xkey.state & self.RELEVANT_MODS
                if ev.xkey.keycode == self._keycode and mods == self._mod_mask:
                    if self._on_toggle:
                        QTimer.singleShot(0, self._on_toggle)

    def cleanup(self):
        try:
            if self._notifier is not None:
                self._notifier.setEnabled(False)
                self._notifier.deleteLater()
                self._notifier = None
            self._ungrab_current()
            if self._dpy:
                self._x11.XCloseDisplay(self._dpy)
                self._dpy = None
        except Exception:
            pass


class GlobalShortcutManager:
    """Manages global keyboard shortcuts by registering them with the desktop environment.

    Supports: Cinnamon, GNOME, KDE Plasma, XFCE, MATE (native installs).
    Inside Flatpak uses org.freedesktop.portal.GlobalShortcuts (Wayland/modern DEs)
    or sandbox-native X11 XGrabKey (X11 sessions) with no host escape or manual setup.
    """

    KEYBINDING_NAME = "Petra Clipboard"

    @property
    def manual_command(self):
        """Fallback command for compositors without GlobalShortcuts portal or X11."""
        flatpak_id = os.environ.get('FLATPAK_ID', 'io.github.gessendarien.petra-clipboard')
        return f"flatpak run {flatpak_id} --toggle"

    @property
    def requires_manual_setup(self):
        """True only inside Flatpak when neither portal nor X11 key grab is active."""
        return self.is_flatpak and self.flatpak_backend == 'manual'

    def __init__(self, on_toggle=None, on_show=None, on_hide=None):
        self.is_flatpak = Path('/.flatpak-info').exists() or bool(os.environ.get('FLATPAK_ID'))
        self.desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()

        # Callbacks
        self._on_toggle = on_toggle
        self._on_show = on_show
        self._on_hide = on_hide

        # Flatpak sandbox-native backends
        self._portal_shortcuts = None
        self._x11_grabber = None
        self.flatpak_backend = None

    # ─────────────────────────────────────
    #  Command execution helpers
    # ─────────────────────────────────────

    def _host_run(self, cmd, **kwargs):
        """Run a desktop-settings command (native installs only).
        Never escapes the Flatpak sandbox."""
        if self.is_flatpak:
            return None
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, **kwargs)
            if result.returncode != 0 and result.stderr:
                print(f"CMD STDERR ({' '.join(cmd[:4])}): {result.stderr.strip()}")
            return result
        except Exception as e:
            print(f"Error running {' '.join(cmd[:3])}...: {e}")
            return None

    def _host_bash(self, bash_cmd):
        """Run a bash command string (native installs only).
        Never escapes the Flatpak sandbox."""
        if self.is_flatpak:
            return None
        cmd = ['bash', '-c', bash_cmd]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0 and result.stderr:
                print(f"BASH STDERR: {result.stderr.strip()}")
            return result
        except Exception as e:
            print(f"Error running bash command: {e}")
            return None

    @staticmethod
    def _escape_path(path_str):
        """Escape spaces in a path for use in shell commands.
        Do NOT use double quotes — gsettings GVariant parser rejects them."""
        return str(path_str).replace(" ", "\\ ")

    def _get_petra_command(self):
        """Return the command string the OS should run to toggle Petra.
        Must be a stable path that survives app restarts and reboots.
        """
        # 1. Flatpak: always use 'flatpak run <id>'
        if self.is_flatpak:
            return self.manual_command

        # 2. AppImage: $APPIMAGE env var points to the real .AppImage file on disk
        appimage_path = os.environ.get('APPIMAGE')
        if appimage_path and Path(appimage_path).exists():
            return f"{self._escape_path(appimage_path)} --toggle"

        # 3. Installed .deb: /usr/bin/petra wrapper exists
        if Path('/usr/bin/petra').exists():
            return '/usr/bin/petra --toggle'

        # 4. Local AppImage in output/ (development builds)
        project_root = Path(__file__).resolve().parent.parent
        output_dir = project_root / "output"
        if output_dir.exists():
            appimages = sorted(output_dir.glob("Petra-*-x86_64.AppImage"), reverse=True)
            for ai in appimages:
                if ai.exists() and os.access(str(ai), os.X_OK):
                    print(f"Using local AppImage for shortcut: {ai}")
                    return f"{self._escape_path(ai)} --toggle"

        # 5. Development: resolve real path of main.py (avoid any symlinks or /tmp mounts)
        import sys
        python_exe = sys.executable
        main_script = self._escape_path(Path(__file__).resolve().parent / "main.py")

        # Verify that the Python interpreter can actually import PyQt6,
        # otherwise the shortcut command will silently fail.
        try:
            verify = subprocess.run(
                [python_exe, '-c', 'import PyQt6'],
                capture_output=True, timeout=5
            )
            if verify.returncode != 0:
                print(f"WARNING: {python_exe} cannot import PyQt6. "
                      f"The shortcut command may fail. "
                      f"Install PyQt6: sudo apt install python3-pyqt6")
        except Exception:
            pass

        return f"{python_exe} {main_script} --toggle"

    def _shortcut_to_binding(self, shortcut_str):
        """Convert 'Alt + space' → '<Alt>space' (gsettings format)."""
        parts = [p.strip() for p in shortcut_str.split('+')]
        binding = ""
        for part in parts:
            lower = part.lower()
            if lower in ('alt',):
                binding += "<Alt>"
            elif lower in ('ctrl', 'control'):
                binding += "<Control>"
            elif lower in ('shift',):
                binding += "<Shift>"
            elif lower in ('super', 'mod4'):
                binding += "<Super>"
            else:
                binding += part.lower()
        return binding

    def _detect_desktop_type(self):
        """Detect the desktop environment."""
        desktop = self.desktop
        if 'cinnamon' in desktop:
            return 'cinnamon'
        elif 'mate' in desktop:
            return 'mate'
        elif 'xfce' in desktop:
            return 'xfce'
        elif 'kde' in desktop or 'plasma' in desktop:
            return 'kde'
        elif 'gnome' in desktop or 'unity' in desktop or 'pop' in desktop or 'budgie' in desktop or 'pantheon' in desktop:
            return 'gnome'
        else:
            # Fallback: try to detect by checking which tools exist
            return self._detect_desktop_by_tools()

    def _detect_desktop_by_tools(self):
        """Fallback detection by checking which settings tools exist on host."""
        # Try cinnamon first (common on Mint)
        r = self._host_run(['gsettings', 'get', 'org.cinnamon.desktop.keybindings', 'custom-list'])
        if r and r.returncode == 0:
            return 'cinnamon'
        # Try GNOME
        r = self._host_run(['gsettings', 'get', 'org.gnome.settings-daemon.plugins.media-keys', 'custom-keybindings'])
        if r and r.returncode == 0:
            return 'gnome'
        # Try KDE
        for kw in ['kwriteconfig6', 'kwriteconfig5']:
            r = self._host_run(['which', kw])
            if r and r.returncode == 0:
                return 'kde'
        # Try XFCE
        r = self._host_run(['which', 'xfconf-query'])
        if r and r.returncode == 0:
            return 'xfce'
        # Try MATE
        r = self._host_run(['gsettings', 'get', 'org.mate.Marco.global-keybindings', 'run-command-1'])
        if r and r.returncode == 0:
            return 'mate'
        return 'unknown'

    # ─────────────────────────────────────
    #  Main entry points
    # ─────────────────────────────────────

    def _setup_flatpak_shortcut(self, shortcut_str, force_rebind=False):
        """Register global shortcut inside Flatpak without touching the host.

        1. Prefer XDG GlobalShortcuts portal (KDE Plasma, GNOME 48+, Hyprland, COSMIC).
        2. Fallback to sandbox-native X11 XGrabKey on X11 sessions (Cinnamon, XFCE, MATE).
        3. Only fall back to manual desktop binding on Wayland compositors without the portal.
        """
        # 1. XDG GlobalShortcuts portal
        if self._portal_shortcuts is None and self.flatpak_backend in (None, 'portal'):
            portal = _PortalGlobalShortcuts(on_toggle=self._on_toggle)
            if portal.is_available():
                self._portal_shortcuts = portal

        if self._portal_shortcuts is not None:
            ok = self._portal_shortcuts.start(shortcut_str, force_rebind=force_rebind)
            if ok:
                self.flatpak_backend = 'portal'
                print(f"Flatpak global shortcut active via GlobalShortcuts portal ({shortcut_str})")
                return True

        # 2. X11 XGrabKey inside the sandbox (works on X11 sessions with --socket=fallback-x11)
        is_wayland = (
            bool(os.environ.get('WAYLAND_DISPLAY'))
            or os.environ.get('XDG_SESSION_TYPE', '').lower() == 'wayland'
        )
        if not is_wayland and os.environ.get('DISPLAY'):
            if self._x11_grabber is None:
                self._x11_grabber = _X11GlobalShortcutGrabber(on_toggle=self._on_toggle)
            self.flatpak_backend = 'x11'
            if self._x11_grabber.grab(shortcut_str):
                print(f"Flatpak global shortcut active via X11 XGrabKey ({shortcut_str})")
                return True
            print(f"Flatpak X11 XGrabKey conflict for '{shortcut_str}'")
            return False

        # 3. Older Wayland compositor without GlobalShortcuts portal
        self.flatpak_backend = 'manual'
        print("Running inside Flatpak on Wayland without GlobalShortcuts portal; "
              f"optional shortcut command: {self.manual_command}")
        return True

    def setup_global_shortcut(self, shortcut_str='Alt + space', force_rebind=False):
        """Register the global shortcut with the desktop environment."""
        if self.is_flatpak:
            return self._setup_flatpak_shortcut(shortcut_str, force_rebind=force_rebind)

        desktop_type = self._detect_desktop_type()
        print(f"Registering global shortcut '{shortcut_str}' for desktop: {desktop_type}")

        handlers = {
            'cinnamon': self._register_cinnamon,
            'gnome': self._register_gnome,
            'kde': self._register_kde,
            'xfce': self._register_xfce,
            'mate': self._register_mate,
        }

        handler = handlers.get(desktop_type)
        if handler:
            try:
                return handler(shortcut_str)
            except Exception as e:
                print(f"Error registering shortcut for {desktop_type}: {e}")
                return False
        else:
            print(f"Desktop '{self.desktop}' not auto-detected. Trying GNOME-compatible fallback...")
            try:
                return self._register_gnome(shortcut_str)
            except Exception:
                print(f"Fallback failed. Shortcut not registered.")
                return False

    def register_global_hotkey(self, shortcut_str='Alt + space'):
        """Register or update the global shortcut (rebinds portal/X11 in Flatpak)."""
        return self.setup_global_shortcut(shortcut_str, force_rebind=True)

    def cleanup_fifo(self):
        """Release any active Flatpak shortcut listeners/grabs on shutdown."""
        if self._portal_shortcuts is not None:
            self._portal_shortcuts.stop()
            self._portal_shortcuts = None
        if self._x11_grabber is not None:
            self._x11_grabber.cleanup()
            self._x11_grabber = None

    # ─────────────────────────────────────
    #  gsettings/dconf helpers (Cinnamon, GNOME, MATE)
    # ─────────────────────────────────────

    def _gsettings(self, args):
        """Run gsettings on host."""
        return self._host_run(['gsettings'] + args)

    def _dconf(self, args):
        """Run dconf on host."""
        return self._host_run(['dconf'] + args)

    def _parse_gsettings_list(self, raw):
        """Parse a gsettings list output like \"['a', 'b']\" into a Python list."""
        raw = raw.strip()
        if raw == '@as []':
            return []
        try:
            return json.loads(raw.replace("'", '"'))
        except Exception:
            return []

    def _find_existing_binding(self, base_path, custom_list, relocatable_schema=None, is_full_path=False):
        """Find if a Petra keybinding already exists. Returns the key/path or None.
        Uses gsettings via bash for Flatpak compatibility."""
        for item in custom_list:
            if is_full_path:
                path = item if item.endswith('/') else item + '/'
            else:
                path = f"{base_path}/{item}/"

            name = None
            if relocatable_schema:
                result = self._host_bash(f"gsettings get '{relocatable_schema}:{path}' name")
                if result and result.returncode == 0:
                    name = result.stdout.strip().strip("'")
            else:
                result = self._dconf(['read', f'{path}name'])
                if result and result.returncode == 0:
                    name = result.stdout.strip().strip("'")

            if name == self.KEYBINDING_NAME:
                return item
        return None

    def _next_custom_num(self, custom_list, prefix='custom'):
        """Find the next available custom number."""
        existing = set()
        for k in custom_list:
            part = k.rstrip('/').split('/')[-1] if '/' in k else k
            try:
                existing.add(int(part.replace(prefix, '')))
            except ValueError:
                pass
        n = 0
        while n in existing:
            n += 1
        return n

    # ─────────────────────────────────────
    #  Cinnamon
    # ─────────────────────────────────────

    def _register_cinnamon(self, shortcut_str):
        base = "/org/cinnamon/desktop/keybindings/custom-keybindings"
        schema = "org.cinnamon.desktop.keybindings"
        relocatable = "org.cinnamon.desktop.keybindings.custom-keybinding"
        binding = self._shortcut_to_binding(shortcut_str)
        command = self._get_petra_command()

        r = self._host_bash(f"gsettings get {schema} custom-list")
        custom_list = self._parse_gsettings_list(r.stdout) if r and r.returncode == 0 else []

        existing = self._find_existing_binding(base, custom_list, relocatable_schema=relocatable)
        if existing:
            key_name = existing
        else:
            key_name = f"custom{self._next_custom_num(custom_list)}"

        path = f"{base}/{key_name}/"
        schema_path = f"{relocatable}:{path}"

        # Use bash -c for reliable D-Bus session access from Flatpak
        self._host_bash(f"gsettings set '{schema_path}' name '{self.KEYBINDING_NAME}'")
        self._host_bash(f"gsettings set '{schema_path}' command '{command}'")
        self._host_bash(f"gsettings set '{schema_path}' binding \"['{binding}']\"")

        if key_name not in custom_list:
            custom_list.append(key_name)
            list_str = str(custom_list).replace('"', "'")
            self._host_bash(f"gsettings set {schema} custom-list \"{list_str}\"")
        else:
            # Force Cinnamon to reload: Cinnamon only re-reads custom keybinding
            # commands when `custom-list` changes (the command string is captured
            # in a closure at setup time).  Toggle the list to trigger the
            # `on_customs_changed` handler which calls remove + setup.
            tmp_list = [x for x in custom_list if x != key_name]
            tmp_str = str(tmp_list).replace('"', "'")
            self._host_bash(f"gsettings set {schema} custom-list \"{tmp_str}\"")
            import time; time.sleep(0.3)
            list_str = str(custom_list).replace('"', "'")
            self._host_bash(f"gsettings set {schema} custom-list \"{list_str}\"")

        print(f"Cinnamon shortcut registered: {binding} -> {command}")
        # Verify the binding was written correctly
        verify = self._host_bash(f"gsettings get '{schema_path}' binding")
        if verify and verify.returncode == 0 and binding in verify.stdout:
            print(f"Cinnamon shortcut VERIFIED OK")
            return True
        else:
            stdout = verify.stdout.strip() if verify else 'None'
            stderr = verify.stderr.strip() if verify and verify.stderr else ''
            print(f"WARNING: Cinnamon shortcut verification failed. stdout='{stdout}' stderr='{stderr}'")
            return False

    # ─────────────────────────────────────
    #  GNOME (also works for Budgie, Pantheon, etc.)
    # ─────────────────────────────────────

    def _register_gnome(self, shortcut_str):
        base = "/org/gnome/settings-daemon/plugins/media-keys/custom-keybindings"
        schema = "org.gnome.settings-daemon.plugins.media-keys"
        relocatable = "org.gnome.settings-daemon.plugins.media-keys.custom-keybinding"
        binding = self._shortcut_to_binding(shortcut_str)
        command = self._get_petra_command()

        r = self._host_bash(f"gsettings get {schema} custom-keybindings")
        custom_list = self._parse_gsettings_list(r.stdout) if r and r.returncode == 0 else []

        existing = self._find_existing_binding(base, custom_list, relocatable_schema=relocatable, is_full_path=True)
        if existing:
            path = existing if existing.endswith('/') else existing + '/'
        else:
            num = self._next_custom_num(custom_list)
            path = f"{base}/custom{num}/"

        schema_path = f"{relocatable}:{path}"

        # Use bash -c for reliable D-Bus session access from Flatpak
        self._host_bash(f"gsettings set '{schema_path}' name '{self.KEYBINDING_NAME}'")
        self._host_bash(f"gsettings set '{schema_path}' command '{command}'")
        self._host_bash(f"gsettings set '{schema_path}' binding '{binding}'")

        if path not in custom_list:
            custom_list.append(path)
            list_str = str(custom_list).replace('"', "'")
            self._host_bash(f"gsettings set {schema} custom-keybindings \"{list_str}\"")
        else:
            # Force GNOME to reload keybindings by toggling the list
            tmp_list = [x for x in custom_list if x != path]
            tmp_str = str(tmp_list).replace('"', "'")
            self._host_bash(f"gsettings set {schema} custom-keybindings \"{tmp_str}\"")
            import time; time.sleep(0.3)
            list_str = str(custom_list).replace('"', "'")
            self._host_bash(f"gsettings set {schema} custom-keybindings \"{list_str}\"")

        print(f"GNOME shortcut registered: {binding} -> {command}")
        # Verify the binding was written correctly
        verify = self._host_bash(f"gsettings get '{schema_path}' binding")
        if verify and verify.returncode == 0 and binding in verify.stdout:
            print(f"GNOME shortcut VERIFIED OK")
            return True
        else:
            stdout = verify.stdout.strip() if verify else 'None'
            stderr = verify.stderr.strip() if verify and verify.stderr else ''
            print(f"WARNING: GNOME shortcut verification failed. stdout='{stdout}' stderr='{stderr}'")
            return False

    # ─────────────────────────────────────
    #  KDE Plasma
    # ─────────────────────────────────────

    def _register_kde(self, shortcut_str):
        binding = self._shortcut_to_binding(shortcut_str)
        # KDE format: Alt+Space (no angle brackets, + separated)
        # Also, KDE expects Meta instead of Super
        kde_binding = shortcut_str.replace(' ', '').replace('Super', 'Meta')
        command = self._get_petra_command()

        # Detect kwriteconfig version
        kwrite = None
        for cmd in ['kwriteconfig6', 'kwriteconfig5']:
            r = self._host_run(['which', cmd])
            if r and r.returncode == 0:
                kwrite = cmd
                break

        if not kwrite:
            print("KDE: kwriteconfig not found, cannot register shortcut")
            return False

        # Write to kglobalshortcutsrc
        group = "petra-clipboard.desktop"
        self._host_run([
            kwrite, '--file', 'kglobalshortcutsrc',
            '--group', group,
            '--key', '_k_friendly_name', self.KEYBINDING_NAME
        ])
        self._host_run([
            kwrite, '--file', 'kglobalshortcutsrc',
            '--group', group,
            '--key', 'Petra', f'{kde_binding},none,Toggle Petra Clipboard'
        ])

        # Write the action to khotkeysrc for custom command
        self._host_run([
            kwrite, '--file', 'khotkeysrc',
            '--group', 'Data_petra',
            '--key', 'Comment', 'Petra Clipboard Manager'
        ])
        self._host_run([
            kwrite, '--file', 'khotkeysrc',
            '--group', 'Data_petra',
            '--key', 'Enabled', 'true'
        ])
        self._host_run([
            kwrite, '--file', 'khotkeysrc',
            '--group', 'Data_petra',
            '--key', 'Type', 'SIMPLE_ACTION_DATA'
        ])
        self._host_run([
            kwrite, '--file', 'khotkeysrc',
            '--group', 'Data_petra_Actions0',
            '--key', 'CommandURL', command
        ])
        self._host_run([
            kwrite, '--file', 'khotkeysrc',
            '--group', 'Data_petra_Actions0',
            '--key', 'Type', 'COMMAND_URL'
        ])
        self._host_run([
            kwrite, '--file', 'khotkeysrc',
            '--group', 'Data_petra_Triggers0',
            '--key', 'Key', kde_binding
        ])
        self._host_run([
            kwrite, '--file', 'khotkeysrc',
            '--group', 'Data_petra_Triggers0',
            '--key', 'Type', 'SHORTCUT'
        ])

        # Reload kglobalaccel
        self._host_run(['dbus-send', '--type=signal', '--dest=org.kde.kglobalaccel',
                         '/kglobalaccel', 'org.kde.KGlobalAccel.reloadConfig'])
        # Also try reconfiguring khotkeys
        self._host_run(['dbus-send', '--type=signal', '--dest=org.kde.keyboard',
                         '/modules/khotkeys', 'org.kde.khotkeys.reread_configuration'])

        print(f"KDE shortcut registered: {kde_binding} -> {command}")
        return True

    # ─────────────────────────────────────
    #  XFCE
    # ─────────────────────────────────────

    def _register_xfce(self, shortcut_str):
        binding = self._shortcut_to_binding(shortcut_str)
        command = self._get_petra_command()

        # XFCE uses xfconf-query for custom shortcuts
        # Channel: xfce4-keyboard-shortcuts
        # Property: /commands/custom/<binding>
        prop = f"/commands/custom/{binding}"

        self._host_run([
            'xfconf-query', '--channel', 'xfce4-keyboard-shortcuts',
            '--property', prop,
            '--create', '--type', 'string',
            '--set', command
        ])

        print(f"XFCE shortcut registered: {binding} -> {command}")
        return True

    # ─────────────────────────────────────
    #  MATE
    # ─────────────────────────────────────

    def _register_mate(self, shortcut_str):
        binding = self._shortcut_to_binding(shortcut_str)
        command = self._get_petra_command()

        # MATE uses dconf with a similar structure to GNOME but different schemas
        base = "/org/mate/desktop/keybindings"
        # Find an available custom slot (MATE has fixed slots: custom0..custom11)
        slot = None
        for i in range(12):
            path = f"{base}/custom{i}/"
            r = self._dconf(['read', f'{path}name'])
            if r and r.returncode == 0:
                name = r.stdout.strip().strip("'")
                if name == self.KEYBINDING_NAME:
                    slot = i
                    break
                if not name or name == "''":
                    if slot is None:
                        slot = i
            else:
                if slot is None:
                    slot = i

        if slot is None:
            slot = 0  # Overwrite first slot as last resort

        path = f"{base}/custom{slot}/"
        self._dconf(['write', f'{path}name', f"'{self.KEYBINDING_NAME}'"])
        self._dconf(['write', f'{path}action', f"'{command}'"])
        self._dconf(['write', f'{path}binding', f"'{binding}'"])

        print(f"MATE shortcut registered: {binding} -> {command}")
        return True