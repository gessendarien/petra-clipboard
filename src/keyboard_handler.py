"""
Keyboard handler module — extracted from window.py.

Contains KeyboardHandlerMixin with:
- eventFilter()                — global key listener
- navigate_up/down()           — clip list navigation
- switch_filter_left/right()   — filter tab navigation
- get_visible_clip_widgets()   — helper to list visible ClipItem widgets
- _set_selected_clip_widget()  — highlight a single clip
- _clear_clip_selection()      — remove all clip highlights

MRO NOTE:
  eventFilter() intentionally overrides QObject.eventFilter().
  No other collisions with ClipboardManager, FilterManager, or ConfigManager.
"""

import os

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt, QEvent, QTimer

from widgets import ClipItem


class KeyboardHandlerMixin:
    """Mixin that adds keyboard-navigation to PetraClipboard.

    MRO collision (intentional):
      eventFilter() overrides QObject.eventFilter().
    """

    def eventFilter(self, obj, event):
        """Override QObject.eventFilter — intentional MRO override."""
        try:
            if getattr(self, '_handling_key', False):
                if hasattr(super(), "eventFilter"):
                    return super().eventFilter(obj, event)
                return False

            # Handle mouse hover on recent emoji buttons safely
            if event.type() == QEvent.Type.Enter and obj in getattr(self, 'recent_emoji_buttons', []):
                try:
                    idx = self.recent_emoji_buttons.index(obj)
                    self._on_emoji_mouse_enter(event, idx)
                except ValueError:
                    pass
                if hasattr(super(), "eventFilter"):
                    return super().eventFilter(obj, event)
                return False

            try:
                active = QApplication.activeWindow()
            except Exception:
                active = None

            if not getattr(self, 'isVisible', None) or not self.isVisible() or active is not self:
                if hasattr(super(), "eventFilter"):
                    return super().eventFilter(obj, event)
                return False

            if event.type() == QEvent.Type.KeyPress:
                try:
                    self._handling_key = True
                except Exception:
                    pass
                
                key = event.key()
                modifiers_only = key in (Qt.Key.Key_Alt, Qt.Key.Key_Control, Qt.Key.Key_Shift, 
                                         Qt.Key.Key_Meta, Qt.Key.Key_Tab)
                alt_pressed = event.modifiers() & Qt.KeyboardModifier.AltModifier
                
                if modifiers_only or alt_pressed:
                    try:
                        self._handling_key = False
                    except Exception:
                        pass
                    if hasattr(super(), "eventFilter"):
                        return super().eventFilter(obj, event)
                    return False
                
                try:
                    focus = QApplication.focusWidget()
                    if not (hasattr(self, 'search_bar') and focus is self.search_bar):
                        if not getattr(self, '_keyboard_selection_active', False):
                            self._keyboard_selection_active = True
                except Exception:
                    pass

                k = event.key()
                try:
                    if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                        is_repeat = True
                    else:
                        is_repeat = False
                except Exception:
                    is_repeat = False

                if os.environ.get('PETRA_DEBUG_KEYS'):
                    try:
                        print(f"[petra-debug] eventFilter key={k} mods={event.modifiers()} visible={self.isVisible()} active={QApplication.activeWindow() is self}")
                    except Exception:
                        pass
                
                # Escape -> 3-step behavior
                if k == Qt.Key.Key_Escape:
                    try:
                        focus = QApplication.focusWidget()
                        search_has_focus = hasattr(self, 'search_bar') and focus is self.search_bar
                        search_has_text = hasattr(self, 'search_bar') and self.search_bar.text()
                        
                        if search_has_text:
                            self.search_bar.clear()
                            try:
                                self._handling_key = False
                            except Exception:
                                pass
                            return True
                        
                        if search_has_focus:
                            self.search_bar.clearFocus()
                            try:
                                self._handling_key = False
                            except Exception:
                                pass
                            return True
                        
                        self.hide()
                        try:
                            self._handling_key = False
                        except Exception:
                            pass
                        return True
                    except Exception:
                        pass

                mods = event.modifiers()
                # Q/W press-and-hold emulation
                try:
                    focus = QApplication.focusWidget()
                    if not (hasattr(self, 'search_bar') and focus is self.search_bar):
                        if k == Qt.Key.Key_Q and not is_repeat:
                            if not getattr(self, '_key_q_down', False):
                                self._key_q_down = True
                                if hasattr(self, 'clear_btn') and self.clear_btn:
                                    self.clear_btn.setDown(True)
                                    self.clear_btn.is_actively_pressed = True
                                    self.clear_btn.setProgress(0)
                                    self.start_clear_animation()
                        if k == Qt.Key.Key_W and not is_repeat:
                            if not getattr(self, '_key_w_down', False):
                                self._key_w_down = True
                                if hasattr(self, 'pin_window_btn') and self.pin_window_btn:
                                    self.pin_window_btn.setDown(True)
                except Exception:
                    pass

                # Ctrl+F -> focus search
                if (mods & Qt.KeyboardModifier.ControlModifier) and k == Qt.Key.Key_F:
                    try:
                        if hasattr(self, 'search_bar'):
                            self.search_bar.setFocus()
                            return True
                    except Exception:
                        pass

                # Enter/Return -> copy selected clip
                if k == Qt.Key.Key_Return or k == Qt.Key.Key_Enter:
                    try:
                        if getattr(self, 'current_filter', None) == 'emoji':
                            selected_idx = getattr(self, 'selected_recent_emoji_index', -1)
                            recent_emojis = getattr(self, 'recent_emojis', [])[:16]
                            if selected_idx >= 0 and selected_idx < len(recent_emojis):
                                emoji = recent_emojis[selected_idx]
                                QTimer.singleShot(0, lambda e=emoji: self.insert_emoji(e))
                                return True
                        
                        sel = getattr(self, '_selected_content', None)

                        def _safe_copy(c):
                            try:
                                self.copy_and_close(c)
                            except Exception as e:
                                print(f"ERROR: copy_and_close failed: {e}")

                        if sel is not None:
                            try:
                                for w in self.get_visible_clip_widgets():
                                    try:
                                        if getattr(w, 'content', None) == sel:
                                            if os.environ.get('PETRA_DEBUG_KEYS'):
                                                print(f"[petra-debug] Enter triggered copy of selected content: {sel}")
                                            QTimer.singleShot(0, lambda c=sel: _safe_copy(c))
                                            return True
                                    except Exception:
                                        pass
                            except Exception:
                                pass

                        for w in self.get_visible_clip_widgets():
                            try:
                                if w.property('selected') == 'true':
                                    content = getattr(w, 'content', None)
                                    if content is not None:
                                        if os.environ.get('PETRA_DEBUG_KEYS'):
                                            print(f"[petra-debug] scheduling copy of content (len={len(str(content))})")
                                        QTimer.singleShot(0, lambda c=content: _safe_copy(c))
                                        return True
                            except Exception:
                                pass
                    except Exception:
                        pass

                if k == Qt.Key.Key_Left:
                    QTimer.singleShot(0, self.switch_filter_left)
                    return True
                if k == Qt.Key.Key_Right:
                    QTimer.singleShot(0, self.switch_filter_right)
                    return True
                if k == Qt.Key.Key_Up:
                    QTimer.singleShot(0, self.navigate_up)
                    return True
                if k == Qt.Key.Key_Down:
                    QTimer.singleShot(0, self.navigate_down)
                    return True

            # handle key releases (needed for Q/W hold semantics)
            if event.type() == QEvent.Type.KeyRelease:
                try:
                    k = event.key()
                    try:
                        if hasattr(event, 'isAutoRepeat') and event.isAutoRepeat():
                            is_repeat = True
                        else:
                            is_repeat = False
                    except Exception:
                        is_repeat = False

                    focus = QApplication.focusWidget()
                    if hasattr(self, 'search_bar') and focus is self.search_bar:
                        if hasattr(super(), "eventFilter"):
                            return super().eventFilter(obj, event)
                        return False

                    if k == Qt.Key.Key_Q:
                        if not is_repeat and getattr(self, '_key_q_down', False):
                            self._key_q_down = False
                            if hasattr(self, 'clear_btn') and self.clear_btn:
                                self.clear_btn.setDown(False)
                                self.cancel_clear_animation()
                                self.clear_btn.is_actively_pressed = False
                                self.clear_btn.setProgress(0)
                            return True

                    if k == Qt.Key.Key_W and not is_repeat:
                        if getattr(self, '_key_w_down', False):
                            self._key_w_down = False
                            if hasattr(self, 'pin_window_btn') and self.pin_window_btn:
                                self.pin_window_btn.setDown(False)
                                self.toggle_window_pin()
                            return True
                except Exception:
                    pass
        except Exception:
            pass
        finally:
            try:
                self._handling_key = False
            except Exception:
                pass

        if hasattr(super(), "eventFilter"):
            return super().eventFilter(obj, event)
        return False

    def get_visible_clip_widgets(self):
        """Return a list of ClipItem widgets currently shown (top to bottom)."""
        widgets = []
        try:
            count = self.content_layout.count()
            last = max(0, count - 1)
            for i in range(last):
                item = self.content_layout.itemAt(i)
                if not item:
                    continue
                container = item.widget()
                if container is None:
                    continue
                clip = container.findChild(ClipItem)
                if clip:
                    widgets.append(clip)
        except Exception:
            pass
        return widgets

    def _set_selected_clip_widget(self, clip_widget):
        try:
            for w in list(self.get_visible_clip_widgets()):
                try:
                    if w is clip_widget:
                        w.setProperty('selected', 'true')
                        try:
                            w.setProperty('hover', 'true')
                        except Exception:
                            pass
                        try:
                            self._selected_content = getattr(w, 'content', None)
                        except Exception:
                            pass
                    else:
                        w.setProperty('selected', 'false')
                        try:
                            w.setProperty('hover', 'false')
                        except Exception:
                            pass
                    w.style().unpolish(w)
                    w.style().polish(w)
                    try:
                        if hasattr(w, '_update_background'):
                            w._update_background()
                    except Exception:
                        pass
                except Exception:
                    pass
        except Exception:
            pass

    def navigate_up(self):
        if not getattr(self, 'isVisible', None) or not self.isVisible():
            return

        if getattr(self, 'current_filter', None) == 'emoji':
            self._navigate_recent_emojis(-1)
            return

        try:
            visible = list(self.get_visible_clip_widgets())
        except Exception:
            visible = []
        if not visible:
            return

        current = None
        for i, w in enumerate(visible):
            if w.property('selected') == 'true':
                current = i
                break

        if current is None:
            new = len(visible) - 1
        else:
            new = (current - 1) if current > 0 else len(visible) - 1

        target = visible[new]
        try:
            container = target.parentWidget()
            if hasattr(self, 'scroll_area') and self.scroll_area:
                self.scroll_area.ensureWidgetVisible(container)
        except Exception:
            pass

        self._set_selected_clip_widget(target)

    def navigate_down(self):
        if not getattr(self, 'isVisible', None) or not self.isVisible():
            return

        if getattr(self, 'current_filter', None) == 'emoji':
            self._navigate_recent_emojis(1)
            return

        try:
            visible = list(self.get_visible_clip_widgets())
        except Exception:
            visible = []
        if not visible:
            return

        current = None
        for i, w in enumerate(visible):
            if w.property('selected') == 'true':
                current = i
                break

        if current is None:
            new = 0
        else:
            new = (current + 1) if current < len(visible) - 1 else 0

        target = visible[new]
        try:
            container = target.parentWidget()
            if hasattr(self, 'scroll_area') and self.scroll_area:
                self.scroll_area.ensureWidgetVisible(container)
        except Exception:
            pass

        self._set_selected_clip_widget(target)

    def switch_filter_left(self):
        try:
            if not getattr(self, 'isVisible', None) or not self.isVisible():
                return
            filters = list(self.filter_buttons.keys())
            current_index = filters.index(self.current_filter) if self.current_filter in filters else 0
            new_index = (current_index - 1) % len(filters)
            self.set_filter(filters[new_index])
            self._clear_clip_selection()
        except Exception:
            pass

    def switch_filter_right(self):
        try:
            if not getattr(self, 'isVisible', None) or not self.isVisible():
                return
            filters = list(self.filter_buttons.keys())
            current_index = filters.index(self.current_filter) if self.current_filter in filters else 0
            new_index = (current_index + 1) % len(filters)
            self.set_filter(filters[new_index])
            self._clear_clip_selection()
        except Exception:
            pass

    def _clear_clip_selection(self):
        """Clear any currently selected clip widget."""
        try:
            self._selected_content = None
            for w in self.get_visible_clip_widgets():
                try:
                    w.setProperty('selected', 'false')
                    w.setProperty('hover', 'false')
                    w.style().unpolish(w)
                    w.style().polish(w)
                    if hasattr(w, '_update_background'):
                        w._update_background()
                except Exception:
                    pass
        except Exception:
            pass
