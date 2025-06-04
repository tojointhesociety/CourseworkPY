from constants import *
import pygame
from game_objects import Button

class ShipSelector:
    def __init__(self, x, y):
        self.selected_ship = None
        self.rect = pygame.Rect(x, y, 220, 250)
        self.background = pygame.Surface((220, 220), pygame.SRCALPHA)
        pygame.draw.rect(self.background, (*OCEAN_BLUE, 200),
                         (0, 0, 220, 220), border_radius=15)
        pygame.draw.rect(self.background, BLACK,
                         (0, 0, 220, 220), 2, border_radius=15)

        self.buttons = [
            Button("4-палубный", x + 20, y + 20, 180, 45,
                   color=WOOD, hover_color=GOLD),
            Button("3-палубный", x + 20, y + 75, 180, 45,
                   color=WOOD, hover_color=GOLD),
            Button("2-палубный", x + 20, y + 130, 180, 45,
                   color=WOOD, hover_color=GOLD),
            Button("1-палубный", x + 20, y + 185, 180, 45,
                   color=WOOD, hover_color=GOLD)
        ]
        self.ships_available = [1, 2, 3, 4]
        self.ship_types = [4, 3, 2, 1]
        self.selected_ship_size = None
        self.ship_orientation = 0
        self.ship_sizes = [4, 3, 2, 1]
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.count_font = pygame.font.SysFont('Arial', 20, bold=True)

    def draw(self, surface, available_ships):
        surface.blit(self.background, (self.rect.x, self.rect.y))

        for i, btn in enumerate(self.buttons):
            count = self.ships_available[i]
            if count > 0:
                btn.color = GOLD if self.ship_sizes[i] == self.selected_ship else WOOD
                btn.draw(surface)

                count_text = self.count_font.render(f"×{count}", True, WHITE)
                surface.blit(count_text, (btn.rect.right + 10, btn.rect.centery - 10))

    def handle_event(self, mouse_pos, available_ships):
        for i, btn in enumerate(self.buttons):
            if btn.rect.collidepoint(mouse_pos):
                if self.ship_sizes[i] in available_ships:
                    self.selected_ship = self.ship_sizes[i] if self.selected_ship != self.ship_sizes[i] else None
                    return self.selected_ship
        return None

    def handle_events(self, events, mouse_pos):
        for event in events:
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                if self.selected_ship_size:
                    self.ship_orientation = 1 - self.ship_orientation

            if event.type == pygame.MOUSEBUTTONDOWN:
                selected = self.ship_selector.handle_event(mouse_pos, self.get_available_ships_list())
                if selected is not None:
                    self.selected_ship_size = selected

                if (self.selected_ship_size and
                        left_margin <= mouse_pos[0] <= left_margin + 10 * block_size and
                        upper_margin <= mouse_pos[1] <= upper_margin + 10 * block_size):

                    grid_x = (mouse_pos[0] - left_margin) // block_size
                    grid_y = (mouse_pos[1] - upper_margin) // block_size

                    if self.validate_placement(grid_x, grid_y, self.selected_ship_size):
                        self.place_ship(grid_x, grid_y, self.selected_ship_size)

                        ship_index = self.ship_types.index(self.selected_ship_size)
                        self.ships_available[ship_index] -= 1

                        if self.ships_available[ship_index] <= 0:
                            self.selected_ship_size = None

                        if all(count == 0 for count in self.ships_available):
                            self.start_battle()

        return True

    def get_available_ships_list(self):
        available = []
        for size, count in zip(self.ship_types, self.ships_available):
            available.extend([size] * count)
        return available

    def place_ship(self, x, y, size):
        for i in range(size):
            dx = i if self.ship_orientation == 0 else 0
            dy = i if self.ship_orientation == 1 else 0
            self.player_grid[y + dy][x + dx] = 1