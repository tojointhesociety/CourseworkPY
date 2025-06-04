from auth import AuthScreen
from gui import MainMenu, draw_grid_labels
from game_objects import Button, GameGrid
from gamelogic import GameLogic
from constants import *
from network import Network


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Морской Бой")
    clock = pygame.time.Clock()

    auth_screen = AuthScreen(screen)
    if not auth_screen.run():
        pygame.quit()
        return

    menu = MainMenu()
    game_logic = None
    network = None
    current_screen = "menu"
    game_winner = None
    player_id = None
    ready_btn = None
    cancel_btn = None
    back_to_menu_btn = None
    waiting_time = 0

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(OCEAN_BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                if network:
                    network.disconnect()
                pygame.quit()
                return

            if current_screen == "menu":
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for i, btn in enumerate(menu.buttons):
                        if btn.rect.collidepoint(mouse_pos):
                            if i == 0:  # Игра с ИИ
                                game_logic = GameLogic(screen)
                                current_screen = "placement"
                                print("Начата игра с ИИ")
                            elif i == 1:
                                try:
                                    game_logic = GameLogic(screen)
                                    network = Network()
                                    print("Попытка подключения к серверу...")

                                    if network.connect():
                                        print("Подключение успешно")
                                        # Получаем данные от сервера
                                        if hasattr(network, 'player_id') and network.player_id is not None:
                                            player_id = network.player_id
                                            game_logic.player_id = player_id

                                            if player_id % 2 == 0:  # Первый игрок в паре
                                                current_screen = "waiting"
                                                game_logic.add_message("Ожидание второго игрока...")
                                                waiting_time = time.time()
                                                cancel_btn = Button("Отмена", SCREEN_WIDTH // 2 - 100,
                                                                    SCREEN_HEIGHT - 100, 200, 50)
                                                print(f"Игрок {player_id}: Ожидание второго игрока")
                                            else:  # Второй игрок в паре
                                                current_screen = "placement"
                                                game_logic.add_message("Соперник найден! Расставьте корабли.")
                                                ready_btn = Button("Готов", SCREEN_WIDTH // 2 - 100,
                                                                   SCREEN_HEIGHT - 100, 200, 50)
                                                print(f"Игрок {player_id}: Начало расстановки кораблей")
                                        else:
                                            game_logic.add_message("Ошибка: не получен ID игрока")
                                            print("Ошибка: не получен ID игрока")
                                    else:
                                        game_logic.add_message("Не удалось подключиться к серверу")
                                        print("Не удалось подключиться к серверу")
                                except Exception as e:
                                    print(f"Ошибка подключения: {str(e)}")
                                    if game_logic:
                                        game_logic.add_message(f"Ошибка: {str(e)}")

            elif current_screen == "waiting":
                if event.type == pygame.MOUSEBUTTONDOWN and cancel_btn and cancel_btn.rect.collidepoint(mouse_pos):
                    if network:
                        network.disconnect()
                    current_screen = "menu"
                    menu = MainMenu()
                    print("Отмена ожидания")

            elif current_screen == "placement":
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    if game_logic.selected_ship_size:
                        game_logic.ship_orientation = 1 - game_logic.ship_orientation
                        print("Корабль повернут")

                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected = game_logic.ship_selector.handle_event(
                        mouse_pos,
                        game_logic.get_available_ships_list()
                    )
                    if selected:
                        game_logic.selected_ship_size = selected
                        print(f"Выбран корабль размером {selected}")

                    elif (left_margin <= mouse_pos[0] <= left_margin + 10 * block_size and
                          upper_margin <= mouse_pos[1] <= upper_margin + 10 * block_size and
                          game_logic.selected_ship_size):

                        grid_x = (mouse_pos[0] - left_margin) // block_size
                        grid_y = (mouse_pos[1] - upper_margin) // block_size

                        if game_logic.validate_placement(grid_x, grid_y, game_logic.selected_ship_size):
                            game_logic.place_ship(grid_x, grid_y, game_logic.selected_ship_size)
                            print(f"Корабль размещен на ({grid_x}, {grid_y})")

                    elif ready_btn and ready_btn.rect.collidepoint(mouse_pos):
                        if all(count == 0 for count in game_logic.ships_available):
                            try:
                                response = network.send({
                                    'type': 'ready',
                                    'player_id': player_id,
                                    'grid': game_logic.player_grid
                                })
                                if response and response.get('status') == 'waiting':
                                    game_logic.add_message("Ожидаем готовности соперника...")
                                    print("Ожидание готовности соперника")
                                elif response and response.get('status') == 'battle':
                                    current_screen = "battle"
                                    game_logic.add_message("Игра начинается!")
                                    game_logic.current_turn = (player_id % 2 == 0)
                                    print("Начало игры")
                            except Exception as e:
                                game_logic.add_message(f"Ошибка: {str(e)}")
                                print(f"Ошибка отправки готовности: {str(e)}")

            elif current_screen == "battle":
                if event.type == pygame.MOUSEBUTTONDOWN and game_logic.current_turn:
                    if (left_margin + 15 * block_size <= mouse_pos[0] <= left_margin + 25 * block_size and
                            upper_margin <= mouse_pos[1] <= upper_margin + 10 * block_size):

                        grid_x = (mouse_pos[0] - (left_margin + 15 * block_size)) // block_size
                        grid_y = (mouse_pos[1] - upper_margin) // block_size

                        if game_logic.ai_grid[grid_y][grid_x] in [2, 3]:
                            game_logic.add_message("Сюда уже стреляли!")
                            continue

                        if network:
                            try:
                                print(f"Отправка выстрела на ({grid_x}, {grid_y})")
                                response = network.send({
                                    'type': 'shot',
                                    'x': grid_x,
                                    'y': grid_y,
                                    'player_id': player_id
                                })

                                if response:
                                    if response.get('hit'):
                                        game_logic.ai_grid[grid_y][grid_x] = 2
                                        if response.get('sunk'):
                                            game_logic.add_message("Вы потопили корабль!")
                                        else:
                                            game_logic.add_message("Вы попали!")
                                    else:
                                        game_logic.ai_grid[grid_y][grid_x] = 3
                                        game_logic.add_message("Вы промахнулись!")
                                        game_logic.current_turn = False

                                    if response.get('game_over'):
                                        current_screen = "game_over"
                                        game_winner = "player" if response.get('winner') == player_id else "enemy"
                            except Exception as e:
                                game_logic.add_message(f"Ошибка: {str(e)}")
                                print(f"Ошибка выстрела: {str(e)}")

                        else:
                            result = game_logic.handle_shot(grid_x, grid_y, True)

                            if result == "miss":
                                game_logic.current_turn = False
                                game_logic.add_message("Ваш ход завершен. Ход ИИ...")

                                x, y = game_logic.ai.make_move()
                                ai_result = game_logic.handle_shot(x, y, False)

                                if ai_result == "hit":
                                    game_logic.add_message("ИИ попал в ваш корабль!")
                                elif ai_result == "sunk":
                                    game_logic.add_message("ИИ потопил ваш корабль!")
                                elif ai_result == "miss":
                                    game_logic.add_message("ИИ промахнулся!")

                                game_logic.current_turn = True

                            winner = game_logic.check_victory()
                            if winner:
                                current_screen = "game_over"
                                game_winner = winner
                                game_logic.add_message("Вы победили!" if winner == "player" else "ИИ победил!")

            elif current_screen == "game_over":
                if event.type == pygame.MOUSEBUTTONDOWN and back_to_menu_btn and back_to_menu_btn.rect.collidepoint(
                        mouse_pos):
                    if network:
                        network.disconnect()
                        network = None
                    current_screen = "menu"
                    menu = MainMenu()
                    print("Возврат в главное меню")

        if network and network.connected:
            message = network.check_data()
            if message:
                print(f"Получено сетевое сообщение: {message}")

                if message.get('status') == 'start_placement' and current_screen == "waiting":
                    current_screen = "placement"
                    game_logic.add_message("Оба игрока подключены! Расставьте корабли.")
                    ready_btn = Button("Готов", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT - 100, 200, 50)
                    print("Начало расстановки кораблей")

                elif message.get('status') == 'battle' and current_screen == "placement":
                    current_screen = "battle"
                    game_logic.add_message("Игра начинается!")
                    game_logic.current_turn = (player_id % 2 == 0)
                    print("Начало игры")

                elif message.get('type') == 'shot_result' and current_screen == "battle":
                    x = message.get('x')
                    y = message.get('y')
                    opponent_id = message.get('player_id')

                    if opponent_id != player_id:
                        result = game_logic.handle_shot(x, y, False)

                        if result == "hit":
                            game_logic.add_message("Противник попал в ваш корабль!")
                        elif result == "sunk":
                            game_logic.add_message("Противник потопил ваш корабль!")
                        elif result == "miss":
                            game_logic.add_message("Противник промахнулся!")
                            game_logic.current_turn = True

                        winner = game_logic.check_victory()
                        if winner:
                            current_screen = "game_over"
                            game_winner = "player" if winner == "player" else "enemy"

        if current_screen == "waiting" and (time.time() - waiting_time > 30):
            game_logic.add_message("Таймаут подключения")
            print("Таймаут подключения")
            if network:
                network.disconnect()
            current_screen = "menu"

        if current_screen == "menu":
            menu.update(mouse_pos)
            menu.draw(screen)
            if game_logic and game_logic.messages:
                y_offset = SCREEN_HEIGHT - 100
                for msg in game_logic.messages[-3:]:
                    text_surf = pygame.font.SysFont('Arial', 20).render(msg, True, WHITE)
                    screen.blit(text_surf, (20, y_offset))
                    y_offset -= 30

        elif current_screen == "waiting":
            menu.background = menu.create_background()
            screen.blit(menu.background, (0, 0))

            font = pygame.font.SysFont('Arial', 36)
            text = font.render("Ожидание второго игрока...", True, WHITE)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

            if cancel_btn:
                cancel_btn.draw(screen)

            if game_logic and game_logic.messages:
                y_offset = SCREEN_HEIGHT - 100
                for msg in game_logic.messages[-3:]:
                    text_surf = pygame.font.SysFont('Arial', 20).render(msg, True, WHITE)
                    screen.blit(text_surf, (20, y_offset))
                    y_offset -= 30

        elif current_screen == "placement":
            GameGrid(left_margin, upper_margin, True).draw(screen, game_logic.player_grid, game_logic)
            GameGrid(left_margin + 15 * block_size, upper_margin, False).draw(screen, [[0] * 10 for _ in range(10)],
                                                                              None)

            game_logic.ship_selector.draw(screen, game_logic.get_available_ships_list())

            draw_grid_labels(screen)

            if ready_btn:
                ready_btn.draw(screen)

            game_logic.draw_messages(screen)

        elif current_screen == "battle":
            GameGrid(left_margin, upper_margin, True).draw(screen, game_logic.player_grid, game_logic)
            GameGrid(left_margin + 15 * block_size, upper_margin, False).draw(screen, game_logic.ai_grid, game_logic)

            draw_grid_labels(screen)

            status_text = "Ваш ход" if game_logic.current_turn else "Ход соперника"
            status_color = GREEN if game_logic.current_turn else RED
            status_surf = pygame.font.SysFont('Arial', 24).render(status_text, True, status_color)
            pygame.draw.rect(screen, (*DARK_BLUE, 200), (CHAT_X, CHAT_Y - 40, CHAT_WIDTH, 30))
            screen.blit(status_surf, (CHAT_X + 10, CHAT_Y - 35))

            game_logic.draw_messages(screen)

        elif current_screen == "game_over":
            menu.background = menu.create_background()
            screen.blit(menu.background, (0, 0))

            font = pygame.font.SysFont('Arial', 48)
            text = font.render("Вы победили!" if game_winner == "player" else "Вы проиграли!",
                               True, GREEN if game_winner == "player" else RED)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

            back_to_menu_btn = Button("В меню", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
            back_to_menu_btn.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    if network:
        network.disconnect()
    pygame.quit()


if __name__ == "__main__":
    main()