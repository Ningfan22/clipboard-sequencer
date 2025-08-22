# -*- coding: utf-8 -*-
from __future__ import annotations
from . import storage

class QueueManager:
    def __init__(self, settings):
        self.settings = settings

    # add
    def add_text(self, text: str) -> int:
        text = (text or "").strip()
        if not text:
            return -1
        return storage.add_text_item(text, self.settings.duplicate_policy)

    def add_image(self, path: str) -> int:
        return storage.add_image_item(path)

    def add_files(self, paths: list[str]) -> int:
        return storage.add_files_item(paths)

    # list
    def list_all(self, limit=500):
        return storage.list_items_all(limit=limit)

    def list_favorites(self, limit=500):
        return storage.list_favorites(limit=limit)

    # status
    def mark_used(self, item_id: int):
        storage.set_item_used(item_id)

    def mark_active(self, item_id: int):
        storage.set_item_active(item_id)

    # delete
    def delete(self, ids: list[int]):
        storage.delete_items(ids)

    # favorites
    def set_favorite(self, item_id: int, fav: bool):
        storage.set_favorite(item_id, fav)

    def is_favorite(self, item_id: int) -> bool:
        return storage.is_favorite(item_id)
