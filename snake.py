"""
Classic snake game.
"""

import sys
import enum
from types import SimpleNamespace
import math

import pygame

import gridlib
from text import TextSprite, max_font_size_in_rect
from music import Sounds, MidiMusic


##############################################
# Change these constants to modify game mode #
##############################################
# Fild size in tiles
GRID_W, GRID_H = 15, 15
# Tile size in pixels
TILE_W, TILE_H = 32, 32
# Wrap around field walls
WRAP_AROUND_BOUNDS = False
# New snake length
START_SIZE = 3
# Snake length to win a level
WIN_SIZE = 10
# How many level to win the game
WIN_LEVEL = 10
# New snake speed, tiles per second
START_SPEED = 6
# Number of good apples
GOOD_APPLES = 1
# Number of bad apples
BAD_APPLES = 5


GRID = gridlib.Grid(GRID_W, GRID_H, WRAP_AROUND_BOUNDS)
TILE = pygame.Rect(0, 0, TILE_W, TILE_H)
SCREEN = pygame.Rect(0, 0, GRID_W * TILE_W, GRID_H * TILE_H)


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
        self.transparent_color = (0, 0, 0)
        self.image.set_colorkey(self.transparent_color, pygame.RLEACCEL)
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
        pygame.draw.ellipse(self.image, color, self.rect)
        self.move(infeasible_locs)

    def move(self, infeasible_locs):
        """Move apple to random location, do not move on snake or other apples."""
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
        # erase segment
        self.image.fill(self.transparent_color)

        # draw north-facing head
        # to have symmetry, draw left half and flip
        image_rect = self.image.get_rect()

        # note: due to rounding in coord_rel_to_abs(), this will leave a gap if tile width is odd
        contour_rel = ((0.5, 1), (0, 1), (0, 0.5), (0.2, 0), (0.5, 0))
        contour_abs = [coord_rel_to_abs(c, image_rect) for c in contour_rel]
        pygame.draw.polygon(self.image, cfill, contour_abs)

        nose_size = (math.ceil(TILE.w * 0.05), math.ceil(TILE.h * 0.05))
        nose_left_top = coord_rel_to_abs((0.3, 0.1), image_rect)
        nose = pygame.Rect(nose_left_top, nose_size)
        pygame.draw.rect(self.image, cedge, nose)

        eye_size = (math.ceil(TILE.w * 0.1), math.ceil(TILE.h * 0.1))
        eye_left_top = coord_rel_to_abs((0.2, 0.5), image_rect)
        eye = pygame.Rect(eye_left_top, eye_size)
        pygame.draw.rect(self.image, cedge, eye)

        right_side = pygame.transform.flip(self.image, True, False)
        self.image.blit(right_side, image_rect)

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
        self.speed = START_SPEED + level - 1
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
        hi = max(WIN_LEVEL, 2)
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

    def speed_to_bpm(self):
        steps_per_second = self.speed
        steps_per_minute = steps_per_second * 60
        steps_per_beat = 2
        return steps_per_minute / steps_per_beat

    def turn(self, facing):
        """Change facing direction. Can not turn backward."""
        if facing != self.backward:
            self.facing = facing
            self.segs[0].turn(facing)

    def move(self, apples):
        """
        Move in the facing direction and return result. Grow if got apple.
        Returns: None (no move), 'move', 'apple', 'self', 'wall' or 'size_zero'.
        """
        now = pygame.time.get_ticks()
        if now - self.last_moved < self.delay:
            return None

        head = self.segs[0]
        new_loc = head.loc.step(self.facing)

        if new_loc is None:
            return 'wall'

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
                if len(self) == 1:
                    return 'size_zero'
                elif len(self) == 2:
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

        title = TextSprite('SNAKE', pygame.Color('white'), rect_size=(SCREEN.w * 0.4, SCREEN.h * 0.2))
        title.rect.centerx = SCREEN.centerx
        title.rect.top = SCREEN.h * 0.1
        title.draw(self.image)

        instructions_text = f'''Move around and eat good apples to grow.
        Grow to size {WIN_SIZE} to get to the next level.
        Bad apples ain't good.
        Comlete {WIN_LEVEL} levels to win the game.
        Speed increases with every level.

        CONTROLS
        W, A, S, D, arrow keys: turn
        SPACEBAR: pause
        G: toggle grid lines
        ESC: quit

        Press any key to start'''
        instructions = TextSprite(instructions_text, pygame.Color('white'), rect_size=(SCREEN.w * 0.95, SCREEN.h * 0.7))
        instructions.rect.centerx = SCREEN.centerx
        instructions.rect.top = SCREEN.h * 0.3
        instructions.draw(self.image)

    def draw(self, surf):
        surf.blit(self.image, self.rect)

