from boards import GameBoard, MarkedBoard
from moves import NakedSingle, HiddenSingle
import unittest


def new_boards(data):
    b = GameBoard()
    for coord, number in data.items():
        b[coord] = number
    mb = MarkedBoard.from_game_board(b)
    return b, mb


class TestNakedSingle(unittest.TestCase):

    def test_naked_single_row(self):
        gb, mb = new_boards({(0, i): i + 1 for i in range(1, 10)})
        ns = NakedSingle.search(mb)
        self.assertEqual(ns, NakedSingle((0, 0), 1))

    def test_naked_single_column(self):
        gb, mb = new_boards({(i, 0): i + 1 for i in range(1, 10)})
        ns = NakedSingle.search(mb)
        self.assertEqual(ns, NakedSingle((0, 0), 1))

    def test_naked_single_box(self):
        gb, mb = new_boards({
                       (0, 1): 2, (0, 2): 3, 
            (1, 0): 4, (1, 1): 5, (1, 2): 6,
            (2, 0): 7, (2, 1): 8, (2, 2): 9
        })
        ns = NakedSingle.search(mb)
        self.assertEqual(ns, NakedSingle((0, 0), 1))

    def test_naked_single_mixed(self):
        gb, mb = new_boards({
            (0, 6): 2, (0, 7): 3, (0, 8): 4,
            (6, 0): 5, (7, 0): 6, (8, 0): 7,
            (1, 1): 8, (2, 2): 9
        })
        ns = NakedSingle.search(mb)
        self.assertEqual(ns, NakedSingle((0, 0), 1))


if __name__ == '__main__':
    unittest.main()
