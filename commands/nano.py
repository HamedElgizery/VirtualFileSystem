import sys
from cmd import Cmd

from structs.base_command import BaseCommand


class NanoEditor(Cmd):
    def __init__(self, file_system_api, file_path):
        super().__init__()
        self.file_system_api = file_system_api
        self.file_path = file_path
        self.data = self.file_system_api.read_file(file_path).decode().splitlines()
        self.current_line = 0
        self.prompt = f"{file_path}> "
        self.intro = "".join(
            f"{idx + 1}: {line}\n" for idx, line in enumerate(self.data)
        )

    def display_file(self):
        print("\n".join(f"{idx + 1}: {line}" for idx, line in enumerate(self.data)))

    def do_show(self, arg):
        self.display_file()

    def do_edit(self, arg):
        try:
            args = arg.split(" ", 1)
            line_number = int(args[0]) - 1
            new_content = args[1] if len(args) > 1 else ""

            if 0 <= line_number < len(self.data):
                self.data[line_number] = new_content
                print(f"Line {line_number + 1} updated.")
            else:
                print("Invalid line number.")
        except ValueError:
            print("Invalid arguments. Usage: edit <line_number> <new_content>")

    def do_insert(self, arg):
        try:
            args = arg.split(" ", 1)
            line_number = int(args[0]) - 1
            content = args[1] if len(args) > 1 else ""

            if 0 <= line_number <= len(self.data):
                self.data.insert(line_number, content)
                print(f"Line inserted at {line_number + 1}.")
            else:
                print("Invalid line number.")
        except ValueError:
            print("Invalid arguments. Usage: insert <line_number> <content>")

    def do_delete(self, arg):
        try:
            line_number = int(arg) - 1

            if 0 <= line_number < len(self.data):
                self.data.pop(line_number)
                print(f"Line {line_number + 1} deleted.")
            else:
                print("Invalid line number.")
        except ValueError:
            print("Invalid arguments. Usage: delete <line_number>")

    def do_search(self, arg):
        keyword = arg.strip()
        if keyword:
            results = [
                f"{idx + 1}: {line}"
                for idx, line in enumerate(self.data)
                if keyword in line
            ]
            if results:
                print("\n".join(results))
            else:
                print(f"No matches found for '{keyword}'.")
        else:
            print("Please provide a keyword to search.")

    def do_save(self, arg):
        self.file_system_api.edit_file(self.file_path, "\n".join(self.data).encode())
        print("File saved successfully.")

    def do_exit(self, arg):
        return "exited successfully"

    def default(self, line):
        """Appends a new line to the end of the file if input doesn't match any command."""
        self.data.append(line)
        print(f"Line added: {line}")

    def postloop(self):
        sys.stdout.write("\n")
        sys.stdout.flush()


class NanoCommand(BaseCommand):
    name = "nano"
    description = "Opens a file in a simple text editor allowing you to make changes and save the file."
    arguments = [{"name": "file_path", "optional": False}]

    def execute(self, args, fs):
        editor = NanoEditor(fs, args[0])
        editor.cmdloop()
        return "exited successfully"
