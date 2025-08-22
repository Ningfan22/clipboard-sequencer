# -*- coding: utf-8 -*-
from __future__ import annotations
import json, time
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QLabel, QStatusBar, QApplication, QMessageBox,
    QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QGuiApplication, QKeySequence

from core import storage, settings as settings_mod, text_joiner
from core.queue_manager import QueueManager
from core.clipboard_watcher import ClipboardWatcher
from core.paste_engine import PasteEngine
from core.hotkeys import Hotkeys
from ui.item_widgets import ListItemWidget
from ui.settings_dialog import SettingsDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Clipboard Sequencer")
        self.resize(980, 680)

        self.settings = settings_mod.load_settings()
        storage.init_db()
        self.queue = QueueManager(self.settings)

        # ---------- 基础框架 ----------
        root = QWidget(); self.setCentralWidget(root)
        root_lay = QVBoxLayout(root); root_lay.setContentsMargins(16,16,16,16); root_lay.setSpacing(10)

        # 顶部工具条（菜单/刷新/图钉）
        top = QHBoxLayout()
        self.btn_menu = QPushButton("≡"); self.btn_menu.setFixedWidth(40)
        self.btn_refresh = QPushButton("⟳"); self.btn_refresh.setFixedWidth(40)
        self.btn_pin = QPushButton("📌"); self.btn_pin.setFixedWidth(40); self.btn_pin.setCheckable(True)
        top.addStretch(1); top.addWidget(self.btn_menu); top.addWidget(self.btn_refresh); top.addWidget(self.btn_pin)
        root_lay.addLayout(top)

        # 虚线内容框 + 页面栈
        self.stack = QStackedWidget()
        # 队列页
        self.page_queue = QWidget(); pq_lay = QVBoxLayout(self.page_queue)
        self.lbl_queue = QLabel("队列（已用会变灰，但仍可选择和粘贴）")
        self.list_queue = QListWidget(); self.list_queue.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        pq_lay.addWidget(self.lbl_queue); pq_lay.addWidget(self.list_queue, 1)
        # 收藏页
        self.page_fav = QWidget(); pf_lay = QVBoxLayout(self.page_fav)
        self.lbl_fav = QLabel("我的收藏")
        self.list_fav = QListWidget(); self.list_fav.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        pf_lay.addWidget(self.lbl_fav); pf_lay.addWidget(self.list_fav, 1)

        self.stack.addWidget(self.page_queue)  # index 0
        self.stack.addWidget(self.page_fav)    # index 1
        root_lay.addWidget(self.stack, 1)
        self.stack.setCurrentIndex(0)

        # 底部大按钮（导航）
        nav = QHBoxLayout()
        self.btn_to_queue = QPushButton("本 次 任 务")
        self.btn_to_fav = QPushButton("我 的 收 藏")
        nav.addWidget(self.btn_to_queue); nav.addWidget(self.btn_to_fav)
        root_lay.addLayout(nav)
        # Setting
        self.btn_setting = QPushButton("Setting")
        root_lay.addWidget(self.btn_setting)

        self.status = QStatusBar(); self.setStatusBar(self.status)
        self._apply_dark_style()
        self._status("Ready")

        # 引擎/监听
        self.paste_engine = PasteEngine(self.settings, storage)
        self.paste_engine.paste_done.connect(self.on_paste_done)
        self.paste_engine.paste_failed.connect(self.on_paste_failed)

        self.watcher = ClipboardWatcher(self.settings, self.queue)
        self.watcher.item_captured.connect(self.reload_current)
        self.watcher.status_changed.connect(lambda _: self._status("监听状态变更"))
        self.watcher.set_enabled(True)

        # 事件绑定
        self.btn_refresh.clicked.connect(self.reload_current)
        self.btn_pin.clicked.connect(self._toggle_always_on_top)
        self.btn_to_queue.clicked.connect(lambda: self._switch_page(0))
        self.btn_to_fav.clicked.connect(lambda: self._switch_page(1))
        self.btn_setting.clicked.connect(self.open_settings)

        # 键盘快捷键（窗口内）
        self._bind_shortcuts()

        # 全局热键（窗口不激活也能触发）
        self.global_hotkeys = Hotkeys(self)
        self.global_hotkeys.register("ctrl+shift+v", self.paste_next)
        self.global_hotkeys.register("ctrl+alt+v", self.paste_all)
        self.global_hotkeys.register("alt+\\", self._toggle_show_hide)

        # 列表键盘控制
        self.list_queue.keyPressEvent = self._list_keypress_wrapper(self.list_queue, source="queue")
        self.list_fav.keyPressEvent = self._list_keypress_wrapper(self.list_fav, source="fav")

        # 默认非置顶
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, False)
        self.show()

        self.reload_current()

    # ---------- 样式 ----------
    def _apply_dark_style(self):
        self.setStyleSheet("""
        * { font-family: "Segoe UI", "Microsoft YaHei", system-ui; }
        QMainWindow { background:#2b2b2b; }
        QLabel { color:#eaeaea; }
        QPushButton {
            background:#d9d9d9; color:#222; border:none; padding:10px 14px;
            border-radius:16px; font-weight:700;
        }
        QPushButton:hover { filter: brightness(0.96); }
        QPushButton:pressed { filter: brightness(0.9); }

        QListWidget {
            background:transparent; border:2px dashed #666; border-radius:16px;
            padding:8px;
        }
        QListWidget::item { margin:8px; padding:0px; }  /* 我们用自定义Widget，外层只需留白 */
        QListWidget::item:selected { outline:none; background:transparent; }
        """)

    # ---------- 基础方法 ----------
    def _bind_shortcuts(self):
        self._shortcut("Ctrl+Shift+V", self.paste_next)
        self._shortcut("Ctrl+Alt+V", self.paste_all)

    def _shortcut(self, seq: str, func):
        act = self.addAction(seq)
        act.setShortcut(QKeySequence(seq))
        act.triggered.connect(func)

    def _status(self, s: str):
        self.status.showMessage(s, 3000)

    def _switch_page(self, idx: int):
        self.stack.setCurrentIndex(idx)
        self.reload_current()

    def _toggle_always_on_top(self):
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, bool(self.btn_pin.isChecked()))
        self.show()

    def _toggle_show_hide(self):
        if self.isVisible(): self.hide()
        else: self.show()

    def _payload(self, row):
        return {
            "id": row[0], "session_id": row[1], "type": row[2],
            "text": row[3], "image_path": row[4], "paths_json": row[5],
            "count": row[6], "status": row[7], "pinned": bool(row[8]),
            "edited": bool(row[9]), "note": row[10],
            "created_at": row[11], "last_used_at": row[12],
        }

    # ---------- 加载列表 ----------
    def reload_current(self, *_):
        if self.stack.currentIndex() == 0:
            self.reload_queue()
        else:
            self.reload_fav()

    def reload_queue(self):
        self.list_queue.clear()
        for row in self.queue.list_all(limit=800):
            d = self._payload(row)
            is_fav = self.queue.is_favorite(d["id"])
            # 队列视图：未收藏默认不显示星（悬停显示）
            widget = ListItemWidget(
                text=self._fmt_text(d),
                is_used=(d["status"]=="used"),
                is_fav=is_fav,
                on_toggle_fav=lambda fav, _id=d["id"]: self.queue.set_favorite(_id, fav),
                on_delete=lambda _id=d["id"]: self._delete_queue_item(_id),
                show_star_when_unfav_hover=True
            )
            item = QListWidgetItem(); item.setData(Qt.ItemDataRole.UserRole, d)
            item.setSizeHint(widget.sizeHint())
            self.list_queue.addItem(item); self.list_queue.setItemWidget(item, widget)

    def reload_fav(self):
        self.list_fav.clear()
        for row in self.queue.list_favorites(limit=800):
            d = self._payload(row)
            # 收藏页：始终显示★，删除=从收藏移除（不删条目）
            widget = ListItemWidget(
                text=self._fmt_text(d),
                is_used=(d["status"]=="used"),
                is_fav=True,
                on_toggle_fav=lambda fav, _id=d["id"]: self.queue.set_favorite(_id, fav),
                on_delete=lambda _id=d["id"]: (self.queue.set_favorite(_id, False), self.reload_current()),
                show_star_when_unfav_hover=False
            )
            item = QListWidgetItem(); item.setData(Qt.ItemDataRole.UserRole, d)
            item.setSizeHint(widget.sizeHint())
            self.list_fav.addItem(item); self.list_fav.setItemWidget(item, widget)

    def _fmt_text(self, d):
        t = d["type"]; c = d["count"]
        if t == "text":
            base = d["text"] or ""
        elif t == "image":
            import os; base = f"[Image] {os.path.basename(d['image_path'] or '')}"
        else:
            try: arr = json.loads(d["paths_json"] or "[]")
            except: arr = []
            base = f"[Files] {len(arr)} items" if len(arr)!=1 else f"[File] {arr[0]}"
        if c and c>1: base += f" ×{c}"
        return base

    def _delete_queue_item(self, item_id: int):
        self.queue.delete([item_id])
        self.reload_current()

    # ---------- 粘贴 ----------
    def paste_next(self):
        lw = self._current_list()
        it = lw.currentItem() or (lw.item(0) if lw.count()>0 else None)
        if not it:
            self._status("队列为空"); return
        d = it.data(Qt.ItemDataRole.UserRole)
        self._paste_item(d)

    def paste_all(self):
        lw = self._current_list()
        parts_text, seq = [], []
        for i in range(lw.count()):
            d = lw.item(i).data(Qt.ItemDataRole.UserRole)
            if d["type"] == "text":
                if self.settings.paste_all_text_mode == "merge":
                    parts_text.append(d["text"] or ""); seq.append((d, "text-merge"))
                else:
                    seq.append((d, "text-step"))
            else:
                seq.append((d, d["type"]))

        if self.settings.paste_all_text_mode == "merge":
            text_blob = ""
            if parts_text:
                if self.settings.joiner_mode == "custom":
                    text_blob = text_joiner.join_texts(parts_text, "custom", self.settings.joiner_custom_sep)
                else:
                    text_blob = text_joiner.join_texts(parts_text, self.settings.joiner_mode)
            if text_blob:
                self.watcher.ignore_for(self.settings.min_interval_ms + 50)
                self.paste_engine.paste_text(-1, text_blob)
                QApplication.processEvents()
                time.sleep(self.settings.min_interval_ms/1000.0)
            for d, kind in seq:
                if d["type"] != "text":
                    self._paste_item(d, update_status=False)
        else:
            for d, kind in seq:
                self._paste_item(d, update_status=False)

    def _paste_item(self, d, update_status=True):
        # 去抖：避免我们设置剪贴板时被 watcher 误判为新复制
        self.watcher.ignore_for(self.settings.min_interval_ms + 50)
        if d["type"] == "text":
            self.paste_engine.paste_text(d["id"], d["text"] or "")
        elif d["type"] == "image":
            self.paste_engine.paste_image(d["id"], d["image_path"] or "")
        else:
            try: arr = json.loads(d["paths_json"] or "[]")
            except: arr = []
            self.paste_engine.paste_files(d["id"], arr)

    def on_paste_done(self, item_id: int):
        # item_id == -1 表示合并文本的 Paste All
        if item_id != -1 and self.settings.dequeue_on_paste:
            self.queue.mark_used(item_id)   # 仅标记为 used（灰），仍留在列表中
        self.reload_current()

    def on_paste_failed(self, item_id: int, msg: str):
        QMessageBox.warning(self, "Paste 失败", f"Item {item_id} 粘贴失败：{msg}")

    # ---------- 列表与键盘 ----------
    def _current_list(self) -> QListWidget:
        return self.list_queue if self.stack.currentIndex()==0 else self.list_fav

    def _list_keypress_wrapper(self, widget: QListWidget, source: str):
        def handler(event):
            key = event.key()
            ctrl = event.modifiers() & Qt.KeyboardModifier.ControlModifier
            if key in (Qt.Key.Key_Up, Qt.Key.Key_Down):
                return QListWidget.keyPressEvent(widget, event)
            if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                it = widget.currentItem()
                if not it: return
                d = it.data(Qt.ItemDataRole.UserRole)
                if ctrl:
                    self._paste_item(d)
                else:
                    cb = QGuiApplication.clipboard()
                    if d["type"] == "text":
                        cb.setText(d["text"] or "")
                    elif d["type"] == "image":
                        from PyQt6.QtGui import QImage; from PyQt6.QtCore import QMimeData
                        img = QImage(d["image_path"] or ""); md = QMimeData(); md.setImageData(img); cb.setMimeData(md)
                    else:
                        from PyQt6.QtCore import QMimeData, QUrl
                        md = QMimeData()
                        try: arr = json.loads(d["paths_json"] or "[]")
                        except: arr = []
                        md.setUrls([QUrl.fromLocalFile(p) for p in arr]); cb.setMimeData(md)
                return
            return QListWidget.keyPressEvent(widget, event)
        return handler

    # ---------- 设置 ----------
    def open_settings(self):
        dlg = SettingsDialog(self)
        if dlg.exec():
            # 重新加载设置后无需重启
            self.settings = settings_mod.load_settings()
            self._status("设置已保存")
