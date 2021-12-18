from functools import partial

import kivy
from kivy.app import App
from kivy.clock import Clock
from kivy.config import Config
from kivy.core.window import Window
from kivy.factory import Factory
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton, ToggleButtonBehavior
from kivy.uix.widget import Widget

import random
import time

Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
kivy.require('2.0.0')

GAME = None

NUM_BOMBS = {"easy": 10, "medium": 40, "hard": 99}
NUM_ROWS = {"easy": 9, "medium": 16, "hard": 16}
NUM_COLS = {"easy": 9, "medium": 16, "hard": 30}

START_TIME = None
GAMEMODE = None
DIFFICULTY = None

SAFE_TILES_COVERED = None


def to_print_tiles(ts):
    """
    Returns a list of tiles, but as (x, y) coordinate pairs rather than MSTile
    objects. Useful for printing tiles.
    """
    to_print = []
    for t in ts:
        to_print.append((t.row_number, t.col_number))
    return to_print


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
    """
    Returns a list of all MSTile objects in that are adjacent to the tile at 
    index (i, j) of MSGrid g.
    """
    neighbors = []
    possible_neighbors = [(i-1, j), (i-1, j+1), (i, j-1),
                          (i+1, j-1), (i+1, j), (i+1, j+1), (i, j+1), (i-1, j-1)]
    for n in possible_neighbors:
        if 0 <= n[0] <= g.rows-1 and 0 <= n[1] <= g.cols-1:
            neighbors.append(n)
    ms_tiles = []
    for neighbor in neighbors:
        x, y = neighbor
        ms_tiles.append(g.grid[x][y])
    return ms_tiles


class AdjacentButtons(BoxLayout):
    buttons = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def add_popup_buttons(self, is_player, popup):
        replay_button = Button(text="Replay",
                               size=(200, 200))
        replay_button.bind(on_release=lambda *args: GAME.restart(GAMEMODE,
                                                                 DIFFICULTY,
                                                                 popup,
                                                                 *args))
        self.buttons.append(replay_button)
        self.add_widget(replay_button)
        if is_player:
            replay_as_button = Button(text="Replay as\nComputer",
                                      size=(200, 200),
                                      halign='center',
                                      valign='center')
            replay_as_button.bind(on_release=lambda *args: GAME.restart("computer",
                                                                        DIFFICULTY,
                                                                        popup,
                                                                        *args))
            self.buttons.append(replay_as_button)
            self.add_widget(replay_as_button)
        else:
            replay_button = Button(text="Replay as\nPlayer",
                                   size=(200, 200),
                                   halign='center',
                                   valign='center')
            replay_button.bind(on_release=lambda *args: GAME.restart("player",
                                                                     DIFFICULTY,
                                                                     popup,
                                                                     *args))
            self.buttons.append(replay_button)
            self.add_widget(replay_button)

        main_menu_button = Button(text="Main Menu", size=(200, 200))
        main_menu_button.bind(
            on_release=lambda *args: GAME.reset(popup, *args))
        self.buttons.append(main_menu_button)
        self.add_widget(main_menu_button)

        quit_button = Button(text="Quit", size=(200, 200))
        quit_button.bind(on_release=App.get_running_app().stop)
        self.buttons.append(quit_button)
        self.add_widget(quit_button)


