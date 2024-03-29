import json
from enum import Enum
from abc import ABC, abstractmethod, abstractstaticmethod
from copy import deepcopy
from itertools import product, compress
from collections import defaultdict

from sudoku.boards import MarkedBoard
from sudoku.utils import unzip, all_empty, pairs_exclude_diagonal, iter_number_pairs

from typing import List, Optional, Dict, Tuple, Set, Union, Type

Coord = Tuple[int, int]
BoxCoord = Tuple[int, int]
Row = int
Col = int
Box = Tuple[int, int]
Number = int
Marks = Set[Number]
NewMarks = Dict[Coord, Marks]

FULL_MARKS: Marks = {1, 2, 3, 4, 5, 6, 7, 8, 9}


class HouseType(Enum):
    ROW = 0
    COLUMN = 1
    BOX = 2


class Move(ABC):
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

    @abstractstaticmethod
    def search(
        marked_board: MarkedBoard, already_found: Optional[Set["Move"]] = None
    ) -> Optional["Move"]:
        pass

    @abstractmethod
    def compute_marks(self, marked_board: MarkedBoard) -> Dict[Coord, Marks]:
        pass

    def __hash__(self) -> int:
        pass


class MoveIOMixin:
    """Methods in common to all move objects.

    This is contains serialization and printing methods.
    """

    def to_dict(self):
        dct = deepcopy(self.__dict__)
        dct["name"] = self.__class__.__name__
        return dct

    @classmethod
    def from_dict(cls, dct):
        d = deepcopy(dct)
        del d["name"]
        return cls(**d)

    def to_json(self):
        return json.dumps(self.to_dict())

    @classmethod
    def from_json(cls, jsn):
        jsn_dict = json.loads(jsn)
        return cls.from_dict(jsn_dict)

    def __repr__(self):
        class_attr_strings = [
            "{}={}".format(name, value) for name, value in self.__dict__.items()
        ]
        return (
            "{}(".format(self.__class__.__name__) + ", ".join(class_attr_strings) + ")"
        )

    def __eq__(self, other):
        return self.to_dict() == other.to_dict()


class Finished(Move, MoveIOMixin):
    """Represents the finished move, returned when a board is completely
    solved.
    """

    def search(
        marked_board: MarkedBoard, already_found: Optional[Set[Move]] = None
    ) -> Optional["Finished"]:
        for (i, j), marks in marked_board.iter.iter_board():
            if marks != MarkedBoard.all_marks:
                return None
        return Finished()

    def compute_marks(self, marked_board: MarkedBoard) -> NewMarks:
        return defaultdict(set)

    def __hash__(self) -> int:
        return 0


class NakedSingle(Move, MoveIOMixin):
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

    def __init__(self, coords: Coord, number: Number):
        self.coords = coords
        self.number = number

    @staticmethod
    def search(
        marked_board: MarkedBoard, already_found: Optional[Set[Move]] = None
    ) -> Optional["NakedSingle"]:
        for (i, j), marks in marked_board.iter.iter_board():
            missing_marks = MarkedBoard.all_marks - marks
            if len(missing_marks) == 1:
                number = next(iter(missing_marks))
                return NakedSingle(coords=(i, j), number=number)
        return None

    def compute_marks(self, marked_board: MarkedBoard) -> NewMarks:
        return marked_board.compute_marks_from_placed_number(self.coords, self.number)

    def __hash__(self) -> int:
        return hash(("NakedSingle", self.coords, self.number))


