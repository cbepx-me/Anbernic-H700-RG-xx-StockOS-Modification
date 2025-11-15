import os
import binascii
import json
import base64
from pathlib import Path
import ssl
from urllib.request import urlopen, Request
import urllib.parse
from systems import get_system_extension, systems
from name_converter import name_converter


class Rom:
    def __init__(self, name, filename, crc=""):
        self.name = name
        self.filename = filename
        self.crc = crc
        self.original_name = name
        self.scraping_name = name


    def set_crc(self, crc):
        self.crc = crc


class Scraper:
    def __init__(self):
        self.user = ""
        self.password = ""
        self.devid = "cmVhdmVu"
        self.devpassword = "MDZXZUY5bTBldWs="
        self.media_type = "ss"
        self.region = "wor"
        self.resize = False

    def load_config_from_json(self, filepath) -> bool:
        if not os.path.exists(filepath):
            print(f"Config file {filepath} not found")
            return False

        with open(filepath, "r") as file:
            config = json.load(file)
            self.user = config.get("user")
            self.password = config.get("password")
            self.media_type = config.get("media_type") or "ss"
            self.region = config.get("region") or "wor"
            self.resize = config.get("resize") is True
        return True

    def get_crc32_from_file(self, rom, chunk_size = 65536):
        crc32 = 0
        with rom.open(mode="rb") as file:
            while chunk := file.read(chunk_size):
                crc32 = binascii.crc32(chunk, crc32)
        crc32 = crc32 & 0xFFFFFFFF
        return "%08X" % crc32

    def get_files_without_extension(self, folder):
        return [f.stem for f in Path(folder).glob("*") if f.is_file()]

    def get_image_files_without_extension(self, folder):
        image_extensions = (".jpg", ".jpeg", ".png")
        return [
            f.stem for f in folder.glob("*") if f.suffix.lower() in image_extensions
        ]

    def get_roms(self, path, system: str) -> list[Rom]:
        roms = []
        system_path = Path(path) / system
        system_extensions = get_system_extension(system)
        if not system_extensions:
            print(f"No extensions found for system: {system}")
            return roms

        for file_path in system_path.rglob("*"):
            if file_path.name.startswith(".") or file_path.name.startswith("-"):
                continue
            if file_path.is_file():
                file_extension = file_path.suffix.lower().lstrip(".")
                if file_extension in system_extensions:
                    name = file_path.stem
                    rel_path = file_path.relative_to(system_path)
                    rom = Rom(filename=str(rel_path), name=name)
                    roms.append(rom)

        return roms

    def get_available_systems(self, roms_path: str) -> list[str]:
        all_systems = [system["name"] for system in systems]
        available_systems = []
        for system in all_systems:
            system_path = Path(roms_path) / system
            if system_path.exists() and any(system_path.iterdir()):
                available_systems.append(system)

        return available_systems

    def get_scraping_name(self, rom: Rom, system_name: str) -> str:
        if name_converter.is_chinese_name(rom.name):
            english_name = name_converter.convert_to_english(system_name, rom.name)
            print(f"Converted '{rom.name}' to '{english_name}' for scraping")
            rom.scraping_name = english_name
            return english_name
        rom.scraping_name = rom.name
        return rom.name

    def scrape_screenshot(
            self, crc: str, game_name: str, system_id: int, system_name: str = ""
    ) -> bytes | None:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        scraping_name = game_name
        if system_name:
            scraping_name = self.get_scraping_name(Rom(game_name, ""), system_name)

        decoded_devid = base64.b64decode(self.devid).decode()
        decoded_devpassword = base64.b64decode(self.devpassword).decode()
        encoded_game_name = urllib.parse.quote(scraping_name)

        query_strategies = [
            f"https://api.screenscraper.fr/api2/jeuInfos.php?devid={decoded_devid}&devpassword={decoded_devpassword}&softname=tiny-scraper&output=json&ssid={self.user}&sspassword={self.password}&crc={crc}&systemeid={system_id}&romtype=rom&romnom={encoded_game_name}",

            f"https://api.screenscraper.fr/api2/jeuInfos.php?devid={decoded_devid}&devpassword={decoded_devpassword}&softname=tiny-scraper&output=json&ssid={self.user}&sspassword={self.password}&systemeid={system_id}&romtype=rom&romnom={encoded_game_name}",
        ]

        if scraping_name != game_name:
            encoded_original_name = urllib.parse.quote(game_name)
            query_strategies.extend([
                f"https://api.screenscraper.fr/api2/jeuInfos.php?devid={decoded_devid}&devpassword={decoded_devpassword}&softname=tiny-scraper&output=json&ssid={self.user}&sspassword={self.password}&crc={crc}&systemeid={system_id}&romtype=rom&romnom={encoded_original_name}",

                f"https://api.screenscraper.fr/api2/jeuInfos.php?devid={decoded_devid}&devpassword={decoded_devpassword}&softname=tiny-scraper&output=json&ssid={self.user}&sspassword={self.password}&systemeid={system_id}&romtype=rom&romnom={encoded_original_name}",
            ])

        print(f"Scraping screenshot for {game_name} (strategies: {len(query_strategies)})...")

        for i, url in enumerate(query_strategies):
            print(f"Trying strategy {i + 1}: {url[:100]}...")
            request = Request(url)
            try:
                with urlopen(request, context=ctx, timeout=10) as response:
                    if response.status == 200:
                        try:
                            data = json.loads(response.read())
                            if data.get("response", {}).get("jeu"):
                                game_data = data["response"]["jeu"]
                                screenshot_url = self.find_best_media(game_data)
                                if screenshot_url:
                                    return self.download_image(screenshot_url, ctx)
                                else:
                                    print(f"No suitable media found in strategy {i + 1}")
                            else:
                                print(f"No game data in strategy {i + 1}")
                        except (ValueError, KeyError) as e:
                            print(f"Invalid response in strategy {i + 1}: {e}")
                    else:
                        print(f"HTTP {response.status} in strategy {i + 1}")
            except Exception as e:
                print(f"Error in strategy {i + 1}: {e}")

        print(f"All strategies failed for {game_name}")
        return None

    def find_best_media(self, game_data: dict) -> str:
        for media in game_data.get("medias", []):
            if (media.get("type") == self.media_type and
                    media.get("region") == self.region):
                return media.get("url")

        for media in game_data.get("medias", []):
            if media.get("type") == self.media_type:
                return media.get("url")

        for media in game_data.get("medias", []):
            return media.get("url")

        return ""

    def download_image(self, url: str, ctx: ssl.SSLContext) -> bytes | None:
        try:
            img_request = Request(url)
            with urlopen(img_request, context=ctx, timeout=10) as img_response:
                if img_response.headers.get("Content-Type") == "image/png":
                    return img_response.read()
                else:
                    print(f"Invalid image format: {img_response.headers.get('Content-Type')}")
        except Exception as e:
            print(f"Error downloading image: {e}")
        return None