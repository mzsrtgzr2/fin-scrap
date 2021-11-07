from typing import *
from itertools import chain

def is_non_empty_iterator(iterable: Iterable) -> Tuple[bool, Iterable]:
    it = iter(iterable)
    try:
        item = next(it)
    except StopIteration:
        return False, iter([])

    return True, chain([item], it)