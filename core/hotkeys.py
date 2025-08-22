# -*- coding: utf-8 -*-
import keyboard
from PyQt6.QtCore import QObject

class Hotkeys(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)

    def register(self, seq: str, callback):
        keyboard.add_hotkey(seq, callback, suppress=False)

    def unregister_all(self):
        keyboard.unhook_all_hotkeys()