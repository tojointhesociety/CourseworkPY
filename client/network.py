import socket
import pickle

class Network:
    def __init__(self):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server = "127.0.0.1"
        self.port = 5555
        self.addr = (self.server, self.port)
        self.player_id = None
        self.connect()

    def connect(self):
        try:
            self.client.connect(self.addr)
            self.player_id = int(self.client.recv(2048).decode())
            return True
        except Exception as e:
            print(f"[CONN ERROR] {e}")
            return False

    def send(self, data):
        try:
            self.client.send(pickle.dumps(data))
            response = self.client.recv(4096)
            return pickle.loads(response)
        except Exception as e:
            print(f"[SEND ERROR] {e}")
            return None

    def get_game_state(self):
        return self.send({"type": "get_state"})

    def send_shot(self, x, y):
        return self.send({
            "type": "shot",
            "coords": (x, y),
            "player": self.player_id
        })

    def ready(self):
        return self.send({"type": "ready"})

    def disconnect(self):
        self.client.close()