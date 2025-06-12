import re
import hashlib
import os
import json
from constants import *
from game_objects import Button

class AuthSystem:
    def __init__(self):
        self.users_file = "users.json"
        self.load_users()

    def load_users(self):
        if not os.path.exists(self.users_file):
            self.users = {}
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f)
        else:
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)

    def save_users(self):
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f)

    def validate_username(self, username):
        if len(username) < 4:
            return "Логин должен содержать минимум 4 символа"
        if not re.match(r'^[a-zA-Z0-9_\-]+$', username):
            return "Логин может содержать только латинские буквы, цифры, _ и -"
        if username in self.users:
            return "Этот логин уже занят"
        return None

    def validate_password(self, password):
        if len(password) < 6:
            return "Пароль должен содержать минимум 6 символов"
        if not re.match(r'^[a-zA-Z0-9!@#$%^&*()_\-+=]+$', password):
            return "Пароль содержит недопустимые символы"
        return None

    def register(self, username, password, confirm_password):
        if password != confirm_password:
            return "Пароли не совпадают"

        username_error = self.validate_username(username)
        if username_error:
            return username_error

        password_error = self.validate_password(password)
        if password_error:
            return password_error

        self.users[username] = hashlib.sha256(password.encode()).hexdigest()
        self.save_users()
        return None

    def login(self, username, password):
        if username not in self.users:
            return "Неверный логин"
        if self.users[username] != hashlib.sha256(password.encode()).hexdigest():
            return "Неверный пароль"
        return None


class AuthScreen:
    def __init__(self, screen):
        self.screen = screen
        self.auth = AuthSystem()
        self.mode = "login"
        self.username = ""
        self.password = ""
        self.confirm_password = ""
        self.active_field = None
        self.error_msg = ""
        self.success_msg = ""
        self.wave_offset = 0
        self.background = self.create_background()
        self.title_font = pygame.font.SysFont('Arial', 48, bold=True)
        self.input_font = pygame.font.SysFont('Arial', 28)
        self.error_font = pygame.font.SysFont('Arial', 24)
        self.update_buttons()

    def create_background(self):
        bg = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        bg.fill(OCEAN_BLUE)
        for y in range(0, SCREEN_HEIGHT, 20):
            wave_y = y + 10 * math.sin((y + self.wave_offset) / 30)
            points = [(x, wave_y + 10 * math.sin(x / 50 + self.wave_offset / 10))
                      for x in range(0, SCREEN_WIDTH + 1, 10)]
            pygame.draw.lines(bg, LIGHT_BLUE, False, points, 2)
        return bg

    def update_buttons(self):
        center_x = SCREEN_WIDTH // 2
        self.action_btn = Button(
            "Войти" if self.mode == "login" else "Регистрация",
            center_x - 220, 450, 200, 50,
            color=WOOD, hover_color=GOLD, text_color=WHITE
        )
        self.switch_btn = Button(
            "Регистрация" if self.mode == "login" else "Вход",
            center_x + 20, 450, 200, 50,
            color=DARK_BLUE, hover_color=LIGHT_BLUE, text_color=WHITE
        )

    def draw_field(self, text, y, is_active, is_password=False):
        width = 400
        height = 50
        x = (SCREEN_WIDTH - width) // 2

        pygame.draw.rect(self.screen, (*LIGHT_BLUE, 100) if is_active else (*DARK_BLUE, 100),
                         (x, y, width, height), border_radius=10)
        pygame.draw.rect(self.screen, BLACK, (x, y, width, height), 2, border_radius=10)

        display_text = "*" * len(text) if is_password else text
        if not display_text and not is_active:
            placeholder = "Пароль" if is_password else "Логин"
            if self.mode == "register" and y == 320:
                placeholder = "Повторите пароль"
            text_surf = self.input_font.render(placeholder, True, (*WHITE, 150))
        else:
            text_surf = self.input_font.render(display_text, True, WHITE)

        self.screen.blit(text_surf, (x + 15, y + 10))

    def draw(self):
        self.wave_offset += 0.5
        self.background = self.create_background()
        self.screen.blit(self.background, (0, 0))

        title = self.title_font.render("Морской Бой", True, GOLD)
        shadow = self.title_font.render("Морской Бой", True, BLACK)

        for dx, dy in [(3, 3), (-3, 3), (3, -3), (-3, -3)]:
            self.screen.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + dx, 100 + dy))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 100))

        subtitle = self.input_font.render(
            "Вход в систему" if self.mode == "login" else "Регистрация",
            True, WHITE
        )
        self.screen.blit(subtitle, (SCREEN_WIDTH // 2 - subtitle.get_width() // 2, 170))

        self.draw_field(self.username, 250, self.active_field == "username")
        self.draw_field(self.password, 310, self.active_field == "password", True)

        if self.mode == "register":
            self.draw_field(self.confirm_password, 370, self.active_field == "confirm_password", True)

        self.action_btn.draw(self.screen)
        self.switch_btn.draw(self.screen)

        if hasattr(self, 'error_msg') and self.error_msg:
            error_text = self.error_font.render(self.error_msg, True, RED)
            self.screen.blit(error_text, (SCREEN_WIDTH // 2 - error_text.get_width() // 2, 470))

        if hasattr(self, 'success_msg') and self.success_msg:
            success_text = self.error_font.render(self.success_msg, True, GREEN)
            self.screen.blit(success_text, (SCREEN_WIDTH // 2 - success_text.get_width() // 2, 470))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            self.active_field = None

            field_x = (SCREEN_WIDTH - 400) // 2
            if field_x <= x <= field_x + 400:
                if 250 <= y <= 300:
                    self.active_field = "username"
                elif 310 <= y <= 360:
                    self.active_field = "password"
                elif self.mode == "register" and 370 <= y <= 420:
                    self.active_field = "confirm_password"

            if self.action_btn.rect.collidepoint(x, y):
                if self.mode == "login":
                    error = self.auth.login(self.username, self.password)
                    if not error:
                        return True
                    self.error_msg = error
                    self.success_msg = ""
                else:
                    error = self.auth.register(self.username, self.password, self.confirm_password)
                    if not error:
                        self.success_msg = "Регистрация успешна! Войдите в систему"
                        self.error_msg = ""
                        self.mode = "login"
                        self.update_buttons()
                    else:
                        self.error_msg = error
                        self.success_msg = ""

            elif self.switch_btn.rect.collidepoint(x, y):
                self.mode = "register" if self.mode == "login" else "login"
                self.error_msg = ""
                self.success_msg = ""
                self.update_buttons()

        elif event.type == pygame.KEYDOWN and self.active_field:
            if event.key == pygame.K_BACKSPACE:
                if self.active_field == "username":
                    self.username = self.username[:-1]
                elif self.active_field == "password":
                    self.password = self.password[:-1]
                elif self.active_field == "confirm_password":
                    self.confirm_password = self.confirm_password[:-1]
            else:
                if self.active_field == "username" and len(self.username) < 20:
                    self.username += event.unicode
                elif self.active_field == "password" and len(self.password) < 30:
                    self.password += event.unicode
                elif self.active_field == "confirm_password" and len(self.confirm_password) < 30:
                    self.confirm_password += event.unicode

    def run(self):
        clock = pygame.time.Clock()
        while True:
            mouse_pos = pygame.mouse.get_pos()
            self.action_btn.is_hovered = self.action_btn.rect.collidepoint(mouse_pos)
            self.switch_btn.is_hovered = self.switch_btn.rect.collidepoint(mouse_pos)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False

                if self.handle_event(event) is True:
                    return True

            self.draw()
            pygame.display.flip()
            clock.tick(60)