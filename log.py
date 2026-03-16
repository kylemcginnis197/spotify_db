import logging

fmt = logging.Formatter("[%(name)s] %(message)s")
file_fmt = logging.Formatter("%(asctime)s [%(name)s] %(message)s", "%H:%M:%S")

file_handler = logging.FileHandler("data/history.log", mode="a")
file_handler.setFormatter(file_fmt)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(fmt)

root = logging.getLogger()
root.setLevel(logging.WARNING)
root.addHandler(file_handler)
root.addHandler(stream_handler)

logging.getLogger("music_db").setLevel(logging.INFO)

logger = logging.getLogger("music_db")