class OutroScreen:
    def __init__(self):
        self.rect = pygame.display.get_surface().get_rect()
        self.image = pygame.Surface(self.rect.size).convert()
        self.image.fill(COLOR.BACKGROUND)

        text = '''
        Design and programming
        Anton Babkin


        Music

        "Morning Mood"
        "In the Hall of the Mountain King"
        from Peer Gynt Suite by Edvard Grieg

        "Ode to Joy"
        from Symphony No. 9 by Ludwig van Beethoven

        "Funeral March"
        from Piano Sonata No. 2 by Frederic Chopin
        '''
        self.text = TextSprite(text, (255, 255, 255), rect_size=(SCREEN.w * 0.95, SCREEN.h * 0.7))
        self.text.rect.centerx = SCREEN.centerx
        self.text.rect.top = SCREEN.h
        self.text.draw(self.image)

    def update(self):
        if self.text.rect.top > SCREEN.h * 0.2:
            self.text.rect.top -= 1
            self.image.fill(COLOR.BACKGROUND)
            self.text.draw(self.image)

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


class StatusBar:
    def __init__(self):
        screen = pygame.display.get_surface()
        self.rect = screen.get_rect()
        self.image = pygame.Surface(self.rect.size).convert()
        font_size = max_font_size_in_rect('Size: 12  Score: 1234  Level: 12', (SCREEN.w, SCREEN.h * 0.06))
        self.font = pygame.font.Font(None, font_size)
        self.color = pygame.Color('white')
        self.transparent_color = (0, 0, 0)
        self.image.set_colorkey(self.transparent_color, pygame.RLEACCEL)

        self.coord_size = dict(left=self.rect.w * 0.05, bottom=self.rect.bottom)
        self.coord_score = dict(centerx=self.rect.centerx, bottom=self.rect.bottom)
        self.coord_level = dict(right=self.rect.w * 0.95, bottom=self.rect.bottom)
        self.coord_fps = dict(right=self.rect.w * 0.95, top=self.rect.top)

        self.size_rect = self.font.render('Size: 12', True, self.color).get_rect(**self.coord_size)
        self.score_rect = self.font.render('Score: 1234', True, self.color).get_rect(**self.coord_score)
        self.level_rect = self.font.render('Level: 12', True, self.color).get_rect(**self.coord_level)
        self.fps_rect = self.font.render('FPS: 12', True, self.color).get_rect(**self.coord_fps)

    def update(self, size=None, score=None, level=None, fps=None):
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
        if fps is not None:
            self.image.fill(self.transparent_color, self.fps_rect)
            text = f'FPS: {int(fps)}'
            surf = self.font.render(text, True, self.color)
            self.fps_rect = surf.get_rect(**self.coord_fps)
            self.image.blit(surf, self.fps_rect)

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
    LEVEL_UP = enum.auto()
    WIN = enum.auto()
    OUTRO = enum.auto()
    LOSE = enum.auto()

