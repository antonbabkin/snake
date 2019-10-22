"""
Classic snake game.
"""

import sys
import enum
from types import SimpleNamespace
import math

import pygame

import gridlib

GRID = gridlib.Grid(15, 15)
TILE = pygame.Rect(0, 0, 32, 32)
START_SIZE = 3
WIN_SIZE = 10
WIN_LEVEL = 10
APPLES = 4 # 1 good, other bad

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
    def __init__(self, good, infeasible_locs):
        super().__init__()
        self.good = good
        color = (0, 255, 0) if good else (150, 75, 0)
        pygame.draw.ellipse(self.image, color,
                            self.rect.inflate(0, -int(0.2 * TILE.h)))
        self.move(infeasible_locs)

    def move(self, infeasible_locs):
        """Move apple to random location, do not move on snake."""
        feasible = False
        while not feasible:
            new_loc = GRID.random_loc()
            if new_loc not in infeasible_locs:
                feasible = True
        self.loc = new_loc
        self._update_rect()


class SnakeSegment(TileSprite):
    """Single segment of a snake."""
    def __init__(self, x, y, colors):
        super().__init__()
        cfill, cedge = colors
        pygame.draw.ellipse(self.image, cedge, self.rect)
        fill_circle = self.rect.inflate(-int(0.25 * TILE.w), -int(0.25 * TILE.h))
        pygame.draw.ellipse(self.image, cfill, fill_circle)
        self.move(x, y)

    def move(self, x, y):
        """Move segment to (x, y) location on grid."""
        self.loc = GRID.loc(x, y)
        self._update_rect()


class SnakeHead(SnakeSegment):
    """Snake head."""
    def __init__(self, x, y, facing, colors):
        cfill, cedge = colors
        super().__init__(x, y, colors)

        # draw north-facing head
        image_rect = self.image.get_rect()
        self.image.fill(COLOR.BACKGROUND)

        contour_rel = ((0, 1), (0, 0.5), (0.2, 0), (0.8, 0), (1, 0.5), (1, 1))
        contour_abs = [coord_rel_to_abs(c, image_rect) for c in contour_rel]
        pygame.draw.polygon(self.image, cfill, contour_abs)

        nose_size = (math.ceil(TILE.w * 0.05), math.ceil(TILE.h * 0.05))
        left_nose_center = coord_rel_to_abs((0.3, 0.1), image_rect)
        left_nose = pygame.Rect(left_nose_center, nose_size)
        pygame.draw.rect(self.image, cedge, left_nose)
        right_nose_center = coord_rel_to_abs((0.7, 0.1), image_rect)
        right_nose = pygame.Rect(right_nose_center, nose_size)
        pygame.draw.rect(self.image, cedge, right_nose)

        eye_size = (math.ceil(TILE.w * 0.1), math.ceil(TILE.h * 0.1))
        left_eye_center = coord_rel_to_abs((0.2, 0.5), image_rect)
        left_eye = pygame.Rect(left_eye_center, eye_size)
        pygame.draw.rect(self.image, cedge, left_eye)
        right_eye_center = coord_rel_to_abs((0.8, 0.5), image_rect)
        right_eye = pygame.Rect(right_eye_center, eye_size)
        pygame.draw.rect(self.image, cedge, right_eye)

        self.facing = 'n'
        self.turn(facing)

    def turn(self, facing):
        rotation = gridlib.angle(self.facing, facing)
        self.image = pygame.transform.rotate(self.image, rotation)
        self.facing = facing


class Snake:
    """Snake consisting of multiple segments."""
    def __init__(self, head_loc, facing, size, level):
        self.facing = facing
        self.backward = gridlib.opposite_dir(facing)
        # speed in steps per second
        self.speed = level + 4
        self.delay = 1000 // self.speed
        self.colors = self._colors_from_level(level)
        self.last_moved = pygame.time.get_ticks()
        head = SnakeHead(*head_loc, facing, self.colors)
        self.segs = [head]
        seg_loc = head.loc
        for _ in range(1, size):
            seg_loc = seg_loc.step(self.backward)
            self.segs.append(SnakeSegment(*seg_loc, self.colors))

    @staticmethod
    def _colors_from_level(level):
        lo = 1
        hi = WIN_LEVEL
        wlo = (hi - level) / (hi - lo)
        whi = 1 - wlo
        clo = (0, 0, 255)
        chi = (255, 0, 0)
        r = int(clo[0] * wlo + chi[0] * whi)
        g = int(clo[1] * wlo + chi[1] * whi)
        b = int(clo[2] * wlo + chi[2] * whi)
        fill = (r, g, b)
        edge = (r, 255, b)
        return fill, edge

    def __len__(self):
        return len(self.segs)

    def turn(self, facing):
        """Change facing direction. Can not turn backward."""
        if facing != self.backward:
            self.facing = facing
            self.segs[0].turn(facing)

    def move(self, apples):
        """
        Move in the facing direction and return result. Grow if got apple.
        Returns: None (no move), 'move', 'apple', 'self'.
        """
        now = pygame.time.get_ticks()
        if now - self.last_moved < self.delay:
            return None

        head = self.segs[0]
        new_loc = head.loc.step(self.facing)

        hit_apple = None
        for apple in apples:
            if new_loc == apple.loc:
                hit_apple = apple
                break

        if hit_apple is not None:
            result = hit_apple
            if hit_apple.good:
                new_neck = SnakeSegment(*head.loc, self.colors)
                self.segs.insert(1, new_neck)
            else:
                if len(self) == 2:
                    # head + 1 segment: delete that segment
                    self.segs.pop()
                elif len(self) > 2:
                    # head + 2 or more segments: delete tail, move pre-tail
                    self.segs.pop()
                    tail = self.segs.pop()
                    tail.move(*head.loc)
                    self.segs.insert(1, tail)

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


