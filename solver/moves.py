import abc
import json
from copy import deepcopy
from itertools import product, combinations, chain
from collections import defaultdict
from boards import GameBoard, MarkedBoard
from utils import pairs_exclude_diagonal 


FULL_MARKS = {1, 2, 3, 4, 5, 6, 7, 8, 9}

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
    def compute_marks(self, marked_board):
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

    def compute_marks(self, marked_board):
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

    def compute_marks(self, marked_board):
        return marked_board.compute_marks_from_placed_number(
                   self.coords, self.number)

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
            is_marked = [number in marks 
                         for _, marks in marked_board.iter_row(row_idx)]
            if sum(is_marked) == 8:
                column_idx = is_marked.index(False)
                return HiddenSingle((row_idx, column_idx), 'row', number)
        return None

    @staticmethod
    def _search_column(marked_board, already_found):
        for column_idx, number in product(range(9), range(1, 10)):
            is_marked = [number in marks
                         for _, marks in marked_board.iter_column(column_idx)]
            if sum(is_marked) == 8:
                row_idx = is_marked.index(False)
                return HiddenSingle((row_idx, column_idx), 'column', number)
        return None

    @staticmethod
    def _search_box(marked_board, already_found):
        for box_idxs, number in product(product(range(3), range(3)), range(1, 10)):
            is_marked = [number in marks
                         for _, marks in marked_board.iter_box(box_idxs)]
            if sum(is_marked) == 8:
                local_box_idx = is_marked.index(False)
                row_idx, column_idx = (3*box_idxs[0] + local_box_idx // 3,
                                       3*box_idxs[1] + local_box_idx % 3)
                return HiddenSingle((row_idx, column_idx), 'box', number)
        return None

    def compute_marks(self, marked_board):
        return marked_board.compute_marks_from_placed_number(
                   self.coords, self.number)

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
            it_in_row = IntersectionTrick._search(marked_board, box_coords,
                                                  already_found, "row")
            if it_in_row:
                return it_in_row
            it_in_column = IntersectionTrick._search(marked_board, box_coords,
                                                     already_found, "column")
            if it_in_column:
                return it_in_column
        return None

    @staticmethod
    def _search(marked_board, box_coords, already_found, house):
        if house == "row":
            # The inner lists represent rows in both of these data structures.
            houses_in_box = [
                [marked_board[(i, j)] 
                    for j in range(3*box_coords[1], 3*box_coords[1] + 3)]
                for i in range(3*box_coords[0], 3*box_coords[0] + 3)]
            houses_out_box = [[marked_board[(i, j)] 
                         for j in chain(range(0, 3*box_coords[1]),
                                        range(3*box_coords[1] + 3, 9))]
                    for i in range(3*box_coords[0], 3*box_coords[0] + 3)]
        elif house == "column":
            # The inner lists represent columns in both of these data structures.
            houses_in_box = [
                [marked_board[(i, j)] 
                    for i in range(3*box_coords[0], 3*box_coords[0] + 3)]
                for j in range(3*box_coords[1], 3*box_coords[1] + 3)]
            houses_out_box = [[marked_board[(i, j)] 
                         for i in chain(range(0, 3*box_coords[0]),
                                        range(3*box_coords[0] + 3, 9))]
                    for j in range(3*box_coords[1], 3*box_coords[1] + 3)]
        else:
            raise ValueError("house must be 'row' or 'column'")
        for number in range(1, 10):
            possible_in_intersection = [
                any(number not in marks for marks in house)
                for house in houses_in_box]
            if sum(possible_in_intersection) == 1:
                intersection_house = possible_in_intersection.index(True)
                possible_somewhere = any(
                    number not in marks
                    for marks in houses_out_box[intersection_house])
                if possible_somewhere:
                    it = IntersectionTrick(box=box_coords,
                                           house=house,
                                           idx=intersection_house,
                                           number=number)
                    if (not already_found or it not in already_found):
                        return it
        return None

    def compute_marks(self, marked_board):
        if self.house == "row":
            self._compute_marks_row(marked_board)
        elif self.house == "column":
            self._compute_marks_column(marked_board)
        else:
            raise RuntimeError("House in IntersectionTrick.apply must be row "
                               "or column.")

    def _apply_to_row(self, marked_board):
        new_marks = defaultdict(set)
        for column_idx in range(9):
            coords = (3*self.box[0] + self.idx, column_idx)
            if not IntersectionTrick._in_box(coords, self.box):
                new_marks[coords].add(self.number)
        return new_marks

    def _apply_to_column(self, marked_board):
        new_marks = defaultdict(set)
        for row_idx in range(9):
            coords = (row_idx, 3*self.box[1] + self.idx)
            if not IntersectionTrick._in_box(coords, self.box):
                new_marks[coords].add(self.number)
        return new_marks

    @staticmethod
    def _in_box(coords, box):
        return (box[0] == coords[0] // 3) and (box[1] == coords[1] // 3)
            
    def __hash__(self):
        return hash((self.box, self.house, self.idx, self.number))


class NakedDouble(AbstractMove, MoveMixin): 
    """A naked double move.

    A naked double occurs in a house when there are only two cells in that
    house capable of holding any two numbers.  This allows these possibilities
    to be eliminated from all other cells in that house.

    A naked double does not place any number on the game board, only marks.
    """
    def __init__(self, house, house_idx, double_idxs, numbers):
        self.house = house
        self.house_idx = house_idx
        self.double_idxs = double_idxs
        self.numbers = set(numbers)

    @staticmethod
    def search(marked_board, already_found=None):
        search_params = [
            ("row", marked_board.iter_row, range(9)),
            ("column", marked_board.iter_column, range(9)),
            ("box", marked_board.iter_box, product(range(3), range(3)))
        ]
        for search_param in search_params:
            nd = NakedDouble._search(marked_board, already_found, *search_param)
            if nd:
                return nd
        return None

    @staticmethod
    def _search(marked_board, already_found, house_name,
                house_iter, house_idx_iter):
        for house_idx in house_idx_iter:
            traverse_twice = pairs_exclude_diagonal(house_iter(house_idx))
            for (coords1, marks1), (coords2, marks2) in traverse_twice:
                if len(marks1) == 7 and len(marks2) == 7 and marks1 == marks2:
                    numbers = list(FULL_MARKS - marks1)
                    nd = NakedDouble(house=house_name,
                                     house_idx=house_idx,
                                     double_idxs=(coords1, coords2),
                                     numbers=numbers)
                    new_marks = nd.compute_marks(marked_board)
                    if new_marks and (not already_found or nd not in already_found):
                        return nd
        return None

    def compute_marks(self, marked_board):
        new_marks = defaultdict(set)
        iterator = {
            'row': marked_board.iter_row,
            'column': marked_board.iter_column,
            'box': marked_board.iter_box
        }[self.house]
        for coords, marks in iterator(self.house_idx):
            if coords not in self.double_idxs:
                for number in self.numbers:
                    if number not in marked_board[coords]:
                        new_marks[coords].add(number)
        return new_marks

    def __hash__(self):
        return hash((self.house, self.house_idx, 
                    self.double_idxs, tuple(sorted(self.numbers))))
