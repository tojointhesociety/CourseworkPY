import socket
import pickle
import time
import logging
import threading
import queue

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(5)
        self.connected = False
        self.player_id = None
        self.game_id = None
        self.player_name = ""
        self.server_ip = ""
        self.server_port = 0
        self.last_pong = time.time()
        self.logger = logging.getLogger("Network")
        self.logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(handler)
        self.incoming_queue = queue.Queue()
        self.receive_thread = None

    def connect(self, server_ip, server_port, player_name):
        try:
            self.logger.debug(f"Попытка подключения к {server_ip}:{server_port}")
            start_time = time.time()

            self.client.connect((server_ip, server_port))
            self.logger.debug(f"TCP-соединение установлено за {time.time() - start_time:.3f} сек")

            # Отправка данных игрока
            connect_msg = {
                'type': 'connect',
                'name': player_name,
                'timestamp': time.time()
            }
            self.send_data(connect_msg)
            self.logger.debug("Отправлено сообщение подключения")

            # Получение ответа
            response = self.receive_data()
            self.logger.debug(f"Получен ответ: {response}")

            if not response:
                self.logger.error("Пустой ответ от сервера")
                return False

            if response.get('type') != 'connect_ack':
                self.logger.error(f"Неверный тип ответа: {response.get('type')}")
                return False

            self.player_id = response.get('player_id')
            if not self.player_id:
                self.logger.error("Не получен player_id")
                return False

            self.connected = True
            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()
            self.logger.info(f"Успешное подключение. ID: {self.player_id}. Поток получения запущен.")
            return True

        except socket.timeout:
            self.logger.error("Таймаут подключения")
        except ConnectionRefusedError:
            self.logger.error("Сервер отверг подключение")
        except Exception as e:
            self.logger.error(f"Ошибка подключения: {str(e)}")
        return False

    def send_data(self, data):
        try:
            serialized_data = pickle.dumps(data)
            len_bytes = len(serialized_data).to_bytes(4, 'big')
            self.client.sendall(len_bytes + serialized_data)
        except socket.error as e:
            self.logger.error(f"Ошибка отправки: {str(e)}")
            self.connected = False

    def receive_data(self):
        try:
            data_len_bytes = self.client.recv(4)
            if not data_len_bytes:
                self.logger.warning("Соединение закрыто сервером (длина)")
                self.connected = False
                return None
            
            data_len = int.from_bytes(data_len_bytes, 'big')
            
            data = b''
            while len(data) < data_len:
                packet = self.client.recv(min(data_len - len(data), 4096))
                if not packet:
                    self.logger.warning("Соединение закрыто сервером (данные)")
                    self.connected = False
                    return None
                data += packet
                
            return pickle.loads(data)
        except socket.timeout:
            return "timeout"
        except (EOFError, ConnectionResetError, BrokenPipeError):
            self.logger.error("Соединение с сервером потеряно")
            self.connected = False
            return None
        except Exception as e:
            self.logger.error(f"Ошибка получения: {str(e)}")
            self.connected = False
            return None

    def _receive_loop(self):
        while self.connected:
            try:
                message = self.receive_data()
                if message == "timeout":
                    continue
                
                if message:
                    self.incoming_queue.put(message)
                else:
                    if self.connected:
                        self.logger.error("Соединение разорвано сервером.")
                        self.disconnect()
                    break
            except Exception as e:
                if self.connected:
                    self.logger.error(f"Критическая ошибка в потоке получения: {e}")
                    self.disconnect()
                break

    def get_message(self):
        if not self.incoming_queue.empty():
            return self.incoming_queue.get()
        return None

    def _ping_loop(self):
        """Периодическая отправка ping сообщений"""
        while self.connected:
            try:
                self.send_data({'type': 'ping'})
                self.last_pong = time.time()
                time.sleep(2)  # Ping каждые 2 секунды

                # Проверяем таймаут
                if time.time() - self.last_pong > 6:
                    print("Таймаут соединения (нет ответа от сервера)")
                    self.connected = False
            except:
                self.connected = False
                break

    def disconnect(self):
        if not self.connected:
            return
        self.connected = False
        try:
            self.send_data({'type': 'disconnect'})
        except Exception:
            pass # Игнорируем ошибки при отправке, т.к. уже отключаемся
        try:
            self.client.close()
        except Exception:
            pass
        self.logger.info("Отключено от сервера")