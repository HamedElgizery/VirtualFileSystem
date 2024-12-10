class TransactionManager:
    def __init__(self):
        self.operations = []
        self.active_transaction = False

    def add_operation(
        self, func, rollback_func=None, func_args=None, rollback_args=None
    ):
        """
        Add an operation with its rollback function and arguments.

        :param func: Callable function for the main operation.
        :param rollback_func: Callable function for rolling back the operation.
        :param func_args: Arguments for the main operation as a tuple.
        :param rollback_args: Arguments for the rollback operation as a tuple.
        """
        self.operations.append(
            {
                "func": func,
                "func_args": func_args or (),
                "rollback": rollback_func,
                "rollback_args": rollback_args or (),
            }
        )

    def commit(self):

        if self.active_transaction:
            # If already inside a transaction, skip committing
            return

        self.active_transaction = True
        executed_operations = []
        try:
            for operation in self.operations:
                # Execute the operation
                operation["func"](*operation["func_args"])
                executed_operations.append(operation)
        except Exception as e:
            self.rollback(executed_operations)
            raise e  # Re-raise the exception
        finally:
            self.operations.clear()
            self.active_transaction = False

    def rollback(self, executed_operations):

        for operation in reversed(executed_operations):
            rollback_func = operation["rollback"]
            rollback_args = operation["rollback_args"]
            if rollback_func:
                rollback_func(*rollback_args)
