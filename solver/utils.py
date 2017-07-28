from itertools import product

def pairs_exclude_diagonal(it):
    # We make a copy here as a common use case is to pass the same
    # iterator twice.
    for x, y in product(it, repeat=2):
        if x != y:
            yield (x, y)

def unzip(lst):
    return zip(*lst)
