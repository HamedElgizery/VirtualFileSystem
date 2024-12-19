import logging
import os
import socket
import sys
import threading

import paramiko

from ssh_cmd_handler import ModularShell
from ssh.account_manager import (
    AccountManager,
)  # Added imports

KEY_PATH = "ssh/rsa_key/server_rsa_key.pem"
logging.basicConfig()
logger = logging.getLogger()


def get_or_create_rsa_key(key_path):
    # Check if the key file already exists
    if os.path.exists(key_path):
        print(f"Key file exists. Loading from {key_path}...")
        key = paramiko.RSAKey(filename=key_path)
    else:
        print(f"Key file not found. Generating a new RSA key at {key_path}...")
        key = paramiko.RSAKey.generate(2048)

        with open(key_path, "w") as key_file:
            key.write_private_key(key_file)
        print("New RSA key successfully generated and saved.")

    return key


get_or_create_rsa_key(KEY_PATH)
host_key = paramiko.RSAKey(filename=KEY_PATH)


class Server(paramiko.ServerInterface):
    def __init__(self, account_manager: AccountManager):
        self.event = threading.Event()
        self.account_manager = account_manager
        self.username = None  # Added to store authenticated user

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED

    def check_auth_password(self, username, password):
        # Authenticate using account_manager
        if username not in self.account_manager.accounts:
            self.account_manager.create_account(username, password)
            print(
                f"Created new account with username '{username}' and password '{password}'."
            )

        if self.account_manager.authenticate_user(username, password):
            print(f"User '{username}' authenticated successfully.")
            self.username = username
            return paramiko.AUTH_SUCCESSFUL
        print(f"Authentication failed for user '{username}'.")
        return paramiko.AUTH_FAILED

    def check_channel_exec_request(self, channel, command):
        # This is the command we need to parse
        print(command)
        self.event.set()
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(self, c, t, w, h, p, ph, m):
        return True


def handle_client(client, addr, host_key, account_manager):
    try:
        t = paramiko.Transport(client)
        t.set_gss_host(socket.getfqdn(""))
        t.load_server_moduli()
        t.add_server_key(host_key)
        server = Server(account_manager)
        t.start_server(server=server)

        channel = t.accept(20)
        if channel is None:
            print(f"[+] No client connection from {addr}.")
            return

        channel.send("[+] Welcome to the SSH Server!\n\r")

        session_output = channel.makefile("wU")
        session_input = channel.makefile("rU")

        if server.username:  # Check if user authenticated
            channel.send(f"[+] Welcome {server.username}!\n\r")

            shell = ModularShell(
                server.username, stdin=session_input, stdout=session_output
            )

            try:
                shell.cmdloop()
            except Exception as e:
                print(f"Error with user {server.username}: {e}")
            finally:
                channel.close()
                t.close()
    except Exception as e:
        print(f"Error handling client {addr}: {e}")
    finally:
        client.close()


def listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 2222))
    sock.listen(100)

    account_manager = AccountManager()

    print("[+] SSH Server listening on port 2222...")
    while True:
        try:
            client, addr = sock.accept()
            print(f"[+] Connection received from {addr}.")

            # Start a new thread for each client
            threading.Thread(
                target=handle_client, args=(client, addr, host_key, account_manager)
            ).start()
        except KeyboardInterrupt:
            print("[+] Shutting down the server.")
            sock.close()
            break
        except Exception as e:
            print(f"Error in listener: {e}")


if __name__ == "__main__":
    import sys
    import logging

    logging.basicConfig(level=logging.INFO)
    host_key = paramiko.RSAKey.generate(
        2048
    )  # Replace with a valid key file for production

    try:
        listener()
    except Exception as e:
        logging.error(f"Unhandled error: {e}")
        sys.exit(1)
