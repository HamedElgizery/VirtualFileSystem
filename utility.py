def reset_seek_to_zero(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        finally:
            self.fs.seek(0)
            self.fs.flush()

    return wrapper
