import copy
import json
from enum import IntEnum
from boards import GameBoard, MarkedBoard
from moves import (MOVES_ORDER, MOVES_DICT,
                   Finished,
                   NakedSingle, HiddenSingle,
                   IntersectionTrickPointing,
                   IntersectionTrickClaiming,
                   NakedDouble)


class NotSolvableException(RuntimeError):
    pass


class Solver:

    def __init__(self, game_board):
        self.game_board = copy.deepcopy(game_board)
        self.marked_board = MarkedBoard.from_game_board(game_board)
        self.found_moves = set()
        self.solution = Solution()

    def find_next_move(self):
        for move in MOVES_ORDER:
            mv, new_marks = move.search(
                self.marked_board, already_found=self.found_moves)
            if mv:
                return mv, new_marks
        raise NotSolvableException("Board is not solvable with current moveset")

    def solve(self):
        while True:
            mv, marks = self.find_next_move()
            if isinstance(mv, Finished):
                self.solution.moves.append(mv)
                return self.solution
            else:
                self.marked_board.add_marks(marks)
                self.found_moves.add(mv)         
                self.solution.moves.append(mv)
                self.solution.marks.append(marks)
        return self.solution


class Solution:

    def __init__(self):
        self.moves = []
        self.marks = []

    def iter_moves(self):
        yield from self.moves

    def iter_marks(self):
        yield from self.marks

    def to_json(self):
        return '[' + ','.join(move.to_json() for move in self.moves) + ']' 

    @classmethod
    def from_json(cls, jsn):
        sln = cls()
        moves = json.loads(jsn)
        for move in moves:
            move_name = move['name']
            sln.moves.append(MOVES_DICT[move_name].from_dict(move))
        return sln
