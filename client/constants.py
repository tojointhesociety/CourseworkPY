import pygame

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (50, 50, 150)
GREY = (200, 200, 200)
DARK_GREY = (150, 150, 150)

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
block_size = 30
left_margin = 40
upper_margin = 50

pygame.font.init()
font_size = int(block_size // 1.5)
font = pygame.font.SysFont('notosans', font_size)
btn_font = pygame.font.SysFont('arial', 24, bold=True)