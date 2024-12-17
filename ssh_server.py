import logging
import os
import socket
import sys
import threading

import paramiko

from ssh_cmd_handler import ModularShell

KEY_PATH = "server_rsa_key.pem"
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
    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED

    def check_auth_password(self, username, password):
        return paramiko.AUTH_SUCCESSFUL

    def check_channel_exec_request(self, channel, command):
        # This is the command we need to parse
        print(command)
        self.event.set()
        return True

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(self, c, t, w, h, p, ph, m):
        return True


def listener():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", 2222))

    sock.listen(100)
    client, addr = sock.accept()

    t = paramiko.Transport(client)
    t.set_gss_host(socket.getfqdn(""))
    t.load_server_moduli()
    t.add_server_key(host_key)
    server = Server()
    t.start_server(server=server)

    channel = t.accept(20)
    if channel is None:
        print("[+] *****************  no one come :(( ***************** ")
        exit(1)
    channel.send("[+]*****************  YAHALLO ***************** \n\r")

    # Wait 30 seconds for a command
    session_output = channel.makefile("wU")
    session_input = channel.makefile("rU")

    shell = ModularShell("waryoyo", stdin=session_input, stdout=session_output)

    try:
        shell.cmdloop()
    except Exception as e:
        print(f"Error with user waryoyo: {e}")
    finally:
        channel.close()
        t.close()

    t.close()


while True:
    try:
        listener()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as exc:
        logger.error(exc)
