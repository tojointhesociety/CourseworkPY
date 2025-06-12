import sys
import threading
from pygame.locals import *
from auth import AuthScreen
from gui import MainMenu, draw_grid_labels, draw_waiting_screen, ConnectingUI, NetworkDialog, InputBox
from game_objects import Button, GameGrid
from gamelogic import GameLogic
from constants import *
from network import Network
import logging


class GameClient:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Морской Бой")
        self.clock = pygame.time.Clock()
        self.player_id = None
        self.auth_screen = AuthScreen(self.screen)
        self.menu = MainMenu()
        self.setup_ui_elements()
        self.current_screen = "auth"
        self.game_logic = None
        self.network = None
        self.connecting_ui = None
        self.ready_btn = Button("Готов", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
        self.cancel_btn = Button("Отмена", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
        self.back_to_menu_btn = Button("В меню", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("GameClient")

    def setup_ui_elements(self):
        self.ready_btn = Button("Готов", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
        self.cancel_btn = Button("Отмена", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
        self.back_to_menu_btn = Button("В меню", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)

    def connect_to_server(self):
        self.network = Network()
        try:
            if not self.network.connect():
                self.game_logic.add_message("Не удалось подключиться к серверу")
                return False

            self.player_id = self.network.player_id
            self.game_logic.player_id = self.player_id
            self.game_logic.network = self.network
            self.game_logic.add_message(f"Подключено! Ваш ID: {self.player_id}")
            return True
        except Exception as e:
            self.game_logic.add_message(f"Ошибка подключения: {str(e)}")
            return False

    def handle_server_messages(self):
        """Обрабатывает входящие сообщения из очереди"""
        if not self.network:
            return
        
        message = self.network.get_message()
        if message:
            self.process_server_message(message)

    def process_server_message(self, message):
        self.logger.info(f"Получено сообщение от сервера: {message}")
        msg_type = message.get('type')

        if msg_type == 'game_start':
            self.current_screen = "placement"
            opponent = message.get('opponent_name', 'Соперник')
            self.game_logic.add_message(f"Соперник найден: {opponent}!")
            self.game_logic.add_message("Расставьте свои корабли.")

        elif msg_type == 'shot_result':
            self.handle_shot_result(message)

        elif msg_type == 'game_over':
            self.current_screen = "game_over"
            self.game_winner = "player" if message.get('winner') == self.player_id else "enemy"

        elif msg_type == 'battle_start':
            self.current_screen = 'battle'
            self.game_logic.current_turn = message.get('your_turn', False)
            turn_msg = "Ваш ход." if self.game_logic.current_turn else "Ход соперника."
            self.game_logic.add_message(f"Игра началась! {turn_msg}")

        elif msg_type == 'opponent_left':
            self.show_error(message.get('message', 'Соперник отключился'))
            self.current_screen = 'menu'
            if self.network:
                self.network.disconnect()
                self.network = None

        elif msg_type == 'error':
            self.game_logic.add_message(f"Ошибка сервера: {message.get('message')}")

    def handle_shot_result(self, message):
        """Обрабатывает результат выстрела"""
        x, y = message['x'], message['y']

        if message['player_id'] != self.player_id:  # Выстрел соперника
            if message['hit']:
                self.game_logic.player_grid_data[y][x] = 2
                if message.get('sunk'):
                    self.game_logic.add_message("Ваш корабль потоплен!")
                else:
                    self.game_logic.add_message("По вашему кораблю попали!")
            else:
                self.game_logic.player_grid_data[y][x] = 3
            
            self.game_logic.current_turn = message['your_turn']

            if message.get('game_over'):
                self.current_screen = "game_over"
                self.game_winner = "player" if message['winner'] == self.player_id else "enemy"
        else:  # Наш выстрел
            if message['hit']:
                self.game_logic.enemy_grid_data[y][x] = 2
                if message.get('sunk'):
                    cells = message.get('sunk_cells', [])
                    self.game_logic.mark_around_ship(cells, self.game_logic.enemy_grid_data)
                    self.game_logic.add_message("Вы потопили корабль!")
                else:
                    self.game_logic.add_message("Вы попали!")
            else:
                self.game_logic.enemy_grid_data[y][x] = 3
                self.game_logic.add_message("Вы промахнулись!")

            self.game_logic.current_turn = message['your_turn']

    def send_placement_to_server(self):
        """Отправляет расстановку на сервер"""
        try:
            placement_data = {
                'type': 'place_ships',
                'grid': self.game_logic.player_grid_data,
                'ships': self.game_logic.get_ship_config()
            }
            self.network.send_data(placement_data)
        except Exception as e:
            self.game_logic.add_message(f"Ошибка отправки: {str(e)}")

    def send_network_shot(self, x, y):
        """Отправляет выстрел на сервер"""
        try:
            self.network.send_data({
                'type': 'shot',
                'x': x,
                'y': y
            })
        except Exception as e:
            self.game_logic.add_message(f"Ошибка: {str(e)}")
            return "network_error"

    def run(self):
        """Главный игровой цикл"""
        running = True
        while running:
            mouse_pos = pygame.mouse.get_pos()
            self.screen.fill(OCEAN_BLUE)

            self.handle_server_messages()

            for event in pygame.event.get():
                if event.type == QUIT:
                    running = False

                self.handle_event(event, mouse_pos)

            self.draw_current_screen(mouse_pos)
            pygame.display.flip()
            self.clock.tick(60)

        if self.network:
            self.network.disconnect()
        pygame.quit()
        sys.exit()

    def handle_event(self, event, mouse_pos):
        if self.current_screen == "auth":
            if self.auth_screen.handle_event(event) is True:
                self.current_screen = "menu"
                self.game_logic = GameLogic(self.screen)

        elif self.current_screen == "menu":
            self.handle_menu_event(event, mouse_pos)

        elif self.current_screen == "connecting":
            self.handle_connecting_event(event)

        elif self.current_screen == "waiting":
            self.handle_waiting_event(event, mouse_pos)

        elif self.current_screen == "placement":
            self.handle_placement_event(event, mouse_pos)

        elif self.current_screen == "battle":
            self.handle_battle_event(event, mouse_pos)

        elif self.current_screen == "game_over":
            self.handle_game_over_event(event, mouse_pos)

    def handle_menu_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, btn in enumerate(self.menu.buttons):
                if btn.rect.collidepoint(event.pos):
                    if i == 0:  # Игра с ИИ
                        self.start_ai_game()
                    elif i == 1:  # Сетевая игра
                        self.start_network_game()

    def handle_connecting_event(self, event):
        if event.type == USEREVENT and hasattr(event, 'action') and event.action == 'network_event':
            if event.status == 'connected':
                self.player_id = self.network.player_id
                self.game_logic = GameLogic(self.screen)
                self.game_logic.player_id = self.player_id
                self.current_screen = "waiting"
                self.game_logic.add_message("Ожидание соперника...")
                self.network.send_data({'type': 'find_game'})
            else:
                error_msg = "Не удалось подключиться"
                if hasattr(event, 'message') and event.message:
                    error_msg += f": {event.message}"
                self.show_error(error_msg)
                self.current_screen = 'menu'
                if self.network:
                    self.network.disconnect()
                    self.network = None
            self.connecting_ui = None

    def start_ai_game(self):
        self.game_logic = GameLogic(self.screen)
        self.current_screen = "placement"
        self.game_logic.add_message("Режим игры с ИИ")

    def start_network_game(self):
        # Создаем окно ввода параметров
        input_dialog = NetworkDialog(self.screen)
        result = input_dialog.run()

        if not result:
            return  # Пользователь отменил ввод

        server_ip, server_port, player_name = result
        
        self.current_screen = "connecting"
        self.connecting_ui = ConnectingUI(self.screen)
        self.connecting_ui.show("Подключение к серверу...")

        # В отдельном потоке пытаемся подключиться
        def connect_task():
            try:
                self.network = Network()
                if self.network.connect(server_ip, server_port, player_name):
                    # Успешное подключение
                    pygame.event.post(pygame.event.Event(
                        USEREVENT,
                        {'action': 'network_event', 'status': 'connected'}
                    ))
                else:
                    pygame.event.post(pygame.event.Event(
                        USEREVENT,
                        {'action': 'network_event', 'status': 'failed'}
                    ))
            except Exception as e:
                pygame.event.post(pygame.event.Event(
                    USEREVENT,
                    {'action': 'network_event', 'status': 'error', 'message': str(e)}
                ))

        threading.Thread(target=connect_task, daemon=True).start()

    def check_game_state(self):
        """Проверяет состояние игры в фоне"""
        while self.network and self.network.connected:
            state = self.network.send({'type': 'get_state'})
            if not state:
                break

            if state.get('status') == 'battle':
                pygame.event.post(pygame.event.Event(
                    pygame.USEREVENT,
                    {'action': 'network_event', 'status': 'start_battle'}
                ))
                break

            time.sleep(1)

    def handle_waiting_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and self.cancel_btn.rect.collidepoint(event.pos):
            self.network.disconnect()
            self.current_screen = "menu"

    def handle_placement_event(self, event, mouse_pos):
        # Rotate ship
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            if self.game_logic.selected_ship_size:
                self.game_logic.ship_orientation = 1 - self.game_logic.ship_orientation
                return

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Click on ship selector
            clicked_ship_size = self.game_logic.ship_selector.handle_event(event)
            if clicked_ship_size:
                if self.game_logic.ships_to_place[clicked_ship_size] > 0:
                    if self.game_logic.selected_ship_size == clicked_ship_size:
                        self.game_logic.selected_ship_size = None  # Deselect
                    else:
                        self.game_logic.selected_ship_size = clicked_ship_size  # Select
                else:
                    self.game_logic.add_message(f"{clicked_ship_size}-палубные корабли закончились.")
                return

            # Click on player grid to place a ship
            if self.game_logic.selected_ship_size and self.game_logic.player_grid_ui.rect.collidepoint(event.pos):
                grid_x = (event.pos[0] - self.game_logic.player_grid_ui.rect.x) // block_size
                grid_y = (event.pos[1] - self.game_logic.player_grid_ui.rect.y) // block_size

                if self.game_logic.validate_placement(grid_x, grid_y, self.game_logic.selected_ship_size):
                    self.game_logic.place_ship(grid_x, grid_y, self.game_logic.selected_ship_size)
                else:
                    self.game_logic.add_message("Нельзя разместить корабль здесь!")
                return

            # Click on Ready button
            if self.ready_btn.rect.collidepoint(event.pos):
                self.finalize_placement()

    def finalize_placement(self):
        if sum(self.game_logic.ships_to_place.values()) > 0:
            self.show_error("Нужно расставить все корабли!")
            return

        self.game_logic.add_message("Ожидаем готовности соперника...")
        self.send_placement_to_server()

    def handle_battle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and self.game_logic.current_turn:
            self.process_battle_click(event.pos)

    def process_battle_click(self, pos):
        if not self.game_logic.current_turn:
            self.game_logic.add_message("Сейчас не ваш ход!")
            return

        # Клик по полю противника
        if self.game_logic.enemy_grid_ui.rect.collidepoint(pos):
            grid_x = (pos[0] - self.game_logic.enemy_grid_ui.rect.x) // block_size
            grid_y = (pos[1] - self.game_logic.enemy_grid_ui.rect.y) // block_size

            if not (0 <= grid_x < 10 and 0 <= grid_y < 10):
                return

            if self.game_logic.enemy_grid_data[grid_y][grid_x] in [2, 3]:
                self.game_logic.add_message("Вы уже стреляли сюда!")
                return
            
            self.send_network_shot(grid_x, grid_y)
        
        # Клик по своему полю
        elif self.game_logic.player_grid_ui.rect.collidepoint(pos):
            self.game_logic.add_message("Это ваше поле! Стреляйте по полю врага.")

    def handle_game_over_event(self, event, mouse_pos):
        self.back_to_menu_btn.is_hovered = self.back_to_menu_btn.rect.collidepoint(mouse_pos)
        if event.type == pygame.MOUSEBUTTONDOWN and self.back_to_menu_btn.is_hovered:
            self.current_screen = "menu"
            self.game_logic = None
            if self.network:
                self.network.disconnect()
                self.network = None

    def draw_current_screen(self, mouse_pos):
        if self.current_screen == "auth":
            self.auth_screen.draw()

        elif self.current_screen == "menu":
            self.menu.update(mouse_pos)
            self.menu.draw(self.screen)
            if self.game_logic and self.game_logic.messages:
                self.draw_messages()

        elif self.current_screen == "connecting":
            if self.connecting_ui:
                self.connecting_ui.update()

        elif self.current_screen == "waiting":
            draw_waiting_screen(self.screen, self.auth_screen.title_font, "Ожидание соперника")

        elif self.current_screen == "placement":
            self.draw_placement_screen(mouse_pos)

        elif self.current_screen == "battle":
            self.draw_battle_screen()

        elif self.current_screen == "game_over":
            self.draw_game_over_screen()

    def draw_menu_screen(self, mouse_pos):
        self.menu.update(mouse_pos)
        self.menu.draw(self.screen)
        if self.game_logic and self.game_logic.messages:
            self.draw_messages()

    def draw_waiting_screen(self):
        draw_waiting_screen(self.screen, self.auth_screen.title_font)
        self.cancel_btn.draw(self.screen)
        self.draw_messages()

    def draw_placement_screen(self, mouse_pos):
        self.screen.fill(OCEAN_BLUE)
        self.game_logic.player_grid_ui.draw(self.screen, self.game_logic.player_grid_data, self.game_logic, is_player_grid=True)
        draw_grid_labels(self.screen, self.game_logic.player_grid_ui.rect.x, self.game_logic.player_grid_ui.rect.y)
        self.game_logic.ship_selector.draw(self.screen, self.game_logic.ships_to_place, self.game_logic.selected_ship_size, mouse_pos)
        
        self.ready_btn.is_hovered = self.ready_btn.rect.collidepoint(mouse_pos)
        self.ready_btn.draw(self.screen)
        self.game_logic.draw_messages(self.screen)

    def draw_battle_screen(self):
        self.screen.fill(OCEAN_BLUE)
        # Ваше поле
        self.game_logic.player_grid_ui.draw(self.screen, self.game_logic.player_grid_data, is_player_grid=True)
        draw_grid_labels(self.screen, self.game_logic.player_grid_ui.rect.x, self.game_logic.player_grid_ui.rect.y)
        
        # Поле врага
        self.game_logic.enemy_grid_ui.draw(self.screen, self.game_logic.enemy_grid_data, is_player_grid=False)
        draw_grid_labels(self.screen, self.game_logic.enemy_grid_ui.rect.x, self.game_logic.enemy_grid_ui.rect.y)
        
        self.game_logic.draw_status_panel(self.screen)
        self.game_logic.draw_messages(self.screen)

    def draw_game_over_screen(self):
        # Продолжаем рисовать поле боя на фоне
        self.draw_battle_screen()

        # Затемняющий оверлей
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))

        # Текст результата
        result_text = "Вы победили!" if self.game_winner == "player" else "Вы проиграли!"
        font = pygame.font.SysFont('Arial', 72, bold=True)
        text_surf = font.render(result_text, True, GOLD)
        text_rect = text_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 50))

        # Тень для текста
        shadow_surf = font.render(result_text, True, BLACK)
        self.screen.blit(shadow_surf, (text_rect.x + 3, text_rect.y + 3))
        self.screen.blit(text_surf, text_rect)

        # Кнопка выхода в меню
        self.back_to_menu_btn.draw(self.screen)

    def draw_messages(self):
        if not self.game_logic.messages:
            return

        y_offset = SCREEN_HEIGHT - 100
        for msg in self.game_logic.messages[-3:]:
            text = self.game_logic.message_font.render(msg, True, WHITE)
            self.screen.blit(text, (20, y_offset))
            y_offset -= 30

    def handle_network_events(self):
        """Обработка сетевых сообщений в основном цикле"""
        if not self.network or not self.network.connected:
            return

        message = self.network.receive_data()
        if not message:
            return

        if message.get('type') == 'game_start':
            self.handle_game_start(message)
        elif message.get('type') == 'battle_start':
            self.handle_battle_start(message)
        elif message.get('type') == 'shot_result':
            self.handle_shot_result(message)
        elif message.get('type') == 'game_over':
            self.handle_game_over(message)

    def handle_game_start(self, message):
        """Обработка начала игры"""
        self.game_logic.player_num = message['player_num']
        self.game_logic.opponent_name = message['opponent_name']
        self.current_screen = "placement"
        self.game_logic.add_message(f"Соперник найден: {message['opponent_name']}")

    def check_server_connection(host="localhost", port=5555):
        try:
            test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            test_sock.settimeout(3)
            test_sock.connect((host, port))
            test_sock.close()
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    if not check_server_connection():
        print("Сервер недоступен. Проверьте:")
        print("1. Запущен ли сервер")
        print("2. Правильный IP/порт")
        print("3. Брандмауэр/антивирус")
        input("Нажмите Enter для выхода...")
        sys.exit()

    def show_error(self, message):
        """Унифицированный метод показа ошибок"""
        # Создаем поверхность для сообщения
        error_surface = pygame.Surface((600, 300))
        error_surface.fill(DARK_BLUE)
        pygame.draw.rect(error_surface, RED, (0, 0, 600, 300), 3)

        # Текст ошибки
        error_font = pygame.font.SysFont('Arial', 24)
        text = error_font.render(message, True, WHITE)
        error_surface.blit(text, (300 - text.get_width() // 2, 100))

        # Кнопка OK
        ok_btn = Button("OK", 250, 200, 100, 50)

        # Основной цикл
        waiting = True
        while waiting:
            mouse_pos = pygame.mouse.get_pos()
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == MOUSEBUTTONDOWN:
                    if ok_btn.rect.collidepoint(
                            (mouse_pos[0] - (SCREEN_WIDTH // 2 - 300),
                             mouse_pos[1] - (SCREEN_HEIGHT // 2 - 150))
                    ):
                        waiting = False

            # Отрисовка
            self.screen.fill((0, 0, 0, 0))  # Полупрозрачный фон
            self.screen.blit(error_surface, (SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 150))
            ok_btn.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    client = GameClient()
    client.run()