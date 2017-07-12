import abc
import json
from boards import GameBoard, MarkedBoard

class Move(metaclass=abc.ABCMeta):
    """An abstract base class for moves used in solving a sudoku board.

    A move is an atomic piece of logic that updates the state of a game board
    or marked board based on some deterministic, deductive logic.
    """
    @staticmethod
    @abc.abstractmethod
    def search(marked_board):
        pass

    @abc.abstractmethod
    def apply(self, game_board, marked_board):
        pass

    @abc.abstractmethod
    def __repr__(self):
        pass

    @abc.abstractmethod
    def to_json(self):
        pass

    @classmethod
    @abc.abstractmethod
    def from_json(cls, jsn):
        pass


class NakedSingle(Move):
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
    def search(marked_board):
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
            'name': 'NakedSinge',
            'coords': self.coords,
            'number': self.number
        })

    @classmethod
    def from_json(cls, jsn):
        jsn_dict = json.loads(jsn)
        return cls(coords=jsn_dict['coords'], number=jsn_dict['number'])
