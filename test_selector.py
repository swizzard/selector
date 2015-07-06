"""
Tests for Selector and LabeledSelector
"""
import unittest

from selector import Selector, LabeledSelector


class TestSelector(unittest.TestCase):
    """
    Tests for the Selector class
    """
    def setUp(self):
        """
        Set up tests
        """
        self.gens = [gen1(), gen2()]

    def test_no_stop(self):
        """
        Test Selector without stop or pause conditions
        """
        sel = Selector(Selector.false, None, [gen1(), gen2()])
        expected = list(gen1()) + list(gen2())
        self.assertEqual(expected, list(sel))

    def test_no_pause(self):
        """
        Test Selector with stop_condition=gt10 and no pause condition
        """
        sel = Selector(gt10, None, self.gens)
        expected = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 5, 6, 7, 8, 9, 10]
        self.assertEqual(expected, list(sel))

    def test_pause(self):
        """
        Test Selector with stop_condition=gt10 and pause_condition=is_even
        """
        sel = Selector(gt10, is_even, self.gens)
        expected = [5, 1, 7, 3, 9, 5, 7, 9]
        self.assertEqual(expected, list(sel))

    def test_stop(self):
        """
        Test .stop()
        """
        sel = Selector(gt10, is_even, self.gens)
        sel.stop()
        self.assertEqual([], sel.gens)
        self.assertIsNone(sel.started)
        self.assertIsNone(sel.curr)

    def test_select_on(self):
        """
        Test .select_on decorator
        """
        sel = Selector(gt10)
        sel.select_on(gen1)
        self.assertEqual(1, len(sel.gens))
        sel_gen = sel.gens[0]
        #self.assertEqual(gen1.__doc__, sel_gen.__doc__)
        self.assertEqual(gen1.__name__, sel_gen.__name__)


class TestLabeledSelector(unittest.TestCase):
    """
    Tests for LabeledSelector class
    """
    def setUp(self):
        """
        Set up tests
        """
        self.labels_dict = {'gen1': gen1(), 'gen2': gen2()}

    @staticmethod
    def sort_results(sel):
        """
        Sort results for easy comparison
        This function is necessary because LabeledSelector results are
        unordered with respect to source generators.
        """
        return sorted(list(sel), key=lambda x: x.keys())

    def test_gens_dict(self):
        """
        Test .gens_dict property
        """
        sel = LabeledSelector(gt10, None, self.labels_dict)
        expected = {val: key for key, val in self.labels_dict.iteritems()}
        self.assertEqual(expected, sel.gens_dict)

    def test_labels_dict(self):
        """
        Test .labels_dict property
        """
        sel = LabeledSelector(gt10, None, self.labels_dict)
        self.assertEqual(self.labels_dict, sel.labels_dict)

    def test_no_stop(self):
        """
        Test LabeledSelector without pause or stop conditions
        """
        sel = LabeledSelector(LabeledSelector.false, None, self.labels_dict)
        expected = [{'gen1': val} for val in xrange(100)]
        expected += [{'gen2': val} for val in xrange(5, 20)]
        actual = self.sort_results(sel)
        self.assertEqual(expected, actual)

    def test_no_pause(self):
        """
        Test LabeledSelector with stop_condition=gt10 and no pause condition
        """
        sel = LabeledSelector(gt10, None, self.labels_dict)
        expected = [{'gen1': val} for val in xrange(11)]
        expected += [{'gen2': val} for val in xrange(5, 11)]
        actual = self.sort_results(sel)
        self.assertEqual(expected, actual)

    def test_pause(self):
        """
        Test LabeledSelector with stop_condition=gt10 and
        pause_condition=is_even
        """
        sel = LabeledSelector(gt10, is_even, self.labels_dict)
        expected = [{'gen2': 5}, {'gen1': 1}, {'gen2': 7}, {'gen1': 3},
                    {'gen2': 9}, {'gen1': 5}, {'gen1': 7}, {'gen1': 9}]
        self.assertEqual(expected, list(sel))

    def test_stop(self):
        """
        Test .stop()
        """
        sel = LabeledSelector(gt10, is_even, self.labels_dict)
        sel.stop()
        self.assertEqual([], sel.gens)
        self.assertEqual([], sel.labels)
        self.assertIsNone(sel.started)
        self.assertIsNone(sel.curr)

    def test_select_on(self):
        """
        Test .select_on decorator
        """
        sel = LabeledSelector(gt10)
        sel.select_on('gen1')(gen1)
        self.assertEqual(1, len(sel.gens))
        sel_gen = sel['gen1']
        #self.assertEqual(gen1.__doc__, sel_gen.__doc__)
        self.assertEqual(gen1.__name__, sel_gen.__name__)


def gen1():
    """
    Generator yielding values between 0 and 99
    """
    i = 0
    while i < 100:
        yield i
        i += 1


def gen2():
    """
    Generator yielding values between 5 and 19
    """
    i = 5
    while i < 20:
        yield i
        i += 1


def gt10(val):
    """
    Predicate testing if a value is less than 10
    """
    return val > 10


def is_even(val):
    """
    Predicate testing if a value is even
    """
    return val % 2 == 0
