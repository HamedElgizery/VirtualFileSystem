# TODO : make sure to add doc string to all classe and methods throughout the project

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
                char = self.stdin.read(1).decode("utf-8")
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
                if char in ("\x08", "\x7f"):
                    if buffer:
                        buffer = buffer[:-1]
                        self.print("\b \b")
                    continue

                # Handle up and down arrow keys

                if char == "\x1b":
                    try:
                        next_char = self.stdin.read(2).decode("utf-8")
                    except:
                        continue

                    char += next_char
                    if char == "\x1b[A":  # Up arrow
                        if self.cmdqueue:
                            buffer = self.cmdqueue.pop(0)
                            self.print(f"\r{buffer}\r")
                        continue
                    elif char == "\x1b[B":  # Down arrow
                        if self.cmdqueue:
                            buffer = self.cmdqueue.pop(0)
                            self.print(f"\r{buffer}\r")
                        continue

                    else:
                        self.stdin.seek(self.stdin.tell() - 2)  # Put that faggot back

                    # Escape
                    continue

                # Add the character and basically just echo it back
                buffer += char
                self.print(char)

        except Exception as e:
            self.printline(f"Error: {e}")


if __name__ == "__main__":
    ModularShell("waryoyo").cmdloop()
