import abc
import json
from itertools import product
from boards import GameBoard, MarkedBoard

class AbstractMove(metaclass=abc.ABCMeta):
    """An abstract base class for moves used in solving a sudoku board.

    A move is an atomic piece of logic that updates the state of a game board
    or marked board based on some deterministic, deductive logic.

    Methods that must be implemented by a Move object
    --------------------------------------------------

    - search: Scan a marked board for a move of the given type. If one is
      found, return the move.
    - apply: Apply a move to a game board and marked board, filling in entries
      and eliminating possiblities as appropriate.
    - to_dict: Return a dictionary representiaton of the move.  Useful for
      serialization to json.
    - from_dict: Construct a move from a dictionary representation of the move,
      useful for de-serializing from json.
    - __repr__
    - __eq__
    """
    @staticmethod
    @abc.abstractmethod
    def search(marked_board, already_found=None):
        pass

    @abc.abstractmethod
    def apply(self, game_board, marked_board):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass

    @abc.abstractmethod
    def to_dict(self):
        pass

    @classmethod
    @abc.abstractmethod
    def from_dict(cls, jsn):
        pass

    def __eq__(self, other):
        pass


class MoveMixin:

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, jsn):
        jsn_dict = json.loads(jsn)
        return cls.from_dict(jsn_dict)


class Finished(AbstractMove, MoveMixin):
    """
    Represents the finished move, returned when a board is completely solved.
    """
    def search(marked_board, already_found=None):
        """Check that the marked board is fully solved.

        Simply checks that all cells have full marks.
        """
        for (i, j), marks in marked_board.iter_board():
            if marks != MarkedBoard.all_marks:
                return None
        return Finished()

    def apply(self, game_board, marked_board):
        pass

    def __repr__(self):
        return "Finished()"

    def to_json(self):
        return json.dumps({'name': 'Finished'})

    @classmethod
    def from_dict(cls, dct):
        return Finished()

    @classmethod
    def to_dict(cls, jsn):
        return {'name': 'Finished'}

    def __eq__(self, other):
        return True


class NakedSingle(AbstractMove, MoveMixin):
    """A naked single move.

    This is the most basic sudoku move. A naked single is when a cell can only
    possibly be filled with one number (all other possibilities have been
    eliminated).
    
    This is one of only two moves that can fill in a number in the board, the
    other is a hidden single.
    """
    def __init__(self, coords, number):
        self.coords = coords
        self.number = number

    @staticmethod
    def search(marked_board, already_found=None):
        found_moves = []
        for (i, j), marks in marked_board.iter_board():
            missing_marks = MarkedBoard.all_marks - marks
            if len(missing_marks) == 1:
                number = next(iter(missing_marks))
                return NakedSingle(coords=(i, j), number=number)
        return None

    def apply(self, game_board, marked_board):
        game_board[self.coords] = self.number
        marked_board.add_marks_from_placed_number(self.coords, self.number)

    def __repr__(self):
        return "NakedSingle(coords={}, number={})".format(
            self.coords, self.number)

    def to_dict(self):
        return {
            'name': 'NakedSingle',
            'coords': self.coords,
            'number': self.number
        }

    @classmethod 
    def from_dict(cls, dct):
        return cls(coords=dct['coords'], number=dct['number'])

    def __eq__(self, other):
        return self.coords == other.coords and self.number == other.number


class HiddenSingle(AbstractMove, MoveMixin):
    """A hidden single move.

    The second most basic sudoku move. A hidden single is when a house (row,
    column, or box) has exaclty one cell that can old a given number, as the
    number has been eliminated from all other cells in the house.

    This is one of only two moves that can fill a number in the board, the
    other is a naked single.
    """
    def __init__(self, coords, house, number):
        self.coords = coords
        self.house = house
        self.number = number

    @staticmethod
    def search(marked_board, already_found=None):
        searchers = [HiddenSingle._search_row,
                     HiddenSingle._search_column,
                     HiddenSingle._search_box]
        for searcher in searchers:
            hs = searcher(marked_board, already_found)
            if hs:
                return hs
        return None

    @staticmethod
    def _search_row(marked_board, already_found):
        for row_idx, number in product(range(9), range(1, 10)):
            is_marked = [number in marks for _, marks in marked_board.iter_row(row_idx)]
            if sum(is_marked) == 8:
                column_idx = is_marked.index(False)
                return HiddenSingle((row_idx, column_idx), 'row', number)
        return None

    @staticmethod
    def _search_column(marked_board, already_found):
        for column_idx, number in product(range(9), range(1, 10)):
            is_marked = [number in marks for _, marks in marked_board.iter_column(column_idx)]
            if sum(is_marked) == 8:
                row_idx = is_marked.index(False)
                return HiddenSingle((row_idx, column_idx), 'column', number)
        return None

    @staticmethod
    def _search_box(marked_board, already_found):
        for box_idxs, number in product(product(range(3), range(3)), range(1, 10)):
            is_marked = [number in marks for _, marks in marked_board.iter_box(box_idxs)]
            if sum(is_marked) == 8:
                local_box_idx = is_marked.index(False)
                row_idx, column_idx = (3*box_idxs[0] + local_box_idx // 3,
                                       3*box_idxs[1] + local_box_idx % 3)
                return HiddenSingle((row_idx, column_idx), 'box', number)
        return None

    def apply(self, game_board, marked_board):
        game_board[self.coords] = self.number
        marked_board.add_marks_from_placed_number(self.coords, self.number)

    def __repr__(self):
        return "HiddenSingle(coords={}, house={}, number={})".format(
            self.coords, self.house, self.number)

    def to_dict(self):
        return {
            'name': 'HiddenSingle',
            'coords': self.coords,
            'house': self.house,
            'number': self.number
        }

    @classmethod 
    def from_dict(cls, dct):
        return cls(coords=dct['coords'], house=dct['house'], number=dct['number'])

    def __eq__(self, other):
        return (self.coords == other.coords and
                self.number == other.number and
                self.house == other.house)
