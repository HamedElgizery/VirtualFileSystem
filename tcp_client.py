import socket
import json


class FileSystemClient:
    def __init__(self, host: str, port: int, username: str):
        self.host = host
        self.port = port
        self.username = username
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.current_directory = "/"
        self.connect()

    def connect(self):
        """Connects to the server and authenticates the user."""
        self.socket.connect((self.host, self.port))
        self.socket.sendall(self.username.encode())
        response = self.socket.recv(1024).decode()
        if "Welcome" not in response:
            raise ConnectionError("Failed to connect to the server.")
        print(response)

    def send_command(self, command: str, *args):
        """Sends a command to the server and retrieves the response."""
        payload = {"command": command, "args": args}
        self.socket.sendall(json.dumps(payload).encode())
        response = self.socket.recv(4096).decode()
        return json.loads(response)

    def create_file(self, file_path: str, file_data: bytes):
        """Creates a file on the server."""
        return self.send_command("create_file", file_path, file_data.decode())

    def list_directory_contents(self, dir_path: str):
        """Lists the contents of a directory."""
        return self.send_command("list_directory_contents", dir_path)

    def change_directory(self, dir_path: str):
        """Changes the current directory."""
        response = self.send_command("change_directory", dir_path)
        self.current_directory = response.get("current_directory", "/")
        return response

    def get_file_metadata(self, file_path: str):
        """Gets metadata for a file."""
        return self.send_command("get_file_metadata", file_path)

    def delete_file(self, file_path: str):
        """Deletes a file."""
        return self.send_command("delete_file", file_path)

    def create_directory(self, dir_path: str):
        """Creates a directory."""
        return self.send_command("create_directory", dir_path)

    def is_directory(self, file_path: str):
        """Checks if a file is a directory."""
        return self.send_command("is_directory", file_path)

    def copy_directory(self, dir_path: str, copy_path: str):
        """Copies a directory."""
        return self.send_command("copy_directory", dir_path, copy_path)

    def copy_file(self, file_path: str, copy_path: str):
        """Copies a file."""
        return self.send_command("copy_file", file_path, copy_path)

    def move_directory(self, dir_path: str, new_path: str):
        """Moves a directory."""
        return self.send_command("move_directory", dir_path, new_path)

    def move_file(self, file_path: str, new_path: str):
        """Moves a file."""
        return self.send_command("move_file", file_path, new_path)

    def read_file(self, file_path: str):
        """Reads a file."""
        return self.send_command("read_file", file_path)

    def resolve_path(self, path: str):
        return self.send_command("resolve_path", path)

    def get_current_directory(self):
        return self.send_command("current_directory")

    def delete_file(self, file_path: str):
        return self.send_command("delete_file", file_path)

    def delete_directory(self, dir_path: str):
        return self.send_command("delete_directory", dir_path)

    def normalize_path(self, path: str):
        return self.send_command("normalize_path", path)

    def edit_file(self, file_path: bytes, new_data: bytes):
        return self.send_command("edit_file", file_path, new_data)

    def disconnect(self):
        """Disconnects from the server."""
        self.socket.sendall(b"exit")
        self.socket.close()
