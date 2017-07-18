import abc
import json
from copy import deepcopy
from itertools import product, combinations
from boards import GameBoard, MarkedBoard, Box

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
    - __eq__
    """
    @staticmethod
    @abc.abstractmethod
    def search(marked_board, already_found=None):
        pass

    @abc.abstractmethod
    def apply(self, game_board, marked_board):
        pass

    def __hash__(self, other):
        pass


class MoveMixin:
    """Methods in common to all move objects.

    This is contains serialization and printing methods. Move objects are
    essentially data containers with a few static methods, so these can be
    safely assimilated in one place.
    """ 
    def to_dict(self):
        dct = deepcopy(self.__dict__)
        dct['name'] = self.__class__.__name__
        return dct
    
    @classmethod
    def from_dict(cls, dct):
        d = deepcopy(dct)
        del d['name']
        return cls(**d)

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, jsn):
        jsn_dict = json.loads(jsn)
        return cls.from_dict(jsn_dict)

    def __repr__(self):
        class_attr_strings = ["{}={}".format(name, value)
                              for name, value in self.__dict__.items()]
        return ("{}(".format(self.__class__.__name__)
                + ', '.join(class_attr_strings)
                + ')')

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()


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

    def __hash__(self):
        return 0


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

    def __hash__(self):
        return hash((self.coords, self.number))


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

    def __hash__(self):
        return hash((self.coords, self.number, self.house))


class IntersectionTrick(AbstractMove, MoveMixin):
    """An intersection trick move.

    An intersection trick is found when the following two conditions are
    satisfied:
        - A number is available to be placed in that box.
        - The number can only be placed inside the intersection of a single row
          or column in that box.
    Consequently, that number *cannot* be placed in any other cell in the same
    row or column.

    The intersection trick does not place any numbers in the game board, it
    only places marks.
    """
    def __init__(self, box, house, idx, number):
        self.box = box
        self.house = house
        self.idx = idx
        self.number = number

    @staticmethod
    def search(marked_board, already_found=None):
        for box_coords in product(range(3), range(3)):
            box = Box(marked_board, box_coords)
            it_in_row = IntersectionTrick._search_row(box, already_found)
            if it_in_row:
                return it_in_row
            it_in_column = IntersectionTrick._search_column(box, already_found)
            if it_in_column:
                return it_in_column
        return None

    @staticmethod
    def _search_row(box, already_found):
        rows = [[box[(j, i)] for i in range(3)] for j in range(3)]
        for i, two_rows in enumerate(combinations(rows, 2)):
            complement_row = rows[2 - i]
            first_row, second_row = two_rows
            for number in range(1, 10):
                found_intersection_trick = (
                    all(number in marks for marks in first_row) and
                    all(number in marks for marks in second_row) and
                    not all(number in marks for marks in complement_row))
                if found_intersection_trick:
                    it = IntersectionTrick(box=box.box_coords,
                                           house="row",
                                           idx=(2 - i),
                                           number=number)
                    if not already_found or it not in already_found:
                        return it
        return None

    @staticmethod
    def _search_column(box, already_found):
        columns = [[box[(i, j)] for i in range(3)] for j in range(3)]
        for i, two_columns in enumerate(combinations(columns, 2)):
            complement_column = columns[2 - i]
            first_column, second_column = two_columns
            for number in range(1, 10):
                found_intersection_trick = (
                    all(number in marks for marks in first_column) and
                    all(number in marks for marks in second_column) and
                    not all(number in marks for marks in complement_column))
                if found_intersection_trick:
                    it = IntersectionTrick(box=box.box_coords,
                                           house="column",
                                           idx=(2 - i),
                                           number=number)
                    if not already_found or it not in already_found:
                        return it
        return None

    def apply(self, game_board, marked_board):
        if self.house == "row":
            self._apply_to_row(marked_board)
        elif self.house == "column":
            self._apply_to_column(marked_board)
        else:
            raise RuntimeError("House in IntersectionTrick.apply must be row "
                               "or column.")

    def _apply_to_row(self, marked_board):
        for column_idx in range(9):
            coords = (3*self.box[0] + self.idx, column_idx)
            if not IntersectionTrick._in_box(coords, self.box):
                marked_board[coords].add(self.number)

    def _apply_to_column(self, marked_board):
        for row_idx in range(9):
            coords = (row_idx, 3*self.box[1] + self.idx)
            if not IntersectionTrick._in_box(coords, self.box):
                marked_board[coords].add(self.number)

    @staticmethod
    def _in_box(coords, box):
        return (box[0] == coords[0] // 3) and (box[1] == coords[1] // 3)
            
    def __hash__(self):
        return hash((self.box, self.house, self.idx, self.number))
