import random
from constants import *
from game_objects import Button

class MainMenu:
    def __init__(self):
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

    def draw(self, surface):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(OCEAN_BLUE)

        for y in range(0, SCREEN_HEIGHT, 20):
            amplitude = 10 * (1 + math.sin((y + self.wave_offset) / 30))
            points = [(x, y + amplitude * math.sin(x / 50 + self.wave_offset / 10))
                        for x in range(0, SCREEN_WIDTH + 1, 10)]
            pygame.draw.lines(bg, LIGHT_BLUE, False, points, 2)

        pygame.draw.circle(bg, GOLD, (SCREEN_WIDTH - 100, 100), 40)

        rotated_ship = pygame.transform.rotate(
            self.ship_img,
            math.sin(self.ship_offset) * 5
        )
        bg.blit(rotated_ship, (
            self.ship_pos[0] - rotated_ship.get_width() // 2,
            self.ship_pos[1] - rotated_ship.get_height() // 2
        ))

        title = "МОРСКОЙ БОЙ"
        for i, char in enumerate(title):
            wave_y = 10 * math.sin(i / 2 + self.wave_offset / 10)
            char_surf = self.title_font.render(char, True, GOLD)
            shadow = self.title_font.render(char, True, BLACK)

            x = SCREEN_WIDTH // 2 - len(title) * 20 + i * 40
            y = 100 + wave_y

            for dx, dy in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
                bg.blit(shadow, (x + dx, y + dy))
            bg.blit(char_surf, (x, y))

        surface.blit(bg, (0, 0))


        for btn in self.buttons:
            btn.draw(surface)

    def update(self, mouse_pos=None):
        self.wave_offset += 0.7
        self.ship_pos[0] += self.ship_speed
        self.ship_pos[1] += math.sin(self.ship_offset) * 2
        self.ship_offset += 0.05

        if self.ship_pos[0] > SCREEN_WIDTH + 100:
            self.ship_pos[0] = -100
            self.ship_pos[1] = SCREEN_HEIGHT // 2 + random.randint(-50, 50)

        if mouse_pos:
            for btn in self.buttons:
                btn.is_hovered = btn.rect.collidepoint(mouse_pos)

def draw_waiting_screen(surface, font, message="Ожидание соперника..."):
    bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
    bg.fill(OCEAN_BLUE)

        # Текст с анимированными точками
    dots = "." * (int(pygame.time.get_ticks() / 500) % 4)
    text = font.render(message + dots, True, WHITE)
    text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))

        # Тень текста
    shadow = font.render(message + dots, True, BLACK)
    for dx, dy in [(2, 2), (-2, 2), (2, -2), (-2, -2)]:
        bg.blit(shadow, (text_rect.x + dx, text_rect.y + dy))

    bg.blit(text, text_rect)
    surface.blit(bg, (0, 0))

