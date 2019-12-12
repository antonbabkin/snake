"""
Text rendering.
"""

import pygame


class TextSprite:
    def __init__(self, text, color, size, align='center'):
        text = text.split('\n')
        text = [t.strip() for t in text]
        font = pygame.font.Font(None, size)
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

