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
        self.ship_sizes = [4, 3, 2, 1]
        self.title_font = pygame.font.SysFont('Arial', 20, bold=True)
        self.count_font = pygame.font.SysFont('Arial', 20, bold=True)

    def draw(self, surface, ships_to_place, selected_ship_size, mouse_pos):
        surface.blit(self.background, (self.rect.x, self.rect.y))

        for i, btn in enumerate(self.buttons):
            btn.is_hovered = btn.rect.collidepoint(mouse_pos)
            
            ship_size = self.ship_sizes[i]
            count = ships_to_place[ship_size]

            if count > 0:
                btn.color = GOLD if ship_size == selected_ship_size else WOOD
                btn.draw(surface)

                count_text = self.count_font.render(f"×{count}", True, WHITE)
                surface.blit(count_text, (btn.rect.right + 10, btn.rect.centery - 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, btn in enumerate(self.buttons):
                if btn.rect.collidepoint(event.pos):
                    return self.ship_sizes[i]
        return None