def draw_grid_labels(surface, x_offset, y_offset):
    letters = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J']
    label_font = pygame.font.SysFont('Arial', 20, bold=True)

    for i in range(10):
        text = label_font.render(letters[i], True, GOLD)
        text_shadow = label_font.render(letters[i], True, BLACK)

        surface.blit(text_shadow, (x_offset + i * block_size + block_size // 2 - text.get_width() // 2 + 1,
                                   y_offset - 30 + 1))
        surface.blit(text, (x_offset + i * block_size + block_size // 2 - text.get_width() // 2,
                            y_offset - 30))

        num = label_font.render(str(i + 1), True, GOLD)
        num_shadow = label_font.render(str(i + 1), True, BLACK)

        surface.blit(num_shadow, (x_offset - 25 + 1,
                                  y_offset + i * block_size + block_size // 2 - num.get_height() // 2 + 1))
        surface.blit(num, (x_offset - 25,
                           y_offset + i * block_size + block_size // 2 - num.get_height() // 2))


class TextBox:
    def __init__(self, text, x, y, color=WHITE, font_size=24):
        self.text = text
        self.x = x
        self.y = y
        self.font = pygame.font.SysFont('Arial', font_size)
        self.color = color

    def draw(self, surface):
        text_surf = self.font.render(self.text, True, self.color)
        surface.blit(text_surf, (self.x - text_surf.get_width() // 2,
                                 self.y - text_surf.get_height() // 2))


class LoadingIndicator:
    def __init__(self, x, y, radius=20, speed=5):
        self.x = x
        self.y = y
        self.radius = radius
        self.speed = speed
        self.angle = 0

    def draw(self, surface):
        self.angle += self.speed
        for i in range(8):
            angle = self.angle + i * 45
            alpha = 255 * (i / 8)
            pygame.draw.circle(
                surface,
                (*LIGHT_BLUE, alpha),
                (self.x + math.cos(math.radians(angle)) * self.radius,
                 self.y + math.sin(math.radians(angle)) * self.radius),
                5
            )


class InputBox:
    def __init__(self, x, y, w, h, placeholder=''):
        self.rect = pygame.Rect(x - w // 2, y - h // 2, w, h)
        self.color = LIGHT_BLUE
        self.text = ''
        self.placeholder = placeholder
        self.font = pygame.font.SysFont('Arial', 24)
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
            self.color = GOLD if self.active else LIGHT_BLUE

        if event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode
        return False

    def draw(self, screen):
        # Рисуем рамку
        pygame.draw.rect(screen, self.color, self.rect, 2)

        # Текст или плейсхолдер
        if self.text:
            text_surface = self.font.render(self.text, True, WHITE)
        else:
            text_surface = self.font.render(self.placeholder, True, (*WHITE, 128))

        screen.blit(text_surface, (self.rect.x + 5, self.rect.y + 5))


class NetworkDialog:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 24)
        self.input_ip = InputBox(SCREEN_WIDTH // 2, 200, 300, 32, "localhost")
        self.input_port = InputBox(SCREEN_WIDTH // 2, 250, 300, 32, "5555")
        self.input_name = InputBox(SCREEN_WIDTH // 2, 300, 300, 32, "Игрок")
        self.btn_connect = Button("Подключиться", SCREEN_WIDTH // 2 - 110, 350, 220, 40)
        self.btn_cancel = Button("Отмена", SCREEN_WIDTH // 2 - 110, 400, 220, 40)

    def run(self):
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None

                self.input_ip.handle_event(event)
                self.input_port.handle_event(event)
                self.input_name.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.btn_connect.rect.collidepoint(mouse_pos):
                        try:
                            port = int(self.input_port.text)
                            return (
                                self.input_ip.text or "localhost",
                                port,
                                self.input_name.text or f"Player_{random.randint(1000, 9999)}"
                            )
                        except ValueError:
                            pass

                    elif self.btn_cancel.rect.collidepoint(mouse_pos):
                        return None
            
            self.btn_connect.is_hovered = self.btn_connect.rect.collidepoint(mouse_pos)
            self.btn_cancel.is_hovered = self.btn_cancel.rect.collidepoint(mouse_pos)

            # Отрисовка
            self.screen.fill(OCEAN_BLUE)

            title = self.font.render("Параметры подключения", True, WHITE)
            self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

            self.input_ip.draw(self.screen)
            self.input_port.draw(self.screen)
            self.input_name.draw(self.screen)
            self.btn_connect.draw(self.screen)
            self.btn_cancel.draw(self.screen)

            pygame.display.flip()


class ConnectingUI:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont('Arial', 24)
        self.progress = 0

    def show(self, message):
        self.message = message
        self.start_time = time.time()

    def update(self):
        self.progress = (time.time() - self.start_time) % 1

        # Отрисовка
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))
        self.screen.blit(overlay, (0, 0))

        text = self.font.render(self.message, True, WHITE)
        self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 20))

        # Анимированная точка
        dot_pos = int(self.progress * 3)
        for i in range(3):
            alpha = 255 if i == dot_pos else 100
            pygame.draw.circle(
                self.screen,
                (*WHITE, alpha),
                (SCREEN_WIDTH // 2 - 30 + i * 30, SCREEN_HEIGHT // 2 + 20),
                5
            )