class IntroScreen:
    def __init__(self):
        self.rect = pygame.display.get_surface().get_rect()
        self.image = pygame.Surface(self.rect.size).convert()
        self.image.fill(COLOR.BACKGROUND)

        def render(text, grid_row, text_size=1):
            font = pygame.font.Font(None, TILE.h * text_size)
            surf = font.render(text, True, pygame.Color('white'))
            rect = surf.get_rect(top=TILE.h * grid_row, centerx=self.rect.centerx)
            self.image.blit(surf, rect)

        render('SNAKE', 2, 3)
        render('Move around and eat good apples to grow.', 6)
        render(f'Grow to size {WIN_SIZE} to get to the next level.', 7)
        render('Speed increases with every level.', 8)
        render('If snake bites itself it dies.', 9)
        render('CONTROLS', 11)
        render('W, A, S, D, arrow keys: turn', 12)
        render('spacebar: pause', 13)
        render('G: toggle grid lines', 14)
        render('ESC: quit', 15)
        render('Press any key to start.', 18)


    def draw(self, surf):
        surf.blit(self.image, self.rect)

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
    def __init__(self):
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

        self.size_rect = self.font.render('Size: XXX', True, self.color).get_rect(**self.coord_size)
        self.score_rect = self.font.render('Score: XXX', True, self.color).get_rect(**self.coord_score)
        self.level_rect = self.font.render('Level: XXX', True, self.color).get_rect(**self.coord_level)


    def update(self, size=None, score=None, level=None):
        if size is not None:
            self.image.fill(self.transparent_color, self.size_rect)
            text = f'Size: {size}'
            surf = self.font.render(text, True, self.color)
            self.size_rect = surf.get_rect(**self.coord_size)
            self.image.blit(surf, self.size_rect)
        if score is not None:
            self.image.fill(self.transparent_color, self.score_rect)
            text = f'Score: {score}'
            surf = self.font.render(text, True, self.color)
            self.score_rect = surf.get_rect(**self.coord_score)
            self.image.blit(surf, self.score_rect)
        if level is not None:
            self.image.fill(self.transparent_color, self.level_rect)
            text = f'Level: {level}'
            surf = self.font.render(text, True, self.color)
            self.level_rect = surf.get_rect(**self.coord_level)
            self.image.blit(surf, self.level_rect)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

class Stats:
    """Game stats: size, score, level."""
    def __init__(self, status_bar):
        self.status_bar = status_bar
        self.size = START_SIZE
        self.score = 0
        self.level = 1
        self.status_bar.update(size=self.size, score=self.score, level=self.level)

    def level_up(self):
        self.level += 1
        self.size = START_SIZE
        self.status_bar.update(size=self.size, level=self.level)

    def size_up(self):
        self.size += 1
        self.score += self.level
        self.status_bar.update(size=self.size, score=self.score)

    def size_down(self):
        if self.size == 1:
            return
        self.size -= 1
        self.status_bar.update(size=self.size)


class GameState(enum.Enum):
    INTRO = enum.auto()
    GET_READY = enum.auto()
    RUN = enum.auto()
    PAUSE = enum.auto()
    WIN = enum.auto()
    LOSE = enum.auto()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((GRID.w * TILE.w, GRID.w * TILE.h))
        self.intro = IntroScreen()
        self.background = Background()
        self.text_pause = Text('PAUSE', pygame.Color('white'))
        self.text_win = Text('You win!', pygame.Color('white'))
        self.text_lose = Text('You lose!', pygame.Color('white'))
        self.status_bar = StatusBar()

        self.stats = Stats(self.status_bar)
        self.snake = None
        self.apples = []
        self.state = GameState.INTRO

    def _start_new_level(self):
        self.snake = Snake((3, 3), 's', self.stats.size, self.stats.level)
        self.apples = [Apple(True, self.occupied_locs())]
        for _ in range(1, APPLES):
            self.apples.append(Apple(False, self.occupied_locs()))
        self.state = GameState.GET_READY

    def occupied_locs(self):
        """Generator returns locations occupied by snake segments or apples."""
        for seg in self.snake.segs:
            yield seg.loc
        for apple in self.apples:
            yield apple.loc

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

            if self.state == GameState.INTRO:
                self._start_new_level()
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

        move_result = self.snake.move(self.apples)
        if isinstance(move_result, Apple):
            apple = move_result
            apple.move(self.occupied_locs())
            if apple.good:
                self.stats.size_up()
            else:
                self.stats.size_down()
            assert self.stats.size == len(self.snake)

            if len(self.snake) == WIN_SIZE:
                if self.stats.level == WIN_LEVEL:
                    self.state = GameState.WIN
                else:
                    self.stats.level_up()
                    self._start_new_level()

        elif move_result == 'self':
            self.state = GameState.LOSE

    def render(self):
        if self.state == GameState.INTRO:
            self.intro.draw(self.screen)
        else:
            self.background.draw(self.screen)
            self.snake.blit(self.screen)
            for apple in self.apples:
                apple.blit(self.screen)
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


if __name__ == '__main__':
    main()
