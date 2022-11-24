from itertools import product


def pairs_exclude_diagonal(it):
    for x, y in product(it, repeat=2):
        if x != y:
            yield (x, y)


def iter_number_pairs():
    for i in range(9):
        for j in range(i + 1, 9):
            yield (i, j)


def unzip(lst):
    return zip(*lst)


def all_empty(dict_of_sets):
    return all(s == set() for s in dict_of_sets.values())
