# snake
Classic snake game.

Learning game dev with Python and pygame.

## roadmap

- first screen with instructions
- levels: start from minimal size and speed, increase speed and restart when max size reached
- snake changes color as speed increases, from blue to red
- good and bad apples: good grow, bad shrink
- polish and balance: colors, speed progression, win size, total levels.
- install instructions and demo gif in readme, binary package on github releases


## issues

- use transparency in all sprites so that they do not cover grid lines
- win screen: any key takes to next level, lose screen: any key restarts game
- status bar: add fps (pygame.time.Clock.get_fps())