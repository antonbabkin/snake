'''
Classic snake game.
'''

import sys
from random import randint

import pygame
from pygame.locals import *

GRID_W = 20
GRID_H = 20
SEG = pygame.Rect(0, 0, 32, 32)

def rect_mod(rect, modulus):
    '''Modulo division: "wrap" rect around modulus.'''
    # ignores x, y of modulus
    rect = rect.copy()
    rect.x %= modulus.w
    rect.y %= modulus.h
    return rect

class Apple:
    def __init__(self, box):
        self.box = box
        self.image = pygame.Surface((SEG.w, SEG.h))
        self.rect = self.image.get_rect()
        pygame.draw.ellipse(self.image, Color('green'), self.rect.inflate(0, -int(0.2 * SEG.h)))
        
    def move(self):
        grid_x = randint(0, GRID_W - 1)
        grid_y = randint(0, GRID_H - 1)
        self.rect.x = grid_x * SEG.w
        self.rect.y = grid_y * SEG.h

    def blit(self, surf):
        surf.blit(self.image, self.rect)


class Snake:
    def __init__(self, pos, facing, box, speed=1):
        self.image = pygame.Surface((SEG.w, SEG.h))
        self.rect = self.image.get_rect(topleft=pos)
        pygame.draw.ellipse(self.image, Color('purple'), self.rect)
        inner_circle = self.rect.inflate(-int(0.25 * SEG.w), -int(0.25 * SEG.h))
        pygame.draw.ellipse(self.image, Color('blue'), inner_circle)
        self.facing = facing
        self.box = box
        self.speed = speed
        self.delay = 1000 // self.speed
        self.last_moved = pygame.time.get_ticks()

    def turn(self, facing):
        self.facing = facing

    def move(self):
        now = pygame.time.get_ticks()
        if now - self.last_moved < self.delay:
            return
        
        if self.facing == 'n':
            self.rect.move_ip(0, -SEG.w)
        elif self.facing == 'e':
            self.rect.move_ip(SEG.h, 0)
        elif self.facing == 's':
            self.rect.move_ip(0, SEG.w)
        elif self.facing == 'w':
            self.rect.move_ip(-SEG.h, 0)
        
        # wrap around edges
        self.rect = rect_mod(self.rect, self.box)
        
        self.last_moved = now

    def blit(self, surf):
        surf.blit(self.image, self.rect)
    

def main():
    pygame.init()

    black = Color('black')
    screen = pygame.display.set_mode((GRID_W * SEG.w, GRID_H * SEG.h))

    start_pos = (0, 0)
    start_facing = 'e'
    start_speed = 8
    snake = Snake(start_pos, start_facing, screen.get_rect(), start_speed)

    apple = Apple(screen.get_rect())
    apple.move()

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

        snake.move()
        if snake.rect.contains(apple.rect):
            apple.move()

        screen.fill(black)
        snake.blit(screen)
        apple.blit(screen)
        pygame.display.flip()

        pygame.time.delay(1000 // 60)


if __name__ == '__main__':
    main()