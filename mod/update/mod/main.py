#!/usr/bin/env python3
# make by G.R.H

from pathlib import Path
import zipfile
import os

board_mapping = {
    'RGcubexx': 1,
    'RG34xx': 2,
    'RG34xxSP': 2,
    'RG28xx': 3,
    'RG35xx+_P': 4,
    'RG35xxH': 5,
    'RG35xxSP': 6,
    'RG40xxH': 7,
    'RG40xxV': 8,
    'RG35xxPRO': 9
}

system_list = ['zh_CN', 'zh_TW', 'en_US', 'ja_JP', 'ko_KR', 'es_LA', 'ru_RU', 'de_DE', 'fr_FR', 'pt_BR']

try:
    board_info = Path("/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
except (FileNotFoundError, IndexError):
    board_info = 'RG35xxH'

try:
    lang_info = Path("/mnt/vendor/oem/language.ini").read_text().splitlines()[0]
except (FileNotFoundError, IndexError):
    lang_info = 2
try:
    hdmi_info = Path("/sys/class/extcon/hdmi/state").read_text().splitlines()[0]
except (FileNotFoundError, IndexError):
    hdmi_info = 'HDMI=0'

hw_info = board_mapping.get(board_info, 5)
system_lang = system_list[int(lang_info)]

def ensure_sdl2():
    try:
        import sdl2
        return True
    except ImportError:
        try:
            program = os.path.dirname(os.path.abspath(__file__))
            module_file = os.path.join(program, "sdl2.zip")
            with zipfile.ZipFile(module_file, 'r') as zip_ref:
                zip_ref.extractall("/")
            print("Successfully installed sdl2")
            return True
        except Exception as e:
            print(f"Failed to install sdl2: {e}")
            return False

def main():

    if ensure_sdl2():
        import update
    
    update.start()

    while True:
        update.update()

if __name__ == "__main__":
    main()