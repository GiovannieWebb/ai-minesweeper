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
from kivy.clock import Clock
from functools import partial
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
GAMEMODE = "AI"


def truncate_decimal(s, n):
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


def get_adjacent_tiles(g, i, j):
    indices = [i, j]
    matrix = np.array(g)
    indices = tuple(np.transpose(np.atleast_2d(indices)))
    arr_shape = np.shape(matrix)
    dist = np.ones(arr_shape)
    dist[indices] = 0
    dist = scipy.ndimage.distance_transform_cdt(dist, metric='chessboard')
    nb_indices = np.transpose(np.nonzero(dist == 1))
    return [matrix[tuple(ind)] for ind in nb_indices]


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
                        time_str = truncate_decimal(
                            str(seconds_elapsed/60.0), 2) + "min"
                        if seconds_elapsed < 60:
                            time_str = truncate_decimal(
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
                    time_str = truncate_decimal(
                        str(seconds_elapsed/60.0), 2) + "min"
                    if seconds_elapsed < 60:
                        time_str = truncate_decimal(
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

    def calculate_adjacent_bombs(self):
        for x in range(self.rows):
            for y in range(self.cols):
                adjacent_tiles = get_adjacent_tiles(self.grid, x, y)
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
    gamemode = GAMEMODE

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_variables(self, difficulty, gamemode):
        self.difficulty = difficulty
        self.gamemode = gamemode
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

    def min_adj_bombs(self):
        min_adj_bombs = 8
        for i in range(self.grid.rows):
            for j in range(self.grid.cols):
                t = self.grid.grid[i][j]
                if t.adjacent_bombs < min_adj_bombs:
                    min_adj_bombs = t.adjacent_bombs
        return min_adj_bombs

    def uncover_first_non_bomb_tile(self):
        global SAFE_TILES_COVERED
        mab = self.min_adj_bombs()
        for i in range(self.grid.rows):
            for j in range(self.grid.cols):
                t = self.grid.grid[i][j]
                if not t.is_bomb and t.adjacent_bombs == mab:
                    t.source = f"images/number-{mab}.png"
                    t.is_uncovered = True
                    SAFE_TILES_COVERED -= 1
                    return

    def initialize_grid(self):
        self.grid.create_layout(bomb_positions=self.bomb_positions())


class GameOverPopup(Popup):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class MSCSP():
    # actions[i] is a tuple (t, s) where t is the tile, and s is either
    # "flag" or "uncover". The action is performed at the (i*0.1)th second of
    # the game.
    actions = []

    def __init__(self, **kwargs):
        self.grid = kwargs.get("grid")

    def print_actions(self):
        to_print = []
        for i in range(len(self.actions)):
            t, s = self.actions[i]
            to_print.append((t.row_number, t.col_number, s))
        print(to_print)

    def perform_actions(self):
        # self.print_actions()
        for i in range(len(self.actions)):
            action = self.actions[i]
            tile, s = action
            if s == "uncover":
                if not tile.is_uncovered:
                    Clock.schedule_once(
                        partial(self.uncover_tile, tile), (i*0.1)+1)
            elif s == "flag":
                Clock.schedule_once(
                    partial(self.flag_tile, tile), (i*0.1)+1)

    def uncover_tile(self, t, *largs):
        global SAFE_TILES_COVERED
        if t.is_bomb:
            t.source = "images/bomb.png"
            exit_button = Button(text="Quit", size=(50, 50))
            seconds_elapsed = time.time() - START_TIME
            time_str = truncate_decimal(
                str(seconds_elapsed/60.0), 2) + "min"
            if seconds_elapsed < 60:
                time_str = truncate_decimal(
                    str(seconds_elapsed), 2) + "s"
            game_over_popup = GameOverPopup(title=f"Game Over!\nTime: {time_str}",
                                            content=exit_button,
                                            auto_dismiss=False,
                                            size=(350, 350),
                                            size_hint=(None, None))
            exit_button.bind(on_press=App.get_running_app().stop)
            game_over_popup.open()
        else:
            t.source = f"images/number-{t.adjacent_bombs}.png"
            if not t.is_uncovered:
                SAFE_TILES_COVERED -= 1
        t.is_uncovered = True

    def flag_tile(self, t, *largs):
        t.source = "images/flag.png"
        t.is_flagged = True

    def zero_tile_dfs(self):
        first_uncovered = None
        for i in range(self.grid.rows):
            for j in range(self.grid.cols):
                t = self.grid.grid[i][j]
                if t.is_uncovered:
                    first_uncovered = t

        tiles_to_uncover = [first_uncovered]
        visited_tiles = set()
        while len(tiles_to_uncover) > 0:
            current_tile = tiles_to_uncover.pop(0)
            x = current_tile.row_number
            y = current_tile.col_number
            adjacent_tiles = get_adjacent_tiles(self.grid.grid, x, y)
            if current_tile not in visited_tiles:
                if current_tile.adjacent_bombs == 0:
                    for a in adjacent_tiles:
                        if a not in visited_tiles:
                            self.actions.append((a, "uncover"))
                visited_tiles.add(current_tile)

            for at in adjacent_tiles:
                if at not in visited_tiles and at.adjacent_bombs == 0:
                    tiles_to_uncover.append(at)


class MinesweeperApp(App):

    def build(self):
        global START_TIME
        START_TIME = time.time()
        difficulty = "medium"
        gamemode = GAMEMODE
        game = MSGame()
        game.set_variables(difficulty=difficulty, gamemode=gamemode)
        game.initialize_grid()
        game.uncover_first_non_bomb_tile()
        if game.gamemode == "AI":
            csp = MSCSP(grid=game.grid)
            csp.zero_tile_dfs()
            csp.perform_actions()
        return game.grid


if __name__ == '__main__':
    MinesweeperApp().run()
