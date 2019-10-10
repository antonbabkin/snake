'''
Working with grid-like maps.
'''

from random import randrange

def opposite_dir(a, b):
    '''
    Test if direction a is opposite to b.
    >>> opposite_dir('e', 'w')
    True
    >>> opposite_dir('e', 's')
    False
    '''
    opposites = dict(n='s', e='w', s='n', w='e')
    return b == opposites[a]



class Grid:
    def __init__(self, w, h):
        # wraps around edges in both directions, can be customized in future
        self.w = w
        self.h = h

    def loc(self, x, y):
        return Location(self, x, y)

    def random_loc(self):
        x = randrange(0, self.w)
        y = randrange(0, self.h)
        return Location(self, x, y)


class Location:
    def __init__(self, grid, x, y):
        assert 0 <= x < grid.w
        assert 0 <= y < grid.h
        self._grid = grid
        self.x = x
        self.y = y

    def __str__(self):
        return f'({self.x}, {self.y})'

    def __eq__(self, other):
        assert self._grid is other._grid
        return self.x == other.x and self.y == other.y

    def __iter__(self):
        yield self.x
        yield self.y

    def copy(self):
        return Location(self._grid, self.x, self.y)

    def move(self, dx, dy):
        x = (self.x + dx) % self._grid.w
        y = (self.y + dy) % self._grid.h
        return Location(self._grid, x, y)

    def move_ip(self, dx, dy):
        l = self.move(dx, dy)
        self.x = l.x
        self.y = l.y
        return self

    def step(self, dir_):
        if dir_ == 'n':
            return self.move(0, -1)
        if dir_ == 'e':
            return self.move(1, 0)
        if dir_ == 's':
            return self.move(0, 1)
        if dir_ == 'w':
            return self.move(-1, 0)
        raise Exception(f'Unknown step direction: {dir_}')

    def step_ip(self, dir_):
        l = self.step(dir_)
        self.x = l.x
        self.y = l.y
        return self


def angle(dir_a, dir_b):
    """Counterclowise rotation angle between dir_a and dir_b in degrees, multiple of 90.
    Always positive, i.e. possible values are 0, 90, 180 and 360.
    """
    dirs = 'enws'
    idx_a = dirs.index(dir_a)
    idx_b = dirs.index(dir_b)
    return 90 * ((idx_b - idx_a) % 4)


def test_angle():
    for d, a in zip('nwse', (0, 90, 180, 270)):
        assert angle('n', d) == a
        assert angle(d, 'n') == -a % 360
    for d, a in zip('enws', (0, 90, 180, 270)):
        assert angle('e', d) == a
        assert angle(d, 'e') == -a % 360
