import json
from itertools import product, chain

class Board:

    def iter_board(self):
        for i, j in product(range(9), range(9)):
            yield (i, j), self.data[(i, j)]

    def iter_row(self, row):
        for j in range(9):
            yield (row, j), self.data[(row, j)]

    def iter_column(self, column):
        for i in range(9):
            yield (i, column), self.data[(i, column)]

    def iter_box(self, box):
        for i in range(3*box[0], 3*box[0] + 3):
            for j in range(3*box[1], 3*box[1] + 3):
                yield (i, j), self.data[(i, j)]

    def iter_row_containing(self, coords):
        row = coords[0]
        yield from self.iter_row(row)

    def iter_column_containing(self, coords):
        column = coords[1]
        yield from self.iter_column(column)

    def iter_box_containing(self, coords):
        box_containing = (coords[0] // 3, coords[1] // 3)
        yield from self.iter_box(box_containing)


class GameBoard(Board):

    def __init__(self):
        self.data = {
            (i, j): None for i in range(9) for j in range(9)
        }
        self.level = None
        self.id = None

    @classmethod
    def read_from_json(cls, jsn):
        board = cls()
        data = json.loads(jsn)
        for ij, (mask_bit, num) in enumerate(zip(data['mask'], data['puzzle'])):
            i, j = ij // 9, ij % 9
            if mask_bit == '1':
                board.data[(i, j)] = int(num)
        board.level = int(data['level'])
        board.id = data['id']
        return board

    def __str__(self):
        h_seperator = "+---+---+---+"
        h_line = "|{}{}{}|{}{}{}|{}{}{}|"
        s = ""
        for i in range(9):
            if i % 3 == 0:
                s += h_seperator + '\n'
            row_tuple = tuple(num if num else ' ' for _, num in self.iter_row(i))
            s += h_line.format(*row_tuple) + '\n'
        s += h_seperator
        return s


def MarkedBoard(Board):

    def __init__(self):
        self.data = {
            (i, j): set() for i in range(9) for j in range(9)
        }
        self.level = None
        self.id = None

    @classmethod
    def from_game_board(cls, game_board):
        

