"""
Echoes a message or writes it to a file.
Usage:
  echo <message>                # Prints the message to the console
  echo <message> > <file_path>  # Writes the message to a file (overwrite)
  echo <message> >> <file_path> # Appends the message to a file
"""

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from file_system_api import FileSystemApi


def execute(args: list, fs: "FileSystemApi"):
    try:
        # Split the argument into components
        if ">>" in args:
            message, file_path = args[-3], args[-1]
            mode = "append"
        elif ">" in args:
            message, file_path = args[-3], args[-1]
            mode = "overwrite"
        else:
            # If no redirection, simply print the message
            print(" ".join(args))
            return

        # Resolve the file path
        resolved_path = fs.resolve_path(file_path)

        # Write or append to the file
        if mode == "overwrite":
            fs.edit_file(resolved_path, message.encode())

        elif mode == "append":
            existing_data = fs.read_file(resolved_path)
            updated_data = existing_data + message.encode()
            fs.edit_file(resolved_path, updated_data)

        print(
            f"Message {'written to' if mode == 'overwrite' else 'appended to'} '{resolved_path}'."
        )

    except Exception as e:
        print(f"Error: {e}")
