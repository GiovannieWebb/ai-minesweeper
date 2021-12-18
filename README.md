# Artificial Intelligence-Based Minesweeper

## Installation and Start Up Instructions

**Keep in mind that this app requires Kivy to use the GUI. Find the official documentation for Kivy [here](https://kivy.org/doc/stable/gettingstarted/intro.html).**

1. Ensure that you have Kivy installed (official installation instructions [here](https://kivy.org/doc/stable/gettingstarted/installation.html)).
    > NOTE: The following commands assumes use of MacOS. Refer to the [Kivy Official Documentation](https://kivy.org/doc/stable/gettingstarted/installation.html) for the corresponding Windows commands (or other operating system if necessary).

2. Create kivy virtual environment
    > `python3 -m virtualenv kivy_env`

3. Activate kivy virtual environment
    > `source kivy_venv/bin/activate`

4. Play Game!
    > `python3 main.py`

## How To Play

In this game, you are given a rectangular grid of tiles, some of which are bombs. To win, uncover all tiles that are not bombs. Left-click to uncover a tile, right-click to flag a tile that you think is a bomb. Each uncovered tile that is not a bomb will display a number representing how many bombs are adjacent to it. An uncovered tile that is blank has zero bombs adjacent to it. The location of the first tile that isn't a bomb is revealed to the user at the start of the game.

From the main menu, select the difficulty level (Easy, Medium or Hard), select the game mode (Player or Computer), and press PLAY.

- Easy: 9 by 9 board, 10 bombs.
- Medium: 16 by 16 board, 40 bombs.
- Hard: 16 by 30 board, 99 bombs.

"Player" mode is manual play. "Computer" mode attempts to solve a grid using the Constraint Satisfaction Problem as an artificial intelligence technique. After a manual-play game has ended, you are given the option to re-run the game using the AI, and vice versa after computer-play has ended.

Try your best to beat the computer, or use the computer's solutions to help improve your own style of play!
