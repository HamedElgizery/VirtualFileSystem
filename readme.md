# Project Overview

This project is a file system management application that provides multiple interfaces for interacting with the file system. It offers a command-line interface, a graphical user interface, and an SSH-based interface. The application supports various file operations like creating, editing, and deleting files, as well as navigating through directories. The system is designed to be user-friendly and flexible, allowing users to choose their preferred method of interaction.

## Features

- **GUI Application**: A graphical interface for managing files and directories with ease.
- **Command Handler**: A shell-like interface for executing file system commands.
- **SSH Server**: A secure way to connect and interact with the file system over a network.

## Instructions to Run

### Running the GUI Application

1. Ensure you have all the dependencies installed. You can do this by running:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the GUI application by executing the following command:
   ```bash
   python gui_app.py
   ```

   This will launch the GUI file explorer where you can connect using your username.

### Running the Command Handler

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the command handler with:
   ```bash
   python cmd_handler.py
   ```

   You will be prompted to enter a user ID. Once entered, you can start executing file system commands in the shell.

### Running the SSH Server

1. Make sure the required packages are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the SSH server by executing:
   ```bash
   python ssh_server.py
   ```

3. Connect to the server using an SSH client (e.g., `ssh` command or PuTTY) with the following details:
   - Host: `localhost` (or the server's IP address if running remotely)
   - Port: `22` (or any other port configured in the server)
   - Username: Your registered username
   - Password: Your account password

   Once connected, you will be able to execute file system commands over the secure SSH connection.
