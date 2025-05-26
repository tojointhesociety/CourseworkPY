import pygame
from constants import *

class Button:
    def __init__(self, text, x, y, w, h, color=BLUE, hover_color=GREEN):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False

    def draw(self, surface):
        color = self.hover_color if self.is_hovered else self.color
        pygame.draw.rect(surface, color, self.rect)
        text = btn_font.render(self.text, True, WHITE)
        surface.blit(text, (self.rect.x + 15, self.rect.y + 10))

class ShipSelector:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 200, 400)
        self.buttons = [
            Button("4-палубный", x+10, y+10, 180, 40),
            Button("3-палубный", x+10, y+70, 180, 40),
            Button("2-палубный", x+10, y+130, 180, 40),
            Button("1-палубный", x+10, y+190, 180, 40)
        ]
        self.selected = None

    def update(self, mouse_pos, available_ships):
        for i, btn in enumerate(self.buttons):
            btn.is_hovered = btn.rect.collidepoint(mouse_pos) and available_ships[i]
        return [i for i, btn in enumerate(self.buttons) if btn.rect.collidepoint(mouse_pos)]

    def draw(self, surface, available_ships):
        pygame.draw.rect(surface, GREY, self.rect)
        for i, btn in enumerate(self.buttons):
            if available_ships[i]:
                btn.color = BLUE if i != self.selected else GREEN
                btn.draw(surface)

class GameGrid:
    def __init__(self, x, y, is_player=True):
        self.rect = pygame.Rect(x, y, 10*block_size, 10*block_size)
        self.cells = [[pygame.Rect(x+i*block_size, y+j*block_size, block_size, block_size)
                     for i in range(10)] for j in range(10)]
        self.is_player = is_player

    def draw(self, surface, grid_data):
        for y in range(10):
            for x in range(10):
                color = WHITE
                if grid_data[y][x] == 1: color = BLUE
                elif grid_data[y][x] == 2: color = RED
                pygame.draw.rect(surface, color, self.cells[y][x])
                pygame.draw.rect(surface, BLACK, self.cells[y][x], 1)

class MainMenu:
    def __init__(self):
        self.buttons = [
            Button("Играть с ИИ", SCREEN_WIDTH//2-100, 250, 200, 50),
            Button("Сетевая игра", SCREEN_WIDTH//2-100, 320, 200, 50),
            Button("Настройки", SCREEN_WIDTH//2-100, 390, 200, 50)
        ]

    def update(self, mouse_pos):
        for btn in self.buttons:
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        title = font.render("МОРСКОЙ БОЙ", True, BLACK)
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 100))
        for btn in self.buttons:
            btn.draw(surface)

def draw_grid_labels(surface):
    letters = ['A','B','C','D','E','F','G','H','I','J']
    for i in range(10):
        text = font.render(letters[i], True, BLACK)
        surface.blit(text, (left_margin + i*block_size + 10, upper_margin - 30))
        text = font.render(str(i+1), True, BLACK)
        surface.blit(text, (left_margin - 30, upper_margin + i*block_size + 10))