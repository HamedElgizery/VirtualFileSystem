import cmd
import os
import importlib
import glob
import signal

import cmd
import os
import importlib
import glob

from file_system_api import FileSystemApi


class ModularShell(cmd.Cmd):
    intro = "Welcome to the Yoyo Shell. Type 'help' or '?' to list commands.\n"
    prompt = "(yoyo) >> "

    def __init__(self, user_id):
        super().__init__()
        self.modules = {}
        self.modules_help = {}

        self.load_file_system(user_id)
        self.load_commands()

    def load_file_system(self, name: str):
        if os.path.exists("file_system_disk/{name}.disk"):
            self.file_system_api = FileSystemApi(name)
        else:
            self.file_system_api = FileSystemApi.create_new_file_system(name)

    def load_commands(self):
        command_files = glob.glob("commands/*.py")
        for file in command_files:
            module_name = os.path.splitext(os.path.basename(file))[0]
            if module_name == "__init__":
                continue

            module = importlib.import_module(f"commands.{module_name}")
            self.modules_help[module_name] = (
                module.__doc__.strip()
                if module.__doc__
                else "No help available for this command."
            )
            self.modules[module_name] = module

            command_func = getattr(module, "execute", None)
            if command_func:
                self.add_command(module_name, command_func)

    def add_command(self, name, func):
        def wrapper(args):
            # Pass the FileSystemApi instance to each command
            func(args.split(" "), self.file_system_api)

        setattr(self, f"do_{name}", wrapper)

        def help_wrapper():
            print(self.modules_help.get(name, "No help available for this command."))

        setattr(self, f"help_{name}", help_wrapper)

    def do_exit(self, arg):
        print("BIBI GO BYEBYE!")
        return True


if __name__ == "__main__":
    ModularShell("waryoyo").cmdloop()
