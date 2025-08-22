# -*- coding: utf-8 -*-
import re
from typing import Literal

def join_texts(parts: list[str], mode: Literal['cjk','english','custom']='cjk', custom_sep: str='') -> str:
    if not parts:
        return ""
    parts = [p.strip() for p in parts if p is not None]
    if mode == 'custom':
        return custom_sep.join(parts)
    if mode == 'english':
        return _join_english(parts)
    return _join_cjk(parts)

def _join_english(parts: list[str]) -> str:
    s = " ".join(parts)
    s = re.sub(r"\s+([,\.\!\?])", r"\1", s)      # remove space before punct
    s = re.sub(r"([,\.\!\?])(\w)", r"\1 \2", s)  # ensure space after punct
    return s

def _is_cjk(ch: str) -> bool:
    return any([
        "\u4e00" <= ch <= "\u9fff",   # CJK Unified Ideographs
        "\u3040" <= ch <= "\u30ff",   # JP Hiragana & Katakana
        "\uac00" <= ch <= "\ud7af",   # Hangul
    ])

def _join_cjk(parts: list[str]) -> str:
    out = []
    prev_last = ""
    for p in parts:
        if not out:
            out.append(p)
        else:
            a = prev_last[-1] if prev_last else ""
            b = p[0] if p else ""
            if (a and _is_cjk(a)) and (b and _is_cjk(b)):
                out.append(p)               # CJK-CJK: no space
            elif (a and _is_cjk(a)) and (b and not _is_cjk(b)):
                out.append(" " + p)         # CJK -> Latin: space
            elif (a and not _is_cjk(a)) and (b and _is_cjk(b)):
                out.append(" " + p)         # Latin -> CJK: space
            else:
                out.append(" " + p)         # Latin -> Latin: space
        prev_last = p[-1] if p else ""
    s = "".join(out)
    s = re.sub(r"\s+([，。！？；：、])", r"\1", s)  # no spaces before CJK punct
    return s
