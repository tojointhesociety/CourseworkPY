import pygame
from auth import AuthScreen
from gui import MainMenu, GameGrid, ShipSelector, draw_grid_labels
from gamelogic import GameLogic, ComputerAI
from constants import *


def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Морской Бой")
    clock = pygame.time.Clock()

    # Инициализация систем
    auth = AuthScreen(screen)
    if not auth.run():
        pygame.quit()
        return

    game_logic = GameLogic(screen)
    main_menu = MainMenu()
    ai = ComputerAI(game_logic.ai_grid)
    current_screen = "main_menu"
    placement_grid = GameGrid(left_margin, upper_margin)
    selector = ShipSelector(SCREEN_WIDTH - 250, 100)

    running = True
    while running:
        mouse_pos = pygame.mouse.get_pos()
        screen.fill(WHITE)

        # Обработка экранов
        if current_screen == "main_menu":
            main_menu.update(mouse_pos)
            main_menu.draw(screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if main_menu.buttons[0].rect.collidepoint(event.pos):
                        current_screen = "placement"
                    elif main_menu.buttons[1].rect.collidepoint(event.pos):
                        pass  # Сетевая игра
                    elif main_menu.buttons[2].rect.collidepoint(event.pos):
                        pass  # Настройки

        elif current_screen == "placement":
            # Отрисовка элементов размещения
            placement_grid.draw(screen, game_logic.player_grid)
            selector.draw(screen, [4 in game_logic.available_ships,
                                   3 in game_logic.available_ships,
                                   2 in game_logic.available_ships,
                                   1 in game_logic.available_ships])
            draw_grid_labels(screen)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected = selector.update(mouse_pos, game_logic.available_ships)
                    if selected:
                        sizes = [4, 3, 2, 1]
                        game_logic.selected_ship = sizes[selected[0]]
                    elif placement_grid.rect.collidepoint(mouse_pos):
                        grid_x = (mouse_pos[0] - left_margin) // block_size
                        grid_y = (mouse_pos[1] - upper_margin) // block_size
                        game_logic.place_ship(grid_x, grid_y)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                    game_logic.rotate_ship()

        elif current_screen == "battle":
            # Логика боя
            player_grid = GameGrid(left_margin, upper_margin)
            ai_grid = GameGrid(left_margin + 15 * block_size, upper_margin, False)

            player_grid.draw(screen, game_logic.player_grid)
            ai_grid.draw(screen, game_logic.ai_grid)
            draw_grid_labels(screen)

            if not game_logic.current_turn:
                x, y = ai.make_move()
                game_logic.handle_shot(x, y, False)
                game_logic.current_turn = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.MOUSEBUTTONDOWN and game_logic.current_turn:
                    if ai_grid.rect.collidepoint(mouse_pos):
                        grid_x = (mouse_pos[0] - ai_grid.rect.x) // block_size
                        grid_y = (mouse_pos[1] - ai_grid.rect.y) // block_size
                        game_logic.handle_shot(grid_x, grid_y)

            if game_logic.check_victory():
                running = False

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()