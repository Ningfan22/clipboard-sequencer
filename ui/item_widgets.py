# -*- coding: utf-8 -*-
from __future__ import annotations
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt

class ListItemWidget(QWidget):
    """
    队列/收藏条目卡片：
      - 左侧：文本
      - 右侧：⭐/☆（收藏） + ×（删除）
    规则：
      - 队列视图：未收藏默认不显示星标；悬停时显示“☆”可点收藏。
      - 收藏视图：始终显示“★”并可取消。
      - 已用(status='used')：整体灰化，但仍可选/可粘贴。
    """
    def __init__(self, text: str, is_used: bool, is_fav: bool,
                 on_toggle_fav, on_delete, show_star_when_unfav_hover: bool=True, parent=None):
        super().__init__(parent)
        self._text = text or ""
        self._is_used = is_used
        self._is_fav = is_fav
        self._on_toggle_fav = on_toggle_fav
        self._on_delete = on_delete
        self._hover_star = show_star_when_unfav_hover

        lay = QHBoxLayout(self); lay.setContentsMargins(12,8,12,8); lay.setSpacing(10)
        self.lbl = QLabel(self._text); self.lbl.setWordWrap(False)
        self.btn_star = QPushButton("★" if self._is_fav else "☆")
        self.btn_star.setFixedWidth(30); self.btn_star.setFlat(True)
        self.btn_close = QPushButton("×"); self.btn_close.setFixedWidth(28); self.btn_close.setFlat(True)

        lay.addWidget(self.lbl, 1, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.btn_star, 0, Qt.AlignmentFlag.AlignVCenter)
        lay.addWidget(self.btn_close, 0, Qt.AlignmentFlag.AlignVCenter)

        # style
        self._apply_style()

        # 交互
        self.btn_star.clicked.connect(self._toggle_fav)
        self.btn_close.clicked.connect(lambda: self._on_delete())

        # 未收藏时在队列页默认隐藏星（悬停显示）
        if not self._is_fav and self._hover_star:
            self.btn_star.setVisible(False)

    def _apply_style(self):
        if self._is_used:
            # 灰化样式
            self.setStyleSheet("""
            QWidget { background:#5a5a5a; border-radius:16px; }
            QLabel { color:#cfcfcf; font-weight:600; }
            QPushButton { color:#cfcfcf; border:none; }
            QPushButton:hover { color:#ffffff; }
            """)
        else:
            self.setStyleSheet("""
            QWidget { background:#d0d0d0; border-radius:16px; }
            QLabel { color:#222; font-weight:700; }
            QPushButton { color:%s; border:none; }
            QPushButton:hover { color:#111; }
            """ % ("#f5b301" if self._is_fav else "#8a8a8a"))

    def _toggle_fav(self):
        self._is_fav = not self._is_fav
        self.btn_star.setText("★" if self._is_fav else "☆")
        self._apply_style()
        if self._on_toggle_fav:
            self._on_toggle_fav(self._is_fav)

    # 悬停显示“☆”
    def enterEvent(self, e):
        if (not self._is_fav) and self._hover_star:
            self.btn_star.setVisible(True)
        return super().enterEvent(e)

    def leaveEvent(self, e):
        if (not self._is_fav) and self._hover_star:
            self.btn_star.setVisible(False)
        return super().leaveEvent(e)
