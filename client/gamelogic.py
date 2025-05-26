import pygame
import random
from constants import *


class GameLogic:
    def __init__(self, screen):
        self.screen = screen
        self.player_grid = [[0] * 10 for _ in range(10)]
        self.ai_grid = [[0] * 10 for _ in range(10)]
        self.ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        self.selected_ship = None
        self.orientation = 0
        self.current_turn = True
        self.game_over = False
        self.available_ships = self.ships.copy()

    def validate_placement(self, x, y, size):
        if self.orientation == 0 and x + size > 10: return False
        if self.orientation == 1 and y + size > 10: return False

        for i in range(-1, size + 1):
            for j in range(-1, 2):
                check_x = x + (i if self.orientation == 0 else j)
                check_y = y + (j if self.orientation == 0 else i)
                if 0 <= check_x < 10 and 0 <= check_y < 10:
                    if self.player_grid[check_y][check_x] != 0:
                        return False
        return True

    def place_ship(self, x, y):
        if not self.selected_ship: return
        if not self.validate_placement(x, y, self.selected_ship): return

        for i in range(self.selected_ship):
            dx = i if self.orientation == 0 else 0
            dy = i if self.orientation == 1 else 0
            self.player_grid[y + dy][x + dx] = 1

        self.available_ships.remove(self.selected_ship)
        self.selected_ship = None
        if not self.available_ships:
            self.start_battle()

    def rotate_ship(self):
        self.orientation = 1 - self.orientation

    def handle_shot(self, x, y, is_player=True):
        grid = self.ai_grid if is_player else self.player_grid
        if grid[y][x] in [2, 3]: return False

        if grid[y][x] == 1:
            grid[y][x] = 2
            if not self.check_ship_sunk(x, y, grid):
                return True
        else:
            grid[y][x] = 3

        self.current_turn = not is_player
        return True

    def check_ship_sunk(self, x, y, grid):
        directions = [(0, 1), (1, 0), (-1, 0), (0, -1)]
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < 10 and 0 <= ny < 10:
                if grid[ny][nx] == 1: return False
        return True

    def check_victory(self):
        return all(cell != 1 for row in self.ai_grid for cell in row) or \
            all(cell != 1 for row in self.player_grid for cell in row)

    def start_battle(self):
        self.current_turn = True
        self.ai_ships = self.place_ai_ships()

    def place_ai_ships(self):
        grid = [[0] * 10 for _ in range(10)]
        for size in self.ships:
            placed = False
            while not placed:
                x = random.randint(0, 9)
                y = random.randint(0, 9)
                orient = random.randint(0, 1)
                if self.validate_ai_placement(x, y, size, orient, grid):
                    for i in range(size):
                        dx = i if orient == 0 else 0
                        dy = i if orient == 1 else 0
                        grid[y + dy][x + dx] = 1
                    placed = True
        return grid

    def validate_ai_placement(self, x, y, size, orient, grid):
        if orient == 0 and x + size > 10: return False
        if orient == 1 and y + size > 10: return False

        for i in range(size):
            dx = i if orient == 0 else 0
            dy = i if orient == 1 else 0
            if grid[y + dy][x + dx] != 0: return False
        return True


class ComputerAI:
    def __init__(self, grid):
        self.grid = grid
        self.possible_targets = [(x, y) for x in range(10) for y in range(10)]

    def make_move(self):
        if not self.possible_targets: return None
        x, y = random.choice(self.possible_targets)
        self.possible_targets.remove((x, y))
        return x, y