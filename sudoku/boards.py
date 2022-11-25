import json
from itertools import product, chain
from collections import defaultdict


from typing import Generic, TypeVar, Iterable, List, Optional, Dict, Tuple, Set


Coord = Tuple[int, int]
Row = int
Col = int
Box = Tuple[int, int]
Number = int
Marks = Set[Number]

NumberOrMarks = TypeVar('NumberOrMarks', Number, Marks)


# ABC
class Board:
    pass


class BoardIteratorComponent(Generic[NumberOrMarks]):
    """Base class for board objects.

    Contains methods commonly useful for dealing with a 9 by 9 array of
    objects - as of now, various methods for iteration.
    """
    def __init__(self, board: Board):
        self._board = board

    def iter_board(self) -> Iterable[Tuple[Coord, NumberOrMarks]]:
        for i, j in product(range(9), range(9)):
            yield (i, j), self._board[(i, j)]

    def iter_row(self, row: Row) -> Iterable[Tuple[Coord, NumberOrMarks]]:
        for j in range(9):
            yield (row, j), self._board[(row, j)]

    def iter_column(self, column: Col) -> Iterable[Tuple[Coord, NumberOrMarks]]:
        for i in range(9):
            yield (i, column), self._board[(i, column)]

    def iter_box(self, box: Box) -> Iterable[Tuple[Coord, NumberOrMarks]]:
        for i in range(3 * box[0], 3 * box[0] + 3):
            for j in range(3 * box[1], 3 * box[1] + 3):
                yield (i, j), self._board[(i, j)]

    def iter_row_containing(self, coords: Coord) -> Iterable[Tuple[Coord, NumberOrMarks]]:
        row = coords[0]
        yield from self.iter_row(row)

    def iter_column_containing(self, coords: Coord) -> Iterable[Tuple[Coord, NumberOrMarks]]:
        column = coords[1]
        yield from self.iter_column(column)

    def iter_box_containing(self, coords: Coord) -> Iterable[Tuple[Coord, NumberOrMarks]]:
        box_containing = (coords[0] // 3, coords[1] // 3)
        yield from self.iter_box(box_containing)

    def iter_boxes_in_row(self, row: Row) -> Iterable[List[NumberOrMarks]]:
        row = [v for _, v in self.iter_row(row)]
        for i in range(3):
            yield row[3 * i : (3 * i + 3)]

    def iter_boxes_in_column(self, column: Col) -> Iterable[List[NumberOrMarks]]:
        column = [v for _, v in self.iter_column(column)]
        for j in range(3):
            yield column[3 * j : (3 * j + 3)]



class GameBoard(Board):
    """Class for representing a sudoku game board.

    A 9 by 9 array. Each entry can be a number between 1-9 inclusive, or None,
    signaling no entry.

    The data is stored in a dictionary, keys are tuples (i, j) in 1-9
    inclusive, and values are either a number 1-9 inclusive, or None.
    """
    def __init__(self):
        self.data = {(i, j): None for i in range(9) for j in range(9)}
        self.iter = BoardIteratorComponent[Number](self)

    def __setitem__(self, coords: Coord, number: Number):
        self.data[coords] = number

    def __getitem__(self, coords: Coord) -> Number:
        return self.data[coords]

    @classmethod
    def from_websudoku_json(cls, jsn) -> 'GameBoard':
        """Read from a json representation.

        Json representations are pulled from websudoku.com, for a discussion of
        the structure, see the from_dict method.
        """
        dct = json.loads(jsn)
        return cls.from_dict(dct)

    @classmethod
    def from_websudoku_dict(cls, dct) -> 'GameBoard':
        """Read from a dictionary representation.

        Dictionary representations are pulled from websudoku.com, so the
        representation here is the one used on that site. Json has the
        following structure:

          - puzzle: An 81 entry array containing the full solution to the
            puzzle in row major order.
          - mask: An 81 entry binary array indicating which entrys are masked
            out in the initial state of the puzzle.
        """
        board = cls()
        for ij, (mask_bit, num) in enumerate(zip(dct["mask"], dct["puzzle"])):
            i, j = ij // 9, ij % 9
            if mask_bit == "0":
                board[(i, j)] = int(num)
        return board

    @classmethod
    def from_color_string(cls, s: str) -> 'GameBoard':
        colors = "ROYGgBbPp"
        board = cls()
        for ij, ch in enumerate(s.replace(" ", "")):
            i, j = ij // 9, ij % 9
            try:
                number = colors.index(ch) + 1
            except ValueError:
                continue
            board[(i, j)] = number
        return board

    def __str__(self) -> str:
        """Construct a string for pretty printing the game board."""
        h_seperator = "+---+---+---+"
        h_line = "|{}{}{}|{}{}{}|{}{}{}|"
        s = ""
        for i in range(9):
            if i % 3 == 0:
                s += h_seperator + "\n"
            row_tuple = tuple(num if num else " " for _, num in self.iter_row(i))
            s += h_line.format(*row_tuple) + "\n"
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

    all_marks: Marks = {1, 2, 3, 4, 5, 6, 7, 8, 9}

    def __init__(self):
        self.data = {(i, j): set() for i in range(9) for j in range(9)}
        self.iter = BoardIteratorComponent[Marks](self)

    def __setitem__(self, coords: Coord, marks: Marks):
        self.data[coords] = marks

    def __getitem__(self, coords: Coord) -> Marks:
        return self.data[coords]

    @classmethod
    def from_game_board(cls, game_board: GameBoard) -> 'MarkedBoard':
        """
        Add all marks that are a consequence of the current state of a game
        board.  I.e. add marks in every row, column, and box containing some
        entry.
        """
        board = cls()
        for coords, number in game_board.iter.iter_board():
            if number != None:
                board.add_marks_from_placed_number(coords, number)
        return board

    def add_marks(self, new_marks: Dict[Coord, Marks]):
        for coords, marks in new_marks.items():
            self[coords].update(marks)

    def add_marks_from_placed_number(self, coords: Coord, number: Number):
        new_marks = self.compute_marks_from_placed_number(coords, number)
        self.add_marks(new_marks)

    def compute_marks_from_placed_number(self, coords: Coord, number: Number) -> Dict[Coord, Marks]:
        new_marks: Dict[Coord, Marks] = defaultdict(set)
        # Solved positions in a marked board are notated by adding all possible
        # marks.
        new_marks[coords] = self.all_marks
        placements = chain(
            self.iter.iter_row_containing(coords),
            self.iter.iter_column_containing(coords),
            self.iter.iter_box_containing(coords),
        )
        for coord, _ in placements:
            new_marks[coord].add(number)
        return new_marks

    def marks_for_number(self, number: Number) -> str:
        """
        Create a string for pretty printing all the marks corresponding to a
        given number.
        """
        h_seperator = "+---+---+---+"
        h_line = "|{}{}{}|{}{}{}|{}{}{}|"
        s = ""
        for i in range(9):
            if i % 3 == 0:
                s += h_seperator + "\n"
            row_tuple = tuple(
                "*" if number in marks else " " for _, marks in self.iter_row(i)
            )
            s += h_line.format(*row_tuple) + "\n"
        s += h_seperator
        return s
