# coding: utf-8
from typing import Generic, TypeVar

from pydantic import BaseModel

TItem = TypeVar("TItem", bound=BaseModel)


def offset_for_page(page: int, page_size: int) -> int:
    """1-based 页码转为 SQL LIMIT/OFFSET 用的 offset。"""
    return (page - 1) * page_size


class PaginatedDTO(BaseModel, Generic[TItem]):
    items: list[TItem]
    total: int
    page: int
    page_size: int