class WelcomeScreen(Label):
    buttons = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size = Window.size

    def set_difficulty(self, diff, *args):
        global DIFFICULTY
        DIFFICULTY = diff

    def set_gamemode(self, mode, *args):
        global GAMEMODE
        GAMEMODE = mode

    def create_buttons(self):
        easy = ToggleButton(text="Easy",
                            size=(0.2 * Window.size[0], 0.1 * Window.size[1]),
                            pos=(0.1 * Window.size[0], 0.3 * Window.size[1]),
                            group="difficulties",
                            on_press=lambda *args: self.set_difficulty("easy", *args))
        self.add_widget(easy)
        self.buttons.append(easy)
        medium = ToggleButton(text="Medium",
                              size=(0.2 * Window.size[0],
                                    0.1 * Window.size[1]),
                              pos=(0.4 * Window.size[0], 0.3 * Window.size[1]),
                              group="difficulties",
                              on_press=lambda *args: self.set_difficulty("medium", *args))
        self.add_widget(medium)
        self.buttons.append(medium)
        hard = ToggleButton(text="Hard",
                            size=(0.2 * Window.size[0], 0.1 * Window.size[1]),
                            pos=(0.7 * Window.size[0], 0.3 * Window.size[1]),
                            group="difficulties",
                            on_press=lambda *args: self.set_difficulty("hard", *args))
        self.add_widget(hard)
        self.buttons.append(hard)

        player = ToggleButton(text="Player",
                              size=(0.2 * Window.size[0],
                                    0.1 * Window.size[1]),
                              pos=(0.25 * Window.size[0],
                                   0.1 * Window.size[1]),
                              group="modes",
                              on_press=lambda *args: self.set_gamemode("player", *args))
        self.add_widget(player)
        self.buttons.append(player)
        computer = ToggleButton(text="Computer",
                                size=(0.2 * Window.size[0],
                                      0.1 * Window.size[1]),
                                pos=(0.55 * Window.size[0],
                                     0.1 * Window.size[1]),
                                group="modes",
                                on_press=lambda *args: self.set_gamemode("computer", *args))
        self.add_widget(computer)
        self.buttons.append(computer)

        play = Button(text="PLAY",
                      size=(0.2 * Window.size[0], 0.1 * Window.size[1]),
                      pos=(0.25 * Window.size[0], 0.6 * Window.size[1]))
        self.add_widget(play)
        self.buttons.append(play)

        quit = Button(text="Quit",
                      size=(0.2 * Window.size[0], 0.1 * Window.size[1]),
                      pos=(0.55 * Window.size[0], 0.6 * Window.size[1]))
        quit.bind(on_release=App.get_running_app().stop)
        self.add_widget(quit)
        self.buttons.append(quit)


class MSTile(Image, ToggleButtonBehavior):
    row_number = 0
    col_number = 0
    running_adjacent_bombs = 0
    adjacent_bombs = 0
    val = None
    is_uncovered = False
    is_flagged = False
    constraints = []
    is_bomb = False
    adjacent_tiles = []

    original_constant = 0
    constant = 0

    last_touch_button = Factory.StringProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.allow_stretch = True
        self.keep_ratio = False

    def on_touch_down(self, touch):
        global GAME
        global GAMEMODE
        global SAFE_TILES_COVERED
        if GAMEMODE != "player":
            return
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
                        seconds_elapsed = time.time() - START_TIME
                        time_str = truncate_decimal(
                            str(seconds_elapsed/60.0), 2) + "min"
                        if seconds_elapsed < 60:
                            time_str = truncate_decimal(
                                str(seconds_elapsed), 2) + "s"
                        popup_buttons = AdjacentButtons(
                            orientation='horizontal')
                        game_won_popup = Popup(title=f"You won!\nTime: {time_str}",
                                               content=popup_buttons,
                                               auto_dismiss=False,
                                               size=(900, 900),
                                               size_hint=(None, None))
                        popup_buttons.add_popup_buttons(
                            is_player=True, popup=game_won_popup)
                        game_won_popup.open()
                    self.source = f"images/number-{self.adjacent_bombs}.png"

                else:
                    self.source = "images/bomb.png"
                    seconds_elapsed = time.time() - START_TIME
                    time_str = truncate_decimal(
                        str(seconds_elapsed/60.0), 2) + "min"
                    if seconds_elapsed < 60:
                        time_str = truncate_decimal(
                            str(seconds_elapsed), 2) + "s"
                    popup_buttons = AdjacentButtons(orientation='horizontal')
                    game_over_popup = Popup(title=f"Game Over!\nTime: {time_str}",
                                            content=popup_buttons,
                                            auto_dismiss=False,
                                            size=(900, 900),
                                            size_hint=(None, None))
                    popup_buttons.add_popup_buttons(
                        is_player=True, popup=game_over_popup)
                    game_over_popup.open()
        return super(MSTile, self).on_touch_down(touch)


