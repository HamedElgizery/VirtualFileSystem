import cmd
import os
import importlib
import glob
import signal

import cmd
import os
import importlib
import glob
from typing import List

from file_system_api import FileSystemApi
from structs.base_command import BaseCommand
from utility import setup_logger


class ModularShell(cmd.Cmd):
    intro = "Welcome to the Yoyo Shell. Type 'help' or '?' to list commands.\n"
    prompt = "(yoyo) >> "

    def __init__(self, user_id):
        super().__init__()
        self.log_path = f"logs/{user_id}"
        self.user_id = user_id
        self.logger = setup_logger(self.log_path, user_id)
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

            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type)
                    and issubclass(attr, BaseCommand)
                    and attr is not BaseCommand
                ):
                    command_instance = attr()
                    self.add_command(command_instance)

                    self.modules_help[command_instance.name] = (
                        command_instance.description
                    )
                    self.modules[command_instance.name] = command_instance
            # self.modules_help[module_name] = (
            #     module.__doc__.strip()
            #     if module.__doc__
            #     else "No help available for this command."
            # )
            # self.modules[module_name] = module

            # command_func = getattr(module, "execute", None)
            # if command_func:
            #     self.add_command(module_name, command_func)

    def parse_args(self, args: str) -> List[str]:
        args_list = []
        current_arg = ""
        in_quotes = False
        for char in args:
            if char == '"':
                in_quotes = not in_quotes
            elif char == " " and not in_quotes:
                if current_arg:
                    args_list.append(current_arg)
                    current_arg = ""
            else:
                current_arg += char
        if current_arg:
            args_list.append(current_arg)

        return args_list

    def add_command(self, command_instance: BaseCommand):
        def wrapper(args):
            # Pass the FileSystemApi instance to each command
            try:
                command_instance.run(self.parse_args(args), self.file_system_api)
            except Exception as e:
                print(f"An Error Occured: {e}")
            finally:
                ModularShell.prompt = (
                    f"(yoyo) {self.file_system_api.current_directory}>> "
                )
                if self.file_system_api.current_directory == "/":
                    ModularShell.prompt = f"(yoyo) >> "

        setattr(self, f"do_{command_instance.name}", wrapper)

    # def add_command(self, name, func):
    #     def wrapper(args):
    #         # Pass the FileSystemApi instance to each command
    #         try:
    #             func(self.parse_args(args), self.file_system_api)
    #         except Exception as e:
    #             print(f"An Error Occured: {e}")
    #         finally:
    #             ModularShell.prompt = (
    #                 f"(yoyo) {self.file_system_api.current_directory}>> "
    #             )
    #             if self.file_system_api.current_directory == "/":
    #                 ModularShell.prompt = f"(yoyo) >> "

    #     setattr(self, f"do_{name}", wrapper)

    def do_exit(self, arg):
        print("BIBI GO BYEBYE!")
        return True

    def do_help(self, arg):
        if not arg:
            # Default help behavior - list all commands
            commands = [name[3:] for name in dir(self) if name.startswith("do_")]
            commands += self.modules.keys()
            commands = set(commands)
            print("Available commands:")
            for command in commands:
                print(f"  {command}")
        else:
            print(self.modules_help.get(arg, "No help available for this command."))


if __name__ == "__main__":
    ModularShell("waryoyo").cmdloop()
