# coding: utf-8


def optional_search(s: str | None) -> str | None:
    """将可选查询串规范为 None 或非空 strip 后的 str（用于可选过滤条件）。"""
    if s is None:
        return None
    s = s.strip()
    return s if s else None
