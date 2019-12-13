"""
Text rendering.
"""

import pygame

def max_font_size_in_rect(text, rect_size):
    """Return largest font size, such that rendered text would fit inside rect."""
    font_size = 0
    text_smaller_than_rect = True
    while text_smaller_than_rect:
        font_size += 1
        font = pygame.font.Font(None, font_size)
        w, h = font.size(text)
        text_smaller_than_rect = (w <= rect_size[0]) and (h <= rect_size[1])
    return font_size - 1


class TextSprite:
    def __init__(self, text, color, font_size=None, rect_size=None, align='center'):
        # if rect_size is used, sprite rect will be withing that rect
        assert (font_size is None) ^ (rect_size is None)
        text = text.split('\n')
        text = [t.strip() for t in text]
        if font_size is None:
            max_height_per_line = rect_size[1] // len(text)
            line_rect = (rect_size[0], max_height_per_line)
            font_size = min(max_font_size_in_rect(t, line_rect) for t in text)
        font = pygame.font.Font(None, font_size)
        sizes = [font.size(t) for t in text]
        sprite_w = max(s[0] for s in sizes)
        sprite_h = sum(s[1] for s in sizes)
        self.image = pygame.Surface((sprite_w, sprite_h)).convert()
        self.image.set_colorkey((0, 0, 0), pygame.RLEACCEL)

        horiz = dict()
        if align == 'left':
            horiz['left'] = 0
        elif align == 'center':
            horiz['centerx'] = sprite_w // 2
        elif align == 'right':
            horiz['right'] = sprite_w
        else:
            raise ValueError(f'align is {align}')

        top = 0
        for t, (w, h) in zip(text, sizes):
            line = font.render(t, True, color)
            dest = line.get_rect(top=top, **horiz)
            self.image.blit(line, dest)
            top += h
        self.rect = self.image.get_rect()

    def draw(self, surf):
        surf.blit(self.image, self.rect)

def font_size_rel_to_abs(rel_size, rect=None):
    if rect is None:
        rect = pygame.display.get_surface().get_rect()
    return int(rel_size * rect.h)


def test_max_font_size_in_rect():
    pygame.font.init()
    text = 'This Is A Test!'
    for w in range(10, 101, 20):
        for h in range(5, 15, 3):
            s = max_font_size_in_rect(text, (w, h))
            print(f'Rect {(w, h)}, font {s}')

def test_TextSprite():
    pygame.init()
    screen = pygame.display.set_mode((400, 400))
    for x in range(0, 400, 50):
        rect = pygame.Rect(0, x, x + 50, 48)
        pygame.draw.rect(screen, (50, 50, 50), rect)
        text = TextSprite('This gunna be gud!', (255, 255, 255), rect_size=rect.size)
        text.rect.topleft = rect.topleft
        text.draw(screen)
    pygame.display.flip()
    while pygame.event.wait().type != pygame.QUIT:
        pass

if __name__ == '__main__':
    # test_max_font_size_in_rect()
    test_TextSprite()