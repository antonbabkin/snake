"""
Temporary module to implement music in game.
Music is loaded from a MIDI file, and as the game speed increases, so does the music tempo.
"""

import io
import pygame
from mido import MidiFile


class MidiMusic:
    def __init__(self, filename):
        self.buffer = io.BytesIO()
        self.mid = MidiFile(filename)
        # self.mid.tracks[0] = self.mid.tracks[0][:20]
        self.mid.save(file=self.buffer)
        self.buffer.seek(0)
        pygame.mixer.init()
        pygame.mixer.music.load(self.buffer)

    def start(self):
        print('start')
        pygame.mixer.music.play(-1)

    def stop(self):
        print('stop')
        pygame.mixer.music.stop()

    def set_tempo(self, bpm):
        track = self.mid.tracks[0]
        for idx, msg in enumerate(track):
            if msg.type == 'set_tempo':
                break
        track[idx] = msg.copy(tempo=int(msg.tempo * 1.1))
        self.stop()
        # pygame.mixer.music.unload() <-- will only be added in pygame 2.0. is it a potential memory leak?
        self.buffer.close()
        self.buffer = io.BytesIO()
        self.mid.save(file=self.buffer)
        self.buffer.seek(0)
        pygame.mixer.music.load(self.buffer)
        self.start()

    def dump(self):
        for i, track in enumerate(self.mid.tracks):
            print(f'TRACK {i}')
            for msg in track:
                print(msg)
            print()

def main():
    pygame.init()

    pygame.display.set_mode((150, 50))

    music = MidiMusic('c_scale.mid')
    music.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    music.start()
                elif event.key == pygame.K_LEFT:
                    music.stop()
                elif event.key == pygame.K_d:
                    music.dump()
                elif event.key == pygame.K_UP:
                    music.set_tempo(150)


if __name__ == '__main__':

    main()