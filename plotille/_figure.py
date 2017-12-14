# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

# The MIT License

# Copyright (c) 2017 Tammo Ippen, tammo.ippen@posteo.de

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

from collections import namedtuple
from itertools import cycle
import os

from six.moves import zip

from ._canvas import Canvas
from ._colors import color
from ._util import hist

# TODO documentation!!!
# TODO tests
# TODO individuel limits


class Figure(object):
    _COLOR_SEQ = [
        {'names': 'white', 'rgb': (255, 255, 255), 'byte': 0X7},
        {'names': 'red', 'rgb': (255, 0, 0), 'byte': 0x1},
        {'names': 'green', 'rgb': (0, 255, 0), 'byte': 0x2},
        {'names': 'yellow', 'rgb': (255, 255, 0), 'byte': 0x3},
        {'names': 'blue', 'rgb': (0, 0, 255), 'byte': 0x4},
        {'names': 'magenta', 'rgb': (255, 0, 255), 'byte': 0x5},
        {'names': 'cyan', 'rgb': (0, 255, 255), 'byte': 0x6},
    ]

    def __init__(self):
        self._color_seq = iter(cycle(Figure._COLOR_SEQ))
        self._width = None
        self._height = None
        self._x_min = None
        self._x_max = None
        self._y_min = None
        self._y_max = None
        self._color_mode = None
        self._with_colors = True
        self.linesep = os.linesep
        self.background = None
        self.x_label = 'X'
        self.y_label = 'Y'
        self._plots = list()

    @property
    def width(self):
        if self._width is not None:
            return self._width
        return 80

    @width.setter
    def width(self, value):
        if not (isinstance(value, int) and value > 0):
            raise ValueError('Invalid width: {}'.format(value))
        self._width = value

    @property
    def height(self):
        if self._height is not None:
            return self._height
        return 40

    @height.setter
    def height(self, value):
        if not (isinstance(value, int) and value > 0):
            raise ValueError('Invalid height: {}'.format(value))
        self._height = value

    @property
    def color_mode(self):
        if self._color_mode is not None:
            return self._color_mode
        return 'names'

    @color_mode.setter
    def color_mode(self, value):
        if value not in ('names', 'byte', 'rgb'):
            raise ValueError('Only supports: names, byte, rgb!')
        if self._plots != []:
            raise RuntimeError('Change color mode only, when no plots are prepared.')
        self._color_mode = value

    @property
    def with_colors(self):
        return self._with_colors

    @with_colors.setter
    def with_colors(self, value):
        if not isinstance(value, bool):
            raise ValueError('Only bool allowed: "{}"'.format(value))
        self._with_colors = value

    def x_limits(self):
        return self._limits(self._x_min, self._x_max, False)

    def set_x_limits(self, min_=None, max_=None):
        if min_ is not None and max_ is not None:
            if min_ >= max_:
                raise ValueError('min_ is larger or equal than max_.')
            self._x_min = min_
            self._x_max = max_
        elif min_ is not None:
            if self._x_max is not None and min_ >= self._x_max:
                raise ValueError('Previous max is smaller or equal to new min_.')
            self._x_min = min_
        elif max_ is not None:
            if self._x_min is not None and self._x_min >= max_:
                raise ValueError('Previous min is larger or equal to new max_.')
            self._x_max = max_
        else:
            self._x_min = None
            self._x_max = None

    def y_limits(self):
        return self._limits(self._y_min, self._y_max, True)

    def set_y_limits(self, min_=None, max_=None):
        if min_ is not None and max_ is not None:
            if min_ >= max_:
                raise ValueError('min_ is larger or equal than max_.')
            self._y_min = min_
            self._y_max = max_
        elif min_ is not None:
            if self._y_max is not None and min_ >= self._y_max:
                raise ValueError('Previous max is smaller or equal to new min_.')
            self._y_min = min_
        elif max_ is not None:
            if self._y_min is not None and self._y_min >= max_:
                raise ValueError('Previous min is larger or equal to new max_.')
            self._y_max = max_
        else:
            self._y_min = None
            self._y_max = None

    def _limits(self, low_set, high_set, is_height):
        if low_set is not None and high_set is not None:
            return low_set, high_set

        low, high = None, None
        for p in self._plots:
            if is_height:
                _min, _max = _limit(p.height_vals())
            else:
                _min, _max = _limit(p.width_vals())
            if low is None:
                low = _min
                high = _max

            low = min(_min, low)
            high = max(_max, high)

        return _choose(low, high, low_set, high_set)

    def clear(self):
        self._plots.clear()

    def plot(self, X, Y, lc=None, interp='linear', label=None):  # noqa: N803
        if len(X) > 0:
            if lc is None:
                lc = next(self._color_seq)[self.color_mode]
            self._plots += [Plot(X, Y, lc, interp, label)]

    def scatter(self, X, Y, lc=None, label=None):  # noqa: N803
        if len(X) > 0:
            if lc is None:
                lc = next(self._color_seq)[self.color_mode]
            self._plots += [Plot(X, Y, lc, None, label)]

    def histogram(self, X, bins=160, lc=None):  # noqa: N803
        if len(X) > 0:
            if lc is None:
                lc = next(self._color_seq)[self.color_mode]
            self._plots += [Histogram(X, bins, lc)]

    def show(self, legend=False):
        xmin, xmax = self.x_limits()
        ymin, ymax = self.y_limits()
        if all(isinstance(p, Histogram) for p in self._plots):
            ymin = 0
        # create canvas
        canvas = Canvas(self.width, self.height,
                        xmin, ymin, xmax, ymax,
                        self.background, self.color_mode)

        plot_origin = False
        for p in self._plots:
            p.write(canvas, self.with_colors)
            if isinstance(p, Plot):
                plot_origin = True

        if plot_origin:
            # print X / Y origin axis
            canvas.line(xmin, 0, xmax, 0)
            canvas.line(0, ymin, 0, ymax)

        plt = canvas.plot(x_axis=True, x_label=self.x_label, y_axis=True,
                          y_label=self.y_label, linesep=self.linesep)

        if legend:
            plt += '\n\nLegend:\n-------\n'
            plt += '\n'.join([
                color('⠤⠤ {}'.format(p.label if p.label is not None
                                     else 'Label {}'.format(i)),
                      fg=p.lc, mode=self.color_mode, no_color=not self.with_colors)
                for i, p in enumerate(self._plots)
                if isinstance(p, Plot)
            ])
        return plt


