"""
Classic snake game.
"""

import sys
import enum
from types import SimpleNamespace
import math

import pygame

import gridlib

GRID = gridlib.Grid(20, 20)
TILE = pygame.Rect(0, 0, 32, 32)
START_SIZE = 2
START_LEVEL = 1
WIN_SIZE = 10

def coord_rel_to_abs(coords, rect):
    """Return coordinate tuple changed from relative to absolute within rect.
    In relative coordinates, top-left is (0, 0) and bottom-right is (1, 1).
    """
    x, y = coords
    x = rect.x + int(rect.w * x)
    y = rect.y + int(rect.h * y)
    return x, y


class COLOR(SimpleNamespace):
    BACKGROUND = pygame.Color('black')
    APPLE = pygame.Color('green')
    SNAKE_EDGE = pygame.Color('purple')
    SNAKE_FILL = pygame.Color('blue')
    GRID_LINE = pygame.Color('gray')

class TileSprite:
    """Base class to represent single tile sprites."""
    def __init__(self):
        self.image = pygame.Surface((TILE.w, TILE.h))
        self.rect = TILE.copy()
        self.loc = None

    def _update_rect(self):
        self.rect.x = self.loc.x * TILE.w
        self.rect.y = self.loc.y * TILE.h

    def blit(self, surf):
        """Blit sprite image onto surface."""
        surf.blit(self.image, self.rect)

class Apple(TileSprite):
    """Apple that the snake eats to grow."""
    def __init__(self):
        super().__init__()
        pygame.draw.ellipse(self.image, COLOR.APPLE,
                            self.rect.inflate(0, -int(0.2 * TILE.h)))
        self.move()

    def move(self):
        """Move apple to random location."""
        self.loc = GRID.random_loc()
        self._update_rect()


class SnakeSegment(TileSprite):
    """Single segment of a snake."""
    def __init__(self, x, y):
        super().__init__()
        pygame.draw.ellipse(self.image, COLOR.SNAKE_EDGE, self.rect)
        fill_circle = self.rect.inflate(-int(0.25 * TILE.w), -int(0.25 * TILE.h))
        pygame.draw.ellipse(self.image, COLOR.SNAKE_FILL, fill_circle)
        self.move(x, y)

    def move(self, x, y):
        """Move segment to (x, y) location on grid."""
        self.loc = GRID.loc(x, y)
        self._update_rect()


class SnakeHead(SnakeSegment):
    """Snake head."""
    def __init__(self, x, y, facing):
        super().__init__(x, y)
        # draw north-facing head
        image_rect = self.image.get_rect()
        self.image.fill(COLOR.BACKGROUND)

        contour_rel = ((0, 1), (0, 0.5), (0.2, 0), (0.8, 0), (1, 0.5), (1, 1))
        contour_abs = [coord_rel_to_abs(c, image_rect) for c in contour_rel]
        pygame.draw.polygon(self.image, COLOR.SNAKE_FILL, contour_abs)

        nose_size = (math.ceil(TILE.w * 0.05), math.ceil(TILE.h * 0.05))
        left_nose_center = coord_rel_to_abs((0.3, 0.1), image_rect)
        left_nose = pygame.Rect(left_nose_center, nose_size)
        pygame.draw.rect(self.image, COLOR.SNAKE_EDGE, left_nose)
        right_nose_center = coord_rel_to_abs((0.7, 0.1), image_rect)
        right_nose = pygame.Rect(right_nose_center, nose_size)
        pygame.draw.rect(self.image, COLOR.SNAKE_EDGE, right_nose)

        eye_size = (math.ceil(TILE.w * 0.1), math.ceil(TILE.h * 0.1))
        left_eye_center = coord_rel_to_abs((0.2, 0.5), image_rect)
        left_eye = pygame.Rect(left_eye_center, eye_size)
        pygame.draw.rect(self.image, COLOR.SNAKE_EDGE, left_eye)
        right_eye_center = coord_rel_to_abs((0.8, 0.5), image_rect)
        right_eye = pygame.Rect(right_eye_center, eye_size)
        pygame.draw.rect(self.image, COLOR.SNAKE_EDGE, right_eye)

        self.facing = 'n'
        self.turn(facing)

    def turn(self, facing):
        rotation = gridlib.angle(self.facing, facing)
        self.image = pygame.transform.rotate(self.image, rotation)
        self.facing = facing


