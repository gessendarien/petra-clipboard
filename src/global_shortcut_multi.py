import subprocess
import os
import json
from pathlib import Path


class GlobalShortcutManager:
    """Manages global keyboard shortcuts by registering them with the desktop environment.

    Supports: Cinnamon, GNOME, KDE Plasma, XFCE, MATE.
    Works from: native install (.deb/AppImage), Flatpak (via flatpak-spawn --host).
    When the shortcut is pressed, the OS runs the Petra command, and Petra's
    single-instance mechanism (Unix socket in main.py) shows the existing window.
    """

    KEYBINDING_NAME = "Petra Clipboard"

    def __init__(self, on_toggle=None, on_show=None, on_hide=None):
        self.is_flatpak = Path('/.flatpak-info').exists()
        self.desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()

        # Callbacks (kept for compatibility)
        self._on_toggle = on_toggle
        self._on_show = on_show
        self._on_hide = on_hide

    # ─────────────────────────────────────
    #  Command execution helpers
    # ─────────────────────────────────────

    def _host_run(self, cmd, **kwargs):
        """Run a command on the HOST system.
        Inside Flatpak, wraps with flatpak-spawn --host.
        Outside Flatpak, runs directly."""
        if self.is_flatpak:
            cmd = ['flatpak-spawn', '--host', '--directory=/'] + cmd
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5, **kwargs)
            if result.returncode != 0 and result.stderr:
                print(f"CMD STDERR ({' '.join(cmd[:4])}): {result.stderr.strip()}")
            return result
        except Exception as e:
            print(f"Error running {' '.join(cmd[:3])}...: {e}")
            return None

    def _host_bash(self, bash_cmd):
        """Run a bash command string on the HOST.
        Using 'bash -c' ensures the host's environment (including DBUS_SESSION_BUS_ADDRESS)
        is available, which is critical for gsettings/dconf to work from Flatpak."""
        cmd = ['bash', '-c', bash_cmd]
        if self.is_flatpak:
            cmd = ['flatpak-spawn', '--host', '--directory=/'] + cmd
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode != 0 and result.stderr:
                print(f"BASH STDERR: {result.stderr.strip()}")
            return result
        except Exception as e:
            print(f"Error running bash command: {e}")
            return None

    def _get_petra_command(self):
        """Return the command string the OS should run to toggle Petra.
        Must be a stable path that survives app restarts and reboots.
        """
        # 1. Flatpak: always use 'flatpak run <id>'
        if self.is_flatpak:
            flatpak_id = os.environ.get('FLATPAK_ID', 'io.github.gessendarien.petra')
            return f"flatpak run {flatpak_id}"

        # 2. AppImage: $APPIMAGE env var points to the real .AppImage file on disk
        appimage_path = os.environ.get('APPIMAGE')
        if appimage_path and Path(appimage_path).exists():
            return appimage_path

        # 3. Installed .deb: /usr/bin/petra wrapper exists
        if Path('/usr/bin/petra').exists():
            return '/usr/bin/petra'

        # 4. Development: resolve real path of main.py (avoid any symlinks or /tmp mounts)
        main_script = Path(__file__).resolve().parent / "main.py"
        return f"python3 {main_script}"

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

    def setup_global_shortcut(self, shortcut_str='Alt + space'):
        """Register the global shortcut with the desktop environment."""
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
        """Alias for setup_global_shortcut (backwards compatibility)."""
        return self.setup_global_shortcut(shortcut_str)

    def cleanup_fifo(self):
        """No-op. Kept for backwards compatibility."""
        pass

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

        print(f"Cinnamon shortcut registered: {binding} -> {command}")
        # Verify the binding was written correctly
        verify = self._host_bash(f"gsettings get '{schema_path}' binding")
        if verify and verify.returncode == 0 and binding in verify.stdout:
            print(f"Cinnamon shortcut VERIFIED OK")
        else:
            stdout = verify.stdout.strip() if verify else 'None'
            stderr = verify.stderr.strip() if verify and verify.stderr else ''
            print(f"WARNING: Cinnamon shortcut verification failed. stdout='{stdout}' stderr='{stderr}'")
        return True

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

        print(f"GNOME shortcut registered: {binding} -> {command}")
        # Verify the binding was written correctly
        verify = self._host_bash(f"gsettings get '{schema_path}' binding")
        if verify and verify.returncode == 0 and binding in verify.stdout:
            print(f"GNOME shortcut VERIFIED OK")
        else:
            stdout = verify.stdout.strip() if verify else 'None'
            stderr = verify.stderr.strip() if verify and verify.stderr else ''
            print(f"WARNING: GNOME shortcut verification failed. stdout='{stdout}' stderr='{stderr}'")
        return True

    # ─────────────────────────────────────
    #  KDE Plasma
    # ─────────────────────────────────────

    def _register_kde(self, shortcut_str):
        binding = self._shortcut_to_binding(shortcut_str)
        # KDE format: Alt+Space (no angle brackets, + separated)
        kde_binding = shortcut_str.replace(' ', '')  # "Alt+space"
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