class MSGrid(GridLayout):
    marked_squares = set()
    num_mines = 0
    moves = []
    starting_point = None
    board_coordinates = []
    mines_flagged = set()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def calculate_adjacent_bombs(self):
        for x in range(self.rows):
            for y in range(self.cols):
                adjacent_tiles = get_adjacent_tiles(self, x, y)
                self.grid[x][y].adjacent_tiles = adjacent_tiles
                cs = [(at.row_number, at.col_number) for at in adjacent_tiles]
                self.grid[x][y].constraints = cs
                for tile in adjacent_tiles:
                    if tile.is_bomb:
                        self.grid[x][y].adjacent_bombs += 1
                        self.grid[x][y].constant += 1
                        self.grid[x][y].running_adjacent_bombs += 1
                        self.grid[x][y].original_constant += 1

    def create_layout(self, bomb_positions):
        global SAFE_TILES_COVERED
        SAFE_TILES_COVERED = (self.rows * self.cols) - len(bomb_positions)

        self.board_coordinates = self.get_coordinates()
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
                    tile.constant = 0
                    tile.original_constant = 9
                    # uncomment next line to see bomb placements
                    # tile.source = "images/bomb.png"
                self.grid[i][j] = tile
                self.add_widget(tile)

        self.calculate_adjacent_bombs()

    def get_coordinates(self):
        coords = []
        for i in range(self.rows):
            for j in range(self.cols):
                if (i, j) != self.starting_point:
                    coords.append((i, j))
        return coords


class MSGame(Widget):
    grid = MSGrid(size=Window.size)
    welcome_screen = WelcomeScreen(
        text="MINESWEEPER\nSelect difficulty, gamemode, and press play!",
        halign='center',
        valign='center')

    bomb_positions = set()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(size=self.resize_grid)

    def resize_grid(self, *args):
        self.grid.size = Window.size
        self.welcome_screen.size = Window.size
        for button in self.welcome_screen.children:
            button.size = (0.2 * Window.size[0], 0.1 * Window.size[1])
            if button.text == "Easy":
                button.pos = (0.1 * Window.size[0], 0.3 * Window.size[1])
            if button.text == "Medium":
                button.pos = (0.4 * Window.size[0], 0.3 * Window.size[1])
            if button.text == "Hard":
                button.pos = (0.7 * Window.size[0], 0.3 * Window.size[1])
            if button.text == "Player":
                button.pos = (0.25 * Window.size[0], 0.1 * Window.size[1])
            if button.text == "Computer":
                button.pos = (0.55 * Window.size[0], 0.1 * Window.size[1])
            if button.text == "PLAY":
                button.pos = (0.25 * Window.size[0], 0.6 * Window.size[1])
            if button.text == "Quit":
                button.pos = (0.55 * Window.size[0], 0.6 * Window.size[1])

    def set_variables(self):
        self.grid.rows = NUM_ROWS[DIFFICULTY]
        self.grid.cols = NUM_COLS[DIFFICULTY]
        self.grid.num_mines = NUM_BOMBS[DIFFICULTY]

    def set_bomb_positions(self):
        num_bombs = NUM_BOMBS[DIFFICULTY]
        while len(self.bomb_positions) < num_bombs:
            rand_row = random.randint(0, NUM_ROWS[DIFFICULTY]-1)
            rand_col = random.randint(0, NUM_COLS[DIFFICULTY]-1)
            self.bomb_positions.add((rand_row, rand_col))

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
                    self.grid.starting_point = (t.row_number, t.col_number)
                    return

    def initialize_game(self):
        self.welcome_screen.create_buttons()
        for button in self.welcome_screen.buttons:
            if button.text == "PLAY":
                button.bind(on_release=self.begin_game)
        self.add_widget(self.welcome_screen)

    def begin_game(self, *args):
        global GAME
        global START_TIME
        if DIFFICULTY is not None and GAMEMODE is not None:
            self.set_variables()
            for button in self.welcome_screen.buttons:
                self.welcome_screen.remove_widget(button)
                self.remove_widget(button)
            self.remove_widget(self.welcome_screen)
            START_TIME = time.time()
            if len(self.bomb_positions) == 0:
                self.set_bomb_positions()
            self.grid.create_layout(bomb_positions=self.bomb_positions)
            self.add_widget(self.grid)
            self.uncover_first_non_bomb_tile()
            GAME = self
            if GAMEMODE == "computer":
                csp = MSCSP(game=self, grid=self.grid)
                csp.start_game()
                csp.perform_actions()

    def restart(self, gamemode, difficulty, popup, *largs):
        global GAMEMODE
        global DIFFICULTY
        global START_TIME
        GAMEMODE = gamemode
        DIFFICULTY = difficulty
        START_TIME = time.time()
        if popup is not None:
            popup.dismiss()
        # clear welcome screen
        self.welcome_screen.clear_widgets()
        # clear grid
        self.grid.marked_squares.clear()
        self.grid.moves.clear()
        self.grid.mines_flagged.clear()
        self.grid.clear_widgets()
        self.grid.clear_widgets()
        # clear game widgets
        self.clear_widgets()

        self.begin_game()

    def reset(self, popup, *largs):
        global GAMEMODE
        global DIFFICULTY
        GAMEMODE = None
        DIFFICULTY = None
        if popup is not None:
            popup.dismiss()
        # clear welcome screen
        self.welcome_screen.clear_widgets()
        # clear grid
        self.grid.marked_squares.clear()
        self.grid.num_mines = 0
        self.grid.moves.clear()
        self.grid.starting_point = None
        self.grid.board_coordinates.clear()
        self.grid.mines_flagged.clear()
        self.grid.clear_widgets()
        # clea game widgets
        self.bomb_positions.clear()
        self.clear_widgets()

        self.initialize_game()


