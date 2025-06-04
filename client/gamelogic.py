import random
from game_objects import GameGrid
from ship_selector import ShipSelector
from constants import *
from network import Network


class GameLogic:
    def __init__(self, screen):
        self.screen = screen
        self.player_grid = [[0] * 10 for _ in range(10)]
        self.ships = [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]
        self.available_ships = self.ships.copy()
        self.placement_mode = True
        self.current_turn = True
        self.game_over = False
        self.ship_selector = ShipSelector(SCREEN_WIDTH - 250, 100)
        self.ai_ships = self.place_ai_ships()
        self.ai_grid = [[0] * 10 for _ in range(10)]
        self.messages = []
        self.message_font = pygame.font.SysFont('Arial', 24)
        self.message_rect = pygame.Rect(SCREEN_WIDTH - 300, 20, 280, 200)
        self.status_font = pygame.font.SysFont('Arial', 28, bold=True)
        self.status_rect = pygame.Rect(SCREEN_WIDTH - 300, 250, 280, 150)
        self.rotation_angle = 0
        self.max_rotation_angle = 90
        self.ships_available = [1, 2, 3, 4]
        self.ship_types = [4, 3, 2, 1]
        self.selected_ship_size = None
        self.ship_orientation = 0
        self.network = None
        self.player_id = None

    def update(self):
        if self.rotation_angle > 0:
            self.rotation_angle = max(0, self.rotation_angle - 10)

    def add_message(self, text):
        if not hasattr(self, 'messages'):
            self.messages = []
        self.messages.append(text)
        if len(self.messages) > 5:
            self.messages.pop(0)

    def get_available_ships_list(self):
        available = []
        for i, count in enumerate(self.ships_available):
            if count > 0:
                available.append(self.ship_types[i])
        return available

    def draw_messages(self, surface):
        pygame.draw.rect(surface, (*DARK_BLUE, 200), self.message_rect)
        pygame.draw.rect(surface, BLACK, self.message_rect, 2)

        for i, msg in enumerate(self.messages[-5:]):
            text = self.message_font.render(msg, True, WHITE)
            surface.blit(text, (self.message_rect.x + 10,
                                self.message_rect.y + 10 + i * 30))

    def draw_status_panel(self, surface):
        pygame.draw.rect(surface, (*DARK_BLUE, 200), self.status_rect)
        pygame.draw.rect(surface, BLACK, self.status_rect, 2)

        status = "Ваш ход" if self.current_turn else "Ход ИИ"
        text = self.status_font.render(status, True,
                                       GREEN if self.current_turn else RED)
        surface.blit(text, (self.status_rect.x + 20, self.status_rect.y + 20))

    def validate_ai_placement(self, x, y, size, orientation, grid):
        if orientation == 0 and x + size > 10:
            return False
        if orientation == 1 and y + size > 10:
            return False

        for i in range(-1, size + 1):
            for j in range(-1, 2):
                check_x = x + (i if orientation == 0 else j)
                check_y = y + (j if orientation == 0 else i)

                if 0 <= check_x < 10 and 0 <= check_y < 10:
                    if grid[check_y][check_x] != 0:
                        return False
        return True

    def init_battle(self):
        self.player_grid = GameGrid(left_margin, upper_margin, is_player=True)
        self.ai_grid = GameGrid(left_margin + 15 * block_size, upper_margin, is_player=False)
        self.battle_initialized = True

    def validate_placement(self, x, y, size):
        if self.ship_orientation == 0 and x + size > 10:
            return False
        if self.ship_orientation == 1 and y + size > 10:
            return False

        for i in range(-1, size + 1):
            for j in range(-1, 2):
                check_x = x + (i if self.ship_orientation == 0 else j)
                check_y = y + (j if self.ship_orientation == 0 else i)

                if 0 <= check_x < 10 and 0 <= check_y < 10:
                    if self.player_grid[check_y][check_x] != 0:
                        return False
        return True

    def place_ship(self, x, y, size):
        for i in range(size):
            dx = i if self.ship_orientation == 0 else 0
            dy = i if self.ship_orientation == 1 else 0
            self.player_grid[y + dy][x + dx] = 1

        ship_index = [4, 3, 2, 1].index(size)
        self.ships_available[ship_index] -= 1

        if self.ships_available[ship_index] <= 0:
            self.selected_ship_size = None

    def handle_shot(self, x, y, is_player=True):
        target_grid = self.ai_grid if is_player else self.player_grid

        if target_grid[y][x] in [2, 3]:
            return None

        if target_grid[y][x] == 1:
            target_grid[y][x] = 2
            sunk, ship_cells = self.check_ship_sunk(x, y, target_grid)

            if sunk:
                self.last_sunk_size = len(ship_cells)
                self.mark_around_ship(ship_cells, target_grid)
                return "sunk"
            return "hit"
        else:
            target_grid[y][x] = 3
            return "miss"

    def mark_around_ship(self, ship_cells, grid):
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1), (0, 1),
                      (1, -1), (1, 0), (1, 1)]

        for x, y in ship_cells:
            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and grid[ny][nx] == 0:
                    grid[ny][nx] = 3

    def check_ship_sunk(self, x, y, grid):
        ship_cells = []
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

        to_check = [(x, y)]
        while to_check:
            cx, cy = to_check.pop()
            if (cx, cy) not in ship_cells and grid[cy][cx] == 2:
                ship_cells.append((cx, cy))
                for dx, dy in directions:
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < 10 and 0 <= ny < 10:
                        to_check.append((nx, ny))

        for cx, cy in ship_cells:
            if grid[cy][cx] != 2:
                return False, []

        return True, ship_cells


    def check_victory(self):
        player_alive = any(1 in row for row in self.player_grid)
        ai_alive = any(1 in row for row in self.ai_grid)

        if not ai_alive:
            return "player"
        elif not player_alive:
            return "ai"
        return None

    def start_battle(self):
        self.current_turn = True
        self.ai_grid = self.ai_ships

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

    def handle_events(self, events, mouse_pos):
        for event in events:
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                if self.selected_ship_size is not None:
                    self.ship_orientation = 1 - self.ship_orientation

            if event.type == pygame.MOUSEBUTTONDOWN:
                selected = self.ship_selector.handle_event(mouse_pos, self.available_ships)
                if selected is not None:
                    self.selected_ship_size = selected

                if (self.selected_ship_size is not None and
                        left_margin <= mouse_pos[0] <= left_margin + 10 * block_size and
                        upper_margin <= mouse_pos[1] <= upper_margin + 10 * block_size):

                    grid_x = (mouse_pos[0] - left_margin) // block_size
                    grid_y = (mouse_pos[1] - upper_margin) // block_size

                    if self.validate_placement(grid_x, grid_y, self.selected_ship_size):
                        ship_index = self.ship_types.index(self.selected_ship_size)
                        self.place_ship(grid_x, grid_y, self.selected_ship_size)
                        self.ships_available[ship_index] -= 1

                        if self.ships_available[ship_index] <= 0:
                            self.selected_ship_size = None

                        if all(count == 0 for count in self.ships_available):
                            self.start_battle()
                            return "battle"
                        return "placement"


    def handle_ship_placement(self, grid_x, grid_y):
        if not self.selected_ship_size:
            return False

        if self.validate_placement(grid_x, grid_y, self.selected_ship_size):
            self.place_ship(grid_x, grid_y, self.selected_ship_size)

            ship_index = [4, 3, 2, 1].index(self.selected_ship_size)
            self.available_ships[ship_index] -= 1

            if self.available_ships[ship_index] <= 0:
                self.selected_ship_size = None

            return True
        return False

    def process_network_response(self, response, x, y):
        if response['hit']:
            self.ai_grid[y][x] = 2
            if response.get('sunk'):
                self.add_message("Вы потопили корабль!")
            else:
                self.add_message("Вы попали!")
        else:
            self.ai_grid[y][x] = 3
            self.add_message("Вы промахнулись!")

        self.current_turn = (response['turn'] == self.player_id)

        if response.get('game_over'):
            return "player" if response['winner'] == self.player_id else "enemy"
        return None

    def handle_network_shot(self, x, y):
        try:
            response = self.network.send({
                'type': 'shot',
                'coords': (x, y)
            })

            if response and response.get('type') == 'shot_result':
                if response['hit']:
                    self.ai_grid[response['y']][response['x']] = 2
                    if response.get('sunk'):
                        self.mark_around_ship(response['x'], response['y'], self.ai_grid)
                    self.add_message("Вы попали!" if response['hit'] else "Вы промахнулись!")

                if response.get('game_over'):
                    return "player" if response['winner'] == self.player_id else "enemy"

                self.current_turn = not response['hit'] or response.get('sunk', False)
                return None

        except Exception as e:
            print(f"Ошибка при обработке выстрела: {e}")
            self.add_message("Ошибка соединения")
            return "disconnected"


    def handle_network(self):
        if not self.network or not self.network.connected:
            return False

        try:
            state = self.network.send({"type": "get_state"})
            if state and 'status' in state:
                if state['status'] == 'battle' and not self.started:
                    self.started = True
                    self.add_message("Игра начинается!")
                    return 'start'
                elif state['status'] == 'disconnected':
                    self.add_message("Соперник отключился")
                    return 'disconnect'
            return True
        except:
            return False
class ComputerAI:
    def __init__(self, grid):
        self.grid = grid
        self.possible_targets = [(x, y) for x in range(10) for y in range(10)]
        self.last_hit = None
        self.directions = [(0,1), (1,0), (0,-1), (-1,0)]
        self.target_mode = False

    def make_move(self):
        if not self.possible_targets:
            return None

        if self.last_hit and not self.target_mode:
            self.target_mode = True
            self.directions = [(0,1), (1,0), (0,-1), (-1,0)]
            random.shuffle(self.directions)

        if self.target_mode:
            for dx, dy in self.directions:
                x, y = self.last_hit[0] + dx, self.last_hit[1] + dy
                if (x, y) in self.possible_targets:
                    self.possible_targets.remove((x, y))
                    return x, y
            self.target_mode = False
            self.last_hit = None

        x, y = random.choice(self.possible_targets)
        self.possible_targets.remove((x, y))
        return x, y