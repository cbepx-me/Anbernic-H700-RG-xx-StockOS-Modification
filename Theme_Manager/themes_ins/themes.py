import subprocess
import shutil
import os
import uuid
import config as cf
from pathlib import Path
from systems import get_system_extension, systems
from PIL import Image


class Files:
    def __init__(self, name, filename, crc=""):
        self.name = name
        self.filename = filename
        self.crc = crc

    def set_crc(self, crc):
        self.crc = crc


class Themes:
    def __init__(self):
        self.user = ""

    @staticmethod
    def get_themes(path, system: str) -> list[Files]:
        themes = []
        system_path = Path(path) / system
        system_extensions = get_system_extension(system)
        if not system_extensions or not system_path.exists():
            os.makedirs(system_path, exist_ok=True)
            print(f"Theme file not found!")
            return themes
        for file in os.listdir(system_path):
            file_path = Path(system_path) / file
            if file.startswith("."):
                continue
            if file_path.is_file():
                file_extension = file_path.suffix.lower().lstrip(".")
                if file_extension in system_extensions:
                    name = file_path.stem
                    theme_file = Files(filename=file, name=name)
                    themes.append(theme_file)
        return themes

    @staticmethod
    def get_logos(path, system: str) -> list[Files]:
        logos = []
        system_path = Path(path) / system
        system_extensions = get_system_extension(system)
        if not system_extensions or not system_path.exists():
            os.makedirs(system_path, exist_ok=True)
            print(f"Bootlogo .bmp file not found!")
            return logos
        for file in os.listdir(system_path):
            file_path = Path(system_path) / file
            if file.startswith("."):
                continue
            if file_path.is_file():
                file_extension = file_path.suffix.lower().lstrip(".")
                if file_extension in system_extensions:
                    name = file_path.stem
                    logo_rom = Files(filename=file, name=name)
                    logos.append(logo_rom)
        return logos

    @staticmethod
    def get_available_systems(roms_path: str) -> list[str]:
        all_systems = [system["name"] for system in systems]
        available_systems = []
        for system in all_systems:
            system_path = Path(roms_path) / system
            if system_path.exists() and any(system_path.iterdir()):
                available_systems.append(system)
        return available_systems

    @staticmethod
    def set_bootlogo(logo_file: str):
        boot_device = '/dev/mmcblk0p2'
        boot_path = '/mnt/boot'
        os.makedirs(boot_path, exist_ok=True)
        mount_command = f"mount -t vfat -o rw,utf8,noatime {boot_device} {boot_path}"
        subprocess.run(mount_command, shell=True, check=True)
        copy_command = f"cp -f {logo_file} {boot_path}/bootlogo.bmp"
        subprocess.run(copy_command, shell=True, check=True)
        umount_command = f"umount {boot_path}"
        subprocess.run(umount_command, shell=True, check=True)
        if os.path.exists(boot_path):
            os.rmdir(boot_path)

    def install_theme(self, theme_path: Path, theme_file: str):
        dir_the = theme_path
        file_path = theme_file
        boot_path = '/mnt/mmc/anbernic/bootlogo'
        stock_dir = '/usr/bin'
        unzip_path = os.path.join(stock_dir, 'unzip')
        board_ini_path = '/mnt/vendor/oem/board.ini'
        try:
            with open(board_ini_path, 'r') as f:
                board_ini_content = f.read()
                is_rg28xx = 'RG28xx' in board_ini_content
        except FileNotFoundError:
            is_rg28xx = False
        tmp_dir = os.path.join(dir_the, 'tmp')
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
        os.makedirs(tmp_dir, exist_ok=True)
        subprocess.run([unzip_path, '-oq', file_path, '-d', tmp_dir], check=True)
        ttf_files = []
        for root, dirs, files in os.walk(tmp_dir):
            for dir_name in dirs:
                if dir_name == '__MACOSX':
                    shutil.rmtree(os.path.join(root, dir_name))
                elif dir_name in ['res1', 'res2']:
                    shutil.copytree(os.path.join(root, dir_name), os.path.join('/mnt/vendor', dir_name), dirs_exist_ok=True)
            for file_name in files:
                if file_name == '.DS_Store':
                    os.remove(os.path.join(root, file_name))
                elif file_name.lower().endswith('.bmp'):
                    logo_file = os.path.join(root, file_name)
                    random_str = str(uuid.uuid4())
                    new_bootlogo_name = f'bootlogo_{random_str}.bmp'
                    if is_rg28xx:
                        img = Image.open(logo_file)
                        rotated_img = img.rotate(90, expand=True)
                        rotated_img.save(logo_file)
                    shutil.copy2(logo_file, os.path.join(boot_path, new_bootlogo_name))
                    self.set_bootlogo(logo_file)
                    cf.set_config("boot.logo", 0)
                elif file_name.lower().endswith('.ttf'):
                    ttf_files.append(os.path.join(root, file_name))
        for font_file in ttf_files:
            if 'ebook' in font_file:
                shutil.copy2(font_file, '/mnt/vendor/bin/ebook/resources/fonts/default.ttf')
            elif 'filemanager' in font_file or 'FreeSans.ttf' in font_file:
                shutil.copy2(font_file, '/mnt/vendor/bin/fileM/res/FreeSans.ttf')
            elif 'system' in font_file or 'default.ttf' in font_file:
                shutil.copy2(font_file, '/mnt/vendor/bin/default.ttf')
            elif 'video' in font_file or 'font.ttf' in font_file:
                shutil.copy2(font_file, '/mnt/vendor/bin/video/font.ttf')
            else:
                shutil.copy2(font_file, '/mnt/vendor/bin/default.ttf')
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir)
