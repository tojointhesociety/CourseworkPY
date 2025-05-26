class Game:
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = [None, None]
        self.players_ready = 0
        self.started = False
        self.grids = [
            [[0] * 10 for _ in range(10)],  # Player 0 grid
            [[0] * 10 for _ in range(10)]  # Player 1 grid
        ]
        self.turn = 0
        self.winner = -1
        self.ships = [
            [4, 3, 3, 2, 2, 2, 1, 1, 1, 1],  # Player 0 ships
            [4, 3, 3, 2, 2, 2, 1, 1, 1, 1]  # Player 1 ships
        ]

    def validate_placement(self, player, data):
        grid = data['grid']
        ships = sorted([sum(row) for row in grid], reverse=True)
        return ships == self.ships[player]

    def process_shot(self, player, x, y):
        if player != self.turn or self.winner != -1:
            return False

        target = 1 - player
        if self.grids[target][y][x] == 1:
            self.grids[target][y][x] = 2
            if self.check_win(target):
                self.winner = player
            return True
        else:
            self.grids[target][y][x] = 3
            self.turn = 1 - player
            return False

    def check_win(self, target):
        return all(cell != 1 for row in self.grids[target] for cell in row)

    def get_state(self, player):
        return {
            'your_grid': self.grids[player],
            'enemy_grid': self.get_visible_enemy_grid(player),
            'turn': self.turn,
            'winner': self.winner,
            'ready': self.players_ready == 2,
            'player_id': player
        }

    def get_visible_enemy_grid(self, player):
        return [
            [3 if cell == 3 else 2 if cell == 2 else 0
             for cell in row]
            for row in self.grids[1 - player]
        ]

    def reset(self):
        self.grids = [
            [[0] * 10 for _ in range(10)],
            [[0] * 10 for _ in range(10)]
        ]
        self.turn = 0
        self.winner = -1
        self.players_ready = 0