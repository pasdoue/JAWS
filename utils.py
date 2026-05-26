import logging
import random
import time

from R2Log import logger
from rich.emoji import Emoji
from rich.progress import ProgressColumn
from rich.text import Text


def print_banner() -> None:
    banners = []
    banners.append("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢠⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⡿⠟⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣶⡌⠉⠉⠉⠉⠉⠉⣹⣿⣦⡄
⠀⠀⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡼⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠀⠀⢀⣴⣯⣴⣿⣿⣿⣿⠁
⠀⠀⠸⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣴⣿⣿⣿⣿⣿⣿⡿⠃⠀
⠀⠀⠀⢻⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠞⠛⠋⠉⠙⠛⠻⢿⡟⣿⣿⣿⣿⠻⠁⠀⠀        ██╗ █████╗ ██╗    ██╗███████╗
⠀⠀⠀⠘⣿⣿⣿⣿⣦⠀⠀⠀⠀⠀⡸⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣆⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⢉⣷⣶⣶⣤⣄⢸⡿⠙⠁⠀⠀⠀⠀        ██║██╔══██╗██║    ██║██╔════╝
⠀⠀⠀⠀⣿⣿⣭⣬⣤⣤⣤⣄⣀⣀⣀⣀⣀⣀⢤⠤⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⠎⠀⠀⠀⠀⠀⠀⠀        ██║███████║██║ █╗ ██║███████╗
⠀⠀⠀⣸⣿⣿⣿⣿⠻⠛⠛⠿⡿⣿⣿⣿⣿⣾⣤⣀⣀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣾⣿⣿⣿⣷⣦⣄⣀⣀⣠⣤⣶⣿⣿⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀        ██║██╔══██║██║███╗██║╚════██║
⠀⠀⣴⣿⣿⣿⠻⠈⠀⠀⠀⠀⠀⠈⠉⠛⠟⡿⢿⠿⡛⣘⣤⣤⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀   ╚█████╔╝██║  ██║╚███╔███╔╝███████║
⠀⢠⣿⣿⠻⠈⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣦⣶⣿⣿⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝
⠐⠛⠙⠈⠀⠀⠀⠀⠀⢀⣄⣦⣶⠿⠿⠿⠛⠛⠛⠉⠉⠉⠀⠀⠀⠘⠛⠻⠿⠿⠿⠿⠟⠛⠛⠙⠉⠁⠀⠈⠉⠛⠿⣿⣿⣿⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⠿⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀Made by pasdoue
""")
    banners.append("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣠⣤⣤⠶⠶⠶⠶⠾⠛⠛⠛⠛⠛⠛⠛⢿
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣶⣿⣛⠛⠛⠛⠓⠢⢄⡀⠀⠤⠟⠂⠀⠀⠀⠀⠀⠀⢀⡿        ██╗ █████╗ ██╗    ██╗███████╗
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⠾⠛⠉⠑⠤⣙⢮⡉⠓⣦⣄⡀⠀⣹⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠃        ██║██╔══██╗██║    ██║██╔════╝
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⡶⠞⠋⠉⠀⠀⠀⠀⠀⠀⠒⠛⠛⠛⠉⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⢰⡟⠀        ██║███████║██║ █╗ ██║███████╗
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⠾⠛⠉⣡⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⢺⢿⢉⡽⡟⢓⣶⠦⢤⣀⡀⠈⠳⣿⠁⠀        ██║██╔══██║██║███╗██║╚════██║
⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⠟⠁⠀⠀⣀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠚⠁⠀⢛⠛⠛⠻⢷⡧⣾⡴⣛⣏⣹⡇⣀⣿⠀⠀    █████╔╝██║  ██║╚███╔███╔╝███████║
⠀⠀⠀⠀⠀⠀⣠⠞⠋⠀⣀⠤⠒⢉⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠔⠋⠀⣀⠴⠚⠛⠛⠯⡑⠂⠀⠀⡏⢹⣿⡾⠟⠋⠁⠀⠀    ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝
⠀⠀⠀⠀⣠⠞⠁⠀⠐⠊⠀⠀⢠⡿⠁⠀⢰⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⣤⡿⠋⠀⠀⠀⠀⠀⠀⡹⠀⠀⠀⣠⡾⠋⠀⠀⠀⠀⠀⠀
⠀⠀⣠⡞⠁⠀⠀⠀⠀⠀⠀⢠⡿⠁⢀⢸⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⡞⠋⠉⠉⠓⠒⠢⢤⣴⣥⣆⣠⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Made by pasdoue
⠀⣼⠋⠀⠀⠀⠀⠀⠀⠀⢀⡟⠀⠀⢸⠀⡆⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⢽⣦⠀⠀⠀⠀⠀⠀⣟⡿⣽⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢸⣇⣤⣤⣤⣤⣄⡀⠀⢀⡾⠁⠀⠀⢘⡆⠱⡈⢆⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⢻⡚⡆⣀⠀⠀⠀⢸⡽⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠙⢷⣾⠃⠀⠀⠀⠈⠾⣦⣙⠪⢷⠄⠀⠀⠀⠀⠀⠀⠀⠈⠻⣭⣟⣹⢦⣀⣀⣟⣹⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⠀⣤⠶⠖⠊⠉⠀⠉⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠦⣼⣞⣹⣯⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """)
    logger.info(random.choice(banners))

def set_logger(level: int) -> None:
    logger.setVerbosity(level)
    file_handler = logging.FileHandler("logs.txt")
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler.setLevel(logger.level)
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)

def print_elapsed_time(start_time) -> None:
    end = time.time()
    logger.info(f"Script took : {str(end - start_time)} seconds")


def get_unique_keys(obj, result=None):
    """
        Allow to retrieve all "keys" recursively in a JSON.
        Usefull for guessing parameters that are required
    """
    if result is None:
        result = set()

    if isinstance(obj, dict):
        for k, v in obj.items():
            result.add(k)
            get_unique_keys(v, result)

    elif isinstance(obj, list):
        for item in obj:
            get_unique_keys(item, result)

    return result

def find_parent(obj, target_key, parent=None):
    if isinstance(obj, dict):
        for key, value in obj.items():

            # clé trouvée -> retourner le parent
            if key == target_key:
                return parent

            # continuer récursivement
            result = find_parent(value, target_key, obj)
            if result is not None:
                return result

    elif isinstance(obj, list):
        for item in obj:
            result = find_parent(item, target_key, parent)
            if result is not None:
                return result

    return None


class SharkBarColumn(ProgressColumn):
    def __init__(self, width=30):
        super().__init__()
        self.width = width

    def render(self, task):
        total = task.total or 1
        # swimmer position
        swimmer_pos = int((task.completed / total) * (self.width - 1))
        # shark stays one step behind
        #shark_pos = max(0, swimmer_pos - 1)
        shark_pos = int(swimmer_pos * 0.8)
        bar = []

        for i in range(self.width):
            if i == swimmer_pos:
                bar.append(Emoji.replace(':rowboat:'))
            elif i == shark_pos and swimmer_pos > 0:
                bar.append(Emoji.replace(':shark:'))
            else:
                bar.append(Emoji.replace(':water_wave:'))
        return Text(" ".join(bar))

