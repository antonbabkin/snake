'''
Classic snake game.
'''

import sys
from random import randint

import pygame
from pygame.locals import *

import gridlib

GRID = gridlib.Grid(20, 20)
TILE = pygame.Rect(0, 0, 32, 32)

class TileSprite:
    def __init__(self):
        self.image = pygame.Surface((TILE.w, TILE.h))
        self.rect = TILE.copy()
        self.loc = None

    def _update_rect(self):
        self.rect.x = self.loc.x * TILE.w
        self.rect.y = self.loc.y * TILE.h

    def blit(self, surf):
        surf.blit(self.image, self.rect)


class Apple(TileSprite):
    def __init__(self):
        super().__init__()
        pygame.draw.ellipse(self.image, Color('green'), self.rect.inflate(0, -int(0.2 * TILE.h)))
        self.move()
        
    def move(self):
        self.loc = GRID.random_loc()
        self._update_rect()


class SnakeSegment(TileSprite):
    def __init__(self, x, y):
        super().__init__()
        pygame.draw.ellipse(self.image, Color('purple'), self.rect)
        inner_circle = self.rect.inflate(-int(0.25 * TILE.w), -int(0.25 * TILE.h))
        pygame.draw.ellipse(self.image, Color('blue'), inner_circle)
        self.move(x, y)

    def move(self, x, y):
        self.loc = GRID.loc(x, y)
        self._update_rect()


class Snake:
    def __init__(self, seg_locs, facing, speed=1):
        self.facing = facing
        self.speed = speed
        self.delay = 1000 // self.speed
        self.last_moved = pygame.time.get_ticks()
        self.segs = [SnakeSegment(*x) for x in seg_locs]

    def turn(self, facing):
        self.facing = facing

    def move(self, apple):
        now = pygame.time.get_ticks()
        if now - self.last_moved < self.delay:
            return
        
        head = self.segs[0]
        new_loc = head.loc.step(self.facing)
        head.move(new_loc.x, new_loc.y)

        self.last_moved = now

        if new_loc == apple.loc:
            # grow
            return True

    def blit(self, surf):
        for seg in self.segs:
            seg.blit(surf)
    

def main():
    pygame.init()

    black = Color('black')
    screen = pygame.display.set_mode((GRID.w * TILE.w, GRID.w * TILE.h))

    start_facing = 'e'
    start_speed = 8
    snake = Snake(((0, 0), ), start_facing, start_speed)

    apple = Apple()

    while True:

        for event in pygame.event.get():
            if event.type == QUIT:
                sys.exit()
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    sys.exit()
                elif event.key in (K_w, K_UP):
                    snake.turn('n')
                elif event.key in (K_d, K_RIGHT):
                    snake.turn('e')
                elif event.key in (K_s, K_DOWN):
                    snake.turn('s')
                elif event.key in (K_a, K_LEFT):
                    snake.turn('w')

        got_apple = snake.move(apple)
        if got_apple:
            apple.move()

        screen.fill(black)
        snake.blit(screen)
        apple.blit(screen)
        pygame.display.flip()

        pygame.time.delay(1000 // 60)


if __name__ == '__main__':
    main()