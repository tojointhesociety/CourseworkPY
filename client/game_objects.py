import pygame
import math
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
        # Анимированная волна на кнопке
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

        # Текст с тенью
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

    def draw(self, surface, grid_data, game_logic=None):
        pygame.draw.rect(surface, OCEAN_BLUE, self.rect)
        if game_logic and game_logic.selected_ship_size and self.is_player:
            mouse_pos = pygame.mouse.get_pos()
            if self.rect.collidepoint(mouse_pos):
                grid_x = (mouse_pos[0] - self.rect.x) // block_size
                grid_y = (mouse_pos[1] - self.rect.y) // block_size

                size = game_logic.selected_ship_size
                orient = game_logic.ship_orientation

                # Проверка валидности позиции
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
                        # Рисуем полупрозрачный прямоугольник
                        s = pygame.Surface((block_size, block_size), pygame.SRCALPHA)
                        s.fill(color)
                        surface.blit(s, cell_rect)
                        # Обводка
                        pygame.draw.rect(surface, BLACK, cell_rect, 1)
        for y in range(10):
            for x in range(10):
                # Отрисовка фонового узора волн
                surface.blit(self.wave_pattern, self.cells[y][x])

                # Для поля противника (ИИ) - показываем только выстрелы
                if not self.is_player:
                    if grid_data[y][x] == 2:  # Попадание
                        # Проверяем, потоплен ли корабль
                        sunk, _ = game_logic.check_ship_sunk(x, y, grid_data) if game_logic else (False, [])
                        if sunk:
                            # Отрисовка потопленного корабля
                            pygame.draw.rect(surface, DARK_RED, self.cells[y][x])
                            pygame.draw.line(surface, BLACK,
                                             self.cells[y][x].topleft,
                                             self.cells[y][x].bottomright, 3)
                            pygame.draw.line(surface, BLACK,
                                             self.cells[y][x].topright,
                                             self.cells[y][x].bottomleft, 3)

                            # Анимация волн при потоплении
                            for i in range(10):
                                radius = int(block_size * 0.3 * (10 - i) / 10)
                                alpha = 255 * (10 - i) // 10
                                s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                                pygame.draw.circle(s, (*WHITE, alpha), (radius, radius), radius)
                                surface.blit(s, (self.cells[y][x].centerx - radius,
                                                 self.cells[y][x].centery - radius))
                        else:
                            # Обычное попадание
                            pygame.draw.circle(surface, RED,
                                               self.cells[y][x].center,
                                               block_size // 3)

                    elif grid_data[y][x] == 3:  # Промах
                        pygame.draw.circle(surface, BLACK,
                                           self.cells[y][x].center,
                                           block_size // 6)

                # Для своего поля - полная отрисовка
                else:
                    if grid_data[y][x] == 1:  # Корабль
                        pygame.draw.rect(surface, WOOD, self.cells[y][x])
                        pygame.draw.rect(surface, BLACK, self.cells[y][x], 2)

                    elif grid_data[y][x] == 2:  # Попадание по вашему кораблю
                        sunk, _ = game_logic.check_ship_sunk(x, y, grid_data) if game_logic else (False, [])
                        if sunk:
                            pygame.draw.rect(surface, DARK_RED, self.cells[y][x])
                            pygame.draw.line(surface, BLACK,
                                             self.cells[y][x].topleft,
                                             self.cells[y][x].bottomright, 3)
                            pygame.draw.line(surface, BLACK,
                                             self.cells[y][x].topright,
                                             self.cells[y][x].bottomleft, 3)
                        else:
                            pygame.draw.rect(surface, RED, self.cells[y][x])
                            pygame.draw.line(surface, BLACK,
                                             self.cells[y][x].topleft,
                                             self.cells[y][x].bottomright, 2)
                            pygame.draw.line(surface, BLACK,
                                             self.cells[y][x].topright,
                                             self.cells[y][x].bottomleft, 2)

                    elif grid_data[y][x] == 3:  # Промах по вашему полю
                        pygame.draw.circle(surface, BLACK,
                                           self.cells[y][x].center,
                                           block_size // 6)

                # Обводка клетки
                pygame.draw.rect(surface, BLACK, self.cells[y][x], 1)