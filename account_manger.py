import os
import hashlib
import json

ACCOUNTS_FILE = "accounts.json"
DATA_DIR = "user_data"


def hash_password(password):
  
    return hashlib.sha256(password.encode()).hexdigest()


def load_accounts():
   
    if not os.path.exists(ACCOUNTS_FILE):
        return {}
    with open(ACCOUNTS_FILE, "r") as file:
        return json.load(file)


def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as file:
        json.dump(accounts, file, indent=4)


def create_account(username, password):
    """Create a new account with isolated data storage."""
    accounts = load_accounts()

    if username in accounts:
        raise ValueError("Account already exists!")

    # Add the user with a hashed password
    accounts[username] = hash_password(password)
    save_accounts(accounts)

    # Create a directory for the user's data
    user_data_path = os.path.join(DATA_DIR, username)
    os.makedirs(user_data_path, exist_ok=True)

    print(f"Account '{username}' created successfully. Data stored in '{user_data_path}'.")


def authenticate_user(username, password):
    """Authenticate a user by checking their credentials."""
    accounts = load_accounts()

    if username not in accounts:
        return False

    return accounts[username] == hash_password(password)


def get_user_data_path(username):
    """Return the path to the user's data directory."""
    return os.path.join(DATA_DIR, username)


# Ensure the data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

if __name__ == "__main__":
    # For testing purposes: Create an account
    try:
        user = input("Enter username: ")
        pwd = input("Enter password: ")
        create_account(user, pwd)
    except Exception as e:
        print(f"Error: {e}")
