"""
Music manipulation.
"""

import io
import pygame
from mido import MidiFile, bpm2tempo, tempo2bpm

class Sounds:
    """Container for multiple sounds.
    Example:
    s = Sounds(moo='moo.wav', boo='boo.mp3')
    s.moo.play()
    """
    def __init__(self, **kwargs):
        for name, file in kwargs.items():
            self.__dict__[name] = pygame.mixer.Sound(file)


class MidiMusic:
    """Class will start and stop infinite loop playback of a given MIDI file.
    Tempo can be changed."""
    def __init__(self, filename):
        self.buffer = io.BytesIO()
        self.mid = MidiFile(filename)
        self.mid.save(file=self.buffer)
        self.buffer.seek(0)
        pygame.mixer.init()
        pygame.mixer.music.load(self.buffer)

    def start(self):
        pygame.mixer.music.play(-1)

    def stop(self):
        pygame.mixer.music.stop()

    def pause(self):
        # music.pause() does not work for midi. instead, just mute and unmute it.
        # can also try to save get_pos(), and then use it to set_pos() when unpause.
        # pygame.mixer.music.pause()
        self.volume_before_pause = pygame.mixer.music.get_volume()
        pygame.mixer.music.set_volume(0)

    def unpause(self):
        # pygame.mixer.music.unpause()
        pygame.mixer.music.set_volume(self.volume_before_pause)

    def set_tempo(self, bpm=None, delta=None):
        """Set first "set_tempo" message to new bpm, or change bpm by delta.
        Integer delta for old+delta, float for old*(1+delta).
        Playback stops and needs to be restarted after."""
        assert not (bpm is None and delta is None)
        track = self.mid.tracks[0]
        for i, msg in enumerate(track):
            if msg.type == 'set_tempo':
                if bpm is None:
                    old_bpm = tempo2bpm(msg.tempo)
                    if isinstance(delta, int):
                        bpm = old_bpm + delta
                    elif isinstance(delta, float):
                        bpm = old_bpm * (1 + delta)
                    else:
                        raise ValueError(f'Unexpected value of delta: {delta}')
                tempo = bpm2tempo(bpm)

                track[i] = msg.copy(tempo=tempo)
                break

        pygame.mixer.music.stop()
        # pygame.mixer.music.unload() <-- will only be added in pygame 2.0. is it a potential memory leak?
        self.buffer.close()
        self.buffer = io.BytesIO()
        self.mid.save(file=self.buffer)
        self.buffer.seek(0)
        pygame.mixer.music.load(self.buffer)


    def dump(self):
        for i, track in enumerate(self.mid.tracks):
            print(f'TRACK {i}')
            for msg in track:
                print(msg)
            print()

def main():
    pygame.init()

    pygame.display.set_mode((150, 50))

    # music = MidiMusic('c_scale.mid')
    music = MidiMusic('assets/mountain_piano_short.mid')
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
                    music.set_tempo(delta=0.1)
                elif event.key == pygame.K_DOWN:
                    music.set_tempo(delta=-0.1)
                elif event.key == pygame.K_SPACE:
                    if pygame.mixer.music.get_volume() > 0:
                        pygame.mixer.music.set_volume(0)
                    else:
                        pygame.mixer.music.set_volume(1)

def test_midi_pause():
    """Looks like pause does not work for MIDI - it works for ogg."""
    pygame.mixer.init()
    pygame.mixer.music.load('assets/mountain_piano_short.mid')
    # pygame.mixer.music.load('assets/mountain_piano_short.ogg')
    pygame.mixer.music.play()
    pygame.time.wait(3000)
    pygame.mixer.music.pause()
    # should pause for 3 seconds - but it keeps playing
    pygame.time.wait(3000)
    pygame.mixer.music.unpause()
    pygame.time.wait(3000)

def test_sounds():
    pygame.mixer.init()
    s = Sounds(moo='assets/sound_eat_good.ogg')
    s.moo.play(5)
    while pygame.mixer.get_busy():
        pygame.time.wait(100)

if __name__ == '__main__':
    pygame.init()

    # main()
    test_sounds()