class HiddenSingle(Move, MoveIOMixin):
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

    def __init__(self, coords: Coord, house_type: HouseType, number: Number):
        self.coords = coords
        self.house_type = house_type
        self.number = number

    @staticmethod
    def search(
        marked_board: MarkedBoard, already_found: Optional[Set[Move]] = None
    ) -> Optional["HiddenSingle"]:
        search_params = [
            (HouseType.ROW, range(9), marked_board.iter.iter_row),
            (HouseType.COLUMN, range(9), marked_board.iter.iter_column),
            (HouseType.BOX, product(range(3), range(3)), marked_board.iter.iter_box),
        ]
        for search_param in search_params:
            hs = HiddenSingle._search_single_house_type(marked_board, *search_param)
            if hs:
                return hs
        return None

    def _search_single_house_type(
        marked_board: MarkedBoard, house_type: HouseType, house_idx_iter, house_iter
    ) -> Optional["HiddenSingle"]:
        coords_for_house: List[Coord]
        marks_for_house: List[Marks]
        for house_idx, number in product(house_idx_iter, range(1, 10)):
            coords_for_house, marks_for_house = unzip(list(house_iter(house_idx)))
            is_marked = [number in marks for marks in marks_for_house]
            if sum(is_marked) == 8:
                idx = is_marked.index(False)
                coords = coords_for_house[idx]
                return HiddenSingle(coords, house_type, number)
        return None

    def compute_marks(self, marked_board: MarkedBoard) -> NewMarks:
        return marked_board.compute_marks_from_placed_number(self.coords, self.number)

    def __hash__(self):
        return hash(("HiddenSingle", self.coords, self.number, self.house_type.value))


