'''
Classic snake game.
'''

import sys
from types import SimpleNamespace

import pygame

import gridlib

GRID = gridlib.Grid(10, 10)
TILE = pygame.Rect(0, 0, 32, 32)

class COLOR(SimpleNamespace):
    BACKGROUND = pygame.Color('black')
    APPLE = pygame.Color('green')
    SNAKE_EDGE = pygame.Color('purple')
    SNAKE_FILL = pygame.Color('blue')

class TileSprite:
    '''Base class to represent single tile sprites.'''
    def __init__(self):
        self.image = pygame.Surface((TILE.w, TILE.h))
        self.rect = TILE.copy()
        self.loc = None

    def _update_rect(self):
        self.rect.x = self.loc.x * TILE.w
        self.rect.y = self.loc.y * TILE.h

    def blit(self, surf):
        '''Blit sprite image onto surface.'''
        surf.blit(self.image, self.rect)

class Apple(TileSprite):
    '''Apple that the snake eats to grow.'''
    def __init__(self):
        super().__init__()
        pygame.draw.ellipse(self.image, COLOR.APPLE,
                            self.rect.inflate(0, -int(0.2 * TILE.h)))
        self.move()

    def move(self):
        '''Move apple to random location.'''
        self.loc = GRID.random_loc()
        self._update_rect()


class SnakeSegment(TileSprite):
    '''Single segment of a snake.'''
    def __init__(self, x, y):
        super().__init__()
        pygame.draw.ellipse(self.image, COLOR.SNAKE_EDGE, self.rect)
        fill_circle = self.rect.inflate(-int(0.25 * TILE.w), -int(0.25 * TILE.h))
        pygame.draw.ellipse(self.image, COLOR.SNAKE_FILL, fill_circle)
        self.move(x, y)

    def move(self, x, y):
        '''Move segment to (x, y) location on grid.'''
        self.loc = GRID.loc(x, y)
        self._update_rect()


class Snake:
    '''Snake consisting of multiple segments.'''
    def __init__(self, seg_locs, facing, speed=1):
        self.facing = facing
        self.speed = speed
        self.delay = 1000 // self.speed
        self.last_moved = pygame.time.get_ticks()
        self.segs = [SnakeSegment(*x) for x in seg_locs]

    def turn(self, facing):
        '''Change facing direction. Can not turn backwards.'''
        if not gridlib.opposite_dir(self.facing, facing):
            self.facing = facing

    def move(self, apple):
        '''
        Move in the facing direction and return result. Grow if got apple.
        Returns: None (no move), 'move', 'apple', 'self'.
        '''
        now = pygame.time.get_ticks()
        if now - self.last_moved < self.delay:
            return None

        head = self.segs[0]
        new_loc = head.loc.step(self.facing)

        if new_loc == apple.loc:
            result = 'apple'
            new_head = SnakeSegment(*new_loc)
            self.segs.insert(0, new_head)
        elif self.collide(new_loc):
            result = 'self'
        else:
            result = 'move'
            tail = self.segs.pop()
            tail.move(*new_loc)
            self.segs.insert(0, tail)

        self.last_moved = now
        return result

    def collide(self, loc):
        '''Test if loc collides with any segment.'''
        return any(loc == seg.loc for seg in self.segs)

    def blit(self, surf):
        '''Blit whole snake images onto surface.'''
        for seg in self.segs:
            seg.blit(surf)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GRID.w * TILE.w, GRID.w * TILE.h))
        start_facing = 'e'
        self.snake = Snake(((4, 4), (3, 4)), start_facing, 12)
        self.apple = Apple()

    def mainloop(self):
        while True:
            pygame.time.delay(1000 // 60)
            self.events()
            self.logic()
            self.render()

    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    sys.exit()
                elif event.key in (pygame.K_w, pygame.K_UP):
                    self.snake.turn('n')
                elif event.key in (pygame.K_d, pygame.K_RIGHT):
                    self.snake.turn('e')
                elif event.key in (pygame.K_s, pygame.K_DOWN):
                    self.snake.turn('s')
                elif event.key in (pygame.K_a, pygame.K_LEFT):
                    self.snake.turn('w')
        
    def logic(self):
        move_result = self.snake.move(self.apple)
        if move_result == 'apple':
            apple_on_snake = True
            while apple_on_snake:
                self.apple.move()
                apple_on_snake = self.snake.collide(self.apple.loc)
        elif move_result == 'self':
            print('game over')
            pygame.time.delay(2000)
            sys.exit()

    def render(self):
        self.screen.fill(COLOR.BACKGROUND)
        self.snake.blit(self.screen)
        self.apple.blit(self.screen)
        pygame.display.flip()


def main():
    '''Run game app.'''
    game = Game()
    game.mainloop()


if __name__ == '__main__':
    main()
