import kivy
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton, ToggleButtonBehavior
from kivy.uix.image import Image
from kivy.factory import Factory
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.app import App
from kivy.config import Config
import time
import random
import scipy
import scipy.ndimage
import numpy as np
import sys
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
kivy.require('2.0.0')

NUM_BOMBS = {"easy": 10, "medium": 40, "hard": 99}
NUM_ROWS = {"easy": 9, "medium": 16, "hard": 30}
NUM_COLS = {"easy": 9, "medium": 16, "hard": 16}
SAFE_TILES_COVERED = sys.maxsize
START_TIME = 0


class GameOverPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MSTile(Image, ToggleButtonBehavior):
    row_number = 0
    col_number = 0
    is_bomb = False
    is_flagged = False
    adjacent_bombs = 0
    is_uncovered = False

    last_touch_button = Factory.StringProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False

    def truncate_decimal(self, s, n):
        """
        Truncates the decimal represented by string s to n decimal places.
        n must be less than or equal to the number of digits appearing after the
        decimal point.
        """
        index_of_decimal = s.index(".")
        begin = s[:index_of_decimal+1]
        end = s[index_of_decimal+1:]
        after_decimal = ""

        i = index_of_decimal + 1
        while len(after_decimal) < n:
            after_decimal += end[i]
            i += 1

        return begin + after_decimal

    def on_touch_down(self, touch):
        global SAFE_TILES_COVERED
        if self.collide_point(*touch.pos):
            self.last_touch_button = touch.button
            if self.last_touch_button == 'right':
                if self.is_flagged:
                    self.source = "images/tile.png"
                    self.is_flagged = False
                else:
                    self.source = "images/flag.png"
                    self.is_flagged = True
            if self.last_touch_button == 'left':
                self.is_flagged = False
                if not self.is_bomb:
                    if not self.is_uncovered:
                        SAFE_TILES_COVERED -= 1
                        self.is_uncovered = True
                    if SAFE_TILES_COVERED == 0:
                        exit_button = Button(text="Quit", size=(50, 50))
                        seconds_elapsed = time.time() - START_TIME
                        time_str = self.truncate_decimal(
                            str(seconds_elapsed/60.0), 2) + "min"
                        if seconds_elapsed < 60:
                            time_str = self.truncate_decimal(
                                str(seconds_elapsed), 2) + "s"
                        game_won_popup = GameOverPopup(title=f"You won!\nTime: {time_str}",
                                                       content=exit_button,
                                                       auto_dismiss=False,
                                                       size=(350, 350),
                                                       size_hint=(None, None))
                        exit_button.bind(on_press=App.get_running_app().stop)
                        game_won_popup.open()
                    self.source = f"images/number-{self.adjacent_bombs}.png"

                else:
                    self.source = "images/bomb.png"
                    exit_button = Button(text="Quit", size=(50, 50))
                    seconds_elapsed = time.time() - START_TIME
                    time_str = self.truncate_decimal(
                        str(seconds_elapsed/60.0), 2) + "min"
                    if seconds_elapsed < 60:
                        time_str = self.truncate_decimal(
                            str(seconds_elapsed), 2) + "s"
                    game_over_popup = GameOverPopup(title=f"Game Over!\nTime: {time_str}",
                                                    content=exit_button,
                                                    auto_dismiss=False,
                                                    size=(350, 350),
                                                    size_hint=(None, None))
                    exit_button.bind(on_press=App.get_running_app().stop)
                    game_over_popup.open()
        return super(MSTile, self).on_touch_down(touch)


class MSGrid(GridLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def get_adjacent_tiles(self, i, j):
        indices = [i, j]
        matrix = np.array(self.grid)
        indices = tuple(np.transpose(np.atleast_2d(indices)))
        arr_shape = np.shape(matrix)
        dist = np.ones(arr_shape)
        dist[indices] = 0
        dist = scipy.ndimage.distance_transform_cdt(dist, metric='chessboard')
        nb_indices = np.transpose(np.nonzero(dist == 1))
        return [matrix[tuple(ind)] for ind in nb_indices]

    def calculate_adjacent_bombs(self):
        for x in range(self.rows):
            for y in range(self.cols):
                adjacent_tiles = self.get_adjacent_tiles(x, y)
                for tile in adjacent_tiles:
                    if tile.is_bomb:
                        self.grid[x][y].adjacent_bombs += 1

    def create_layout(self, bomb_positions):
        global SAFE_TILES_COVERED
        SAFE_TILES_COVERED = (self.rows * self.cols) - len(bomb_positions)

        self.grid = [[None for _ in range(self.cols)]
                     for _ in range(self.rows)]
        for i in range(self.rows):
            for j in range(self.cols):
                tile = MSTile(source="images/tile.png")
                tile.row_number = i
                tile.col_number = j
                tile.bombs_remaining = len(bomb_positions)
                if ((i, j) in bomb_positions):
                    tile.is_bomb = True
                    # uncomment next line to see bomb placements
                    # tile.source = "images/bomb.png"
                self.grid[i][j] = tile
                self.add_widget(tile)

        self.calculate_adjacent_bombs()


class MSGame(Widget):
    difficulty = "easy"
    grid = MSGrid()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_variables(self, difficulty):
        self.difficulty = difficulty
        self.grid.rows = NUM_ROWS[self.difficulty]
        self.grid.cols = NUM_COLS[self.difficulty]

    def bomb_positions(self):
        bomb_tiles = set()
        num_bombs = NUM_BOMBS[self.difficulty]
        while len(bomb_tiles) < num_bombs:
            rand_row = random.randint(0, NUM_ROWS[self.difficulty]-1)
            rand_col = random.randint(0, NUM_COLS[self.difficulty]-1)
            bomb_tiles.add((rand_row, rand_col))
        return bomb_tiles

    def initialize_grid(self):
        self.grid.create_layout(bomb_positions=self.bomb_positions())


class MinesweeperApp(App):

    def build(self):
        global START_TIME
        START_TIME = time.time()
        difficulty = "medium"
        game = MSGame()
        game.set_variables(difficulty=difficulty)
        game.initialize_grid()
        return game.grid


if __name__ == '__main__':
    MinesweeperApp().run()
