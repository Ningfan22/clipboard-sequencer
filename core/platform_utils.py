# -*- coding: utf-8 -*-
import sys

def paste_hotkey() -> tuple[str, str]:
    if sys.platform == "darwin":
        return ("command", "v")
    return ("ctrl", "v")
