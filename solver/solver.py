import copy
from boards import GameBoard, MarkedBoard
from moves import Finished, NakedSingle


class Solver:

    moves = [Finished, NakedSingle]

    def __init__(self, game_board):
        self.game_board = copy.deepcopy(game_board)
        self.marked_board = MarkedBoard.from_game_board(game_board)
        self.found_moves = set()

    def find_next_move(self):
        for move in Solver.moves:
            mv = move.search(self.marked_board, already_found=self.found_moves)
            if mv:
                return mv
        raise NotImplementedError("Board is not solvable with current moveset")

    def solve(self):
        solution = []
        while True:
            mv = self.find_next_move()
            if isinstance(mv, Finished):
                solution.append(mv)
                return solution
            else:
                mv.apply(self.game_board, self.marked_board)
                solution.append(mv)
                self.found_moves.add(mv)                
