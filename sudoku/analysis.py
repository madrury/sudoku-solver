from typing import List
from math import log, exp

from sudoku.moves import MOVES_ORDER, Move
from sudoku.solver import Solution


def sigmoid(t):
    return 2 * exp(t) / (exp(t) + 1) - 1


class MoveSchedule:

    def __init__(self, solution: Solution):
        self.solution = solution
        self.schedule: List[List[int]] = self._build_schedule()

    def _build_schedule(self):
        schedule = []
        move_vector = [0 for _ in MOVES_ORDER]
        for move in self.solution.iter_moves():
            schedule.append(move_vector[:])
            move_idx = MOVES_ORDER.index(move.__class__)
            move_vector[move_idx] += 1
        schedule.append(move_vector[:])
        return schedule


class DifficultySchedule:

    MOVE_INCREMENT = log(0.75/0.25)

    def __init__(self, solution: Solution):
        self.move_schedule = MoveSchedule(solution)
        self.schedule: List[float] = self._build_schedule()

    def _build_schedule(self):
        return [
            sum(sigmoid(self.MOVE_INCREMENT * mvcnt) for mvcnt in row)
            # The final move is always Finished, which should not bump the
            # difficulty.
            for row in self.move_schedule.schedule[:-1]
        ]

    def plot_difficulty_curve(self, ax, **kwargs):
        n_moves = len(self.schedule)
        ax.plot(list(range(n_moves)), self.schedule, **kwargs)

    @property
    def difficulty(self) -> float:
        return self.schedule[-1]