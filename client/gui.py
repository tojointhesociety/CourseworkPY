import random
from constants import *
from game_objects import Button


class MainMenu:
    def __init__(self):
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.title_font = pygame.font.SysFont('Arial', 72, bold=True)
        self.subtitle_font = pygame.font.SysFont('Arial', 24)
        self.wave_offset = 0
        self.ship_offset = 0
        self.ship_speed = 0.5
        self.ship_img = self.create_ship_image()
        self.ship_pos = [-100, SCREEN_HEIGHT // 2]

        self.buttons = [
            Button("Играть с ИИ", SCREEN_WIDTH // 2 - 150, 300, 300, 60),
            Button("Сетевая игра", SCREEN_WIDTH // 2 - 150, 380, 300, 60),
            Button("Настройки", SCREEN_WIDTH // 2 - 150, 460, 300, 60)
        ]

    def create_ship_image(self):
        ship = pygame.Surface((80, 40), pygame.SRCALPHA)
        pygame.draw.polygon(ship, WOOD, [(0, 20), (60, 5), (80, 20), (60, 35)])
        pygame.draw.line(ship, BLACK, (40, 20), (40, 5), 3)
        pygame.draw.polygon(ship, WHITE, [(40, 5), (75, 15), (40, 25)])
        return ship

    def create_background(self):
        self.background.fill(OCEAN_BLUE)

        # Волны
        for y in range(0, SCREEN_HEIGHT, 20):
            amplitude = 10 * (1 + math.sin((y + self.wave_offset) / 30))
            points = [(x, y + amplitude * math.sin(x / 50 + self.wave_offset / 10))
                      for x in range(0, SCREEN_WIDTH + 1, 10)]
            pygame.draw.lines(self.background, LIGHT_BLUE, False, points, 2)

        # Солнце
        pygame.draw.circle(self.background, GOLD,
                           (SCREEN_WIDTH - 100, 100), 40)

        # Облака
        for i in range(3):
            x = 100 + i * 300 + math.sin(self.wave_offset / 20 + i) * 50
            pygame.draw.ellipse(self.background, WHITE,
                                (x, 80, 120, 40))
            pygame.draw.ellipse(self.background, WHITE,
                                (x + 30, 60, 100, 50))

    def update(self, mouse_pos=None):  # Добавляем необязательный параметр
        self.wave_offset += 0.7

        # Анимация кораблика
        self.ship_pos[0] += self.ship_speed
        self.ship_pos[1] += math.sin(self.ship_offset) * 2
        self.ship_offset += 0.05

        if self.ship_pos[0] > SCREEN_WIDTH + 100:
            self.ship_pos[0] = -100
            self.ship_pos[1] = SCREEN_HEIGHT // 2 + random.randint(-50, 50)

        # Обновление состояния кнопок
        if mouse_pos:
            for btn in self.buttons:
                btn.is_hovered = btn.rect.collidepoint(mouse_pos)

    def draw(self, surface):
        self.create_background()
        surface.blit(self.background, (0, 0))

        # Кораблик
        rotated_ship = pygame.transform.rotate(
            self.ship_img,
            math.sin(self.ship_offset) * 5
        )
        surface.blit(rotated_ship, (
            self.ship_pos[0] - rotated_ship.get_width() // 2,
            self.ship_pos[1] - rotated_ship.get_height() // 2
        ))

        # Заголовок с эффектом волны
        title = "МОРСКОЙ БОЙ"
        for i, char in enumerate(title):
            wave_y = 10 * math.sin(i / 2 + self.wave_offset / 10)
            char_surf = self.title_font.render(char, True, GOLD)
            shadow = self.title_font.render(char, True, BLACK)

            x = SCREEN_WIDTH // 2 - len(title) * 20 + i * 40
            y = 100 + wave_y

            for dx, dy in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
                surface.blit(shadow, (x + dx, y + dy))
            surface.blit(char_surf, (x, y))

        # Кнопки
        for btn in self.buttons:
            btn.draw(surface)

def draw_grid_labels(surface):
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    label_font = pygame.font.SysFont('Arial', 20, bold=True)

    for i in range(10):
        # Буквы
        text = label_font.render(letters[i], True, GOLD)
        text_shadow = label_font.render(letters[i], True, BLACK)

        # Тень
        surface.blit(text_shadow, (left_margin + i * block_size + block_size // 2 - text.get_width() // 2 + 1,
                                   upper_margin - 30 + 1))
        # Основной текст
        surface.blit(text, (left_margin + i * block_size + block_size // 2 - text.get_width() // 2,
                            upper_margin - 30))

        # Цифры
        num = label_font.render(str(i + 1), True, GOLD)
        num_shadow = label_font.render(str(i + 1), True, BLACK)

        # Тень
        surface.blit(num_shadow, (left_margin - 25 + 1,
                                  upper_margin + i * block_size + block_size // 2 - num.get_height() // 2 + 1))
        # Основной текст
        surface.blit(num, (left_margin - 25,
                           upper_margin + i * block_size + block_size // 2 - num.get_height() // 2))