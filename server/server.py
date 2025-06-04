import socket
import threading
import pickle
import traceback


class Server:
    def __init__(self, host='localhost', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen()
        self.players = {}
        self.games = {}
        self.player_count = 0
        print(f"Сервер запущен на {host}:{port}")

    def handle_client(self, conn, addr):
        print(f"Новое подключение: {addr}")
        player_id = self.player_count
        self.player_count += 1

        try:
            init_data = {"player_id": player_id}
            conn.sendall(pickle.dumps(init_data))
            print(f"Отправлено игроку {player_id}: {init_data}")

            self.players[player_id] = {
                "conn": conn,
                "addr": addr,
                "status": "waiting",
                "ready": False
            }

            if len(self.players) % 2 == 0:
                game_id = len(self.games)
                players_in_game = [player_id - 1, player_id]
                self.games[game_id] = {
                    "players": players_in_game,
                    "status": "placement",
                    "ready": 0
                }

                for pid in players_in_game:
                    self.players[pid]["status"] = "placement"
                    self.players[pid]["game_id"] = game_id
                    start_msg = {
                        "status": "start_placement",
                        "message": "Оба игрока подключены! Расставьте корабли."
                    }
                    self.players[pid]["conn"].sendall(pickle.dumps(start_msg))
                print(f"Создана игра #{game_id} для игроков {players_in_game}")

            while True:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break

                    message = pickle.loads(data)
                    print(f"Получено от {player_id}: {message}")

                    if message.get('type') == 'ready':
                        game_id = self.players[player_id]["game_id"]
                        self.games[game_id]["ready"] += 1
                        self.players[player_id]["ready"] = True

                        if self.games[game_id]["ready"] == 2:
                            self.games[game_id]["status"] = "battle"
                            self.games[game_id]["turn"] = 0

                            for i, pid in enumerate(self.games[game_id]["players"]):
                                battle_msg = {
                                    "status": "battle",
                                    "message": "Игра начинается!",
                                    "turn": i
                                }
                                self.players[pid]["conn"].sendall(pickle.dumps(battle_msg))
                            print(f"Игра #{game_id} началась")

                    elif message.get('type') == 'shot':
                        game_id = self.players[player_id]["game_id"]
                        opponent_id = next(
                            p for p in self.games[game_id]["players"]
                            if p != player_id
                        )

                        shot_msg = {
                            "type": "shot_result",
                            "x": message["x"],
                            "y": message["y"],
                            "player_id": player_id
                        }
                        self.players[opponent_id]["conn"].sendall(pickle.dumps(shot_msg))

                except Exception as e:
                    print(f"Ошибка обработки данных: {str(e)}")
                    traceback.print_exc()
                    break

        except Exception as e:
            print(f"Ошибка в основном цикле клиента: {str(e)}")
            traceback.print_exc()
        finally:
            print(f"Отключение: {addr}")
            try:
                conn.close()
            except:
                pass
            if player_id in self.players:
                del self.players[player_id]

    def run(self):
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_client, args=(conn, addr))
            thread.daemon = True
            thread.start()


if __name__ == "__main__":
    server = Server()
    server.run()