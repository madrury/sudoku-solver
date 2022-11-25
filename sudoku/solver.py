import copy
import json
from typing import List, Set, Optional

from sudoku.boards import GameBoard, MarkedBoard
from sudoku.moves import MOVES_ORDER, MOVES_DICT, Finished, Move


class Solution:
    def __init__(self):
        self.moves: List[Move] = []
        self.marks = []
        self.is_full_solution = False

    def iter_moves(self):
        yield from self.moves

    def iter_marks(self):
        yield from self.marks

    def to_json(self):
        return "[" + ",".join(move.to_json() for move in self.moves) + "]"

    @classmethod
    def from_json(cls, jsn):
        sln = cls()
        moves = json.loads(jsn)
        for move in moves:
            move_name = move["name"]
            sln.moves.append(MOVES_DICT[move_name].from_dict(move))
        return sln


class Solver:
    def __init__(self, game_board: GameBoard):
        self.game_board = copy.deepcopy(game_board)
        self.marked_board = MarkedBoard.from_game_board(game_board)
        self.found_moves: Set[Move] = set()
        self.solution = Solution()
        self.is_complete = False

    def find_next_move(self) -> Optional[Move]:
        for move in MOVES_ORDER:
            mv = move.search(self.marked_board, already_found=self.found_moves)
            if mv:
                return mv
        return None

    def solve(self) -> Solution:
        while not self.is_complete:
            mv = self.find_next_move()
            match mv:
                case None:
                    self.solution.is_fully_solved = False
                    self.is_complete = True
                case Finished():
                    self.solution.moves.append(mv)
                    self.solution.is_full_solution = True
                    self.is_fully_solved = True
                    self.is_complete = True
                case _:
                    marks = mv.compute_marks(self.marked_board)
                    self.marked_board.add_marks(marks)
                    self.found_moves.add(mv)
                    self.solution.moves.append(mv)
                    self.solution.marks.append(marks)
        return self.solution
