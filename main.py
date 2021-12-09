import kivy
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton, ToggleButtonBehavior
from kivy.uix.image import Image
from kivy.factory import Factory
from kivy.app import App
from kivy.config import Config
import random
import sys
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
kivy.require('2.0.0')

NUM_BOMBS = {"easy": 10, "medium": 40, "hard": 99}
NUM_ROWS = {"easy": 9, "medium": 16, "hard": 30}
NUM_COLS = {"easy": 9, "medium": 16, "hard": 16}


class MSTile(Image, ToggleButtonBehavior):
    row_number = 0
    col_number = 0
    is_bomb = False
    is_flagged = False
    adjacent_bombs = 0

    last_touch_button = Factory.StringProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False
    #     self.bind(on_press=self.onPress)

    # def onPress(self):
    #     print(self.last_touch_button)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.last_touch_button = touch.button
            if self.last_touch_button == 'right':
                if self.is_flagged:
                    self.source = "images/tile.png"
                    self.is_flagged = False
                else:
                    self.source = "images/flag.png"
                    self.is_flagged = True
        return super(MSTile, self).on_touch_down(touch)


class MSGrid(GridLayout):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def generate_random_bombs(self, difficulty="easy"):
        bomb_tiles = set()
        num_bombs = NUM_BOMBS[difficulty]
        while len(bomb_tiles) < num_bombs:
            rand_row = random.randint(0, self.rows-1)
            rand_col = random.randint(0, self.cols-1)
            bomb_tiles.add((rand_row, rand_col))
        return bomb_tiles

    def create_layout(self, bomb_positions):
        self.grid = [[None for _ in range(self.cols)]
                     for _ in range(self.rows)]
        for i in range(self.rows):
            for j in range(self.cols):
                tile = MSTile(source="images/tile.png")
                tile.row_number = i
                tile.col_number = j
                if ((i, j) in bomb_positions):
                    tile.is_bomb = True
                self.grid[i][j] = tile
                self.add_widget(tile)


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
        difficulty = "easy"
        game = MSGame()
        game.set_variables(difficulty=difficulty)
        game.initialize_grid()
        return game.grid


if __name__ == '__main__':
    MinesweeperApp().run()
