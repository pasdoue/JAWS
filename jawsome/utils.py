import logging
import random
import sys
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List

from R2Log import logger
from rich.emoji import Emoji
from rich.progress import ProgressColumn
from rich.text import Text


def print_banner() -> None:
    banners = {"ansi": [], "raw": []}
    banners_fldr = Path(__file__).parent / "assets"
    for file in banners_fldr.rglob("*.ansi"):
        content = file.read_text(encoding="utf-8")
        content += "                                                                                  [38;2;72;180;220mMade by pasdoue[0m\n\n"
        banners["ansi"].append(content)
    banners["raw"].append("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⢠⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣿⣿⡿⠟⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣶⡌⠉⠉⠉⠉⠉⠉⣹⣿⣦⡄
⠀⠀⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡼⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠛⠀⠀⢀⣴⣯⣴⣿⣿⣿⣿⠁
⠀⠀⠸⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣴⣿⣿⣿⣿⣿⣿⡿⠃⠀
⠀⠀⠀⢻⣿⣿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠞⠛⠋⠉⠙⠛⠻⢿⡟⣿⣿⣿⣿⠻⠁⠀⠀        ██╗ █████╗ ██╗    ██╗███████╗ ██████╗ ███╗   ███╗███████╗
⠀⠀⠀⠘⣿⣿⣿⣿⣦⠀⠀⠀⠀⠀⡸⠷⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣆⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⢉⣷⣶⣶⣤⣄⢸⡿⠙⠁⠀⠀⠀⠀        ██║██╔══██╗██║    ██║██╔════╝██╔═══██╗████╗ ████║██╔════╝
⠀⠀⠀⠀⣿⣿⣭⣬⣤⣤⣤⣄⣀⣀⣀⣀⣀⣀⢤⠤⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⠎⠀⠀⠀⠀⠀⠀⠀        ██║███████║██║ █╗ ██║███████╗██║   ██║██╔████╔██║█████╗
⠀⠀⠀⣸⣿⣿⣿⣿⠻⠛⠛⠿⡿⣿⣿⣿⣿⣾⣤⣀⣀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣾⣿⣿⣿⣷⣦⣄⣀⣀⣠⣤⣶⣿⣿⣿⣿⣿⡿⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀        ██║██╔══██║██║███╗██║╚════██║██║   ██║██║╚██╔╝██║██╔══╝
⠀⠀⣴⣿⣿⣿⠻⠈⠀⠀⠀⠀⠀⠈⠉⠛⠟⡿⢿⠿⡛⣘⣤⣤⣶⣶⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    █████╔╝██║  ██║╚███╔███╔╝███████║╚██████╔╝██║ ╚═╝ ██║███████╗
⠀⢠⣿⣿⠻⠈⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣦⣶⣿⣿⣿⣿⣿⡿⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀    ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
⠐⠛⠙⠈⠀⠀⠀⠀⠀⢀⣄⣦⣶⠿⠿⠿⠛⠛⠛⠉⠉⠉⠀⠀⠀⠘⠛⠻⠿⠿⠿⠿⠟⠛⠛⠙⠉⠁⠀⠈⠉⠛⠿⣿⣿⣿⣷⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⠿⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀Made by pasdoue
""")
    banners["raw"].append("""
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣠⣤⣤⠶⠶⠶⠶⠾⠛⠛⠛⠛⠛⠛⠛⢿
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣶⣿⣛⠛⠛⠛⠓⠢⢄⡀⠀⠤⠟⠂⠀⠀⠀⠀⠀⠀⢀⡿         ██╗ █████╗ ██╗    ██╗███████╗ ██████╗ ███╗   ███╗███████╗
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⠾⠛⠉⠑⠤⣙⢮⡉⠓⣦⣄⡀⠀⣹⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠃         ██║██╔══██╗██║    ██║██╔════╝██╔═══██╗████╗ ████║██╔════╝
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⣤⣤⡶⠞⠋⠉⠀⠀⠀⠀⠀⠀⠒⠛⠛⠛⠉⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⢀⡀⠀⢰⡟⠀         ██║███████║██║ █╗ ██║███████╗██║   ██║██╔████╔██║█████╗
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⠾⠛⠉⣡⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣴⢺⢿⢉⡽⡟⢓⣶⠦⢤⣀⡀⠈⠳⣿⠁⠀         ██║██╔══██║██║███╗██║╚════██║██║   ██║██║╚██╔╝██║██╔══╝
⠀⠀⠀⠀⠀⠀⠀⠀⣀⡴⠟⠁⠀⠀⣀⣴⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡤⠚⠁⠀⢛⠛⠛⠻⢷⡧⣾⡴⣛⣏⣹⡇⣀⣿⠀⠀     █████╔╝██║  ██║╚███╔███╔╝███████║╚██████╔╝██║ ╚═╝ ██║███████╗
⠀⠀⠀⠀⠀⠀⣠⠞⠋⠀⣀⠤⠒⢉⡿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠔⠋⠀⣀⠴⠚⠛⠛⠯⡑⠂⠀⠀⡏⢹⣿⡾⠟⠋⠁⠀⠀     ╚════╝ ╚═╝  ╚═╝ ╚══╝╚══╝ ╚══════╝ ╚═════╝ ╚═╝     ╚═╝╚══════╝
⠀⠀⠀⠀⣠⠞⠁⠀⠐⠊⠀⠀⢠⡿⠁⠀⢰⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡏⣤⡿⠋⠀⠀⠀⠀⠀⠀⡹⠀⠀⠀⣠⡾⠋⠀⠀⠀⠀⠀⠀
⠀⠀⣠⡞⠁⠀⠀⠀⠀⠀⠀⢠⡿⠁⢀⢸⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⡞⠋⠉⠉⠓⠒⠢⢤⣴⣥⣆⣠⡾⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀Made by pasdoue
⠀⣼⠋⠀⠀⠀⠀⠀⠀⠀⢀⡟⠀⠀⢸⠀⡆⢧⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⢽⣦⠀⠀⠀⠀⠀⠀⣟⡿⣽⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢸⣇⣤⣤⣤⣤⣄⡀⠀⢀⡾⠁⠀⠀⢘⡆⠱⡈⢆⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⢻⡚⡆⣀⠀⠀⠀⢸⡽⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠙⢷⣾⠃⠀⠀⠀⠈⠾⣦⣙⠪⢷⠄⠀⠀⠀⠀⠀⠀⠀⠈⠻⣭⣟⣹⢦⣀⣀⣟⣹⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⠀⠀⣤⠶⠖⠊⠉⠀⠉⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠦⣼⣞⣹⣯⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
    """)
    category, values = random.choice(list(banners.items()))
    random_choice = values[0] if len(values) == 1 else random.choice(values) # because random.choice() does not works on single elem.. generate Traceback
    if category == "raw":
        logger.info(random_choice)
    else:
        sys.stdout.write(random_choice)

def set_logger(level: int, logfile: bool = False) -> None:
    logger.setVerbosity(level)

    if logfile:
        log_file = Path.cwd() / "logs.txt"
        file_handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=5 * 1024 * 1024,  # 5 Mo
            backupCount=3,
            encoding="utf-8",
        )
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setLevel(logger.level)
        file_handler.setFormatter(formatter)
        # Add the file handler to the logger
        logger.addHandler(file_handler)

def print_elapsed_time(start_time) -> None:
    end = time.time()
    logger.info(f"Script took : {str(end - start_time)} seconds")


def get_unique_keys(obj, result=None) -> set:
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
            # key found -> return the parent
            if key == target_key:
                return parent
            # continue recursively
            result = find_parent(value, target_key, obj)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = find_parent(item, target_key, parent)
            if result is not None:
                return result
    return None

def get_json_string_keys(data) -> list[str]:
    """
        Retrieve possible param keys from nested response.
        See test_utils.py : test_get_json_string_keys()
    """
    result = []

    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                result.extend(get_json_string_keys(value))
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        result.extend(get_json_string_keys(item))
                # List[str]
                if value and all(isinstance(item, str) for item in value):
                    result.append(key)
            else:
                # Leaf value: string, int, bool, etc.
                result.append(key)
    return result


def find_json_key_paths(data, target_key, path=()) -> List:
    results = []
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = path + (key,)
            if key == target_key:
                results.append(current_path)
            if isinstance(value, (dict, list)):
                results.extend(find_json_key_paths(value, target_key, current_path))
    elif isinstance(data, list):
        for index, item in enumerate(data):
            results.extend(find_json_key_paths(item, target_key, path + (index,)))
    return results

def get_json_by_path(data, path: List[str]):
    for key in path:
        data = data[key]
    return data


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
            elif i < swimmer_pos:
                bar.append(Emoji.replace(':water_wave:'))
            else:
                bar.append("　")
        return Text(" ".join(bar))

