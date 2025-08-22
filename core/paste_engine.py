# -*- coding: utf-8 -*-
from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from PyQt6.QtGui import QGuiApplication, QImage
from PyQt6.QtCore import QMimeData, QUrl
import pyautogui, json, time
from .platform_utils import paste_hotkey

class _PasteWorker(QThread):
    done = pyqtSignal(int)
    fail = pyqtSignal(int, str)

    def __init__(self, item_id: int, setter, interval_ms: int, parent=None):
        super().__init__(parent)
        self.item_id = item_id
        self.setter = setter
        self.interval_ms = interval_ms

    def run(self):
        try:
            self.setter()
            time.sleep(self.interval_ms/1000.0)
            mod, key = paste_hotkey()
            pyautogui.hotkey(mod, key)
            self.done.emit(self.item_id)
        except Exception as e:
            self.fail.emit(self.item_id, str(e))

class PasteEngine(QObject):
    paste_done = pyqtSignal(int)        # item_id
    paste_failed = pyqtSignal(int, str) # item_id, message

    def __init__(self, settings, storage, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.storage = storage

    def _launch(self, item_id: int, setter):
        w = _PasteWorker(item_id, setter, self.settings.min_interval_ms, self)
        w.done.connect(self.paste_done)
        w.fail.connect(self.paste_failed)
        w.start()

    def paste_text(self, item_id: int, text: str):
        def setter():
            cb = QGuiApplication.clipboard()
            md = QMimeData(); md.setText(text)
            cb.setMimeData(md)
            QGuiApplication.processEvents()
        self._launch(item_id, setter)

    def paste_image(self, item_id: int, image_path: str):
        def setter():
            cb = QGuiApplication.clipboard()
            img = QImage(image_path)
            md = QMimeData(); md.setImageData(img)
            cb.setMimeData(md)
            QGuiApplication.processEvents()
        self._launch(item_id, setter)

    def paste_files(self, item_id: int, paths: list[str]):
        def setter():
            cb = QGuiApplication.clipboard()
            md = QMimeData()
            md.setUrls([QUrl.fromLocalFile(p) for p in paths])
            cb.setMimeData(md)
            QGuiApplication.processEvents()
        self._launch(item_id, setter)
