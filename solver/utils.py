from itertools import product

def pairs_exclude_diagonal(it):
    # We make a copy here as a common use case is to pass the same
    # iterator twice.
    for x, y in product(it, repeat=2):
        if x != y:
            yield (x, y)

def unzip(lst):
    return zip(*lst)

def all_empty(dict_of_sets):
    return all(s == set() for s in dict_of_sets.values())
