import socket
import threading
import json

from file_system_api import FileSystemApi


class FileSystemServer:
    def __init__(self, host="127.0.0.1", port=65432):
        self.host = host
        self.port = port
        self.clients = {}  # Store FileSystemApi instances by username
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def handle_client(self, client_socket, address):
        try:
            client_socket.send(b"Enter your username: ")
            username = client_socket.recv(1024).decode().strip()
            if username not in self.clients:
                if FileSystemApi.file_system_exists(username):
                    self.clients[username] = FileSystemApi(user_id=username)
                else:
                    self.clients[username] = FileSystemApi.create_new_file_system(
                        username
                    )

            client_socket.send(b"Welcome! Enter commands:\n")

            while True:
                command = client_socket.recv(4096).decode().strip()
                if not command:
                    break

                response = self.process_command(username, command)
                client_socket.send(json.dumps(response).encode())
        except Exception as e:
            print(f"Error handling client {address}: {e}")
        finally:
            client_socket.close()

    def process_command(self, username, command):
        """
        Process commands dynamically from the client.
        Example command payload: {"command": "create_file", "args": ["/test.txt", "Hello"]}
        """
        try:
            user_fs = self.clients[username]
            payload = json.loads(command)

            # Extract command and arguments
            action = payload.get("command")
            args = payload.get("args", [])

            if not action:
                return {"error": "No command specified"}

            # Dynamically call the method
            if hasattr(user_fs, action):
                method = getattr(user_fs, action)
                if callable(method):
                    result = method(*args)
                    return {"status": "success", "result": result}
                else:
                    return {"error": f"{action} is not a callable method"}
            else:
                return {"error": f"Unknown command: {action}"}
        except Exception as e:
            return {"error": str(e)}

    def start(self):
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        print(f"Server listening on {self.host}:{self.port}")

        while True:
            client_socket, address = self.server_socket.accept()
            print(f"Connected by {address}")
            thread = threading.Thread(
                target=self.handle_client, args=(client_socket, address)
            )
            thread.start()


if __name__ == "__main__":
    server = FileSystemServer()
    server.start()
