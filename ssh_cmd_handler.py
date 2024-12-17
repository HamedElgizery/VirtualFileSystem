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
import uuid

from file_system_api import FileSystemApi
from structs.base_command import BaseCommand
from utility import setup_logger
from cmd_handler import ModularShell


class ModularShell(ModularShell):

    def default(self, line):
        self.printline(f"*** Unknown syntax: {line}")

    def cmdloop(self, intro=None):
        self.intro = intro or self.intro
        self.printline(self.intro)
        buffer = ""  # Buffer to store user input

        try:
            # Set up the prompt
            self.print(self.prompt)

            while True:
                char = self.stdin.read(1).decode(
                    "utf-8"
                )  # Read one character from the channel
                if not char:  # End of input
                    break

                # Handle Enter key
                if char == "\r" or char == "\n":
                    self.print("\r\n")  # Echo newline
                    if buffer.strip():  # Execute command if not empty
                        if self.onecmd(buffer.strip()):  # Exit the shell on 'exit'
                            break
                    buffer = ""  # Reset buffer
                    self.print(self.prompt)  # Reprint the prompt
                    continue

                # Handle Backspace
                if char in ("\x08", "\x7f"):  # Backspace or delete character
                    if buffer:  # If there's something to delete
                        buffer = buffer[:-1]  # Remove the last character
                        self.print("\b \b")  # Move cursor back, clear char
                    continue

                # Add character to buffer and echo it
                buffer += char
                self.print(char)  # Echo back the typed character

        except Exception as e:
            self.printline(f"Error: {e}")


if __name__ == "__main__":
    ModularShell("waryoyo").cmdloop()
