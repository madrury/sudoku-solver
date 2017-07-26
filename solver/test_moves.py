from boards import GameBoard, MarkedBoard
from moves import (NakedSingle, HiddenSingle,
                   IntersectionTrickPointing, 
                   IntersectionTrickClaiming,
                   NakedDouble)
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


class TestHiddenSingle(unittest.TestCase):

    def test_hidden_single_row_top(self):
        gb, mb = new_boards({
            (1, 3): 1, (2, 6): 1, (0, 1): 2, (0, 2): 3
        })
        hs = HiddenSingle.search(mb)
        self.assertEqual(hs, HiddenSingle((0, 0), 'row', 1))

    def test_hidden_single_row_middle(self):
        gb, mb = new_boards({
            (3, 0): 1, (5, 6): 1, (4, 3): 2, (4, 5): 3
        })
        hs = HiddenSingle.search(mb)
        self.assertEqual(hs, HiddenSingle((4, 4), 'row', 1))

    def test_hidden_single_column_side(self):
        gb, mb = new_boards({
            (3, 1): 1, (6, 2): 1, (1, 0): 2, (2, 0): 3
        })
        hs = HiddenSingle.search(mb)
        self.assertEqual(hs, HiddenSingle((0, 0), 'column', 1))

    def test_hidden_single_column_middle(self):
        gb, mb = new_boards({
            (0, 3): 1, (6, 5): 1, (3, 4): 2, (5, 4): 3
        })
        hs = HiddenSingle.search(mb)
        self.assertEqual(hs, HiddenSingle((4, 4), 'column', 1))


    def test_hidden_single_box_top(self):
        gb, mb = new_boards({
            (1, 3): 1, (6, 1): 1, (2, 0): 2, (2, 2): 3, (0, 2): 4
        })
        hs = HiddenSingle.search(mb)
        self.assertEqual(hs, HiddenSingle((0, 0), 'box', 1))

    def test_hidden_single_box_middle(self):
        gb, mb = new_boards({
            (5, 0): 1, (0, 5): 1,
            (4, 3): 2, (4, 4): 3, (3, 4): 4
        })
        hs = HiddenSingle.search(mb)
        self.assertEqual(hs, HiddenSingle((3, 3), 'box', 1))


class TestIntersectionTrickPointing(unittest.TestCase):

    def test_intersection_trick_row(self):
        gb, mb = new_boards({
            (0, 0): 2, (0, 1): 3, (0, 2): 4,
            (1, 6): 8, (1, 7): 9,
            (2, 0): 5, (2, 1): 6, (2, 2): 7,
        })
        it = IntersectionTrickPointing.search(mb)
        self.assertEqual(it, 
            IntersectionTrickPointing((0, 0), "row", 1, 1))

    def test_intersection_trick_row_no_marks(self):
        gb, mb = new_boards({
            (0, 0): 2, (0, 1): 3, (0, 2): 4,
            (1, 5): 2, (1, 6): 8, (1, 7): 9,
            (2, 0): 5, (2, 1): 6, (2, 2): 7,
            (4, 4): 1,
            (7, 3): 1,
            (8, 8): 1
        })
        it = IntersectionTrickPointing.search(mb)
        self.assertEqual(it, None)

    def test_intersection_trick_column(self):
        gb, mb = new_boards({
            (0, 0): 2, (1, 0): 3, (2, 0): 4,
            (0, 2): 5, (1, 2): 6, (2, 2): 7,
            (6, 1): 8, (7, 1): 9
        })
        it = IntersectionTrickPointing.search(mb)
        self.assertEqual(it, 
            IntersectionTrickPointing((0, 0), "column", 1, 1))

    def test_intersection_trick_column_no_marks(self):
        gb, mb = new_boards({
            (0, 0): 2, (1, 0): 3, (2, 0): 4,
            (5, 1): 2, (6, 1): 8, (7, 1): 9,
            (0, 2): 5, (1, 2): 6, (2, 2): 7,
            (4, 4): 1,
            (3, 7): 1,
            (8, 8): 1
        })
        it = IntersectionTrickPointing.search(mb)
        self.assertEqual(it, None)

    def test_intersection_trick_top_middle(self):
        gb, mb = new_boards({
            (0, 0): 9, (1, 3): 2, (1, 4): 3, (1, 5): 4
        })
        it = IntersectionTrickPointing.search(mb)
        self.assertEqual(it, 
            IntersectionTrickPointing((0, 1), "row", 2, 9))

    def test_intersection_trick_center(self):
        gb, mb = new_boards({
            (0, 4): 1, (3, 5): 2, (4, 5): 3, (5, 5): 4
        })
        it = IntersectionTrickPointing.search(mb)
        self.assertEqual(it, 
            IntersectionTrickPointing((1, 1), "column", 0, 1))


class TestIntersectionTrickClaiming(unittest.TestCase):

    def test_intersection_trick_row(self):
        gb, mb = new_boards({
            (0, 0): 2, (0, 1): 3, (0, 2): 4,
            (0, 6): 5, (0, 7): 6, (0, 8): 7,
        })
        it = IntersectionTrickClaiming.search(mb)
        self.assertEqual(it, 
            IntersectionTrickClaiming("row", 0, 1, 1))

    def test_intersection_trick_column(self):
        gb, mb = new_boards({
            (0, 0): 2, (1, 0): 3, (2, 0): 4,
            (6, 0): 5, (7, 0): 6, (8, 0): 7,
        })
        it = IntersectionTrickClaiming.search(mb)
        self.assertEqual(it, 
            IntersectionTrickClaiming("column", 0, 1, 1))

class TestNakedDouble(unittest.TestCase):

    def test_naked_double_row(self):
        gb, mb = new_boards({
            (0, 0): 3, (0, 1): 4, (0, 2): 5,
            (1, 0): 6, (1, 6): 7, (1, 7): 8, (1, 8): 9
        })
        nd = NakedDouble.search(mb)
        self.assertEqual(nd, 
            NakedDouble("row", 1, ((1, 1), (1, 2)), (1, 2)))

    def test_naked_double_column(self):
        gb, mb = new_boards({
            (0, 0): 3, (0, 1): 6,
            (1, 0): 4, 
            (2, 0): 5,
            (6, 1): 7, 
            (7, 1): 8, 
            (8, 1): 9
        })
        nd = NakedDouble.search(mb)
        self.assertEqual(nd, 
            NakedDouble("column", 1, ((1, 1), (2, 1)), (1, 2)))

    def test_naked_double_box(self):
        gb, mb = new_boards({
            (0, 0): 3, (0, 1): 4, (0, 6): 8, (0, 7): 9,
            (1, 0): 5, (1, 1): 6, (1, 6): 1,
            (2, 2): 7,
            (6, 0): 8,
            (7, 0): 9, (7, 1): 2
        })
        nd = NakedDouble.search(mb)
        self.assertEqual(nd, 
            NakedDouble("box", (0, 0), ((0, 2), (2, 0)), (1, 2)))

    def test_naked_double_box_no_move(self):
        gb, mb = new_boards({
            (0, 0): 3, (0, 1): 4, (0, 6): 8, (0, 7): 9,
            (1, 0): 5, (1, 1): 6, (1, 6): 1, (1, 7): 2,
            (2, 2): 7,
            (6, 0): 8, (6, 1): 1,
            (7, 0): 9, (7, 1): 2
        })
        nd = NakedDouble.search(mb)
        self.assertEqual(nd, None)


if __name__ == '__main__':
    unittest.main()
