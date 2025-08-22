# -*- coding: utf-8 -*-
from __future__ import annotations
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QCheckBox,
    QLineEdit, QPushButton
)
from core import settings as settings_mod

class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("设置")
        self.setMinimumWidth(420)
        self.s = settings_mod.load_settings()

        lay = QVBoxLayout(self)

        # 重复策略
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("重复策略："))
        self.cmb_dup = QComboBox()
        self.cmb_dup.addItems(["count(相同合并×N)", "separate(分开存放)"])
        self.cmb_dup.setCurrentIndex(0 if self.s.duplicate_policy=="count" else 1)
        row1.addWidget(self.cmb_dup); lay.addLayout(row1)

        # 出队策略（粘贴后变灰）
        self.chk_dequeue = QCheckBox("粘贴后标记为已用（变灰）")
        self.chk_dequeue.setChecked(self.s.dequeue_on_paste)
        lay.addWidget(self.chk_dequeue)

        # Paste All
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Paste All 文本处理："))
        self.cmb_pmall = QComboBox()
        self.cmb_pmall.addItems(["merge(合并一段)", "step(逐条)"])
        self.cmb_pmall.setCurrentIndex(0 if self.s.paste_all_text_mode=="merge" else 1)
        row2.addWidget(self.cmb_pmall); lay.addLayout(row2)

        # 拼接规则
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("拼接规则："))
        self.cmb_join = QComboBox()
        self.cmb_join.addItems(["cjk(中日韩)", "english(英文)", "custom(自定义分隔)"])
        idx = {"cjk":0,"english":1,"custom":2}[self.s.joiner_mode]
        self.cmb_join.setCurrentIndex(idx)
        row3.addWidget(self.cmb_join)
        self.txt_sep = QLineEdit(self.s.joiner_custom_sep or "")
        self.txt_sep.setPlaceholderText("自定义分隔符，例如：, 或 空格")
        row3.addWidget(self.txt_sep); lay.addLayout(row3)

        # interval
        row4 = QHBoxLayout()
        row4.addWidget(QLabel("最小粘贴间隔(ms)："))
        self.txt_ms = QLineEdit(str(self.s.min_interval_ms))
        row4.addWidget(self.txt_ms); lay.addLayout(row4)

        # buttons
        btns = QHBoxLayout()
        btn_ok = QPushButton("保存")
        btn_cancel = QPushButton("取消")
        btns.addStretch(1); btns.addWidget(btn_ok); btns.addWidget(btn_cancel)
        lay.addLayout(btns)

        btn_ok.clicked.connect(self.save_and_close)
        btn_cancel.clicked.connect(self.reject)

    def save_and_close(self):
        # 重复策略
        self.s.duplicate_policy = "count" if self.cmb_dup.currentIndex()==0 else "separate"
        # 出队策略
        self.s.dequeue_on_paste = self.chk_dequeue.isChecked()
        # Paste All
        self.s.paste_all_text_mode = "merge" if self.cmb_pmall.currentIndex()==0 else "step"
        # 拼接
        self.s.joiner_mode = {0:"cjk",1:"english",2:"custom"}[self.cmb_join.currentIndex()]
        self.s.joiner_custom_sep = self.txt_sep.text()
        # 间隔
        try:
            self.s.min_interval_ms = max(60, int(self.txt_ms.text()))
        except:
            pass
        settings_mod.save_settings(self.s)
        self.accept()
