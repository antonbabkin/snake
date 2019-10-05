'''
Classic snake game.
'''

import sys
import pygame
from pygame.locals import *

def rect_mod(rect, modulus):
    '''Modulo division: "wrap" rect around modulus.'''
    # ignores x, y of modulus
    rect = rect.copy()
    rect.x %= modulus.w
    rect.y %= modulus.h
    return rect



class Snake:
    seg = pygame.Rect(0, 0, 16, 16)

    def __init__(self, pos, facing, box, speed=1):
        self.image = pygame.image.load('segment.png').convert()
        self.rect = self.image.get_rect(topleft=pos)
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
            self.rect.move_ip(0, -self.seg.w)
        elif self.facing == 'e':
            self.rect.move_ip(self.seg.h, 0)
        elif self.facing == 's':
            self.rect.move_ip(0, self.seg.w)
        elif self.facing == 'w':
            self.rect.move_ip(-self.seg.h, 0)
        
        # wrap around edges
        self.rect = rect_mod(self.rect, self.box)
        
        self.last_moved = now

    def blit(self, surf):
        surf.blit(self.image, self.rect)
    

def main():
    pygame.init()

    black = pygame.Color('black')
    screen = pygame.display.set_mode((640, 480))

    snake = Snake((0, 0), 'e', screen.get_rect(), 16)

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
        screen.fill(black)
        snake.blit(screen)
        pygame.display.flip()
        pygame.time.delay(1000 // 60)


if __name__ == '__main__':
    main()