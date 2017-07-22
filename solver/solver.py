import copy
import json
from boards import GameBoard, MarkedBoard
from moves import (Finished, NakedSingle,
                   HiddenSingle, IntersectionTrick,
                   NakedDouble)


class NotSolvableException(RuntimeError):
    pass


class Solver:

    moves = [Finished,
             NakedSingle, 
             HiddenSingle,
             IntersectionTrick,
             NakedDouble]

    def __init__(self, game_board):
        self.game_board = copy.deepcopy(game_board)
        self.marked_board = MarkedBoard.from_game_board(game_board)
        self.found_moves = set()
        self.solution = Solution()

    def find_next_move(self):
        for move in Solver.moves:
            mv = move.search(self.marked_board, already_found=self.found_moves)
            if mv:
                return mv
        raise NotSolvableException("Board is not solvable with current moveset")

    def solve(self):
        while True:
            mv = self.find_next_move()
            if isinstance(mv, Finished):
                self.solution.append(mv)
                return self.solution
            else:
                mv.apply(self.game_board, self.marked_board)
                self.solution.append(mv)
                self.found_moves.add(mv)                
        return self.solution


class Solution(list):

    moves_dict = {
        'Finished': Finished,
        'NakedSingle': NakedSingle,
        'HiddenSingle': HiddenSingle,
        'IntersectionTrick': IntersectionTrick,
        'NakedDouble': NakedDouble
    }

    def to_json(self):
        return '[' + ','.join(move.to_json() for move in self) + ']' 

    @classmethod
    def from_json(cls, jsn):
        sln = cls()
        moves = json.loads(jsn)
        for move in moves:
            move_name = move['name']
            sln.append(cls.moves_dict[move_name].from_dict(move))
        return sln
