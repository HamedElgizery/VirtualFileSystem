"""
This module provides a modified version of the Cmd class in the cmd module meant for ssh
"""

import sys
from cmd_handler import ModularShell


class SshModularShell(ModularShell):
    """
    This class is a modified version of the Cmd class in the cmd module
    """

    def default(self, line) -> None:
        """Prints an error message if the user enters a command that is not recognized"""
        self.printline(f"*** Unknown syntax: {line}")

    def cmdloop(self, intro=None) -> None:
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

                if char in ("\r", "\n"):
                    self.print("\r\n")
                    if buffer.strip():
                        if self.onecmd(buffer.strip()):
                            break
                    buffer = ""
                    self.print(self.prompt)
                    continue

                # Handle Backspace
                if char in ("\x08", "\x7f"):
                    if buffer:
                        buffer = buffer[:-1]
                        self.print("\b \b")
                    continue

                if char == "\x1b":
                    try:
                        next_char = self.stdin.read(2).decode("utf-8")
                    except:
                        continue

                    char += next_char
                    if char == "\x1b[A":
                        if self.cmdqueue:
                            buffer = self.cmdqueue.pop(0)
                            self.print(f"\r{buffer}\r")
                        continue
                    if char == "\x1b[B":
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
    # for testing
    SshModularShell("waryoyo").cmdloop()