class Snake:
    """Snake consisting of multiple segments."""
    def __init__(self, seg_locs, facing, speed=1):
        self.facing = facing
        self.backward = gridlib.opposite_dir(facing)
        self.speed = speed
        self.delay = 1000 // self.speed
        self.last_moved = pygame.time.get_ticks()
        self.segs = [SnakeHead(*seg_locs[0], facing)]
        self.segs += [SnakeSegment(*x) for x in seg_locs[1:]]

    def __len__(self):
        return len(self.segs)

    def turn(self, facing):
        """Change facing direction. Can not turn backward."""
        if facing != self.backward:
            self.facing = facing
            self.segs[0].turn(facing)

    def move(self, apple):
        """
        Move in the facing direction and return result. Grow if got apple.
        Returns: None (no move), 'move', 'apple', 'self'.
        """
        now = pygame.time.get_ticks()
        if now - self.last_moved < self.delay:
            return None

        head = self.segs[0]
        new_loc = head.loc.step(self.facing)

        if new_loc == apple.loc:
            result = 'apple'
            new_neck = SnakeSegment(*head.loc)
            self.segs.insert(1, new_neck)
            head.move(*new_loc)
        elif self.collide(new_loc):
            result = 'self'
        else:
            result = 'move'
            tail = self.segs.pop()
            tail.move(*head.loc)
            self.segs.insert(1, tail)
            head.move(*new_loc)

        self.backward = gridlib.opposite_dir(self.facing)
        self.last_moved = now
        return result

    def collide(self, loc):
        """Test if loc collides with any segment."""
        return any(loc == seg.loc for seg in self.segs)

    def blit(self, surf):
        """Blit whole snake images onto surface."""
        for seg in self.segs:
            seg.blit(surf)


class Background:
    def __init__(self):
        self.grid_lines = False
        self.rect = pygame.display.get_surface().get_rect()
        self.image = pygame.Surface(self.rect.size).convert()
        self.image.fill(COLOR.BACKGROUND)

    def _draw_grid_lines(self):
        for x in range(-1, self.rect.w, TILE.w):
            pygame.draw.line(self.image, COLOR.GRID_LINE, (x, 0), (x, self.rect.h), 2)
        for y in range(-1, self.rect.h, TILE.h):
            pygame.draw.line(self.image, COLOR.GRID_LINE, (0, y), (self.rect.w, y), 2)

    def toggle_grid_lines(self):
        if self.grid_lines:
            self.image.fill(COLOR.BACKGROUND)
            self.grid_lines = False
        else:
            self._draw_grid_lines()
            self.grid_lines = True

    def draw(self, surf):
        surf.blit(self.image, self.rect)

class Text:
    def __init__(self, text, color, center=None):
        font = pygame.font.Font(None, 128)
        self.image = font.render(text, True, color)
        if center is None:
            center = pygame.display.get_surface().get_rect().center
        self.rect = self.image.get_rect(center=center)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

class StatusBar:
    def __init__(self, size, score, level):
        self.image = pygame.Surface((GRID.w * TILE.w, TILE.h)).convert()
        self.rect = self.image.get_rect(bottom=GRID.h * TILE.h)
        self.font = pygame.font.Font(None, int(TILE.h * 0.9))
        self.color = pygame.Color('white')
        self.transparent_color = (0, 0, 0)
        self.image.set_colorkey(self.transparent_color, pygame.RLEACCEL)

        surf_rect = self.image.get_rect()
        self.coord_size = dict(left=int(TILE.w * 0.5), centery=surf_rect.centery)
        self.coord_score = dict(centerx=surf_rect.centerx, centery=surf_rect.centery)
        self.coord_level = dict(right=surf_rect.right - int(TILE.w * 0.5), centery=surf_rect.centery)

        self.update(level=level, size=size, score=score)


    def update(self, size=None, score=None, level=None):
        if size is not None:
            text = f'Size: {size}'
            surf = self.font.render(text, True, self.color)
            rect = surf.get_rect(**self.coord_size)
            self.image.fill(self.transparent_color, rect)
            self.image.blit(surf, rect)
        if score is not None:
            text = f'Score: {score}'
            surf = self.font.render(text, True, self.color)
            rect = surf.get_rect(**self.coord_score)
            self.image.fill(self.transparent_color, rect)
            self.image.blit(surf, rect)
        if level is not None:
            text = f'Level: {level}'
            surf = self.font.render(text, True, self.color)
            rect = surf.get_rect(**self.coord_level)
            self.image.fill(self.transparent_color, rect)
            self.image.blit(surf, rect)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

