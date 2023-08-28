from typing import TypeVar

T = TypeVar('T')

def flatten(a: list[list[T]]) -> list[T]:
    res = []
    for i in a:
        res.extend(i)
    return res
