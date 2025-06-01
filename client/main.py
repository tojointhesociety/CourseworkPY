import pygame
from auth import AuthScreen
from gui import MainMenu, draw_grid_labels
from game_objects import Button, GameGrid
from gamelogic import GameLogic, ComputerAI
from ship_selector import ShipSelector
from constants import *


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Морской Бой")
    clock = pygame.time.Clock()

    # Авторизация
    auth_screen = AuthScreen(screen)
    if not auth_screen.run():
        pygame.quit()
        return

    game_logic = GameLogic(screen)
    ai = ComputerAI(game_logic.ai_grid)
    current_screen = "placement"
    running = True

    player_grid = GameGrid(left_margin, upper_margin, is_player=True)
    ai_grid = GameGrid(left_margin + 15 * block_size, upper_margin, is_player=False)

    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(OCEAN_BLUE)

        if current_screen == "placement":
            ai_grid.draw(screen, [[0] * 10 for _ in range(10)])
            game_logic.ship_selector.draw(screen, game_logic.get_available_ships_list())
            draw_grid_labels(screen)
            player_grid.draw(screen, game_logic.player_grid, game_logic)

            for event in pygame.event.get():
                if not game_logic.handle_events([event], pygame.mouse.get_pos()):
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected = game_logic.ship_selector.handle_event(
                        pygame.mouse.get_pos(),
                        game_logic.ships_available
                    )
                    if selected:
                        game_logic.selected_ship_size = selected
                        game_logic.ship_orientation = 0

                    elif player_grid.rect.collidepoint(mouse_pos) and game_logic.selected_ship_size:
                        grid_x = (mouse_pos[0] - player_grid.rect.x) // block_size
                        grid_y = (mouse_pos[1] - player_grid.rect.y) // block_size

                        if game_logic.validate_placement(grid_x, grid_y, game_logic.selected_ship_size):
                            game_logic.place_ship(grid_x, grid_y, game_logic.selected_ship_size)
                            game_logic.available_ships.remove(game_logic.selected_ship_size)
                            game_logic.selected_ship_size = None

                            # Проверка завершения расстановки
                            if not game_logic.available_ships:
                                current_screen = "battle"
                                game_logic.start_battle()

        # Фаза боя
        elif current_screen == "battle":
            # Отрисовка полей
            player_grid.draw(screen, game_logic.player_grid, game_logic)  # Передаем game_logic
            ai_grid.draw(screen, game_logic.ai_grid, game_logic)

            game_logic.draw_messages(screen)
            game_logic.draw_status_panel(screen)
            draw_grid_labels(screen)

            # Ход игрока
            if game_logic.current_turn:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if ai_grid.rect.collidepoint(event.pos):
                        grid_x = (event.pos[0] - ai_grid.rect.x) // block_size
                        grid_y = (event.pos[1] - ai_grid.rect.y) // block_size

                        result = game_logic.handle_shot(grid_x, grid_y, True)
                        if result is False:  # Только при промахе передаем ход
                            game_logic.current_turn = False

                        winner = game_logic.check_victory()
                        if winner:
                            current_screen = "game_over"

            if not game_logic.current_turn:
                pygame.time.delay(500)  # Короткая пауза для "раздумий" ИИ
                x, y = ai.make_move()
                hit = game_logic.handle_shot(x, y, is_player=False)
                if not hit:
                    game_logic.current_turn = True  # Передаем ход только при промахе

                winner = game_logic.check_victory()
                if winner:
                    current_screen = "game_over"
                # Отрисовка сообщений
            game_logic.draw_messages(screen)

        # Экран завершения игры
        elif current_screen == "game_over":
            screen.fill(OCEAN_BLUE)
            font = pygame.font.SysFont('Arial', 48)

            if winner == "player":
                text = font.render("Вы победили!", True, GREEN)
            else:
                text = font.render("ИИ победил!", True, RED)

            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 50))

            # Кнопка "В меню"
            menu_btn = Button("В главное меню", SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2 + 50, 200, 50)
            menu_btn.draw(screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if menu_btn.rect.collidepoint(event.pos):
                        current_screen = "placement"
                        game_logic = GameLogic(screen)  # Новая игра
                        ai = ComputerAI(game_logic.ai_grid)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()