class Stats:
    """Game stats: size, level, score."""
    def __init__(self):
        self.size = START_SIZE
        self.level = START_LEVEL
        self.score = 0

    def next_level(self):
        self.level += 1
        self.size = START_SIZE

    def next_size(self):
        self.size += 1
        self.score += self.level


class GameState(enum.Enum):
    GET_READY = enum.auto()
    RUN = enum.auto()
    PAUSE = enum.auto()
    WIN = enum.auto()
    LOSE = enum.auto()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GRID.w * TILE.w, GRID.w * TILE.h))
        self.background = Background()
        self.status_bar = StatusBar(2, 0, 1)
        start_facing = 'e'
        self.snake = Snake(((4, 4), (3, 4)), start_facing, 10)
        self.apple = Apple()
        self.state = GameState.GET_READY
        self.stats = Stats()
        self.text_pause = Text('PAUSE', pygame.Color('white'))
        self.text_win = Text('You win!', pygame.Color('white'))
        self.text_lose = Text('You lose!', pygame.Color('white'))

    def mainloop(self):
        clock = pygame.time.Clock()
        while True:
            clock.tick(60)
            self.events()
            self.logic()
            self.render()


    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                sys.exit()

            if self.state in (GameState.WIN, GameState.LOSE):
                continue

            if event.type != pygame.KEYDOWN:
                continue

            self._event_handle_pause(event)
            self._event_handle_dir(event)
            self._event_handle_grid(event)


    def _event_handle_pause(self, event):
        if event.key == pygame.K_SPACE:
            if self.state == GameState.PAUSE:
                self.state = GameState.RUN
            elif self.state == GameState.RUN:
                self.state = GameState.PAUSE


    def _event_handle_dir(self, event):
        if self.state == GameState.PAUSE:
            return

        if event.key in (pygame.K_w, pygame.K_UP):
            dir_ = 'n'
        elif event.key in (pygame.K_d, pygame.K_RIGHT):
            dir_ = 'e'
        elif event.key in (pygame.K_s, pygame.K_DOWN):
            dir_ = 's'
        elif event.key in (pygame.K_a, pygame.K_LEFT):
            dir_ = 'w'
        else:
            return
        self.snake.turn(dir_)

        if self.state == GameState.GET_READY and dir_ != self.snake.backward:
            self.state = GameState.RUN

    def _event_handle_grid(self, event):
        if event.key == pygame.K_g:
            self.background.toggle_grid_lines()

    def logic(self):
        if self.state != GameState.RUN:
            return

        move_result = self.snake.move(self.apple)
        if move_result == 'apple':
            apple_on_snake = True
            while apple_on_snake:
                self.apple.move()
                apple_on_snake = self.snake.collide(self.apple.loc)
            self.stats.next_size()
            assert self.stats.size == len(self.snake)
            self.status_bar.update(size=self.stats.size, score=self.stats.score)
            if len(self.snake) == WIN_SIZE:
                self.state = GameState.WIN
        elif move_result == 'self':
            self.state = GameState.LOSE

    def render(self):
        self.background.draw(self.screen)
        self.snake.blit(self.screen)
        self.apple.blit(self.screen)
        if self.state == GameState.PAUSE:
            self.text_pause.draw(self.screen)
        elif self.state == GameState.WIN:
            self.text_win.draw(self.screen)
        elif self.state == GameState.LOSE:
            self.text_lose.draw(self.screen)
        self.status_bar.draw(self.screen)
        pygame.display.flip()


def main():
    """Run game app."""
    game = Game()
    game.mainloop()

def test_head():
    """Test head segment rendering."""
    pygame.init()
    screen = pygame.display.set_mode((GRID.w * TILE.w, GRID.w * TILE.h))
    screen.fill(COLOR.BACKGROUND)
    head = SnakeHead(4, 4, 'n')
    head.blit(screen)
    pygame.display.flip()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
        pygame.time.delay(200)

if __name__ == '__main__':
    main()
