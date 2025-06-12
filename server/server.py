import socket
import threading
import pickle
import time
import logging
from collections import defaultdict
import random


class GameServer:
    def __init__(self, host='0.0.0.0', port=5555):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((host, port))
        self.server.listen(5)
        self.lock = threading.RLock()

        # Структуры данных
        self.players = {}  # {socket: {'id': int, 'name': str, 'game_id': int}}
        self.waiting_players = []
        self.games = {}  # {game_id: {'players': [socket1, socket2], 'grids': [grid1, grid2], 'turn': int}}
        self.player_counter = 1
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("GameServer")

        print(f"Сервер запущен на {host}:{port}")

    def broadcast_to_game(self, game_id, message, exclude_socket=None):
        """Отправка сообщения всем игрокам в игре"""
        with self.lock:
            game = self.games.get(game_id)
            if not game:
                return

            for player_socket in game['players']:
                if player_socket != exclude_socket:
                    try:
                        player_socket.send(pickle.dumps(message))
                    except:
                        self.remove_player(player_socket)

    def handle_client(self, conn, addr):
        with self.lock:
            player_id = self.player_counter
            self.player_counter += 1
        
        self.logger.info(f"Новое подключение от {addr}, ID: {player_id}")

        try:
            data = self.receive_data(conn)
            if not data or data.get('type') != 'connect':
                self.logger.error("Неверное начальное сообщение")
                return

            player_name = data.get('name', f"Player_{player_id}")

            ack_msg = {
                'type': 'connect_ack',
                'player_id': player_id,
                'status': 'waiting',
                'timestamp': time.time()
            }
            self.send_data(conn, ack_msg)
            self.logger.info(f"Подтверждение отправлено для {player_name}")

            with self.lock:
                self.players[conn] = {
                    'id': player_id,
                    'name': player_name,
                    'addr': addr,
                    'status': 'waiting'
                }

            while True:
                msg = self.receive_data(conn)
                if not msg:
                    break
                self.process_message(conn, msg)

        except Exception as e:
            self.logger.error(f"Ошибка обработки клиента: {str(e)}")
        finally:
            self.remove_player(conn)

    def process_message(self, client_socket, message):
        msg_type = message.get('type')

        if msg_type == 'find_game':
            self.add_to_waiting(client_socket)
            with self.lock:
                if len(self.waiting_players) >= 2:
                    self.create_game()

        elif msg_type == 'place_ships':
            self.handle_placement(client_socket, message)

        elif msg_type == 'shot':
            self.handle_shot(client_socket, message)

        elif msg_type == 'ping':
            self.send_data(client_socket, {'type': 'pong'})

    def add_to_waiting(self, client_socket):
        with self.lock:
            if client_socket in self.waiting_players:
                return

            player_data = self.players[client_socket]
            self.waiting_players.append(client_socket)
            player_data['game_id'] = None  # Сбрасываем игру

            self.logger.info(f"Игрок {player_data['name']} в очереди ожидания")

            self.send_data(client_socket, {
                'type': 'waiting',
                'message': 'Ожидаем второго игрока...'
            })

    def create_game(self):
        with self.lock:
            if len(self.waiting_players) < 2:
                return

            player1 = self.waiting_players.pop(0)
            player2 = self.waiting_players.pop(0)

            game_id = len(self.games) + 1
            self.games[game_id] = {
                'players': [player1, player2],
                'grids': [None, None],  # Пока нет данных о расстановке
                'turn': 0,  # Первым ходит player1
                'ships': [None, None]
            }

            # Обновляем информацию об игроках
            self.players[player1]['game_id'] = game_id
            self.players[player2]['game_id'] = game_id

            self.logger.info(f"Создана игра #{game_id} между {self.players[player1]['name']} и {self.players[player2]['name']}")

            # Уведомляем игроков
            for i, player_socket in enumerate([player1, player2]):
                msg_to_send = {
                    'type': 'game_start',
                    'game_id': game_id,
                    'player_num': i,
                    'opponent_name': self.players[player2 if i == 0 else player1]['name']
                }
                self.logger.info(f"Отправка game_start игроку {self.players[player_socket].get('name')}")
                self.send_data(player_socket, msg_to_send)

    def handle_placement(self, client_socket, message):
        """Обработка расстановки кораблей"""
        with self.lock:
            player_data = self.players.get(client_socket)
            if not player_data or not player_data['game_id']:
                self.logger.warning(f"Данные о расстановке от неизвестного игрока или игрока без игры.")
                return

            game_id = player_data['game_id']
            game = self.games.get(game_id)
            if not game:
                self.logger.warning(f"Получены данные о расстановке для несуществующей игры #{game_id}.")
                return

            player_num = game['players'].index(client_socket)
            game['grids'][player_num] = message.get('grid')
            game['ships'][player_num] = message.get('ships')
            self.logger.info(f"Игрок {player_data['name']} (P{player_num}) прислал расстановку. grids: {[g is not None for g in game['grids']]}")

            # Проверяем готовность обоих игроков
            if all(grid is not None for grid in game['grids']):
                self.logger.info(f"Оба игрока в игре #{game_id} готовы. Начинаем бой!")
                game['turn'] = random.choice([0, 1])

                # Уведомляем игроков
                for i, player_socket_in_game in enumerate(game['players']):
                    self.send_data(player_socket_in_game, {
                        'type': 'battle_start',
                        'your_turn': (i == game['turn'])
                    })
            else:
                self.logger.info(f"Игра #{game_id} ожидает второго игрока.")

    def handle_shot(self, client_socket, message):
        """Обработка выстрела"""
        with self.lock:
            player_data = self.players.get(client_socket)
            if not player_data or not player_data['game_id']:
                return

            game_id = player_data['game_id']
            game = self.games.get(game_id)
            if not game:
                return

            # Проверяем, что это ход этого игрока
            current_player_num = game['players'].index(client_socket)
            if current_player_num != game['turn']:
                self.logger.warning(f"Игрок {player_data['name']} попытался сходить не в свою очередь.")
                return
            
            shooting_player_id = player_data['id']

            x, y = message['x'], message['y']
            opponent_num = 1 - current_player_num
            opponent_socket = game['players'][opponent_num]
            opponent_grid = game['grids'][opponent_num]

            # Проверяем попадание
            hit = opponent_grid[y][x] == 1 if 0 <= x < 10 and 0 <= y < 10 else False
            sunk = False
            game_over = False
            sunk_ship_cells = []

            if hit:
                opponent_grid[y][x] = 2  # Помечаем попадание

                # Проверяем потопление корабля
                sunk, sunk_ship_cells = self.check_ship_sunk(x, y, opponent_grid)
                if sunk:
                    self.logger.info(f"Корабль потоплен в игре #{game_id}")

                # Проверяем конец игры
                game_over = all(cell != 1 for row in opponent_grid for cell in row)
            else:
                opponent_grid[y][x] = 3
                game['turn'] = opponent_num

            # Отправляем результат выстрела обоим игрокам
            for i, player_socket_in_game in enumerate(game['players']):
                self.send_data(player_socket_in_game, {
                    'type': 'shot_result',
                    'player_id': shooting_player_id,
                    'x': x,
                    'y': y,
                    'hit': hit,
                    'sunk': sunk,
                    'sunk_cells': sunk_ship_cells,
                    'your_turn': (i == game['turn']),
                    'game_over': game_over,
                    'winner': shooting_player_id if game_over else None
                })

            if game_over:
                # Завершаем игру
                self.logger.info(f"Игра #{game_id} завершена. Победитель: {player_data['name']}")
                del self.games[game_id]
                for player_socket in game['players']:
                    self.players[player_socket]['game_id'] = None

    def check_ship_sunk(self, x, y, grid):
        """Проверяет, был ли потоплен корабль, и возвращает его клетки."""
        
        # Сначала найдем все связанные клетки с попаданием
        q = [(x, y)]
        visited = set([(x, y)])
        hit_cells = []

        while q:
            cx, cy = q.pop(0)
            hit_cells.append((cx, cy))
            for dx, dy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < 10 and 0 <= ny < 10 and (nx, ny) not in visited and grid[ny][nx] in [1, 2]:
                    visited.add((nx, ny))
                    q.append((nx, ny))
        
        # Теперь проверим, есть ли среди найденных клеток "живые" части
        for cx, cy in visited:
            if grid[cy][cx] == 1:
                return False, [] # Корабль еще не потоплен

        return True, list(visited)

    def remove_player(self, client_socket):
        """Удаление отключившегося игрока"""
        with self.lock:
            if client_socket not in self.players:
                return

            player_data = self.players.pop(client_socket)
            game_id = player_data.get('game_id')

            if client_socket in self.waiting_players:
                self.waiting_players.remove(client_socket)

            if game_id and game_id in self.games:
                game = self.games[game_id]
                other_player = None
                if client_socket in game['players']:
                    game['players'].remove(client_socket)
                    if game['players']:
                        other_player = game['players'][0]

                if other_player:
                    # Уведомляем другого игрока
                    self.send_data(other_player, {
                        'type': 'opponent_left',
                        'message': 'Ваш соперник отключился.'
                    })
                # Удаляем игру, если она осталась пустой
                del self.games[game_id]
                print(f"Игра #{game_id} завершена из-за отключения.")

            try:
                client_socket.close()
            except:
                pass

            print(f"Игрок {player_data.get('name')} отключился.")

    def receive_data(self, client_socket):
        try:
            # Сначала получаем длину сообщения (4 байта)
            data_len_bytes = client_socket.recv(4)
            if not data_len_bytes:
                return None
            data_len = int.from_bytes(data_len_bytes, 'big')

            # Теперь получаем само сообщение
            data = b''
            while len(data) < data_len:
                packet = client_socket.recv(min(data_len - len(data), 4096))
                if not packet:
                    return None
                data += packet
            return pickle.loads(data)
        except (ConnectionResetError, EOFError, BrokenPipeError):
            self.logger.warning("Соединение разорвано клиентом")
            return None
        except Exception as e:
            self.logger.error(f"Ошибка при получении данных: {e}")
            return None

    def send_data(self, client_socket, data):
        try:
            serialized_data = pickle.dumps(data)
            # Сначала отправляем длину сообщения
            len_bytes = len(serialized_data).to_bytes(4, 'big')
            client_socket.sendall(len_bytes + serialized_data)
        except (ConnectionResetError, BrokenPipeError):
            self.logger.warning(f"Не удалось отправить данные: соединение разорвано.")
            self.remove_player(client_socket)
        except Exception as e:
            self.logger.error(f"Ошибка при отправке данных: {e}")
            self.remove_player(client_socket)

    def run(self):
        """Главный игровой цикл"""
        while True:
            try:
                conn, addr = self.server.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                thread.daemon = True
                thread.start()
            except Exception as e:
                self.logger.error(f"Ошибка при принятии соединения: {e}")


if __name__ == "__main__":
    server = GameServer()
    server.run()