class Plot(namedtuple('Plot', ['X', 'Y', 'lc', 'interp', 'label'])):
    def __init__(self, *args, **kwargs):
        super(Plot, self).__init__()
        if len(self.X) != len(self.Y):
            raise ValueError('X and Y dim have to be the same.')
        if self.interp not in ('linear', None):
            raise ValueError('Only "linear" and None are allowed values for `interp`.')

    def width_vals(self):
        return self.X

    def height_vals(self):
        return self.Y

    def write(self, canvas, with_colors):
        # make point iterators
        from_points = zip(self.X, self.Y)
        to_points = zip(self.X, self.Y)

        # remove first point of to_points
        next(to_points)

        color = self.lc if with_colors else None
        # plot points
        for (x0, y0), (x, y) in zip(from_points, to_points):
            canvas.point(x0, y0, color=color)

            canvas.point(x, y, color=color)
            if self.interp == 'linear':
                canvas.line(x0, y0, x, y, color=color)


class Histogram(namedtuple('Histogram', ['X', 'bins', 'lc'])):
    def __init__(self, *args, **kwargs):
        super(Histogram, self).__init__()
        self.frequencies, self.buckets = hist(self.X, self.bins)

    def width_vals(self):
        return self.X

    def height_vals(self):
        return self.frequencies

    def write(self, canvas, with_colors):
        # how fat will one bar of the histogram be
        x_diff = canvas.dots_between(self.buckets[0], 0, self.buckets[1], 0)[0] or 1
        bin_size = (self.buckets[1] - self.buckets[0]) / x_diff

        color = self.lc if with_colors else None
        for i in range(self.bins):
            # for each bucket
            if self.frequencies[i] > 0:
                for j in range(x_diff):
                    # print bar
                    x_ = self.buckets[i] + j * bin_size

                    if canvas.xmin <= x_ <= canvas.xmax:
                        canvas.line(x_, 0,
                                    x_, self.frequencies[i],
                                    color=color)


def _limit(values):
    _min = 0
    _max = 1
    if len(values) > 0:
        _min = min(values)
        _max = max(values)

    return (_min, _max)


def _diff(low, high):
    if low == high:
        if low == 0:
            return 0.5
        else:
            return abs(low * 0.1)
    else:
        return abs(high - low) * 0.1


def _default(low_set, high_set):
    if low_set is None and high_set is None:
        return 0.0, 1.0  # defaults

    if low_set is None and high_set is not None:
        if high_set <= 0:
            return high_set - 1, high_set
        else:
            return 0.0, high_set

    if low_set is not None and high_set is None:
        if low_set >= 1:
            return low_set, low_set + 1
        else:
            return low_set, 1.0

    # Should never get here! => checked in function before


def _choose(low, high, low_set, high_set):
    no_data = low is None and high is None
    if no_data:
        return _default(low_set, high_set)

    else:  # some data
        if low_set is None and high_set is None:
            # no restrictions from user, use low & high
            diff = _diff(low, high)
            return low - diff, high + diff

        if low_set is None and high_set is not None:
            # user sets high end
            if high_set < low:
                # high is smaller than lowest value
                return high_set - 1, high_set

            diff = _diff(low, high_set)
            return low - diff, high_set

        if low_set is not None and high_set is None:
            # user sets low end
            if low_set > high:
                # low is larger than highest value
                return low_set, low_set + 1

            diff = _diff(low_set, high)
            return low_set, high + diff

        # Should never get here! => checked in function before
