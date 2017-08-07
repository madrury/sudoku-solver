from moves import (MOVES_ORDER, MOVES_DICT,
                   Finished,
                   NakedSingle, HiddenSingle,
                   IntersectionTrickPointing,
                   IntersectionTrickClaiming,
                   NakedDouble)


def sigmoid(t):
    return t / (t + 1)


class MoveVector:

    def __init__(self, solution):
        self.solution = solution
    
    @staticmethod
    def empty_move_vector():
        return [0 for _ in MOVES_ORDER]

    @staticmethod
    def increment_from_move(vector, move):
        move_idx = MOVES_ORDER.index(move.__class__)
        new_vector = vector[:]
        new_vector[move_idx] += 1
        return new_vector

    def __iter__(self):
        solution_vector = MoveVector.empty_move_vector()
        yield solution_vector
        for move in self.solution.iter_moves():
            solution_vector = MoveVector.increment_from_move(
                solution_vector, move)
            yield solution_vector


class DifficultyVector:

    def __init__(self, solution):
        self.move_vector = MoveVector(solution)

    def __iter__(self):
        yield from (
            1 + sum(sigmoid(move_count) for move_count in move_vector[2:]) 
                    for move_vector in self.move_vector
        )

    def plot_difficulty_curve(self, ax, **kwargs):
        difficulties = list(self)
        n_moves = len(difficulties)
        ax.plot(list(range(n_moves)), difficulties, **kwargs)
