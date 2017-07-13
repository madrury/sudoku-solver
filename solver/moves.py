import abc
import json
from boards import GameBoard, MarkedBoard

class AbstractMove(metaclass=abc.ABCMeta):
    """An abstract base class for moves used in solving a sudoku board.

    A move is an atomic piece of logic that updates the state of a game board
    or marked board based on some deterministic, deductive logic.
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


class NakedSingle(AbstractMove, MoveMixin):
    """A naked single move.

    This is the most basic sudoku move. A naked single is when a cell can only
    possibly be filled with one number (all other possibilities have been
    eliminated).
    
    This is one of only two moves that can fill in a number in the board, the
    other is a HiddenSingle.
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

    def to_json(self):
        return json.dumps({
            'name': 'NakedSingle',
            'coords': self.coords,
            'number': self.number
        })

    @classmethod 
    def from_dict(cls, dct):
        return cls(coords=dct['coords'], number=dct['number'])