# This class is a modified version of the Cmd class in the cmd module
# It has been modified to allow for basic line editing using the arrow keys
# The line editing is quite basic and does not support things like
# deleting characters or moving the cursor to a different position in the line
# It just remembers the last 10 commands and allows you to recall them by pressing the up arrow
# The down arrow will move down the list of previous commands

"""
This module provides a modified version of the Cmd class in the cmd module
It has been modified to allow for basic line editing using the arrow keys
The line editing is quite basic and does not support things like
deleting characters or moving the cursor to a different position in the line
It just remembers the last 10 commands and allows you to recall them by pressing the up arrow
The down arrow will move down the list of previous commands
"""


import sys
from cmd_handler import ModularShell


class SshModularShell(ModularShell):
    """
    This class is a modified version of the Cmd class in the cmd module
    """

    def default(self, line):
        """Prints an error message if the user enters a command that is not recognized"""
        self.printline(f"*** Unknown syntax: {line}")

    def cmdloop(self, intro=None):
        """
        This method is the main loop of the command shell.
        It will keep reading commands from the user
        and executing them until the user enters 'exit'.
        """
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
                if char in ("\r", "\n"):
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
                    if char == "\x1b[B":  # Down arrow
                        if self.cmdqueue:
                            buffer = self.cmdqueue.pop(0)
                            self.print(f"\r{buffer}\r")
                        continue

                    self.stdin.seek(self.stdin.tell() - 2)  # Put that faggot back

                    # Escape
                    continue

                # Add the character and basically just echo it back
                buffer += char
                self.print(char)

        except Exception:
            self.printline(f"Error: {sys.exc_info()[1]}")


if __name__ == "__main__":
    SshModularShell("waryoyo").cmdloop()
