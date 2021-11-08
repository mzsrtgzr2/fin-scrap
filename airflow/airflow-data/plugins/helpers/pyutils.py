from typing import *
from itertools import chain, islice, chain

def batches(iterable, size):
    sourceiter = iter(iterable)
    while True:
        batchiter = islice(sourceiter, size)
        yield chain([batchiter.next()], batchiter)

def is_non_empty_iterator(iterable: Iterable) -> Tuple[bool, Iterable]:
    it = iter(iterable)
    try:
        item = next(it)
    except StopIteration:
        return False, iter([])

    return True, chain([item], it)