class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init()
        self.sounds = Sounds(**{'eat_good': 'assets/eat_good.ogg',
            'eat_bad': 'assets/eat_bad.ogg',
            'pause': 'assets/pause.ogg',
            'win_level': 'assets/win_level.ogg',
            'lose': 'assets/lose_level.ogg'})

        self.clock = pygame.time.Clock()

        # ignore keyboard input for a given duration after certain events (level up, win, lose)
        self.ignore_input = False
        self.ignore_input_duration = 1000
        self.ignore_input_start_time = pygame.time.get_ticks() - self.ignore_input_duration - 1

        self.screen = pygame.display.set_mode(SCREEN.size)
        pygame.display.set_caption('Snake')
        self.intro = IntroScreen()
        self.background = Background()

        def big_text(text):
            t = TextSprite(text, pygame.Color('white'), rect_size=(SCREEN.w * 0.95, SCREEN.h * 0.2))
            t.rect.center = SCREEN.center
            return t
        def sub_text(text):
            t = TextSprite(text, pygame.Color('white'), rect_size=(SCREEN.w * 0.95, SCREEN.h * 0.05))
            t.rect.center = (SCREEN.centerx, SCREEN.h * 0.7)
            return t

        self.text_pause = big_text('PAUSE')
        self.text_level_up = big_text('Level complete!')
        self.text_win = big_text('You win!')
        self.text_lose = big_text('You lose!')
        self.text_get_ready = sub_text('Press direction to start moving')
        self.text_get_ready.rect.centery = SCREEN.centery
        self.text_press_restart = sub_text('Press any key to restart')
        self.text_level_up_press = sub_text('Press any key to continue')

        self.status_bar = StatusBar()

        self.start_new_game()

    def start_new_game(self):
        pygame.mixer.music.load('assets/intro.mid')
        pygame.mixer.music.play(-1)
        self.outro = OutroScreen()
        self.stats = Stats(self.status_bar)
        self.apples = []
        self.state = GameState.INTRO
        self.after_level_up = False

    def start_new_level(self):
        self.snake = Snake((0, 0), 'n', self.stats.size, self.stats.level)
        self.music.set_tempo(self.snake.speed_to_bpm())
        self.apples = []
        for _ in range(GOOD_APPLES):
            self.apples.append(Apple(True, self.occupied_locs()))
        for _ in range(BAD_APPLES):
            self.apples.append(Apple(False, self.occupied_locs()))
        self.state = GameState.GET_READY

    def occupied_locs(self):
        """List of locations occupied by snake segments or apples."""
        return [s.loc for s in self.snake.segs] + [a.loc for a in self.apples]

    def mainloop(self):
        while True:
            self.clock.tick(60)
            self.events()
            self.logic()
            self.render()


    def events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                sys.exit()

            if event.type != pygame.KEYDOWN or self.ignore_input:
                continue

            if self.state == GameState.WIN:
                self.state = GameState.OUTRO
                pygame.event.pump()
                return

            if self.state in (GameState.OUTRO, GameState.LOSE):
                self.start_new_game()
                pygame.event.pump()
                return

            if self.state == GameState.INTRO:
                pygame.mixer.music.stop()
                self.music = MidiMusic('assets/level.mid')
                self.start_new_level()
                pygame.event.pump()
                return

            if self.state == GameState.LEVEL_UP:
                self.state = GameState.GET_READY
                self.after_level_up = True
                pygame.event.pump()
                return

            self._event_handle_pause(event)
            self._event_handle_dir(event)
            self._event_handle_grid(event)


    def _event_handle_pause(self, event):
        if event.key == pygame.K_SPACE:
            if self.state == GameState.PAUSE:
                self.music.unpause()
                self.sounds.pause.play()
                self.state = GameState.RUN
            elif self.state == GameState.RUN:
                self.sounds.pause.play()
                self.music.pause()
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
            self.music.start()
            self.state = GameState.RUN

    def _event_handle_grid(self, event):
        if event.key == pygame.K_g:
            self.background.toggle_grid_lines()

    def logic(self):
        if self.state == GameState.GET_READY and self.after_level_up:
            self.stats.level_up()
            self.start_new_level()
            self.after_level_up = False

        if pygame.time.get_ticks() > self.ignore_input_start_time + self.ignore_input_duration:
            self.ignore_input = False

        if self.state == GameState.OUTRO:
            self.outro.update()

        if self.state != GameState.RUN:
            return

        move_result = self.snake.move(self.apples)
        if isinstance(move_result, Apple):
            apple = move_result
            apple.move(self.occupied_locs())
            if apple.good:
                self.stats.size_up()
                self.sounds.eat_good.play()
            else:
                self.stats.size_down()
                self.sounds.eat_bad.play()
            assert self.stats.size == len(self.snake)

            if len(self.snake) == WIN_SIZE:
                self.music.stop()
                self.ignore_input = True
                self.ignore_input_start_time = pygame.time.get_ticks()
                if self.stats.level == WIN_LEVEL:
                    self.state = GameState.WIN
                    pygame.mixer.music.load('assets/win_game.mid')
                    pygame.mixer.music.play(-1)
                else:
                    self.state = GameState.LEVEL_UP
                    self.sounds.win_level.play()


        elif move_result in ('self', 'wall', 'size_zero'):
            self.state = GameState.LOSE
            self.music.stop()
            self.ignore_input = True
            self.ignore_input_start_time = pygame.time.get_ticks()
            self.sounds.lose.play()
            pygame.mixer.music.load('assets/lose_game.mid')
            pygame.mixer.music.play()

        self.status_bar.update(fps=self.clock.get_fps())

    def render(self):
        if self.state == GameState.INTRO:
            self.intro.draw(self.screen)
        elif self.state == GameState.OUTRO:
            self.outro.draw(self.screen)
        else:
            self.background.draw(self.screen)
            self.snake.blit(self.screen)
            for apple in self.apples:
                apple.blit(self.screen)
            if self.state == GameState.PAUSE:
                self.text_pause.draw(self.screen)
            elif self.state == GameState.GET_READY:
                self.text_get_ready.draw(self.screen)
            elif self.state == GameState.LEVEL_UP:
                self.text_level_up.draw(self.screen)
                if not self.ignore_input:
                    self.text_level_up_press.draw(self.screen)
            elif self.state == GameState.WIN:
                self.text_win.draw(self.screen)
                if not self.ignore_input:
                    self.text_press_restart.draw(self.screen)
            elif self.state == GameState.LOSE:
                self.text_lose.draw(self.screen)
                if not self.ignore_input:
                    self.text_press_restart.draw(self.screen)
            self.status_bar.draw(self.screen)

        pygame.display.flip()


def main():
    """Run game app."""
    game = Game()
    game.mainloop()


if __name__ == '__main__':
    main()
