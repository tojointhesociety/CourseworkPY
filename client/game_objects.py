from constants import *


class Button:
    def __init__(self, text, x, y, w, h, color=WOOD, hover_color=GOLD, text_color=WHITE):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False
        self.wave_offset = 0
        self.font = pygame.font.SysFont('Arial', 24, bold=True)

    def draw(self, surface):
        wave_surface = pygame.Surface((self.rect.w, self.rect.h), pygame.SRCALPHA)
        for i in range(self.rect.w):
            wave_height = 5 * math.sin((i + self.wave_offset) / 15)
            pygame.draw.line(wave_surface, (*LIGHT_BLUE, 50),
                            (i, self.rect.h // 2 + wave_height),
                            (i, self.rect.h), 1)

        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect, border_radius=10)
        surface.blit(wave_surface, (self.rect.x, self.rect.y))
        pygame.draw.rect(surface, BLACK, self.rect, 2, border_radius=10)

        text = self.font.render(self.text, True, self.text_color)
        text_rect = text.get_rect(center=self.rect.center)

        for dx, dy in [(1, 1), (-1, 1), (1, -1), (-1, -1)]:
            shadow = self.font.render(self.text, True, BLACK)
            surface.blit(shadow, (text_rect.x + dx, text_rect.y + dy))

        surface.blit(text, text_rect)
        self.wave_offset += 0.5

class GameGrid:
    def __init__(self, x, y, is_player=True):
        self.rect = pygame.Rect(x, y, 10 * block_size, 10 * block_size)
        self.cells = [[pygame.Rect(x + i * block_size, y + j * block_size,
                                 block_size, block_size) for i in range(10)] for j in range(10)]
        self.is_player = is_player
        self.wave_pattern = self.create_wave_pattern()

    def create_wave_pattern(self):
        pattern = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
        for i in range(0, block_size, 3):
            alpha = 30 + int(120 * abs((i % 6) - 3) / 3)
            pygame.draw.line(pattern, (*LIGHT_BLUE, alpha),
                           (0, i), (block_size, i), 1)
        return pattern

    def draw(self, surface, grid_data, game_logic=None, is_player_grid=False):
        """
        Параметры:
        - grid_data: данные сетки
        - game_logic: ссылка на игровую логику (для предпросмотра размещения)
        - is_player_grid: True, если это поле игрока (показывать корабли)
        """
        pygame.draw.rect(surface, OCEAN_BLUE, self.rect)

        # Предпросмотр размещения кораблей (только для своего поля)
        if game_logic and game_logic.selected_ship_size and is_player_grid:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                grid_x = (mouse_pos[0] - self.rect.x) // block_size
                grid_y = (mouse_pos[1] - self.rect.y) // block_size

                size = game_logic.selected_ship_size
                orient = game_logic.ship_orientation

                valid = game_logic.validate_placement(grid_x, grid_y, size)
                color = (*GREEN, 100) if valid else (*RED, 100)

                for i in range(size):
                    dx = i if orient == 0 else 0
                    dy = i if orient == 1 else 0
                    if 0 <= grid_x + dx < 10 and 0 <= grid_y + dy < 10:
                        cell_rect = pygame.Rect(
                            self.rect.x + (grid_x + dx) * block_size,
                            self.rect.y + (grid_y + dy) * block_size,
                            block_size, block_size
                        )
                        s = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
                        s.fill(color)
                        surface.blit(s, cell_rect)
                        pygame.draw.rect(surface, BLACK, cell_rect, 1)

        # Отрисовка сетки и содержимого
        for y in range(10):
            for x in range(10):
                # Фоновый узор волн
                surface.blit(self.wave_pattern, self.cells[y][x])

                cell = grid_data[y][x]
                cell_rect = self.cells[y][x]

                # Для своего поля (показываем корабли)
                if is_player_grid:
                    if cell == 1:  # Корабль
                        pygame.draw.rect(surface, WOOD, cell_rect)
                        pygame.draw.rect(surface, BLACK, cell_rect, 2)

                    elif cell == 2:  # Подбитая часть
                        pygame.draw.rect(surface, RED, cell_rect)
                        pygame.draw.line(surface, BLACK, cell_rect.topleft, cell_rect.bottomright, 2)
                        pygame.draw.line(surface, BLACK, cell_rect.topright, cell_rect.bottomleft, 2)

                    elif cell == 3:  # Промах
                        pygame.draw.circle(surface, BLACK, cell_rect.center, block_size // 6)

                # Для вражеского поля (скрываем корабли)
                else:
                    if cell == 2:  # Попадание
                        pygame.draw.rect(surface, RED, cell_rect)
                        pygame.draw.line(surface, BLACK, cell_rect.topleft, cell_rect.bottomright, 3)
                        pygame.draw.line(surface, BLACK, cell_rect.topright, cell_rect.bottomleft, 3)

                    elif cell == 3:  # Промах
                        pygame.draw.circle(surface, BLACK, cell_rect.center, block_size // 6)

                # Границы клеток
                pygame.draw.rect(surface, BLACK, cell_rect, 1)