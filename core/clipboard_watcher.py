# -*- coding: utf-8 -*-
from __future__ import annotations
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QGuiApplication
from . import storage
import os, uuid

class ClipboardWatcher(QObject):
    item_captured = pyqtSignal(int)
    status_changed = pyqtSignal(bool)

    def __init__(self, settings, queue_manager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.queue = queue_manager
        self.enabled = True
        self._ignore_until = 0  # ms
        self.cb = QGuiApplication.clipboard()
        self.cb.dataChanged.connect(self.on_changed)

    def set_enabled(self, b: bool):
        self.enabled = b
        self.status_changed.emit(b)

    def ignore_for(self, ms: int):
        import time
        self._ignore_until = int(time.time()*1000) + ms

    def on_changed(self):
        import time
        if not self.enabled:
            return
        if int(time.time()*1000) < self._ignore_until:
            return
        mime = self.cb.mimeData()
        if mime is None:
            return
        # files (urls)
        if mime.hasUrls():
            paths = [u.toLocalFile() for u in mime.urls() if u.isLocalFile()]
            if paths:
                item_id = self.queue.add_files(paths)
                self.item_captured.emit(item_id); return
        # image
        if mime.hasImage():
            image = self.cb.image()
            if not image.isNull():
                img_dir = storage.cache_img_dir()
                name = f"{uuid.uuid4().hex}.png"
                path = os.path.join(img_dir, name)
                image.save(path, "PNG")
                item_id = self.queue.add_image(path)
                self.item_captured.emit(item_id); return
        # text
        if mime.hasText():
            text = mime.text()
            item_id = self.queue.add_text(text)
            if item_id != -1:
                self.item_captured.emit(item_id)
