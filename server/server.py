import socket
import threading
import pickle
from _thread import *
import time


class Server:
    def __init__(self):
        self.host = "0.0.0.0"
        self.port = 5555
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.games = {}
        self.id_count = 0
        self.connected = set()

    def start(self):
        try:
            self.sock.bind((self.host, self.port))
            self.sock.listen()
            print(f"[SRV] Server started on {self.host}:{self.port}")
            self.listen_connections()
        except Exception as e:
            print(f"[SRV ERROR] {e}")

    def client_thread(self, conn, player_id, game_id):
        conn.send(str.encode(str(player_id)))

        while True:
            try:
                data = conn.recv(4096)
                if not data: break

                message = pickle.loads(data)
                if game_id in self.games:
                    game = self.games[game_id]

                    if message['type'] == 'ready':
                        game.players_ready += 1
                        if game.players_ready == 2:
                            game.start = True

                    elif message['type'] == 'shot':
                        x, y = message['coords']
                        game.process_shot(player_id, x, y)

                    elif message['type'] == 'get_state':
                        conn.sendall(pickle.dumps(game.get_state(player_id)))

                    elif message['type'] == 'reset':
                        game.reset()

            except Exception as e:
                print(f"[SRV ERROR] {e}")
                break

        print(f"[SRV] Player {player_id} disconnected")
        try:
            del self.games[game_id]
        except:
            pass
        conn.close()

    def listen_connections(self):
        while True:
            conn, addr = self.sock.accept()
            print(f"[SRV] New connection: {addr}")

            self.id_count += 1
            current_player = 0
            game_id = (self.id_count - 1) // 2

            if self.id_count % 2 == 1:
                self.games[game_id] = Game(game_id)
                print(f"[SRV] New game: {game_id}")
            else:
                self.games[game_id].start = False
                current_player = 1

            start_new_thread(self.client_thread, (conn, current_player, game_id))


class Game:
    def __init__(self, game_id):
        self.game_id = game_id
        self.players = [None, None]
        self.players_ready = 0
        self.start = False
        self.grids = [[[0] * 10 for _ in range(10)],
                      [[0] * 10 for _ in range(10)]]
        self.turn = 0
        self.winner = -1

    def process_shot(self, player, x, y):
        if player != self.turn: return

        opponent = 1 - player
        if self.grids[opponent][y][x] == 1:
            self.grids[opponent][y][x] = 2
            if self.check_win(opponent):
                self.winner = player
            else:
                self.turn = opponent
        else:
            self.grids[opponent][y][x] = 3
            self.turn = opponent

    def check_win(self, opponent):
        return all(cell != 1 for row in self.grids[opponent] for cell in row)

    def get_state(self, player):
        return {
            'grids': self.grids,
            'turn': self.turn,
            'winner': self.winner,
            'player_id': player,
            'start': self.start
        }

    def reset(self):
        self.grids = [[[0] * 10 for _ in range(10)],
                      [[0] * 10 for _ in range(10)]]
        self.turn = 0
        self.winner = -1
        self.players_ready = 0


if __name__ == "__main__":
    srv = Server()
    srv.start()