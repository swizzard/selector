"""
Mimic `select`-type behavior over a set of generators
"""
from itertools import cycle
from operator import itemgetter


class Selector(object):
    """
    'Select' inputs from a collection of generators. Generators are paused or
    stopped based on user-defined conditions.
    """
    def __init__(self, stop_condition, pause_condition=None, gens=None):
        """
        :param stop_condition: a predicate that should return `True` when a
        generator should be stopped
        :type stop_condition: function (predicate)
        :param pause_condition: a predicate that should return `True` when a
        generator should be paused so inputs can be taken from other
        generators. Defaults to `Selector.false`, which returns False
        regardless of input; each generator will thus be exhausted in turn,
        similar to `itertools.chain`
        :type pause_condition: function (predicate)
        NB: the functions passed to `stop_condition` and `pause_condition`
            should each take a single argument and return a boolean.
        :param gens: list of generators to add to the Selector
        :type gens: list of generator objects
        """
        self.gens = gens or []
        self.started = None
        self.curr = None
        self.stop_condition = stop_condition
        self.pause_condition = pause_condition or self.false

    def add_gen(self, gen):
        """
        Add a generator to this Selector.
        :param gen: the generator to add
        :type gen: generator object
        """
        self.gens.append(gen)

    def add_gens(self, gens):
        """
        Add multiple generators
        :param gens: generators to add
        :type gens: sequence of generator objects
        """
        for gen in gens:
            self.add_gen(gen)

    def start(self):
        """
        Start the selector
        :return: generator object
        """
        self.started = cycle(self.gens)
        self.curr = next(self.started)
        while True:
            try:
                res = next(self.curr)
            except StopIteration:
                self.remove_gen(self.curr)
            else:
                if self.stop_condition(res):
                    self.remove_gen(self.curr)
                elif self.pause_condition(res):
                    self.pause_gen()
                else:
                    yield res

    def stop(self):
        """
        Stop the selector by resetting it to its original state
        """
        self.started = None
        self.gens = []
        self.curr = None

    def pause_gen(self):
        """
        Start taking values from the next generator
        """
        self.curr = next(self.started)

    def remove_gen(self, gen):
        """
        Remove a generator from the selector and re-initialize self.started
        """
        self.gens.remove(gen)
        self.started = cycle(self.gens)
        self.curr = next(self.started)

    def __iter__(self):
        """
        Allow selector to be iterated through
        :return: generator object
        """
        return self.start()

    def __getitem__(self, idx):
        """
        Access an individual generator
        :param idx: index of the generator to be accessed
        :type idx: int
        """
        return self.gens[idx]

    def __repr__(self):
        """
        Formatted representation of `Selector` object
        """
        fmt_str = "{}: stop_condition: {}, pause_condition: {}, gens: {}>"
        return fmt_str.format(str(self.__class__)[:-1], self.stop_condition,
                              self.pause_condition, self.gens)

    def select_on(self, gen):
        """
        Wrapper around `.add_gen` that can be used as a decorator
        """
        # pylint: disable=missing-docstring
        def wrapper(*args, **kwargs):
            self.add_gen(gen(*args, **kwargs))
            return gen(*args, **kwargs)
        # TODO: doc assignment doesn't seem to be working
        wrapper.__doc__ = gen.__doc__
        wrapper.__name__ = gen.__name__
        return wrapper()

    @staticmethod
    def false(_):
        """
        A dummy predicate that returns `False` regardless of input

        >>> Selector.false(True)
        False
        """
        return False


class LabeledSelector(Selector):
    """
    Subclass of Selector that allows outputs to be labeled by origin
    """
    def __init__(self, stop_condition, pause_condition=None, gen_dict=None):
        """
        :param stop_condition: a predicate that should return `True` when a
        generator should be stopped
        :type stop_condition: function (predicate)
        :param pause_condition: a predicate that should return `True` when a
        generator should be paused so inputs can be taken from other
        generators. Defaults to `Selector.false`, which returns False
        regardless of input; each generator will thus be exhausted in turn,
        similar to `itertools.chain`
        :type pause_condition: function (predicate)
        NB: the functions passed to `stop_condition` and `pause_condition`
            should each take a single argument and return a boolean.
        :param gen_dict: a dict of labeled generators to add to the Selector
        :param gen_dict: dict ({'label': <generator>})
        """
        super(LabeledSelector, self).__init__(stop_condition, pause_condition)
        self.labels = []
        if gen_dict:
            self.add_gens(gen_dict)

    @property
    def gens_dict(self):
        """
        A dictionary mapping generators to labels
        """
        return dict(zip(self.gens, self.labels))

    @property
    def labels_dict(self):
        """
        A dictionary mapping labels to generators
        """
        return dict(zip(self.labels, self.gens))

    def start(self):
        """
        Start the LabeledSelector
        """
        gen = super(LabeledSelector, self).start()
        while True:
            val = next(gen)
            label = self.gens_dict[self.curr]
            yield {label: val}

    def remove_gen(self, gen):
        """
        Remove a generator and its label, and reinitialize self.started
        :param gen: the generator object to remove
        :type gen: a generator object
        """
        self.labels.remove(self.gens_dict[gen])
        super(LabeledSelector, self).remove_gen(gen)

    # pylint: disable=arguments-differ
    def add_gen(self, gen, label):
        """
        Add a generator to this LabeledSelector
        :param gen: the generator to add
        :type gen: generator object
        :param label: label to assign to the generator's output
        :type label: str
        """
        self.labels.append(label)
        super(LabeledSelector, self).add_gen(gen)

    def add_gens(self, gen_dict):
        """
        Add generators from a {'label': <generator>} dict
        :param gen_dict: dict of labeled generators
        :type gen_dict: dict ({'label': <generator>})
        """
        for label, gen in sorted(gen_dict.iteritems(), key=itemgetter(1)):
            self.add_gen(gen, label)

    def select_on(self, label):
        """
        Wrapper around `.add_gen` that can be used as a decorator
        :param label: the label to assign to the decorated generator's
                      output
        """
        # pylint: disable=missing-docstring
        def gen_wrapper(gen):
            def wrapper(*args, **kwargs):
                self.add_gen(gen(*args, **kwargs), label)
                return gen(*args, **kwargs)
            # TODO: doc assignment doesn't seem to be working
            gen_wrapper.__doc__ = gen.__doc__
            gen_wrapper.__name__ = gen.__name__
            return wrapper()
        return gen_wrapper

    def stop(self):
        """
        Stop the selector by resetting it to an empty state
        """
        super(LabeledSelector, self).stop()
        self.labels = []

    def __repr__(self):
        """
        Formatted representation of `LabeledSelector` object
        """
        fmt_str = "{}: stop_condition: {}, pause_condition: {}, gens: {}>"
        return fmt_str.format(str(self.__class__)[:-1], self.stop_condition,
                              self.pause_condition, self.labels_dict)

    def __getitem__(self, label):
        """
        Access a specific generator by label
        """
        return self.labels_dict[label]

