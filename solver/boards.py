import json
from itertools import product, chain

class Board:
    """Base class for board objects.

    Contains methods commonly useful for dealing with a 9 by 9 array of
    objects - as of now, various methods for iteration.
    """
    def iter_board(self):
        for i, j in product(range(9), range(9)):
            yield (i, j), self[(i, j)]

    def iter_row(self, row):
        for j in range(9):
            yield (row, j), self[(row, j)]

    def iter_column(self, column):
        for i in range(9):
            yield (i, column), self[(i, column)]

    def iter_box(self, box):
        for i in range(3*box[0], 3*box[0] + 3):
            for j in range(3*box[1], 3*box[1] + 3):
                yield (i, j), self[(i, j)]

    def iter_row_containing(self, coords):
        row = coords[0]
        yield from self.iter_row(row)

    def iter_column_containing(self, coords):
        column = coords[1]
        yield from self.iter_column(column)

    def iter_box_containing(self, coords):
        box_containing = (coords[0] // 3, coords[1] // 3)
        yield from self.iter_box(box_containing)

    def __getitem__(self, coords):
        return self.data[coords]


class GameBoard(Board):
    """Class for representing a sudoku game board.

    A 9 by 9 array. Each entry can be a number between 1-9 inclusive, or None,
    signaling no entry.

    The data is stored in a dictionary, keys are tuples (i, j) in 1-9
    inclusive, and values are either a number 1-9 inclusive, or None.
    """
    def __init__(self):
        self.data = {
            (i, j): None for i in range(9) for j in range(9)
        }
        self.level = None
        self.id = None

    def __setitem__(self, coords, number):
        self.data[coords] = number

    @classmethod
    def from_json(cls, jsn):
        """Read from a json representation.

        Json representations are pulled from websudoku.com, for a discussion of
        the structure, see the from_dict method.
        """
        dct = json.loads(jsn)
        return cls.from_dict(dct)

    @classmethod
    def from_dict(cls, dct):
        """Read from a dictionary representation.

        Dictionary representations are pulled from websudoku.com, so the
        representation here is the one used on that site. Json has the
        following structure:

          - puzzle: An 81 entry array containing the full solution to the
            puzzle in row major order.
          - mask: An 81 entry binary array indicating which entrys are masked
            out in the initial state of the puzzle.
          - level: The difficulty level of the puzzle, according to
            websudoku.com.
          - id: The unique identifier of the puzzle on websudoku.com.
        """
        board = cls()
        for ij, (mask_bit, num) in enumerate(zip(dct['mask'], dct['puzzle'])):
            i, j = ij // 9, ij % 9
            if mask_bit == '1':
                board[(i, j)] = int(num)
        board.level = int(dct['level'])
        board.id = dct['id']
        return board

    def __str__(self):
        """Construct a string for pretty printing the game board."""
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


class MarkedBoard(Board):
    """Class for representing a marked up game board.

    MarkedBoard is the main abstraction used to track information when solving
    a puzzle. A MarkedBoard is a 9 by 9 grid, with each entry (cell) consisting
    of a subset of {1, 2, 3, 4, 5, 6, 7, 8, 9}. A mark is an element in one of
    these subsets, and its presense indicates that the given number *cannot* be
    placed in that cell in the solution to the puzzle.
    """
    all_marks = {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def __init__(self):
        self.data = {
            (i, j): set() for i in range(9) for j in range(9)
        }
        self.level = None
        self.id = None

    @classmethod
    def from_game_board(cls, game_board):
        """
        Add all marks that are a consequence of the current state of a game
        board.  I.e. add marks in every row, column, and box containing some
        entry.
        """
        board = cls()
        for coords, number in game_board.iter_board():
            if number != None:
                board.add_marks_from_placed_number(coords, number)
        return board

    def add_marks_from_placed_number(self, coords, entry):
        self.data[coords] = self.all_marks
        placements = chain(self.iter_row_containing(coords),
                           self.iter_column_containing(coords),
                           self.iter_box_containing(coords))
        for (i, j), marks in placements:
            marks.add(entry)

    def marks_for_number(self, number):
        """
        Create a string for pretty printing all the marks corresponding to a
        given number.
        """
        h_seperator = "+---+---+---+"
        h_line = "|{}{}{}|{}{}{}|{}{}{}|"
        s = ""
        for i in range(9):
            if i % 3 == 0:
                s += h_seperator + '\n'
            row_tuple = tuple('*' if number in marks else ' '
                              for _, marks in self.iter_row(i))
            s += h_line.format(*row_tuple) + '\n'
        s += h_seperator
        return s


class Box:

    def __init__(self, board, box_coords):
        self.board = board
        self.box_coords = box_coords

    def __getitem__(self, coords):
        return self.board[(
            3*self.box_coords[0] + coords[0],
            3*self.box_coords[1] + coords[1] 
        )]
