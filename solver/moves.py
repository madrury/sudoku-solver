import abc
import json
from copy import deepcopy
from itertools import product, combinations, chain
from collections import defaultdict
from boards import GameBoard, MarkedBoard
from utils import unzip, pairs_exclude_diagonal 


FULL_MARKS = {1, 2, 3, 4, 5, 6, 7, 8, 9}

class AbstractMove(metaclass=abc.ABCMeta):
    """An abstract base class for moves used in solving a sudoku board.

    A move is an atomic piece of logic that updates the state of a game board
    or marked board based on some deterministic, deductive rule.
 
    A move object has two roles:
      1) Serve as a representation of a single example of such a move. Contains
      data for how the marks resulting from such a move should be applied.
      2) Serve as a namespace for methods related to that move. Most
      fundamentally, algorithms for searching for, and computing the
      consequences of a move.

    Methods that a move object must implement:

    - search: 
      Scan a marked board for a move of the given type. If one is found, return
      an object representing the object.
    - compute_marks: Compute the new marks resulting from the application of a
      move to a board and/or marked board.
    -__hash__: Compute a hash value for a board. Useful for storing moves in
      sets.
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

    This is contains serialization and printing methods.
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
    """Represents the finished move, returned when a board is completely
    solved.
    """
    def search(marked_board, already_found=None):
        for (i, j), marks in marked_board.iter_board():
            if marks != MarkedBoard.all_marks:
                return None
        return Finished()

    def compute_marks(self, marked_board):
        return defaultdict(set)

    def __hash__(self):
        return 0


class NakedSingle(AbstractMove, MoveMixin):
    """A naked single move.

    This is the most basic sudoku move. A naked single is found when a cell can
    only possibly be filled with one number (all other possibilities have been
    eliminated).
    
    This is one of only two moves that can fill in a number in the board, the
    other is a hidden single.

    Attributes
    ----------
      - coords: The coordinates of the cell with the naked single.
      - number: The only number that can appear in the given cell.

    Resulting Marks
    ---------------
    Results in adding the number to the marks of every cell sharing the same
    row, column, or box with the naked single.
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

    A hidden single is when a house (row, column, or box) has exaclty one cell
    that can hold a given number, as the number has been eliminated from all
    other cells in the house.

    This is one of only two moves that can fill a number in the board, the
    other is a naked single.

    Attributes
    ----------
      - coords: The coordinates of the cell with the hidden single.
      - house_type: The name of the house contining the hidden single.
      - number: The number that must appear in the given cell.

    Resulting Marks
    ---------------
    Results in adding the number to the marks of every cell sharing the same
    row, column, or box with the naked single.
    """
    def __init__(self, coords, house_type, number):
        self.coords = coords
        self.house_type = house_type
        self.number = number

    @staticmethod
    def search(marked_board, already_found=None):
        search_params = [
            ("row", range(9), marked_board.iter_row),
            ("column", range(9), marked_board.iter_column),
            ("box", product(range(3), range(3)), marked_board.iter_box)
        ]
        for search_param in search_params:
            hs = HiddenSingle._search(marked_board, *search_param)
            if hs:
                return hs
        return None

    def _search(marked_board, house_type, house_idx_iter, house_iter):
        for house_idx, number in product(house_idx_iter, range(1, 10)):
            coords_for_house, marks_for_house = unzip(list(house_iter(house_idx)))
            is_marked = [number in marks for marks in marks_for_house]
            if sum(is_marked) == 8:
                idx = is_marked.index(False)
                coords = coords_for_house[idx]
                return HiddenSingle(coords, house_type, number)
        return None

    def compute_marks(self, marked_board):
        return marked_board.compute_marks_from_placed_number(
                   self.coords, self.number)

    def __hash__(self):
        return hash((self.coords, self.number, self.house_type))


class IntersectionTrickPointing(AbstractMove, MoveMixin):
    """An pointing intersection trick move.

    An pointing intersection trick is found when the following two conditions
    are satisfied:

      1) A number is available to be placed in that box.
      2) The number can only be placed inside the intersection of a single row
      or column in that box.  
      3) The number, a prori, can be placed in at least one other place in the
      intersecting row or column.

    Attributes
    ----------
      - box: The coordinates of the box in which the move is found.
      - house_type: The type of house that intersects with the box.
      - house_idx: The index of the intersection house *within* the box. A
        number 0, 1, or 2. 
      - number: The number that can only be placed in the intersection.

    Resulting Marks
    ---------------
    Results in marking the given number in every cell in the intersecting row
    or column that does *not* lie within the box.

    The pointing intersection trick does not place any numbers in the game
    board, it only places marks.
    """
    def __init__(self, box, house_type, house_idx, number):
        self.box = box
        self.house_type = house_type
        self.house_idx = house_idx
        self.number = number

    @staticmethod
    def search(marked_board, already_found=None):
        for box_coords in product(range(3), range(3)):
            it_in_row = IntersectionTrickPointing._search(
                marked_board, box_coords, already_found, "row")
            if it_in_row:
                return it_in_row
            it_in_column = IntersectionTrickPointing._search(
                marked_board, box_coords, already_found, "column")
            if it_in_column:
                return it_in_column
        return None

    @staticmethod
    def _search(marked_board, box_coords, already_found, house_type):
        if house_type == "row":
            # The inner lists represent rows in both of these data structures.
            houses_in_box = [
                [marked_board[(i, j)] 
                    for j in range(3*box_coords[1], 3*box_coords[1] + 3)]
                for i in range(3*box_coords[0], 3*box_coords[0] + 3)]
        elif house_type == "column":
            # The inner lists represent columns in both of these data structures.
            houses_in_box = [
                [marked_board[(i, j)] 
                    for i in range(3*box_coords[0], 3*box_coords[0] + 3)]
                for j in range(3*box_coords[1], 3*box_coords[1] + 3)]
        else:
            raise ValueError("house_type must be 'row' or 'column'")
        for number in range(1, 10):
            possible_in_intersection = [
                any(number not in marks for marks in house)
                for house in houses_in_box]
            if sum(possible_in_intersection) == 1:
                intersection_house = possible_in_intersection.index(True)
                it = IntersectionTrickPointing(
                    box=box_coords,
                    house_type=house_type,
                    house_idx=intersection_house,
                    number=number)
                new_marks = it.compute_marks(marked_board)
                if new_marks and (not already_found or it not in already_found):
                    return it
        return None

    # TODO: This logic can be cleaned up.
    def compute_marks(self, marked_board):
        if self.house_type == "row":
            return self._compute_marks_row(marked_board)
        elif self.house_type == "column":
            return self._compute_marks_column(marked_board)
        else:
            raise RuntimeError("House in IntersectionTrickPointing.apply must"
                "be row or column.")

    def _compute_marks_row(self, marked_board):
        new_marks = defaultdict(set)
        for column_idx in range(9):
            coords = (3*self.box[0] + self.house_idx, column_idx)
            if (not self.number in marked_board[coords] and 
                not IntersectionTrickPointing._in_box(coords, self.box)):
                new_marks[coords].add(self.number)
        return new_marks

    def _compute_marks_column(self, marked_board):
        new_marks = defaultdict(set)
        for row_idx in range(9):
            coords = (row_idx, 3*self.box[1] + self.house_idx)
            if (not self.number in marked_board[coords] and 
                not IntersectionTrickPointing._in_box(coords, self.box)):
                new_marks[coords].add(self.number)
        return new_marks

    @staticmethod
    def _in_box(coords, box):
        return (box[0] == coords[0] // 3) and (box[1] == coords[1] // 3)
            
    def __hash__(self):
        return hash((self.box, self.house_type, self.house_idx, self.number))


class IntersectionTrickClaiming(AbstractMove, MoveMixin):
    """An claiming intersection trick move.

    A claiming intersection trick is found when the following conditions are
    satisfied.

    1) A number can be placed in a given row or column.
    2) The only place a number can be placed in a given row or column is in the
    intersection with some box.
    3) The number can, a prori, be placed in at least one place in that box
    outside of the intersecting house.

    Attributes
    ----------
      - house_type: The type of house that intersects with the box, row or
        column.
      - house_idx: The index of the row or column that intersects with the box.
      - box_idx: The index of the box *within* the row, 0, 1, or 2.
      - number: The number that can only be placed in the intersection.

    Resulting Marks
    ---------------
    Results in marking the given number in every cell in the intersecting box
    that does *not* lie within the intersection house.

    The claiming intersection trick does not place any numbers in the game
    board, it only places marks.
    """
    def __init__(self, house_type, house_idx, box_idx, number):
        self.house_type = house_type
        self.house_idx = house_idx
        self.box_idx = box_idx
        self.number = number

    @staticmethod
    def search(marked_board, already_found=None):
        search_params = [
            ("row", marked_board.iter_boxes_in_row),
            ("column", marked_board.iter_boxes_in_column)
        ]
        for search_param in search_params:
            it = IntersectionTrickClaiming._search(
                marked_board, already_found, *search_param)
            if it:
                return it
        return None

    @staticmethod
    def _search(marked_board, already_found, house_type, iterator):
        for house_idx, number in product(range(9), range(1, 10)):
            possible_in_box_intersection = [
                any(number not in marks for marks in box_intersection)
                for box_intersection in iterator(house_idx)]
            if sum(possible_in_box_intersection) == 1:
                box_idx = possible_in_box_intersection.index(True)
                it = IntersectionTrickClaiming(
                    house_type = house_type,
                    house_idx = house_idx,
                    box_idx = box_idx,
                    number = number)
                new_marks = it.compute_marks(marked_board)
                if new_marks and (not already_found or nd not in already_found):
                    return it
        return None

    def compute_marks(self, marked_board):
        new_marks = defaultdict(set)
        box_coords = self.box_coords
        for coords, marks in marked_board.iter_box(box_coords):
            if (not self._in_house(coords) and
                self.number not in marked_board[coords]):
                new_marks[coords].add(self.number)
        return new_marks

    def _in_house(self, coords):
        return {
            "row": coords[0] == self.house_idx,
            "column": coords[1] == self.house_idx
        }[self.house_type]
       
    @property
    def box_coords(self):
        box_row, box_column = {
            "row": (self.house_idx // 3, self.box_idx),
            "column": (self.box_idx, self.house_idx // 3)
        }[self.house_type]
        return (box_row, box_column)

    def __hash__(self):
        return hash((self.house_type, self.house_idx,
                     self.box_idx, self.number))


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
