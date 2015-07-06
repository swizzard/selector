# Selector
I'm jealous of constructions like Go's `select`. This represents an attempt
to replicate that kind of behavior in Python.

## What
Get inputs from multiple generators, switching between and/or stopping them
based on user-defined conditions.

You can use `Selector` objects to pull inputs from say, multiple streams
created with [`twitter.TwitterStream`](https://github.com/sixohsix/twitter#the-twitterstream-class)
by pausing a stream that yields `{'timeout': True}` and stopping one that
returns `{'hangup': True}`

## How

    >>> from selector import Selector, LabeledSelector
    >>> sel = Selector(lambda x: x > 10, lambda x: x % 2 == 0)
    >>> @sel.select_on # you can add generators via a decorator...
    ... def gen1():
    ...     i = 0
    ...     while i < 100:
    ...         yield i
    ...         i += 1
    >>> def gen2():
    ...     i = 5
    ...     while i < 20:
    ...         yield i
    ...         i += 1
    >>> sel.add_gen(gen2()) # ...or directly
    >>> for x in sel:
    ...     print x
    5
    1
    7
    3
    9
    5
    7
    9
    >>> from operator import methodcaller
    # doesn't throw KeyError on missing key, unlike `operator.itemgetter`
    >>> get_timeout = methodcaller('get', 'timeout', False)
    >>> get_hangup = methodcaller('get', 'hangup', False)
    >>> labeled_sel = LabeledSelector(get_hangup, get_timeout)
    >>> from my_twitter_client import my_preconfigured_twitter_stream as TS
    >>> labeled_sel.add_gen(TS.statuses.filter(track='#python', timeout=30),
    ... '#python')
    >>> labeled_sel.add_gen(TS.statuses.filter(track='swizzard.pizza',
    ... timeout=30), 'swizzarddotpizza')
    >>> for label, result in labeled_sel.iteritems():
    ...     print label, result['text']
    #python I love \#python it is such a cool language
    #python I am also a fake person on twitter who loves #python
    swizzarddotpizza I have never visited https://swizzard.pizza
    ...

Selectors are initialized with a `stop_condition` and a `pause_condition`,
which, if omitted at init, defaults to `Selector.false`, which just returns
`False` regardless of input. Selectors initialized with `Selector.false` as
a pause condition will only switch between generators when one is exhausted
or fails the stop condition.

(A selector initialized with `Selector.false` as its stop condition will yield
every value in the generator. A selector with `Selector.false` as both its stop
and pause conditions is functionally equivalent to [`itertools.chain`](https://docs.python.org/2/library/itertools.html#itertools.chain),
although likely orders of magnitude slower. With a non-trivial pause condition,
the effect is that of a combination between `itertools.chain` and
[`itertools.ifilter`](https://docs.python.org/2/library/itertools.html#itertools.ifilterfalse).)

###Other notes
* functions used as stop and pause conditions should be what might be called
  'predicates': single-arity functions that return a Boolean value. Note that
  these functions are called _per value_, so any internal state will have to
  be snuck in:

    # with a global var...
    seen = set()
    def stop_on_seen(val):
        if val in seen:
            return True
        else:
            seen.add(val)
            return False
    sel = Selector(stop_on_seen, ...)
    # ...or a callable object...
    class Seen(object):
        def __init__(self):
            self.seen = set()
        def __call__(self, val):
            if val in self.seen:
                return True
            else:
                self.seen.add(val)
                return False
    sel = Selector(Seen(), ...)
    # ...or by subclassing
    class SeenSelector(Selector):
        def __init__(self, pause_condition=None, gens=None):
            self.seen = set()
            super(SeenSelector, self).__init__(self.stop_on_seen,
                                               pause_condition, gens)
        def stop_on_seen(self, val):
            if val in self.seen:
                return True
            else:
                self.seen.append(val)
                return False
    sel = SeenSelector(...)

* Similarly, `pause_condition` and `start_condition` can only be _one_
  function. Multiple conditions require either custom functions or a DIY
  HOF (since Python something like Clojure's
  [`every-pred`](http://conj.io/store/v1/org.clojure/clojure/1.7.0-beta3/clj/clojure.core/every-pred).)

* `Selector` can be initialized with a sequence (list, iterable, etc.) of
  generators -- `s = Selector(my_stop, my_pause, [gen1(), gen2(), gen3()])`
* Similarly, `LabeledSelector` can be initialized with a dictionary --
  `ls = LabeledSelector(my_stop, my_pause, {'gen1': gen1(), 'gen2': gen2()})`
* `.add_gen` (and `.add_gens`) need to be passed _actual generators_, not
  just functions with `yield` in their bodies. Referring to the example above,
  you have to pass in `gen1()` (a generator), not `gen1` (a function.) Of
  course, Python's duck typing means `generator` just means 'has a `next`
  method', so you can define your own class and plug it right in.
* `LabeledSelector.select_on` takes a label:

    ls = LabeledSelector(...)
    @ls.select_on('gen1')
    def gen1():
        ...
    # or if you're feeling particularly obtuse
    def gen2():
        ...
    ls.select_on('gen2')(gen2)

* Both classes' `.select_on` decorators copy the `__name__` attribute of the
  function they wrap, so that they show up as `<function foo at 0x...>` as
  opposed to `<function selector.Selector.wrapper>` or whatever. They
  _should_ also copy the wrapped function's `__doc__`, but that's not
  working right now for reasons I don't understand. (If you do, HMU at
  [@swizzard](https://twitter.com/swizzard) or open a PR.)


## Who
Copyright © 2015 Sam Raker <sam.raker@gmail.com>.
This work is free. You can redistribute it and/or modify it under the
terms of the Do What The Fuck You Want To Public License, Version 2,
as published by Sam Hocevar. See the COPYING file for more details.

