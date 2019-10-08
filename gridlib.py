'''
Working with grid-like maps.
'''

from random import randrange


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
        self.grid = grid
        self.x = x
        self.y = y

    def __eq__(self, other):
        assert self.grid is other.grid
        return self.x == other.x and self.y == other.y
    
    def move(self, dx, dy):
        x = (self.x + dx) % self.grid.w
        y = (self.y + dy) % self.grid.h
        return Location(self.grid, x, y)

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