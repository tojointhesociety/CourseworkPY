import pygame
import json
import os
from constants import *


class AuthScreen:
    def __init__(self, screen):
        self.screen = screen
        self.username = ""
        self.password = ""
        self.active_input = "user"
        self.error_msg = ""
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

    def draw_input_field(self, text, y, active):
        width = 300
        height = 40
        x = (SCREEN_WIDTH - width) // 2
        color = DARK_GREY if active else GREY
        pygame.draw.rect(self.screen, color, (x, y, width, height))
        text_surf = btn_font.render(text, True, WHITE)
        self.screen.blit(text_surf, (x + 10, y + 10))

    def draw_buttons(self):
        btn_width = 120
        btn_height = 40
        x = (SCREEN_WIDTH - btn_width * 2 - 20) // 2

        login_btn = pygame.Rect(x, 300, btn_width, btn_height)
        pygame.draw.rect(self.screen, GREEN, login_btn)
        text = btn_font.render("Вход", True, WHITE)
        self.screen.blit(text, (x + 40, 310))

        reg_btn = pygame.Rect(x + btn_width + 20, 300, btn_width, btn_height)
        pygame.draw.rect(self.screen, BLUE, reg_btn)
        text = btn_font.render("Регистрация", True, WHITE)
        self.screen.blit(text, (x + btn_width + 25, 310))

        return login_btn, reg_btn

    def draw_error(self):
        if self.error_msg:
            text = font.render(self.error_msg, True, RED)
            x = (SCREEN_WIDTH - text.get_width()) // 2
            self.screen.blit(text, (x, 350))

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if self.active_input == "user":
                if event.key == pygame.K_BACKSPACE:
                    self.username = self.username[:-1]
                else:
                    self.username += event.unicode
            elif self.active_input == "pass":
                if event.key == pygame.K_BACKSPACE:
                    self.password = self.password[:-1]
                else:
                    self.password += event.unicode

        if event.type == pygame.MOUSEBUTTONDOWN:
            x, y = pygame.mouse.get_pos()
            user_field = pygame.Rect((SCREEN_WIDTH - 300) // 2, 200, 300, 40)
            pass_field = pygame.Rect((SCREEN_WIDTH - 300) // 2, 250, 300, 40)

            if user_field.collidepoint(x, y):
                self.active_input = "user"
            elif pass_field.collidepoint(x, y):
                self.active_input = "pass"
            else:
                self.active_input = None

    def authenticate(self, login=True):
        if len(self.username) < 3 or len(self.password) < 4:
            self.error_msg = "Логин > 3 символов, пароль > 4!"
            return False

        if login:
            if self.users.get(self.username) == self.password:
                return True
            self.error_msg = "Неверные данные!"
        else:
            if self.username in self.users:
                self.error_msg = "Пользователь существует!"
                return False
            self.users[self.username] = self.password
            self.save_users()
            return True
        return False

    def run(self):
        running = True
        while running:
            self.screen.fill(WHITE)

            title = font.render("Морской бой - Авторизация", True, BLACK)
            self.screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 100))

            self.draw_input_field(self.username, 200, self.active_input == "user")
            self.draw_input_field("*" * len(self.password), 250, self.active_input == "pass")
            login_btn, reg_btn = self.draw_buttons()
            self.draw_error()

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return False

                self.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if login_btn.collidepoint(event.pos):
                        if self.authenticate(login=True):
                            return True
                    elif reg_btn.collidepoint(event.pos):
                        if self.authenticate(login=False):
                            return True
        return False