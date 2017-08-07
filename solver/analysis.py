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
    def empty_solution_vector():
        return [0 for _ in MOVES_ORDER]

    @staticmethod
    def increment_from_move(vector, move):
        move_idx = MOVES_ORDER.index(move.__class__)
        new_vector = vector[:]
        new_vector[move_idx] += 1
        return new_vector

    def __iter__(self):
        solution_vector = MoveVector.empty_solution_vector()
        yield solution_vector
        for move in self.solution.iter_moves():
            solution_vector = MoveVector.increment_from_move(
                solution_vector, move)
            yield solution_vector