class MSCSP():
    def __init__(self, **kwargs):
        self.game = kwargs.get("game")
        self.grid = kwargs.get("grid")
        self.num_mines_flagged = 0
        self.squares_to_probe = [self.grid.starting_point]
        self.probed_squares = set()
        self.marked_count = {}
        self.path_uncovered = []
        self.lost_game = False

        # actions[i] is a tuple (t, s) where t is the tile, and s is either
        # "flag" or "uncover". The action is performed at the (i*0.1)th second of
        # the game.
        self.actions = []

    def uncover_tile(self, t, *largs):
        global SAFE_TILES_COVERED
        if t.is_bomb:
            t.source = "images/bomb.png"
            seconds_elapsed = time.time() - START_TIME
            time_str = truncate_decimal(
                str(seconds_elapsed/60.0), 2) + "min"
            if seconds_elapsed < 60:
                time_str = truncate_decimal(
                    str(seconds_elapsed), 2) + "s"
            popup_buttons = AdjacentButtons(
                orientation='horizontal')
            game_over_popup = Popup(title=f"Game Lost!\nTime: {time_str}",
                                    content=popup_buttons,
                                    auto_dismiss=False,
                                    size=(900, 900),
                                    size_hint=(None, None))
            popup_buttons.add_popup_buttons(
                is_player=False, popup=game_over_popup)
            game_over_popup.open()
        else:
            t.source = f"images/number-{t.adjacent_bombs}.png"
            SAFE_TILES_COVERED -= 1
            if SAFE_TILES_COVERED == 0:
                t.source = f"images/number-{t.adjacent_bombs}.png"
                seconds_elapsed = time.time() - START_TIME
                time_str = truncate_decimal(
                    str(seconds_elapsed/60.0), 2) + "min"
                if seconds_elapsed < 60:
                    time_str = truncate_decimal(
                        str(seconds_elapsed), 2) + "s"
                popup_buttons = AdjacentButtons(
                    orientation='horizontal')
                game_won_popup = Popup(title=f"Game Won!\nTime: {time_str}",
                                       content=popup_buttons,
                                       auto_dismiss=False,
                                       size=(900, 900),
                                       size_hint=(None, None))
                popup_buttons.add_popup_buttons(
                    is_player=False, popup=game_won_popup)
                game_won_popup.open()

    def flag_tile(self, t, *largs):
        t.source = "images/flag.png"

    def print_actions(self):
        to_print = []
        for i in range(len(self.actions)):
            t, s = self.actions[i]
            to_print.append((t.row_number, t.col_number, s))
        print(to_print)

    def perform_actions(self):
        global SAFE_TILES_COVERED
        # self.print_actions()
        for i in range(len(self.actions)):
            action = self.actions[i]
            tile, s = action
            if s == "uncover":
                Clock.schedule_once(
                    partial(self.uncover_tile, tile), (i*0.1))
            elif s == "flag":
                Clock.schedule_once(
                    partial(self.flag_tile, tile), (i*0.1))

    def print_grid(self):
        for i in range(self.grid.rows):
            for j in range(self.grid.cols):
                sq = self.get_current_square(i, j)
                print(
                    f"{(i, j)}, flagged = {sq.is_flagged}, uncovered = {sq.is_uncovered}, is bomb = {sq.is_bomb}")

    def start_game(self):
        while self.squares_to_probe:
            square = self.squares_to_probe.pop()
            uncovered = self.uncover_square(square)
            if uncovered == True:
                self.lost_game = True
                return
            self.simplify_constraints()
        mines_left = self.grid.num_mines - self.num_mines_flagged
        if len(self.grid.moves) > 0 and mines_left > 0:
            self.search()
        mines_left = self.grid.num_mines - self.num_mines_flagged
        if mines_left:
            squares_left = list(
                set(self.grid.board_coordinates) - self.grid.marked_squares)
            if squares_left:
                if len(squares_left) == mines_left:
                    for sq in squares_left:
                        self.mark_square_as_mine(sq)
        else:
            if self.grid.moves:
                for square in self.grid.moves:
                    for constraint in square.constraints:
                        self.uncover_square(constraint)
        return

    def uncover_square(self, square):
        if square in self.probed_squares:
            return
        x, y = square
        self.probed_squares.add(square)
        self.path_uncovered.append((square, 'uncovered'))
        current = self.get_current_square(x, y)
        current.is_uncovered = True
        if current.original_constant == 9:
            return True
        else:
            self.mark_square_as_safe(square)
            if current.original_constant == 0:
                neighbors = get_adjacent_tiles(self.grid, x, y)
                for neighbor in neighbors:
                    n = (neighbor.row_number, neighbor.col_number)
                    if n not in self.probed_squares:
                        nx, ny = n
                        self.uncover_square((nx, ny))
            elif current.original_constant > 0 and current.original_constant < 9:
                if current not in self.grid.moves:
                    self.grid.moves.append(current)
                return
        return

    def search(self):
        leftovers = {}
        for m in self.grid.moves:
            if m.constraints:
                for constraint in m.constraints:
                    if constraint not in leftovers:
                        leftovers[constraint] = 1
                    else:
                        leftovers[constraint] += 1
        squares = list(leftovers.keys())
        mines_left = self.grid.num_mines - self.num_mines_flagged
        squares_left = len(squares)
        solutions = []

        def backtrack(comb):
            nonlocal solutions
            if len(comb) > squares_left:
                return
            elif sum(comb) > mines_left:
                return
            else:
                for choice in [0, 1]:
                    comb.append(choice)
                    if sum(comb) == mines_left and len(comb) == squares_left:
                        valid = self.check_solution_validity(squares, comb)
                        if valid:
                            c = comb.copy()
                            solutions.append(c)
                    backtrack(comb)
                    removed = comb.pop()
                return solutions
        if mines_left < squares_left:
            backtrack([])
        if solutions:
            square_solution_counts = {}
            for s in range(len(solutions)):
                for sq in range(len(solutions[s])):
                    current_square = squares[sq]
                    if current_square not in square_solution_counts:
                        square_solution_counts[current_square] = solutions[s][sq]
                    else:
                        square_solution_counts[current_square] += solutions[s][sq]
            added_safe_squares = False
            for square, count in square_solution_counts.items():
                if count == 0:
                    added_safe_squares = True
                    self.squares_to_probe.append(square)
            if not added_safe_squares:
                random_solution = random.randint(0, len(solutions)-1)
                comb = solutions[random_solution]
                for square, value in zip(squares, comb):
                    if value == 0:
                        self.squares_to_probe.append(square)
        else:
            squares_left = list(
                set(self.grid.board_coordinates) - self.grid.marked_squares)
            random_square = random.randint(0, len(squares_left)-1)
            next_square = squares_left[random_square]
            self.squares_to_probe.append(next_square)
        self.start_game()
        return

    def meets_constraints(self, variable, val):
        x, y = variable
        square = self.get_current_square(x, y)
        square.val = val
        neighbors = get_adjacent_tiles(self.grid, x, y)
        for n in neighbors:
            nx = n.row_number
            ny = n.col_number
            neighbor_square = self.get_current_square(nx, ny)
            neighbor_constant = neighbor_square.original_constant
            if neighbor_square.val is not None and neighbor_square.val != 1:
                mines, safe, unknown = self.get_neighbor_count((nx, ny))
                if mines > neighbor_constant:
                    return False
                elif (neighbor_constant - mines) > unknown:
                    return False
        return True

    def get_neighbor_count(self, variable):
        nx, ny = variable
        nbors = get_adjacent_tiles(self.grid, nx, ny)
        mine_count = 0
        unknown_count = 0
        safe_count = 0
        for nb in nbors:
            nbx = nb.row_number
            nby = nb.col_number
            nbor_square = self.get_current_square(nbx, nby)
            if nbor_square.val == 1:
                mine_count += 1
            elif nbor_square.val == 0:
                safe_count += 1
            elif not nbor_square.val:
                unknown_count += 1
        return mine_count, safe_count, unknown_count

    def check_solution_validity(self, squares, comb):
        all_valid = False
        for square, value in zip(squares, comb):
            all_valid = self.meets_constraints(square, value)
        for square in squares:
            x, y = square
            sq = self.get_current_square(x, y)
            sq.val = None
        return all_valid

    def simplify(self, c1, c2):
        if c1 == c2:
            return
        to_remove = set()
        c1_constraints = set(c1.constraints)
        c2_constraints = set(c2.constraints)
        if c1_constraints and c2_constraints:
            if c1_constraints.issubset(c2_constraints):
                c2.constraints = list(c2_constraints - c1_constraints)
                c2.constant -= c1.constant
                if c2.constant == 0 and len(c2.constraints) > 0:
                    while c2.constraints:
                        c = c2.constraints.pop()
                        if c not in self.squares_to_probe and c not in self.probed_squares:
                            self.squares_to_probe.append(c)
                    to_remove.add(c2)
                elif c2.constant > 0 and c2.constant == len(c2.constraints):
                    while c2.constraints:
                        c = c2.constraints.pop()
                        self.mark_square_as_mine(c)
                    to_remove.add(c2)
                if c1.constant > 0 and c1.constant == len(c1.constraints):
                    while c1.constraints:
                        c = c1.constraints.pop()
                        self.mark_square_as_mine(c)
                    to_remove.add(c1)

                return to_remove
            elif c2_constraints.issubset(c1_constraints):
                return self.simplify(c2, c1)

    def simplify_constraints(self):
        constraints_to_remove = set()
        for move in self.grid.moves:
            if len(move.constraints) == move.constant:
                while move.constraints:
                    square = move.constraints.pop()
                    self.mark_square_as_mine(square)
                constraints_to_remove.add(move)
            elif move.constant == 0:
                while move.constraints:
                    square = move.constraints.pop()
                    self.squares_to_probe.append(square)
                constraints_to_remove.add(move)
        for m in constraints_to_remove:
            self.grid.moves.remove(m)

        constraints_to_remove = set()
        if len(self.grid.moves) > 1:
            i = 0
            j = i+1
            while i < len(self.grid.moves):
                while j < len(self.grid.moves):
                    c1 = self.grid.moves[i]
                    c2 = self.grid.moves[j]
                    to_remove = self.simplify(c1, c2)
                    if to_remove:
                        constraints_to_remove.update(to_remove)
                    j += 1
                i += 1
                j = i+1
        for m in constraints_to_remove:
            self.grid.moves.remove(m)
        return

    def mark_square_as_safe(self, square):
        self.mark_square(square)
        self.actions.append(
            (self.get_current_square(square[0], square[1]), "uncover"))
        return

    def mark_square_as_mine(self, square):
        self.path_uncovered.append((square, 'flagged'))
        self.num_mines_flagged += 1
        self.grid.mines_flagged.add(square)
        self.mark_square(square, is_mine=True)
        self.actions.append(
            (self.get_current_square(square[0], square[1]), "flag"))
        return

    def mark_square(self, square, is_mine=False):
        x, y = square
        if (x, y) not in self.marked_count:
            self.marked_count[(x, y)] = 1
        else:
            self.marked_count[(x, y)] += 1
        self.grid.marked_squares.add(square)
        current_square = self.get_current_square(x, y)
        if current_square.val is not None:
            return
        else:
            if is_mine:
                current_square.val = 1
                current_square.is_flagged = True
            else:
                current_square.val = 0
            neighbors = get_adjacent_tiles(self.grid, x, y)
            for neighbor in neighbors:
                nx = neighbor.row_number
                ny = neighbor.col_number
                neighbor_square = self.get_current_square(nx, ny)
                if (x, y) in neighbor_square.constraints:
                    neighbor_square.constraints.remove(square)
                    if is_mine:
                        neighbor_square.constant -= 1
        return

    def get_current_square(self, x, y):
        return self.grid.grid[x][y]


class MinesweeperApp(App):

    def build(self):
        global START_TIME
        START_TIME = time.time()
        game = MSGame()
        game.initialize_game()
        return game


if __name__ == '__main__':
    MinesweeperApp().run()
