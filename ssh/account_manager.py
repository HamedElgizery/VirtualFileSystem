import os
import hashlib
import json


class AccountManager:
    ACCOUNTS_DIR = "accounts_store"
    ACCOUNTS_FILE = f"ssh/{ACCOUNTS_DIR}/accounts.json"

    def __init__(self):
        self.accounts = self.load_accounts()

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def load_accounts(self):
        if not os.path.exists(self.ACCOUNTS_FILE):
            return {}
        with open(self.ACCOUNTS_FILE, "r") as file:
            return json.load(file)

    def save_accounts(self):
        with open(self.ACCOUNTS_FILE, "w") as file:
            json.dump(self.accounts, file, indent=4)

    def create_account(self, username, password):
        """Create a new account with isolated data storage."""
        if username in self.accounts:
            raise ValueError("Account already exists!")

        # Add the user with a hashed password
        self.accounts[username] = self.hash_password(password)
        self.save_accounts()

        print(f"Account '{username}' created successfully.")

    def authenticate_user(self, username, password):
        """Authenticate a user by checking their credentials."""
        if username not in self.accounts:
            return False

        return self.accounts[username] == self.hash_password(password)

    # Ensure the data directory exists
    def __enter__(self):
        os.makedirs(self.ACCOUNTS_DIR, exist_ok=True)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# if __name__ == "__main__":
#     # For testing purposes: Create an account
#     try:
#         user = input("Enter username: ")
#         pwd = input("Enter password: ")
#         create_account(user, pwd)
#     except Exception as e:
#         print(f"Error: {e}")
