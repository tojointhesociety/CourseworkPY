import socket
import pickle


class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.data = None
        self.player_id = None
        self.buffer = b""

    def connect(self, server="localhost", port=5555):
        try:
            self.client.connect((server, port))
            # Устанавливаем таймаут для операций с сокетом
            self.client.settimeout(5.0)

            # Получаем начальные данные
            data = self._receive()
            if data and 'player_id' in data:
                self.player_id = data['player_id']
                self.connected = True
                return True
            else:
                print("Неверный ответ сервера:", data)
        except Exception as e:
            print(f"Ошибка подключения: {e}")
        return False

    def _receive(self):
        try:
            data = self.client.recv(4096)
            if data:
                return pickle.loads(data)
        except socket.timeout:
            print("Таймаут приема данных")
        except Exception as e:
            print(f"Ошибка приема данных: {e}")
        return None

    def send(self, data):
        try:
            if not self.connected:
                return None

            # Добавляем player_id в каждое сообщение
            data['player_id'] = self.player_id
            self.client.sendall(pickle.dumps(data))
            return self._receive()
        except Exception as e:
            print(f"Ошибка отправки: {e}")
            return None

    def check_data(self):
        try:
            self.client.settimeout(0.1)  # Короткий таймаут
            data = self.client.recv(4096)
            if data:
                return pickle.loads(data)
        except socket.timeout:
            return None
        except Exception as e:
            print(f"Ошибка проверки данных: {e}")
            return None
        finally:
            self.client.settimeout(5.0)
        return None

    def disconnect(self):
        try:
            self.client.close()
        except:
            pass
        self.connected = False