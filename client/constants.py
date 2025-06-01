import pygame
import math


DARK_RED = (150, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 0, 0)
GREEN = (0, 200, 0)
BLUE = (50, 50, 150)
GREY = (200, 200, 200)
DARK_GREY = (150, 150, 150)
OCEAN_BLUE = (65, 105, 225)
SAND = (210, 180, 140)
WOOD = (139, 69, 19)
GOLD = (255, 215, 0)
DARK_BLUE = (0, 0, 139)
LIGHT_BLUE = (173, 216, 230)
INPUT_FIELD_ALPHA = 180
PLACEHOLDER_ALPHA = 150
LIGHT_GOLD = (255, 235, 150)
DARK_WOOD = (160, 80, 20)
GREEN_ALPHA = (0, 255, 0, 100)
RED_ALPHA = (255, 0, 0, 100)

SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
block_size = 30
left_margin = 40
upper_margin = 50

pygame.font.init()
font_size = int(block_size // 1.5)
font = pygame.font.SysFont('notosans', font_size)
btn_font = pygame.font.SysFont('arial', 24, bold=True)