def reset_seek_to_zero(func):
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        finally:
            self.fs.seek(0)
            self.fs.flush()

    return wrapper


import logging
import os


def open_file_without_cache(filepath, mode):
    # Convert mode to os flags
    mode_flags = {
        "r": os.O_RDONLY,
        "w": os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        "a": os.O_WRONLY | os.O_CREAT | os.O_APPEND,
        "r+": os.O_RDWR,
        "w+": os.O_RDWR | os.O_CREAT | os.O_TRUNC,
        "a+": os.O_RDWR | os.O_CREAT | os.O_APPEND,
        "r+b": os.O_RDWR,  # Binary read/write
        "w+b": os.O_RDWR | os.O_CREAT | os.O_TRUNC,
        "a+b": os.O_RDWR | os.O_CREAT | os.O_APPEND,
    }
    if mode not in mode_flags:
        raise ValueError(f"Unsupported mode: {mode}")

    flags = mode_flags[mode]

    if os.name == "nt":
        flags |= os.O_BINARY
    else:
        flags |= os.O_SYNC

    fd = os.open(filepath, flags)

    return os.fdopen(fd, mode, buffering=0)


def setup_logger(log_path: str, user_id: str):
    os.makedirs(log_path, exist_ok=True)
    log_file = os.path.join(log_path, "filesystem.log")

    logger = logging.getLogger(user_id)
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    if not logger.hasHandlers():
        logger.addHandler(file_handler)

    return logger
