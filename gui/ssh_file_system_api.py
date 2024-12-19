import paramiko


class SSHFileSystemApi:
    def __init__(self, host, port, username, password):
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            self.ssh_client.connect(host, port, username, password)
        except Exception as e:
            raise ConnectionError(f"Failed to connect to {host}:{port}. {str(e)}")

    def execute_command(self, command):
        try:
            stdin, stdout, stderr = self.ssh_client.exec_command(command)
            error = stderr.read().decode()
            if error:
                raise Exception(error)
            return stdout.read().decode()
        except Exception as e:
            raise Exception(f"Command execution failed: {str(e)}")

    def list_directory_contents(self, path):
        output = self.execute_command(f"ls {path}")
        return output.strip().split("\n")

    def is_directory(self, path):
        output = self.execute_command(f"is_dir {path}")
        return output.strip() == "True"

    def pwd(self):
        output = self.execute_command(f"pwd")
        return output.strip()

    def get_file_metadata(self, path):
        output = self.execute_command(f"python3 gfs.py {path}")
        details = output.strip().split(",")
        return {
            "file_size": int(details[0]),
            "is_directory": details[1] == "directory",
            "modification_date": details[2],
        }

    def change_directory(self, path):
        self.execute_command(f"cd {path}")

    def close(self):
        self.ssh_client.close()