class IntersectionTrickPointing(Move, MoveIOMixin):
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

    def __init__(
        self, box: BoxCoord, house_type: HouseType, house_idx: int, number: Number
    ):
        self.box = box
        self.house_type = house_type
        self.house_idx = house_idx
        self.number = number

    @staticmethod
    def search(
        marked_board: MarkedBoard, already_found: Optional[Set[Move]] = None
    ) -> Optional["IntersectionTrickPointing"]:
        for box_coords in product(range(3), range(3)):
            for house_type in [HouseType.ROW, HouseType.COLUMN]:
                it = IntersectionTrickPointing._search(
                    marked_board, house_type, box_coords, already_found
                )
                if it:
                    return it
        return None

    @staticmethod
    def _search(
        marked_board: MarkedBoard,
        house_type: HouseType,
        box_coords: BoxCoord,
        already_found: Optional[Set[Move]],
    ) -> Optional["IntersectionTrickPointing"]:

        houses_in_box: List[List[Marks]]
        match house_type:
            case HouseType.ROW:
                houses_in_box = IntersectionTrickPointing._get_marks_for_rows_in_box(
                    marked_board, box_coords
                )
            case HouseType.COLUMN:
                houses_in_box = IntersectionTrickPointing._get_marks_for_columns_in_box(
                    marked_board, box_coords
                )
            case _:
                raise ValueError(f"HouseType {house_type} not allowed.")

        for number in range(1, 10):
            possible_in_intersection = [
                any(number not in marks for marks in house) for house in houses_in_box
            ]
            if sum(possible_in_intersection) == 1:
                intersection_house = possible_in_intersection.index(True)
                it = IntersectionTrickPointing(
                    box=box_coords,
                    house_type=house_type,
                    house_idx=intersection_house,
                    number=number,
                )
                new_marks = it.compute_marks(marked_board)
                if not all_empty(new_marks) and (
                    not already_found or it not in already_found
                ):
                    return it
        return None

    def _get_marks_for_rows_in_box(
        marked_board: MarkedBoard, box_coords: BoxCoord
    ) -> List[List[Marks]]:
        return [
            [
                marked_board[(i, j)]
                for j in range(3 * box_coords[1], 3 * box_coords[1] + 3)
            ]
            for i in range(3 * box_coords[0], 3 * box_coords[0] + 3)
        ]

    def _get_marks_for_columns_in_box(
        marked_board: MarkedBoard, box_coords: BoxCoord
    ) -> List[List[Marks]]:
        return [
            [
                marked_board[(i, j)]
                for i in range(3 * box_coords[0], 3 * box_coords[0] + 3)
            ]
            for j in range(3 * box_coords[1], 3 * box_coords[1] + 3)
        ]

    def compute_marks(self, marked_board: MarkedBoard) -> NewMarks:
        match self.house_type:
            case HouseType.ROW:
                return self._compute_marks_for_row(marked_board)
            case HouseType.COLUMN:
                return self._compute_marks_for_column(marked_board)
            case _:
                raise ValueError(f"HouseType {self.house_type} not allowed.")

    def _compute_marks_for_row(self, marked_board: MarkedBoard) -> NewMarks:
        new_marks = defaultdict(set)
        for col_idx_within_row in range(9):
            coords = (3 * self.box[0] + self.house_idx, col_idx_within_row)
            if not self.number in marked_board[
                coords
            ] and not IntersectionTrickPointing._in_box(coords, self.box):
                new_marks[coords].add(self.number)
        return new_marks

    def _compute_marks_for_column(self, marked_board: MarkedBoard) -> NewMarks:
        new_marks = defaultdict(set)
        for row_idx_within_col in range(9):
            coords = (row_idx_within_col, 3 * self.box[1] + self.house_idx)
            if not self.number in marked_board[
                coords
            ] and not IntersectionTrickPointing._in_box(coords, self.box):
                new_marks[coords].add(self.number)
        return new_marks

    @staticmethod
    def _in_box(coords, box: BoxCoord) -> bool:
        return (box[0] == coords[0] // 3) and (box[1] == coords[1] // 3)

    def __hash__(self) -> int:
        return hash(
            (
                "IntersectionTrickPointing",
                self.box,
                self.house_type,
                self.house_idx,
                self.number,
            )
        )


class IntersectionTrickClaiming(Move, MoveIOMixin):
    """An claiming intersection trick move.

    A claiming intersection trick is found when the following conditions are
    satisfied.

    1) A number can be placed in a given row or column.
    2) The only place a number can be placed in a given row or column is in the
    intersection with some box.
    3) The number can, a prori, be placed in at least one place in that box
    outside of the intersecting row or column.

    Attributes
    ----------
      - house_type: The type of house that intersects with the box, row or
        column.
      - house_idx: The index of the row or column that intersects with the box.
      - box_idx: The index of the box *within* the row or column: 0, 1, or 2.
      - number: The number that can only be placed in the intersection.

    Resulting Marks
    ---------------
    Results in marking the given number in every cell in the intersecting box
    that does *not* lie within the intersection house.

    The claiming intersection trick does not place any numbers in the game
    board, it only places marks.
    """

    def __init__(
        self,
        house_type: HouseType,
        house_idx: Union[Row, Col],
        box_idx: int,
        number: Number,
    ):
        self.house_type = house_type
        self.house_idx = house_idx
        self.box_idx = box_idx
        self.number = number

    @staticmethod
    def search(
        marked_board: MarkedBoard, already_found: Optional[Set[Move]] = None
    ) -> Optional["IntersectionTrickClaiming"]:
        for house_type in [HouseType.ROW, HouseType.COLUMN]:
            it = IntersectionTrickClaiming._search(
                marked_board, house_type, already_found
            )
            if it:
                return it
        return None

    @staticmethod
    def _search(
        marked_board: MarkedBoard,
        house_type: HouseType,
        already_found: Optional[Set[Move]],
    ):
        for house_idx, number in product(range(9), range(1, 10)):

            # List of length three, for three boxes in each row or column.
            # Is the number possible to place in this box ∩ (row or column)?
            possible_in_box_intersection: List[bool]
            match house_type:
                case HouseType.ROW:
                    possible_in_box_intersection = [
                        any(number not in marks for marks in box_intersection)
                        for box_intersection in marked_board.iter.iter_boxes_in_row(
                            house_idx
                        )
                    ]
                case HouseType.COLUMN:
                    possible_in_box_intersection = [
                        any(number not in marks for marks in box_intersection)
                        for box_intersection in marked_board.iter.iter_boxes_in_column(
                            house_idx
                        )
                    ]
                case _:
                    raise ValueError(f"HouseType {house_type} not allowed.")

            # Number is possible in exactly one box intersecting the row or column.
            if sum(possible_in_box_intersection) == 1:
                box_idx = possible_in_box_intersection.index(True)
                it = IntersectionTrickClaiming(
                    house_type=house_type,
                    house_idx=house_idx,
                    box_idx=box_idx,
                    number=number,
                )
                new_marks = it.compute_marks(marked_board)
                if not all_empty(new_marks) and (
                    not already_found or it not in already_found
                ):
                    return it

        return None

    def compute_marks(self, marked_board: MarkedBoard) -> NewMarks:
        new_marks: NewMarks = defaultdict(set)
        box_coords = self.box_coords
        for coords, _ in marked_board.iter.iter_box(box_coords):
            if not self._in_house(coords) and self.number not in marked_board[coords]:
                new_marks[coords].add(self.number)
        return new_marks

    def _in_house(self, coords: Coord) -> bool:
        match self.house_type:
            case HouseType.ROW:
                return coords[0] == self.house_idx
            case HouseType.COLUMN:
                return coords[1] == self.house_idx
            case _:
                raise ValueError(f"HouseType {self.house_type} not allowed.")

    @property
    def box_coords(self) -> BoxCoord:
        match self.house_type:
            case HouseType.ROW:
                return (self.house_idx // 3, self.box_idx)
            case HouseType.COLUMN:
                return (self.box_idx, self.house_idx // 3)
            case _:
                raise ValueError(f"HouseType {self.house_type} not allowed.")

    def __hash__(self) -> int:
        return hash(
            (
                "IntersectionTrickClaiming",
                self.house_type,
                self.house_idx,
                self.box_idx,
                self.number,
            )
        )


class NakedDouble(Move, MoveIOMixin):
    """A naked double move.

    A naked double occurs in a house when there are only two cells in that
    house capable of holding a set of exactly two numbers.

    Attributes
    ----------
      - house_type: The type of house in which the double is found, row,
        column, or box.
      - house_idx: The index of the house in which the double in round.  This
        is an integer in range(9) for a row or column, and is a pair in
        (range(3), range(3)) if a box.
      - double_idxs: A pair of coordinates, the two cells in which the double
        is found.
      - numbers: A set of two numbers from range(9), the two numbers that are
        only capable in the two cells.

    Resulting Marks
    ---------------
    The two numbers are added within every cell in the house that is not one of
    the two cells composing the double.
    """

    def __init__(
        self,
        house_type: HouseType,
        house_idx: Union[Row, Col, BoxCoord],
        double_idxs: Tuple[Coord, Coord],
        numbers: Tuple[Number, Number],
    ):
        self.house_type = house_type
        self.house_idx = house_idx
        self.double_idxs = double_idxs
        self.numbers = set(numbers)

    @staticmethod
    def search(
        marked_board: MarkedBoard, already_found: Optional[Set[Move]] = None
    ) -> Optional["NakedDouble"]:
        search_params = [
            (HouseType.ROW, marked_board.iter.iter_row, range(9)),
            (HouseType.COLUMN, marked_board.iter.iter_column, range(9)),
            (HouseType.BOX, marked_board.iter.iter_box, product(range(3), range(3))),
        ]
        for search_param in search_params:
            nd = NakedDouble._search_in_single_house_type(
                marked_board, already_found, *search_param
            )
            if nd:
                return nd
        return None

    @staticmethod
    def _search_in_single_house_type(
        marked_board,
        already_found: Optional[Set[Move]],
        house_type: HouseType,
        house_iter,
        house_idx_iter,
    ) -> Optional["NakedDouble"]:
        for house_idx in house_idx_iter:
            traverse_twice = pairs_exclude_diagonal(house_iter(house_idx))
            for (coords1, marks1), (coords2, marks2) in traverse_twice:
                if len(marks1) == 7 and len(marks2) == 7 and marks1 == marks2:
                    numbers = list(FULL_MARKS - marks1)
                    nd = NakedDouble(
                        house_type=house_type,
                        house_idx=house_idx,
                        double_idxs=(coords1, coords2),
                        numbers=numbers,
                    )
                    new_marks = nd.compute_marks(marked_board)
                    if not all_empty(new_marks) and (
                        not already_found or nd not in already_found
                    ):
                        return nd
        return None

    def compute_marks(self, marked_board: MarkedBoard) -> NewMarks:
        iterator = {
            HouseType.ROW: marked_board.iter.iter_row,
            HouseType.COLUMN: marked_board.iter.iter_column,
            HouseType.BOX: marked_board.iter.iter_box,
        }[self.house_type]

        new_marks = defaultdict(set)
        for coords, _ in iterator(self.house_idx):
            if coords not in self.double_idxs:
                added_marks = self.numbers - marked_board[coords]
                new_marks[coords].update(added_marks)
        return new_marks

    def __hash__(self) -> int:
        return hash(
            (
                "NakedDouble",
                self.house_type,
                self.house_idx,
                self.double_idxs,
                tuple(sorted(self.numbers)),
            )
        )


class HiddenDouble(Move, MoveIOMixin):
    """A hidden double move.

    A hidden double occurs in a house when there are two numbers that are only
    capable of being placed in two of the cells within that house.

    Attributes
    ----------
      - house_type: The type of house in which the double is found, row,
        column, or box.
      - house_idx: The index of the house in which the double in round.  This
        is an integer in range(9) for a row or column, and is a pair in
        (range(3), range(3)) if a box.
      - double_idxs: A pair of coordinates, the two cells in which the double
        is found.
      - numbers: A set of two numbers from range(9), the two numbers that are
        capable of being placed only in the two cells.

    Resulting Marks
    ---------------
    All other numbers are placed as marks in the two cells constituting the
    double.
    """

    def __init__(
        self,
        house_type: HouseType,
        house_idx: Union[Row, Col, BoxCoord],
        double_idxs: Tuple[Coord, Coord],
        numbers: Tuple[Number, Number],
    ):
        self.house_type = house_type
        self.house_idx = house_idx
        self.double_idxs = double_idxs
        self.numbers = set(numbers)

    @staticmethod
    def search(
        marked_board, already_found: Optional[Set[Move]] = None
    ) -> Optional["HiddenDouble"]:
        search_params = [
            (HouseType.ROW, marked_board.iter.iter_row, range(9)),
            (HouseType.COLUMN, marked_board.iter.iter_column, range(9)),
            (HouseType.BOX, marked_board.iter.iter_box, product(range(3), range(3))),
        ]
        for search_param in search_params:
            hd = HiddenDouble._search(marked_board, already_found, *search_param)
            if hd:
                return hd
        return None

    @staticmethod
    def _search(
        marked_board: MarkedBoard,
        already_found: Optional[Set[Move]],
        house_type: HouseType,
        house_iter,
        house_idx_iter,
    ) -> Optional["HiddenDouble"]:
        for house_idx, (n1, n2) in product(house_idx_iter, iter_number_pairs()):
            n1_coords, n1_possible = zip(
                *[(coords, n1 not in marks) for coords, marks in house_iter(house_idx)]
            )
            n2_coords, n2_possible = zip(
                *[(coords, n2 not in marks) for coords, marks in house_iter(house_idx)]
            )
            if (
                sum(n1_possible) == 2
                and sum(n2_possible) == 2
                and n1_possible == n2_possible
            ):
                double_coords = tuple(compress(n1_coords, n1_possible))
                hd = HiddenDouble(
                    house_type=house_type,
                    house_idx=house_idx,
                    double_idxs=double_coords,
                    numbers=(n1, n2),
                )
                new_marks = hd.compute_marks(marked_board)
                if not all_empty(new_marks) and (
                    not already_found or hd not in already_found
                ):
                    return hd
        return None

    def compute_marks(self, marked_board: MarkedBoard) -> NewMarks:
        return defaultdict(
            set,
            {
                self.double_idxs[0]: (
                    (FULL_MARKS - marked_board[self.double_idxs[0]]) - self.numbers
                ),
                self.double_idxs[1]: (
                    (FULL_MARKS - marked_board[self.double_idxs[1]]) - self.numbers
                ),
            },
        )

    def __hash__(self) -> int:
        return hash(
            (
                "HiddenDouble",
                self.house_type,
                self.house_idx,
                self.double_idxs,
                tuple(sorted(self.numbers)),
            )
        )


MOVES_ORDER: List[Type[Move]] = [
    Finished,
    HiddenSingle,
    NakedSingle,
    IntersectionTrickPointing,
    IntersectionTrickClaiming,
    HiddenDouble,
    NakedDouble,
]

MOVES_DICT = {
    "Finished": Finished,
    "NakedSingle": NakedSingle,
    "HiddenSingle": HiddenSingle,
    "IntersectionTrickPointing": IntersectionTrickPointing,
    "IntersectionTrickClaiming": IntersectionTrickClaiming,
    "NakedDouble": NakedDouble,
    "HidenDouble": HiddenDouble,
}
