#!/usr/bin/env python3
"""
Stock OS Software Center - Professional Edition
"""
from __future__ import annotations

# =========================
# Standard Library Imports
# =========================
import ctypes
import json
import logging
import math
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
import zipfile
from dataclasses import dataclass, asdict, fields, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

# =========================
# Third-Party Imports
# =========================
from PIL import Image, ImageDraw, ImageFont

cur_app_ver = "3.0.1"
assets_date = "260215"

def ensure_requests():
    try:
        import sdl2
        import requests
        import urllib3
        from urllib3.util import Retry
        from requests.adapters import HTTPAdapter
        return True
    except ImportError:
        try:
            program = os.path.dirname(os.path.abspath(__file__))
            module_file = os.path.join(program, "module.zip")
            with zipfile.ZipFile(module_file, 'r') as zip_ref:
                zip_ref.extractall("/")
            print("Successfully installed requests and urllib3")
            return True
        except Exception as e:
            print(f"Failed to install requests: {e}")
            return False


if ensure_requests():
    import requests
    from urllib3.util import Retry
    from requests.adapters import HTTPAdapter
    import sdl2

# =========================
# Logging Setup
# =========================
APP_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_PATH, "software_center.log")
log_delete = 1
if log_delete and os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
LOGGER = logging.getLogger("software_center")
LOGGER.info(f"=== Software Center Start ===")


# =========================
# Enhanced Configuration
# =========================
@dataclass
class Config:
    board_mapping: Dict[str, int] = None
    system_list: Tuple[str, ...] = (
        "zh_CN",
        "zh_TW",
        "en_US",
        "ja_JP",
        "ko_KR",
        "es_LA",
        "ru_RU",
        "de_DE",
        "fr_FR",
        "pt_BR",
    )

    # Enhanced Color Scheme - Modern Gradient Theme
    COLOR_PRIMARY: str = "#6366f1"
    COLOR_PRIMARY_LIGHT: str = "#818cf8"
    COLOR_PRIMARY_DARK: str = "#4f46e5"
    COLOR_SECONDARY: str = "#f59e0b"
    COLOR_ACCENT: str = "#10b981"
    COLOR_DANGER: str = "#ef4444"
    COLOR_SUCCESS: str = "#22c55e"
    COLOR_WARNING: str = "#f59e0b"

    # Enhanced Background Colors
    COLOR_BG: str = "#0f172a"
    COLOR_BG_LIGHT: str = "#1e293b"
    COLOR_BG_GRADIENT: str = "#1e1b4b"

    # Enhanced Card Colors
    COLOR_CARD: str = "#1e293b"
    COLOR_CARD_LIGHT: str = "#334155"
    COLOR_CARD_HOVER: str = "#475569"

    # Enhanced Text Colors
    COLOR_TEXT: str = "#f8fafc"
    COLOR_TEXT_SECONDARY: str = "#cbd5e1"
    COLOR_TEXT_TERTIARY: str = "#94a3b8"

    # Enhanced Border and Effects
    COLOR_BORDER: str = "#334155"
    COLOR_BORDER_LIGHT: str = "#475569"
    COLOR_SHADOW: str = "#020617"
    COLOR_OVERLAY: str = "#00000099"
    COLOR_GLOW: str = "#6366f155"

    # Enhanced Button Colors
    COLOR_BUTTON_PRIMARY: str = "#4f46e5"
    COLOR_BUTTON_SECONDARY: str = "#475569"
    COLOR_BUTTON_HOVER: str = "#6366f1"

    if os.name == "nt":
        root_path = APP_PATH + "/sys"
    else:
        root_path = ""
    font_file: str = os.path.join(APP_PATH, "font", "font.ttf")
    if not os.path.exists(font_file):
        font_file: str = root_path + "/mnt/vendor/bin/default.ttf"

    # Software Center Specific Paths
    database_path: str = root_path + "/mnt/mod/ctrl/configs/software_center/installed.json"
    uninstall_path: str = root_path + "/mnt/mod/ctrl/configs/software_center/uninstall"
    screenshots_path: str = root_path + "/mnt/mod/ctrl/configs/software_center/screenshots"
    if not os.path.exists(uninstall_path):
        os.makedirs(uninstall_path, exist_ok=True)
    cache_dir = root_path + "/tmp/software_center/screenshots"

    # Software Categories
    categories: Tuple[str, ...] = (
        "all",
        "games",
        "tools",
        "emulators",
        "themes",
        "other"
    )

    tmp_list = [
        root_path + "/dev/shm",
        root_path + "/tmp",
        root_path + "/mnt/mmc",
        root_path + "/mnt/sdcard"
    ]

    free_space = []
    for tmp in tmp_list:
        if os.path.exists(tmp):
            usage = shutil.disk_usage(tmp)
            free_num = usage.free + 1 if tmp == root_path + "/tmp" else usage.free
            free_space.append((free_num, tmp))
    free_space.sort(key=lambda x: x[0], reverse=True)
    if free_space:
        cache_path: str = (free_space[0][1] if free_space[0][1] else root_path + "/tmp") + "/tmp_install"
    else:
        cache_path: str = (root_path + "/tmp") + "/tmp_install"
    os.makedirs(cache_path, exist_ok=True)
    LOGGER.info(f"Use the temporary download path: {cache_path}")

    bytes_per_pixel: int = 4
    keymap: Dict[int, str] = None

    retry_config = {
        'total': 3,
        'backoff_factor': 0.5,
        'status_forcelist': [500, 502, 503, 504],
        'allowed_methods': ['GET', 'HEAD']
    }

    # Software Repositories
    mirrors = [
        {
            "name": "Gitcode",
            "url": "https://raw.gitcode.com/cbepx/install/raw/main/software_list.json",
            "region": "CN",
            "server": "https://gitcode.com/cbepx/install/releases/download/download/"
        },
        {
            "name": "Github",
            "url": "https://github.com/cbepx-me/Online_installation/raw/refs/heads/main/software_list.json",
            "region": "Global",
            "server": "https://github.com/cbepx-me/Online_installation/releases/download/download/"
        }
    ]
    repositories = [
        {
            "name": "None",
            "url": "None",
            "region": "None",
            "server": "None"
        }
    ]

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0'
    }

    fallback_mirror = mirrors[0]
    speeds = []
    for mirror in mirrors:
        try:
            start = time.time()
            response = requests.get(mirror["url"], timeout=3, headers=headers, stream=True)
            response.close()
            end = time.time() - start
            if response.status_code != 200:
                LOGGER.error(f"Mirror {mirror['name']} accessible but file software_list.json returned error code: {response.status_code}")
                end = float('inf')
        except:
            end = float('inf')

        speeds.append((end, mirror))
    speeds.sort(key=lambda x: x[0])
    repositories[0]["name"] = speeds[0][1]["name"] if speeds[0][0] != float('inf') else fallback_mirror["name"]
    repositories[0]["url"] = speeds[0][1]["url"] if speeds[0][0] != float('inf') else fallback_mirror["url"]
    repositories[0]["region"] = speeds[0][1]["region"] if speeds[0][0] != float('inf') else fallback_mirror["region"]
    repositories[0]["server"] = speeds[0][1]["server"] if speeds[0][0] != float('inf') else fallback_mirror["server"]
    server_name = repositories[0]["name"]
    info_server = repositories[0]["url"]
    server_url = repositories[0]["server"]
    LOGGER.info(f"Use the downloaded server: {server_name}")

    def __post_init__(self):
        if self.board_mapping is None:
            self.board_mapping = {
                "RGcubexx": 1,
                "RG34xx": 2,
                "RG34xxSP": 2,
                "RG28xx": 3,
                "RG35xx+_P": 4,
                "RG35xxH": 5,
                "RG35xxSP": 6,
                "RG40xxH": 7,
                "RG40xxV": 8,
                "RG35xxPRO": 9,
            }
        if self.keymap is None:
            self.keymap = {
                304: "A",
                305: "B",
                306: "Y",
                307: "X",
                308: "L1",
                309: "R1",
                314: "L2",
                315: "R2",
                17: "DY",
                16: "DX",
                310: "SELECT",
                311: "START",
                312: "MENUF",
                114: "V+",
                115: "V-",
            }

    @staticmethod
    def screen_resolutions() -> Dict[int, Tuple[int, int, int]]:
        return {
            1: (640, 640, 18),
            2: (720, 480, 11),
            3: (640, 480, 11),
            4: (640, 480, 11),
            5: (640, 480, 11),
            6: (640, 480, 11),
            7: (640, 480, 11),
            8: (640, 480, 11),
            9: (640, 480, 11),
        }


# =========================
# Software Data Structures
# =========================
@dataclass
class SoftwarePackage:
    id: str
    name: str
    version: str
    category: str
    size: int
    md5: str
    download_url: str
    description: str
    description_zh: str = ""
    description_en: str = ""
    instruction: str = ""
    instruction_zh: str = ""
    instruction_en: str = ""
    icon_url: str = ""
    author: str = ""
    screenshots: List[str] = None
    dependencies: List[str] = None
    compatibility: List[str] = None
    min_os_version: str = ""
    changelog: str = ""
    changelog_zh: str = ""
    changelog_en: str = ""
    installed: bool = False
    local_version: str = ""
    update_available: bool = False
    install_path: str = ""
    extra_fields: Dict[str, Any] = field(default_factory=dict)


    def __post_init__(self):
        if self.screenshots is None:
            self.screenshots = []
        if self.dependencies is None:
            self.dependencies = []
        if self.compatibility is None:
            self.compatibility = []


    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SoftwarePackage':
        known_fields = {f.name for f in fields(cls) if f.name != 'extra_fields'}
        known_data = {k: v for k, v in data.items() if k in known_fields}
        extra_fields = {k: v for k, v in data.items() if k not in known_fields}

        instance = cls(**known_data)
        instance.extra_fields = extra_fields
        return instance

# =========================
# Translator
# =========================
class Translator:
    def __init__(self, lang_code: str = "en_US"):
        self.lang_data: Dict[str, str] = {}
        self.lang_code = lang_code
        self.load_language(lang_code)

    def load_language(self, lang_code: str) -> None:
        base = os.path.dirname(os.path.abspath(__file__))
        lang_file = os.path.join(base, "lang", f"{lang_code}.json")
        if not os.path.exists(lang_file):
            lang_file = os.path.join(base, "lang", "en_US.json")
            LOGGER.warning(
                "Language file %s.json not found, using default en_US", lang_code
            )
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self.lang_data = json.load(f)
            LOGGER.info("Loaded language file: %s", lang_file)
        except FileNotFoundError:
            LOGGER.error("Language file %s not found!", lang_file)
            raise
        except json.JSONDecodeError as e:
            LOGGER.error("Error parsing language file %s: %s", lang_file, e)
            raise

    def t(self, key: str, **kwargs) -> str:
        message = self.lang_data.get(key, key)
        try:
            return message.format(**kwargs)
        except KeyError as e:
            LOGGER.warning("Missing key in translation: %s", e)
            return message


# =========================
# Input Handling
# =========================
class InputHandler:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.code_name: str = ""
        self.value: int = 0

        if os.name == "nt":
            self.key_map = {
                sdl2.SDLK_UP: ("DY", -1),
                sdl2.SDLK_DOWN: ("DY", 1),
                sdl2.SDLK_LEFT: ("DX", -1),
                sdl2.SDLK_RIGHT: ("DX", 1),
                sdl2.SDLK_RETURN: ("A", 1),
                sdl2.SDLK_SPACE: ("Y", 1),
                sdl2.SDLK_ESCAPE: ("SELECT", 1),
                sdl2.SDLK_BACKSPACE: ("B", 1),
                sdl2.SDLK_TAB: ("L1", 1),
                sdl2.SDLK_PAGEUP: ("R1", 1),
                sdl2.SDLK_PAGEDOWN: ("L2", 1),
                sdl2.SDLK_HOME: ("R2", 1),
            }

    def poll(self) -> None:
        if os.name == "nt":
            event = sdl2.SDL_Event()
            while sdl2.SDL_PollEvent(ctypes.byref(event)):
                if event.type == sdl2.SDL_KEYDOWN:
                    sym = event.key.keysym.sym
                    if sym in self.key_map:
                        name, val = self.key_map[sym]
                        self.code_name = name
                        self.value = val
                        return
                elif event.type == sdl2.SDL_QUIT:
                    self.code_name = "SELECT"
                    self.value = 1
                    return
            self.code_name = ""
            self.value = 0
        else:
            try:
                with open("/dev/input/event1", "rb") as f:
                    while True:
                        event = f.read(24)
                        if not event:
                            break
                        (tv_sec, tv_usec, etype, kcode, kvalue) = struct.unpack(
                            "llHHI", event
                        )
                        if kvalue != 0:
                            if kvalue != 1:
                                kvalue = -1
                            else:
                                kvalue = 1
                            self.code_name = self.cfg.keymap.get(kcode, str(kcode))
                            self.value = kvalue
                            LOGGER.debug(
                                "Key pressed: %s (code: %s, value: %s)",
                                self.code_name,
                                kcode,
                                kvalue,
                            )
                            return
            except Exception as e:
                LOGGER.error("Error reading input: %s", e)
                self.code_name = ""
                self.value = 0

    def is_key(self, name: str, key_value: int = 99) -> bool:
        if self.code_name == name:
            if key_value != 99:
                return self.value == key_value
            return True
        return False

    def slide_key(self) -> bool:
        if self.code_name:
            return True
        return False

    def reset(self) -> None:
        self.code_name = ""
        self.value = 0


# =========================
# Enhanced UI Renderer (Modified for Software Center)
# =========================
class UIRenderer:
    _instance: Optional["UIRenderer"] = None
    _initialized: bool = False

    def __init__(self, cfg: Config, translator: Translator, hw_info: int):
        self.cfg = cfg
        self.t = translator
        self.hw_info = hw_info

        x_size, y_size, _ = Config.screen_resolutions().get(hw_info, (640, 480, 11))
        self.x_size = x_size
        self.y_size = y_size
        self.screen_size = x_size * y_size * cfg.bytes_per_pixel

        self.active_image: Optional[Image.Image] = None
        self.active_draw: Optional[ImageDraw.ImageDraw] = None

        if self._initialized:
            return
        self.window = self._create_window()
        self.renderer = self._create_renderer()
        self.opt_stretch = True
        self._initialized = True

        self._draw_start()
        self.screen_reset()
        self.set_active(self.create_image())

        try:
            self.hdmi_info = Path("/sys/class/extcon/hdmi/state").read_text().splitlines()[0]
        except (FileNotFoundError, IndexError):
            self.hdmi_info = 'HDMI=0'

    def screen_reset(self) -> None:
        for i in range(self.y_size):
            ratio = i / self.y_size
            color = self._blend_colors(self.cfg.COLOR_BG_GRADIENT, self.cfg.COLOR_BG, ratio)
            self.active_draw.rectangle([0, i, self.x_size, i + 1], fill=color)

    def _draw_start(self) -> None:
        sdl2.SDL_SetRenderDrawColor(self.renderer, 0, 0, 0, 255)
        sdl2.SDL_RenderClear(self.renderer)
        self.active_image = self.create_image()
        self.active_draw = ImageDraw.Draw(self.active_image)

    def _create_window(self):
        if os.name == "nt":
            window_width = self.x_size
            window_height = self.y_size
            window = sdl2.SDL_CreateWindow(
                "Software Center".encode("utf-8"),
                sdl2.SDL_WINDOWPOS_UNDEFINED,
                sdl2.SDL_WINDOWPOS_UNDEFINED,
                window_width,
                window_height,
                sdl2.SDL_WINDOW_SHOWN
            )
        else:
            window = sdl2.SDL_CreateWindow(
                "Software Center".encode("utf-8"),
                sdl2.SDL_WINDOWPOS_UNDEFINED,
                sdl2.SDL_WINDOWPOS_UNDEFINED,
                0,
                0,
                sdl2.SDL_WINDOW_FULLSCREEN_DESKTOP | sdl2.SDL_WINDOW_SHOWN,
            )

        if not window:
            print(f"Failed to create window: {sdl2.SDL_GetError()}")
            raise RuntimeError("Failed to create window")

        return window

    def _create_renderer(self):
        renderer = sdl2.SDL_CreateRenderer(
            self.window, -1, sdl2.SDL_RENDERER_ACCELERATED
        )

        if not renderer:
            print(f"Failed to create renderer: {sdl2.SDL_GetError()}")
            raise RuntimeError("Failed to create renderer")

        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"0")
        return renderer

    def draw_end(self) -> None:
        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    def create_image(self) -> Image.Image:
        try:
            return Image.new("RGBA", (self.x_size, self.y_size), color=self.cfg.COLOR_BG)
        except Exception as e:
            LOGGER.error("Error creating image: %s", e)
            raise

    def set_active(self, image: Image.Image) -> None:
        self.active_image = image
        self.active_draw = ImageDraw.Draw(self.active_image)

    def paint(self) -> None:
        if self.hw_info == 3:
            rotated_image = self.active_image.rotate(90, expand=True)
            rgba_data = rotated_image.tobytes()
            temp_width, temp_height = rotated_image.size
        else:
            rgba_data = self.active_image.tobytes()
            temp_width, temp_height = self.x_size, self.y_size

        surface = sdl2.SDL_CreateRGBSurfaceWithFormatFrom(
            rgba_data,
            temp_width,
            temp_height,
            32,
            temp_width * 4,
            sdl2.SDL_PIXELFORMAT_RGBA32,
        )
        texture = sdl2.SDL_CreateTextureFromSurface(self.renderer, surface)
        sdl2.SDL_FreeSurface(surface)

        window_width = ctypes.c_int()
        window_height = ctypes.c_int()
        sdl2.SDL_GetWindowSize(
            self.window, ctypes.byref(window_width), ctypes.byref(window_height)
        )
        window_width, window_height = window_width.value, window_height.value

        if not self.opt_stretch:
            scale = min(
                window_width / temp_width, window_height / temp_height
            )
            dst_width = int(temp_width * scale)
            dst_height = int(temp_height * scale)
            dst_x = (window_width - dst_width) // 2
            dst_y = (window_height - dst_height) // 2
            dst_rect = sdl2.SDL_Rect(dst_x, dst_y, dst_width, dst_height)
        else:
            dst_rect = sdl2.SDL_Rect(0, 0, window_width, window_height)

        sdl2.SDL_RenderCopy(self.renderer, texture, None, dst_rect)
        sdl2.SDL_RenderPresent(self.renderer)
        sdl2.SDL_DestroyTexture(texture)

    def clear(self) -> None:
        self.screen_reset()

    def text(self, pos, text, font=22, color=None, anchor=None, bold=False, shadow=False) -> None:
        color = color or self.cfg.COLOR_TEXT
        font_path = self.cfg.font_file

        try:
            font_size = font
            if bold and hasattr(ImageFont, 'FreeTypeFont'):
                try:
                    fnt = ImageFont.truetype(font_path, font_size)
                    if shadow:
                        shadow_color = self.cfg.COLOR_SHADOW
                        for offset_x, offset_y in [(1, 1), (1, -1), (-1, 1), (-1, -1)]:
                            self.active_draw.text((pos[0] + offset_x, pos[1] + offset_y), text,
                                                  font=fnt, fill=shadow_color, anchor=anchor)
                except:
                    fnt = ImageFont.load_default()
            else:
                fnt = ImageFont.truetype(font_path, font_size)

            self.active_draw.text(pos, text, font=fnt, fill=color, anchor=anchor)
        except Exception:
            fnt = ImageFont.load_default()
            self.active_draw.text(pos, text, font=fnt, fill=color, anchor=anchor)

    def display_image(self, image_path, target_x=0, target_y=0, target_width=None, target_height=None, rota=1):
        if target_width is None:
            target_width = self.x_size - target_x
        if target_height is None:
            target_height = self.y_size - target_y
            
        try:
            img = Image.open(image_path)
            max_width, max_height = 1920, 1080
            if img.width > max_width or img.height > max_height:
                LOGGER.warning(f"Image {image_path} exceeds max resolution, resizing...")
                img.thumbnail((max_width, max_height))

            img.thumbnail((target_width, target_height))
            paste_x = target_x + (target_width - img.width) // 2
            paste_y = target_y + (target_height - img.height) // 2

            if self.hw_info == 3 and rota == 1 and self.hdmi_info != "HDMI=1":
                img = img.rotate(-90, expand=True)

            self.active_image.paste(img, (paste_x, paste_y))

        except Exception as e:
            LOGGER.error(f"Failed to load image {image_path}: {e}")
            return

    def rect(self, xy, fill=None, outline=None, width: int = 1, radius: int = 0, shadow: bool = False) -> None:
        if shadow and radius > 0:
            shadow_xy = [xy[0] + 2, xy[1] + 2, xy[2] + 2, xy[3] + 2]
            self.active_draw.rounded_rectangle(shadow_xy, radius=radius,
                                               fill=self.cfg.COLOR_SHADOW, outline=None)

        if radius > 0:
            self.active_draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            self.active_draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def panel(self, xy, title: Optional[str] = None, shadow=True, accent: bool = False) -> None:
        panel_color = self.cfg.COLOR_CARD
        if accent:
            panel_color = self.cfg.COLOR_PRIMARY_DARK

        if shadow:
            shadow_xy = [xy[0] + 3, xy[1] + 3, xy[2] + 3, xy[3] + 3]
            self.rect(shadow_xy, fill=self.cfg.COLOR_SHADOW, radius=16)

        self.rect(xy, fill=panel_color, outline=self.cfg.COLOR_BORDER_LIGHT, width=2, radius=16)

        if title:
            title_height = 36
            title_bg = [xy[0], xy[1], xy[2], xy[1] + title_height]
            for i in range(title_height):
                ratio = i / title_height
                color = self._blend_colors(self.cfg.COLOR_PRIMARY_DARK, self.cfg.COLOR_PRIMARY, ratio)
                self.active_draw.rectangle([title_bg[0], title_bg[1] + i,
                                            title_bg[2], title_bg[1] + i + 1],
                                           fill=color)

            self.text((self.x_size // 2, xy[1] + title_height // 2), title,
                      font=20, anchor="mm", bold=True, shadow=True)

    def button(self, xy, label: str, icon: str = None, primary: bool = False, disabled: bool = False, type = 0) -> None:
        if disabled:
            fill_color = self.cfg.COLOR_BUTTON_SECONDARY
            text_color = self.cfg.COLOR_TEXT_TERTIARY
        else:
            fill_color = self.cfg.COLOR_BUTTON_PRIMARY if primary else self.cfg.COLOR_BUTTON_SECONDARY
            text_color = self.cfg.COLOR_TEXT

        self.rect(xy, fill=fill_color, outline=self.cfg.COLOR_BORDER_LIGHT, radius=12, shadow=True)

        font_path = self.cfg.font_file
        try:
            fnt = ImageFont.truetype(font_path, 18)
        except Exception:
            fnt = ImageFont.load_default()

        bbox = self.active_draw.textbbox((0, 0), label, font=fnt)
        text_width = bbox[2] - bbox[0]

        button_width = xy[2] - xy[0]
        text_x = (xy[0] + xy[2]) // 2
        text_y = (xy[1] + xy[3]) // 2

        font_size = 22
        if text_width > button_width * 0.7:
            font_size = max(12, int(18 * (button_width * 0.7) / text_width))
            try:
                fnt = ImageFont.truetype(font_path, font_size)
            except Exception:
                fnt = ImageFont.load_default()

        if icon:
            if type == 0:
                self.text((text_x - 40, text_y), icon, font=22, anchor="mm", color=text_color)
                self.text((text_x, text_y), label, font=font_size, anchor="lm",
                      color=text_color, bold=primary and not disabled)
            elif type == 2:
                self.text((text_x - 70, text_y), icon, font=22, anchor="mm", color=text_color)
                self.text((text_x - 40, text_y), label, font=font_size, anchor="lm",
                              color=text_color, bold=primary and not disabled)
            else:
                self.text((text_x - 30, text_y), icon, font=20, anchor="mm", color=text_color)
                self.text((text_x - 10, text_y), label, font=font_size, anchor="lm",
                      color=text_color, bold=primary and not disabled)
        else:
                self.text((text_x, text_y), label, font=font_size, anchor="mm",
                      color=text_color, bold=primary and not disabled)

    def info_header(self, title: str, subtitle: str = None, ver: str = None) -> None:
        header_height = 100

        for i in range(header_height):
            ratio = i / header_height
            r = self._blend_colors(self.cfg.COLOR_PRIMARY_DARK, self.cfg.COLOR_BG_GRADIENT, ratio)
            self.rect([0, i, self.x_size, i + 1], fill=r)

            if i < 30:
                reflect_ratio = i / 30
                reflect_color = self._blend_colors(self.cfg.COLOR_GLOW, self.cfg.COLOR_BG, 1 - reflect_ratio)
                self.rect([0, self.y_size - i, self.x_size, self.y_size - i + 1], fill=reflect_color)

        self.text((self.x_size // 2, 35), title, font=28, anchor="mm", bold=True, shadow=True)

        if subtitle:
            self.text((self.x_size // 2, 65), subtitle, font=18, anchor="mm",
                      color=self.cfg.COLOR_TEXT_SECONDARY, shadow=True)
        if ver:
            self.text((self.x_size - 50, 65), f'v{ver}', font=18, anchor="mm", bold=True, shadow=True)

    def status_badge(self, center: Tuple[int, int], text: str, status: str = "info") -> None:
        colors = {
            "success": self.cfg.COLOR_SUCCESS,
            "warning": self.cfg.COLOR_WARNING,
            "error": self.cfg.COLOR_DANGER,
            "info": self.cfg.COLOR_PRIMARY_LIGHT
        }
        color = colors.get(status, self.cfg.COLOR_PRIMARY_LIGHT)

        font_path = self.cfg.font_file
        try:
            fnt = ImageFont.truetype(font_path, 18)
        except Exception:
            fnt = ImageFont.load_default()

        bbox = self.active_draw.textbbox((0, 0), text, font=fnt)
        text_width = bbox[2] - bbox[0] + 30
        text_height = bbox[3] - bbox[1] + 16

        x, y = center
        badge_rect = [x - text_width // 2, y - text_height // 2,
                      x + text_width // 2, y + text_height // 2]

        self.rect(badge_rect, fill=color, radius=int(text_height // 2), shadow=True)
        self.text((x, y), text, font=18, anchor="mm", color=self.cfg.COLOR_TEXT, bold=True)

    def progress_bar(self, y_center: int, percent: float, label_top: Optional[str] = None,
                     label_bottom: Optional[str] = None, show_percent: bool = True) -> None:
        bar_left = 50
        bar_right = self.x_size - 50
        bar_top = y_center - 16
        bar_bottom = y_center + 16
        bar_height = bar_bottom - bar_top

        bar_left = int(bar_left)
        bar_right = int(bar_right)
        bar_top = int(bar_top)
        bar_bottom = int(bar_bottom)
        bar_height = int(bar_height)

        shadow_offset = 2
        self.rect([bar_left - shadow_offset, bar_top - shadow_offset,
                   bar_right + shadow_offset, bar_bottom + shadow_offset],
                  fill=self.cfg.COLOR_SHADOW, radius=int(bar_height // 2))

        self.rect([bar_left, bar_top, bar_right, bar_bottom],
                  fill=self.cfg.COLOR_BG_LIGHT, radius=int(bar_height // 2))

        pct = max(0, min(100, int(percent))) / 100.0
        filled_right = bar_left + int((bar_right - bar_left) * pct)

        if filled_right > bar_left:
            progress_width = filled_right - bar_left

            if progress_width < bar_height:
                progress_radius = int(progress_width // 2)
            else:
                progress_radius = int(bar_height // 2)

            if progress_width > 0:
                gradient_rect = [bar_left, bar_top, filled_right, bar_bottom]

                overall_ratio = pct
                color = self._blend_colors(self.cfg.COLOR_PRIMARY, self.cfg.COLOR_ACCENT, overall_ratio)

                self.rect(gradient_rect, fill=color, radius=progress_radius)

            if show_percent:
                progress_text = f"{int(percent)}%"
                text_x = (bar_left + bar_right) // 2
                text_y = y_center

                if percent < 50:
                    text_color = self.cfg.COLOR_TEXT
                else:
                    text_color = self.cfg.COLOR_BG

                self.text((text_x, text_y), progress_text, font=20, anchor="mm",
                          color=text_color, shadow=percent >= 50)

        if label_top:
            self.text((self.x_size // 2, bar_top - 25), label_top,
                      font=22, anchor="mm", bold=True, shadow=True)
        if label_bottom:
            self.text((self.x_size // 2, bar_bottom + 25), label_bottom,
                      font=18, anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)

    def _blend_colors(self, color1: str, color2: str, ratio: float) -> str:
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        r = max(0, min(255, int(r1 + (r2 - r1) * ratio)))
        g = max(0, min(255, int(g1 + (g2 - g1) * ratio)))
        b = max(0, min(255, int(b1 + (b2 - b1) * ratio)))

        return f"#{r:02x}{g:02x}{b:02x}"

    def draw_loading_screen(self, title: str, subtitle: str = None) -> None:
        self.clear()

        for i in range(self.y_size):
            ratio = i / self.y_size
            color = self._blend_colors(self.cfg.COLOR_BG_GRADIENT, self.cfg.COLOR_BG, ratio)
            self.rect([0, i, self.x_size, i + 1], fill=color)

        center_x, center_y = self.x_size // 2, self.y_size // 2 - 40
        radius = 40
        current_time = time.time()
        rotation = (current_time * 90) % 360

        segments = 8
        for i in range(segments):
            angle = rotation - i * 45
            rad = angle * 3.14159 / 180
            dot_x = center_x + radius * math.cos(rad)
            dot_y = center_y + radius * math.sin(rad)

            dot_radius = 4
            self.circle((int(dot_x), int(dot_y)), dot_radius,
                        fill=self.cfg.COLOR_PRIMARY_LIGHT)

        self.text((center_x, center_y + radius + 40), title, font=26, anchor="mm", bold=True, shadow=True)
        if subtitle:
            self.text((center_x, center_y + radius + 70), subtitle, font=18, anchor="mm",
                      color=self.cfg.COLOR_TEXT_SECONDARY)

        self.paint()

    def circle(self, center: Tuple[int, int], radius: int, fill=None, outline=None, shadow: bool = False) -> None:
        x, y = center
        if shadow:
            shadow_radius = radius + 2
            self.active_draw.ellipse([x - shadow_radius, y - shadow_radius,
                                      x + shadow_radius, y + shadow_radius],
                                     fill=self.cfg.COLOR_SHADOW)
        self.active_draw.ellipse([x - radius, y - radius, x + radius, y + radius],
                                 fill=fill, outline=outline)

    def tips_info(self, info_txt: str = None) -> None:
        if info_txt:
            self.panel([20, self.y_size // 2 - 60, self.x_size - 20, self.y_size // 2 + 60])
            self.text((self.x_size // 2, self.y_size // 2), info_txt, anchor="mm",)
            self.paint()

# =========================
# Software Manager
# =========================
class SoftwareManager:
    def __init__(self, cfg: Config, ui: UIRenderer, translator: Translator):
        self.cfg = cfg
        self.ui = ui
        self.t = translator
        self.software_list: List[SoftwarePackage] = []
        self.installed_software: Dict[str, SoftwarePackage] = {}
        self.current_category = "all"
        self.selected_software: Optional[SoftwarePackage] = None
        self.search_query = ""
        self.board_info = Path(self.cfg.root_path + "/mnt/vendor/oem/board.ini").read_text().splitlines()[0]

        self.session = requests.Session()
        self.session.headers.update(self.cfg.headers)

        retry = Retry(
            total=self.cfg.retry_config['total'],
            backoff_factor=self.cfg.retry_config['backoff_factor'],
            status_forcelist=self.cfg.retry_config['status_forcelist'],
            allowed_methods=self.cfg.retry_config['allowed_methods']
        )

        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)

        # Load installed software database
        self.load_installed_software()

    def load_installed_software(self) -> None:
        """Load installed software from database"""
        try:
            if os.path.exists(self.cfg.database_path):
                with open(self.cfg.database_path, 'r', encoding='utf-8') as f:
                    installed_data = json.load(f)
                    for software_id, data in installed_data.items():
                        self.installed_software[software_id] = SoftwarePackage(**data)
                LOGGER.info(f"Loaded {len(self.installed_software)} installed software entries")
        except Exception as e:
            LOGGER.error(f"Error loading installed software database: {e}")
            self.installed_software = {}

    def save_installed_software(self) -> None:
        """Save installed software to database"""
        try:
            os.makedirs(os.path.dirname(self.cfg.database_path), exist_ok=True)
            with open(self.cfg.database_path, 'w', encoding='utf-8') as f:
                json.dump({k: asdict(v) for k, v in self.installed_software.items()}, f, indent=2)
            LOGGER.info("Saved installed software database")
        except Exception as e:
            LOGGER.error(f"Error saving installed software database: {e}")

    def fetch_software_list(self) -> bool:
        """Fetch software list from repositories"""
        for repo in self.cfg.repositories:
            try:
                LOGGER.info(f"Fetching software list from {repo['name']}: {repo['url']}")
                response = self.session.get(repo['url'], timeout=10)
                response.raise_for_status()

                software_data = response.json()
                self.software_list = []

                lang = self.t.lang_code
                is_chinese = lang.startswith('zh')
                desc_key = 'description_zh' if is_chinese else 'description_en'
                chang_key = 'changelog_zh' if is_chinese else 'changelog_en'
                inst_key = 'instruction_zh' if is_chinese else 'instruction_en'

                if 'software' not in software_data:
                    LOGGER.error(f"Invalid software list format: missing 'software' key")
                    continue

                for i, item in enumerate(software_data.get('software', [])):
                    try:
                        compatibility = item.get('compatibility', [])
                        if compatibility and self.board_info not in compatibility:
                            LOGGER.info(f"Skipping {item.get('name', 'unknown')} due to compatibility mismatch")
                            continue
                    
                        description = item.get(desc_key) or item.get('description', '')
                        item['description'] = description
                        changelog = item.get(chang_key) or item.get('changelog', '')
                        item['changelog'] = changelog
                        instruction = item.get(inst_key) or item.get('instruction', '')
                        item['instruction'] = instruction

                        required_fields = ['id', 'name', 'version', 'description', 'category', 'size', 'download_url']
                        for field in required_fields:
                            if field not in item:
                                LOGGER.warning(f"Missing required field '{field}' in software item {i}")
                                item[field] = f"unknown_{field}"

                        software = SoftwarePackage(**item)

                        # Check if installed
                        if software.id in self.installed_software:
                            installed = self.installed_software[software.id]
                            software.installed = True
                            software.local_version = installed.local_version
                            software.install_path = installed.install_path
                            software.update_available = (software.version != installed.local_version)

                        self.software_list.append(software)
                        LOGGER.info(f"Loaded software: {software.name} (ID: {software.id})")

                    except Exception as e:
                        LOGGER.error(f"Error processing software item {i}: {e}")
                        continue

                LOGGER.info(f"Successfully loaded {len(self.software_list)} software packages from {repo['name']}")
                return True

            except Exception as e:
                LOGGER.error(f"Error fetching from {repo['name']}: {e}")
                continue

        LOGGER.error("Failed to fetch software list from all repositories")
        return False

    def get_software_by_category(self, category: str) -> List[SoftwarePackage]:
        """Get software filtered by category"""
        if category == "all":
            return self.software_list
        elif category == "installed":
            return [s for s in self.software_list if s.installed]
        else:
            return [s for s in self.software_list if s.category == category]

    def search_software(self, query: str) -> List[SoftwarePackage]:
        """Search software by name or description"""
        query = query.lower()
        return [s for s in self.software_list
                if query in s.name.lower() or query in s.description.lower()]

    def install_software(self, software: SoftwarePackage) -> bool:
        """Install software package"""
        try:
            LOGGER.info(f"Starting installation of {software.name}")

            # Create necessary directories
            os.makedirs(self.cfg.cache_path, exist_ok=True)

            # Download the software
            download_path = os.path.join(self.cfg.cache_path, f"{software.id}.zip")
            download_result = self._download_software(software, download_path)

            if not download_result:
                shutil.rmtree(self.cfg.cache_path, ignore_errors=True)
                return False

            # Create installation directory
            install_dir = os.path.join(self.cfg.cache_path, software.category, software.id)
            os.makedirs(install_dir, exist_ok=True)

            # Extract and install
            if not self._extract_software(download_path, install_dir, software):
                shutil.rmtree(self.cfg.cache_path, ignore_errors=True)
                return False

            install_script = os.path.join(install_dir, "install.sh")
            uninstall_script = os.path.join(install_dir, "uninstall.sh")
            has_install = os.path.isfile(install_script)
            has_uninstall = os.path.isfile(uninstall_script)
            print(software)

            if has_install and os.name != 'nt':
                LOGGER.info(f"Executing install.sh for {software.name}")
                self.ui.tips_info(self.t.t("Installing") + ' ...')
                try:
                    st = os.stat(os.path.join(install_dir, "install.sh"))
                    os.chmod(os.path.join(install_dir, "install.sh"), st.st_mode | 0o111)
                    result = subprocess.run(
                        ["/bin/bash", "install.sh"],
                        cwd=install_dir,
                        capture_output=True,
                        text=True,
                        timeout=300
                    )
                    if result.returncode != 0:
                        LOGGER.error(f"install.sh failed with return code {result.returncode}")
                        LOGGER.error(f"stdout: {result.stdout}")
                        LOGGER.error(f"stderr: {result.stderr}")
                        shutil.rmtree(self.cfg.cache_path, ignore_errors=True)
                        return False
                    LOGGER.info(f"install.sh executed successfully")
                except Exception as e:
                    LOGGER.error(f"Error executing install.sh: {e}")
                    shutil.rmtree(self.cfg.cache_path, ignore_errors=True)
                    return False

            if has_uninstall and os.name != 'nt':
                LOGGER.info(f"Copying uninstall.sh from {software.name}")
                uninstall_dir = os.path.join(self.cfg.uninstall_path, software.category, software.id)
                os.makedirs(uninstall_dir, exist_ok=True)
                shutil.copyfile(uninstall_script, os.path.join(uninstall_dir, "uninstall.sh"))

            if software.instruction:
                self.show_instruction(software)

            # Update database
            software.installed = True
            software.local_version = software.version
            software.install_path = install_dir
            self.installed_software[software.id] = software
            self.save_installed_software()

            LOGGER.info(f"Successfully installed {software.name}")
            return True

        except Exception as e:
            LOGGER.error(f"Error installing {software.name}: {e}")
            return False

        finally:
            shutil.rmtree(self.cfg.cache_path, ignore_errors=True)

    def uninstall_software(self, software: SoftwarePackage) -> bool:
        """Uninstall software package"""
        try:
            if software.id in self.installed_software:
                # Remove installation directory
                if software.install_path and os.path.exists(software.install_path):
                    shutil.rmtree(software.install_path)

                uninstall_dir = os.path.join(self.cfg.uninstall_path, software.category, software.id)
                uninstall_script = os.path.join(uninstall_dir, "uninstall.sh")
                if os.path.exists(uninstall_script):
                    LOGGER.info(f"Executing uninstall.sh for {software.name}")
                    try:
                        st = os.stat(os.path.join(uninstall_dir, "uninstall.sh"))
                        os.chmod(os.path.join(uninstall_dir, "uninstall.sh"), st.st_mode | 0o111)
                        result = subprocess.run(
                            ["/bin/bash", "uninstall.sh"],
                            cwd=uninstall_dir,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        if result.returncode != 0:
                            LOGGER.error(f"uninstall.sh failed with return code {result.returncode}")
                            LOGGER.error(f"stdout: {result.stdout}")
                            LOGGER.error(f"stderr: {result.stderr}")
                    except Exception as e:
                        LOGGER.error(f"Error uninstalling {software.name}: {e}")
                    finally:
                        os.remove(uninstall_script)

                # Remove from database
                del self.installed_software[software.id]
                self.save_installed_software()

                # Update software list
                for s in self.software_list:
                    if s.id == software.id:
                        s.installed = False
                        s.update_available = False
                        break

                LOGGER.info(f"Successfully uninstalled {software.name}")
                return True
            return False
        except Exception as e:
            LOGGER.error(f"Error uninstalling {software.name}: {e}")
            return False

    def _download_software(self, software: SoftwarePackage, download_path: str) -> bool:
        """Download software package with progress"""

        def progress_hook(block_num: int, block_size: int, total_size: int):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 // total_size)

                    self.ui.clear()
                    self.ui.info_header(
                        self.t.t("Downloading"),
                        f"{software.name} - {software.version}"
                    )

                    # Calculate download speed
                    speed_text = self._calculate_speed(downloaded)
                    size_mb = total_size / (1024 * 1024)
                    downloaded_mb = downloaded / (1024 * 1024)

                    label_bottom = f"{downloaded_mb:.1f}MB / {size_mb:.1f}MB | {speed_text}"

                    self.ui.progress_bar(
                        self.ui.y_size // 2 + 20,
                        percent,
                        label_top=self.t.t("Downloading Software"),
                        label_bottom=label_bottom
                    )

                    self.ui.paint()
            except Exception as e:
                LOGGER.error(f"Error updating progress: {e}")

        try:
            LOGGER.info(f"Downloading {self.cfg.server_url + software.download_url}")
            response = self.session.get(self.cfg.server_url + software.download_url, stream=True, timeout=(60, 300))
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            block_size = 512 * 1024  # 512KB
            downloaded = 0

            with open(download_path, 'wb') as f:
                for data in response.iter_content(block_size):
                    downloaded += len(data)
                    f.write(data)
                    f.flush()

                    # Update progress
                    progress_hook(downloaded // block_size, block_size, total_size)

            return True

        except Exception as e:
            LOGGER.error(f"Error downloading {software.name}: {e}")
            return False

    def _extract_software(self, zip_path: str, extract_path: str, software: SoftwarePackage) -> bool:
        """Extract software package with progress"""
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                file_list = zip_ref.namelist()
                total_files = len(file_list)

                for i, file in enumerate(file_list):
                    zip_ref.extract(file, extract_path)

                    # Update progress
                    percent = (i + 1) * 100 / max(1, total_files)

                    self.ui.clear()
                    self.ui.info_header(
                        self.t.t("Installing"),
                        f"{software.name} - {software.version}"
                    )

                    file_name = os.path.basename(file)
                    if len(file_name) > 30:
                        file_name = file_name[:27] + "..."

                    self.ui.text(
                        (self.ui.x_size // 2, self.ui.y_size // 2 - 20),
                        f"{self.t.t('Extracting')}: {file_name}",
                        font=22, anchor="mm"
                    )

                    progress_text = f"{i + 1} / {total_files} {self.t.t('files')}"
                    self.ui.text(
                        (self.ui.x_size // 2, self.ui.y_size // 2 + 40),
                        progress_text,
                        font=18, anchor="mm", color=self.ui.cfg.COLOR_TEXT_SECONDARY
                    )

                    self.ui.progress_bar(self.ui.y_size // 2 + 10, percent)
                    self.ui.paint()

            return True

        except Exception as e:
            LOGGER.error(f"Error extracting {software.name}: {e}")
            return False

    def _calculate_speed(self, downloaded: int) -> str:
        current_time = time.time()

        if not hasattr(self, '_speed_data'):
            self._speed_data = {
                'start_time': current_time,
                'last_time': current_time,
                'last_downloaded': downloaded,
                'speed_text': "..."
            }

        time_diff = current_time - self._speed_data['last_time']
        if time_diff >= 1.0:
            downloaded_diff = downloaded - self._speed_data['last_downloaded']

            if downloaded_diff < 0:
                self._speed_data['last_downloaded'] = downloaded
                downloaded_diff = 0

            download_speed = downloaded_diff / time_diff if time_diff > 0 else 0

            if download_speed >= 1024 * 1024:
                speed_text = f"{download_speed / (1024 * 1024):.1f} MB/s"
            elif download_speed >= 1024:
                speed_text = f"{download_speed / 1024:.1f} KB/s"
            else:
                speed_text = f"{download_speed:.1f} B/s"

            self._speed_data['last_time'] = current_time
            self._speed_data['last_downloaded'] = downloaded
            self._speed_data['speed_text'] = speed_text

        return self._speed_data['speed_text']

    def show_instruction(self, software: SoftwarePackage) -> None:
        """Show installation instructions for the given software"""
        if software.instruction:
            if hasattr(self, 'ui_helper'):
                self.ui_helper.show_instruction_view(software.name, software.instruction)
            else:
                LOGGER.warning("ui_helper not set, cannot show instruction")



# =========================
# Software Center UI Components
# =========================
class SoftwareCenterUI:
    def __init__(self, manager: SoftwareManager, input_handler: InputHandler):
        self.manager = manager
        self.input = input_handler
        self.ui = manager.ui
        self.t = manager.t
        self.cfg = manager.cfg

        self.current_page = 0
        self.board_info = Path(self.cfg.root_path + "/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
        self.hw_info = self.cfg.board_mapping.get(self.board_info, 5)
        if self.hw_info == 1:
            self.software_per_page = 6
        else:
            self.software_per_page = 4
        self.selected_index = 0

    def draw_main_interface(self) -> None:
        """Draw the main software center interface"""
        self.ui.clear()

        # Header
        self.ui.info_header(
            self.t.t("Software Center"),
            self.t.t("Discover and install amazing applications"),
            cur_app_ver
        )

        # Category tabs
        self.draw_category_tabs()

        if self.manager.search_query:
            software_list = self.manager.search_software(self.manager.search_query)
            title = self.t.t("Search Results")
        else:
            software_list = self.manager.get_software_by_category(self.manager.current_category)
            title = self.get_category_title()

        total_software = len(software_list)
        total_pages = max(1, (total_software + self.software_per_page - 1) // self.software_per_page)

        if self.current_page >= total_pages:
            self.current_page = max(0, total_pages - 1)

        start_idx = self.current_page * self.software_per_page
        end_idx = min(start_idx + self.software_per_page, total_software)
        current_software = software_list[start_idx:end_idx]

        if self.selected_index >= len(current_software):
            self.selected_index = max(0, len(current_software) - 1)

        # Software grid
        self.draw_software_grid(current_software)

        # Page info
        if total_pages > 1:
            page_text = f"{self.current_page + 1}/{total_pages}"
            self.ui.text(
                (self.ui.x_size - 20, 150),
                page_text, font=16, anchor="rm", color=self.ui.cfg.COLOR_TEXT_SECONDARY
            )

        # Bottom actions
        self.draw_bottom_actions()

        self.ui.paint()

    def draw_category_tabs(self) -> None:
        """Draw category navigation tabs"""
        tab_height = 40
        tab_width = self.ui.x_size // len(self.cfg.categories)
        y_pos = 100

        for i, category in enumerate(self.cfg.categories):
            x_start = i * tab_width
            x_end = (i + 1) * tab_width

            is_active = (category == self.manager.current_category)
            tab_color = self.cfg.COLOR_PRIMARY if is_active else self.cfg.COLOR_CARD

            self.ui.rect([x_start, y_pos, x_end, y_pos + tab_height],
                         fill=tab_color, radius=8 if is_active else 0)

            category_name = self.get_category_display_name(category)
            self.ui.text(
                (x_start + tab_width // 2, y_pos + tab_height // 2),
                category_name, font=16, anchor="mm", bold=is_active
            )

    def get_category_display_name(self, category: str) -> str:
        """Get localized category name"""
        category_names = {
            "all": self.t.t("All"),
            "games": self.t.t("Games"),
            "tools": self.t.t("Tools"),
            "emulators": self.t.t("Emulators"),
            "themes": self.t.t("Themes"),
            "other": self.t.t("Other")
        }
        return category_names.get(category, category)

    def get_category_title(self) -> str:
        """Get title for current category"""
        if self.manager.current_category == "installed":
            count = len(self.manager.get_software_by_category("installed"))
            return f"{self.t.t('Installed Software')} ({count})"
        else:
            category_name = self.get_category_display_name(self.manager.current_category)
            count = len(self.manager.get_software_by_category(self.manager.current_category))
            return f"{category_name} ({count})"

    def draw_software_grid(self, software_list: List[SoftwarePackage]) -> None:
        """Draw software grid layout"""

        if not software_list:
            self.draw_empty_state()
            return

        grid_cols = 2
        card_width = (self.ui.x_size - 30) // grid_cols
        card_height = 120
        start_y = 160


        for idx, software in enumerate(software_list):
            row = idx // grid_cols
            col = idx % grid_cols

            x = 10 + col * (card_width + 10)
            y = start_y + row * (card_height + 15)


            is_selected = (idx == self.selected_index)
            self.draw_software_card(software, (x, y, x + card_width, y + card_height), is_selected)

    def draw_software_card(self, software: SoftwarePackage, rect: Tuple[int, int, int, int],
                           selected: bool = False) -> None:
        """Draw individual software card"""
        try:
            x1, y1, x2, y2 = rect

            # Card background with selection highlight
            self.ui.panel([x1, y1, x2, y2], shadow=True)

            if selected:
                self.ui.rect([x1 - 3, y1 - 3, x2 + 3, y2 + 3],
                             outline=self.cfg.COLOR_PRIMARY, width=2, radius=16)

            if x1 < 0 or y1 < 0 or x2 > self.ui.x_size or y2 > self.ui.y_size:
                LOGGER.warning(f"Card coordinates out of bounds: [{x1}, {y1}, {x2}, {y2}]")

            # Software icon placeholder
            card_height = 120
            icon_size = 40
            icon_x = x1 + 25
            icon_y = y1 + (card_height // 2)
            self.ui.circle((icon_x, icon_y), icon_size // 2,
                           fill=self.cfg.COLOR_PRIMARY_DARK, shadow=True)

            # Default icon based on category
            icon_text = self.get_category_icon(software.category)["txt"]
            self.ui.text((icon_x + 1, icon_y), icon_text, font=25, anchor="mm",
                         color=self.cfg.COLOR_TEXT)

            # Software info
            info_x = icon_x + icon_size - 10
            max_name_width = x2 - info_x - 10

            # Software name (truncate if too long)
            name = software.name
            name_width = self.ui.active_draw.textlength(name, font=ImageFont.truetype(self.cfg.font_file, 18))
            if name_width > max_name_width:
                while name and self.ui.active_draw.textlength(name + "...", font=ImageFont.truetype(self.cfg.font_file,
                                                                                                    18)) > max_name_width:
                    name = name[:-1]
                name = name + "..."

            self.ui.text((info_x, y1 + 20), name, font=18, bold=True)

            # Description (truncated)
            desc = software.description
            if len(desc) > 17:
                desc = desc[:14] + "..."
            self.ui.text((info_x, y1 + 45), desc, font=15,
                         color=self.cfg.COLOR_TEXT_SECONDARY)

            # Version and size
            size_mb = software.size // (1024 * 1024)
            info_text = f"v{software.version} • {size_mb}MB" if software.version else  f"{size_mb}MB"
            self.ui.text((info_x, y1 + 70), info_text, font=14,
                         color=self.cfg.COLOR_TEXT_TERTIARY)

            # Install status button
            button_width = 80
            button_x = x2 - button_width - 10
            button_y = y2 - 30

            if software.installed:
                uninstall_dir = os.path.join(self.cfg.uninstall_path, software.category, software.id)
                uninstall_script = os.path.join(uninstall_dir, "uninstall.sh")
                if software.update_available:
                    self.ui.button([button_x, button_y, x2 - 5, y2 - 5],
                                   self.t.t("Update"), "A", primary=True, type=1)
                elif not os.path.exists(uninstall_script):
                    self.ui.button([button_x, button_y, x2 - 5, y2 - 5],
                               self.t.t("REINST"), "A", disabled=True, type=1)
                else:
                    self.ui.button([button_x, button_y, x2 - 5, y2 - 5],
                                   self.t.t("UNINST"), "A", disabled=True, type=1)
            else:
                self.ui.button([button_x, button_y, x2 - 5, y2 - 5],
                               self.t.t("INST"), "A", primary=selected, type=1)
        except Exception as e:
            LOGGER.error(f"Error drawing software card {software.name}: {e}")

    def get_category_icon(self, category: str, id: str = None, icon_url: str = None) -> dict:
        """Get icon for software category"""
        icons = {
            "games": "✈",
            "tools": "☢",
            "emulators": "☸",
            "themes": "☯"
        }

        if id is None or icon_url is None or icon_url == "":
            return {"txt": icons.get(category, "☆")}
        else:
            try:
                icon_path = os.path.join(self.cfg.screenshots_path, id, icon_url)
                if os.path.exists(icon_path):
                    return {"icon": icon_path}
                else:
                    return {"txt": icons.get(category, "☆")}
            except Exception as e:
                return {"txt": icons.get(category, "☆")}

    def draw_empty_state(self) -> None:
        """Draw empty state when no software available"""
        center_x, center_y = self.ui.x_size // 2, self.ui.y_size // 2

        self.ui.text((center_x, center_y - 40), "☆", font=48, anchor="mm")
        self.ui.text((center_x, center_y + 20), self.t.t("No software available"),
                     font=22, anchor="mm", bold=True)
        self.ui.text((center_x, center_y + 50),
                     self.t.t("Check your internet connection or try another category"),
                     font=16, anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)

    def draw_bottom_actions(self) -> None:
        """Draw bottom action buttons"""
        button_y = self.ui.y_size - 50
        button_width = 160
        button_height = 36

        # Navigation buttons
        page_x = 20
        self.ui.button([page_x, button_y, page_x + button_width, button_y + button_height],
                       self.t.t("Page"), "L1/R1", False)
        group_x = self.ui.x_size // 2 - button_width // 2
        self.ui.button([group_x, button_y, group_x + button_width, button_y + button_height],
                       self.t.t("Group"), "L2/R2", False)

        exit_x = self.ui.x_size - button_width - 20
        self.ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                           self.t.t("Exit"), "SE", False)

    def draw_software_detail(self, software: SoftwarePackage) -> None:
        """Draw software detail view"""
        self.ui.clear()

        # Header with back button
        self.ui.info_header(software.name, self.t.t("Software Details"))

        content_top = 100
        panel_width = self.ui.x_size - 40
        panel_height = self.ui.y_size - content_top - 80

        self.ui.panel([20, content_top, 20 + panel_width, content_top + panel_height],
                      title=None, shadow=True, accent=True)

        # Software icon and basic info
        icon_x = 70
        icon_y = content_top + 55
        icon_size = 60

        icon_file = self.get_category_icon(software.category, software.id, software.icon_url)
        for key, value in icon_file.items():
            if key == "txt":
                self.ui.circle((icon_x, icon_y), icon_size // 2,
                               fill=self.cfg.COLOR_PRIMARY_DARK, shadow=True)
                self.ui.text((icon_x, icon_y), value,
                             font=24, anchor="mm", color=self.cfg.COLOR_TEXT)
            elif key == "icon":
                self.ui.display_image(value, icon_x - icon_size // 2, icon_y - icon_size // 2, icon_size, icon_size)

        # Software details
        detail_x = icon_x + icon_size - 20
        self.ui.text((detail_x, content_top + 18), software.name, font=22, bold=True)
        self.ui.text((detail_x, content_top + 50), f"v{software.version}" if software.version else "", font=16,
                     color=self.cfg.COLOR_TEXT_SECONDARY)

        author_text = f"by {software.author}" if software.author else self.t.t("Unknown Author")
        self.ui.text((detail_x, content_top + 75), author_text, font=14,
                     color=self.cfg.COLOR_TEXT_TERTIARY)

        if software.screenshots:
            screenshot = software.screenshots[0]
            screenshot_path = os.path.join(self.cfg.screenshots_path, software.id, screenshot)
        else:
            screenshot_path = os.path.join(self.cfg.screenshots_path, "default.png")
        if not os.path.exists(screenshot_path):
            screenshot_path = os.path.join(self.cfg.screenshots_path, "default.png")

        try:
            img = Image.open(screenshot_path)
            ratio = img.size[1] / img.size[0]
            target_x = int(30 + panel_width // 2)
            target_width = int(panel_width // 2 - 30)
            target_height = int(target_width * ratio)
            target_y = int(content_top + panel_height - target_height -15)
            self.ui.display_image(screenshot_path, target_x, target_y, target_width, target_height)
        except Exception as e:
            LOGGER.error(f"Failed to load screenshot {screenshot_path}: {e}")

        # Description
        desc_y = content_top + 100
        desc_width = panel_width // 2 - 20
        wrapped_desc = self.wrap_text(software.description, 19, desc_width)

        available_lines = 8
        display_lines = wrapped_desc[:available_lines]

        for i, line in enumerate(display_lines):
            if i == available_lines - 1:
                line = line[:-3] + "..."
            self.ui.text((40, desc_y + i * 25), line, font=19,
                         color=self.cfg.COLOR_TEXT_SECONDARY)

        # Installation info
        info_y = content_top + 20
        size_mb = software.size // (1024 * 1024) if software.size >= 1024 * 1024 else software.size // 1024
        unit = "MB" if software.size >= 1024 * 1024 else "KB"
        font_size = 19
        try:
            font = ImageFont.truetype(self.cfg.font_file, font_size)
        except:
            font = ImageFont.load_default()

        size_text = f"{self.t.t('Size')}: {size_mb}{unit}"
        cat_text = f"{self.t.t('Category')}: {self.get_category_display_name(software.category)}"

        size_width = self.ui.active_draw.textlength(size_text, font=font)
        cat_width = self.ui.active_draw.textlength(cat_text, font=font)

        right_start_x = int(30 + panel_width // 2)
        right_end_x = self.ui.x_size - 30
        available_width = right_end_x - right_start_x

        if size_width + cat_width + 10 <= available_width:
            self.ui.text((right_start_x, info_y), size_text, font=font_size)
            self.ui.text((right_start_x + size_width + 10, info_y), cat_text, font=font_size)
        else:
            self.ui.text((right_start_x, info_y), size_text, font=font_size)
            self.ui.text((right_start_x, info_y + 20), cat_text, font=font_size)

        if software.changelog:
            changelog_y = info_y + 20
            right_start_x = 30 + panel_width // 2
            right_end_x = self.ui.x_size - 30
            right_width = right_end_x - right_start_x
            changelog_info = f"{self.t.t('Changelog')}: {software.changelog}"
            wrapped_desc = self.wrap_text(changelog_info, 16, right_width)

            available_lines = 3
            display_lines = wrapped_desc[:available_lines]

            for i, line in enumerate(display_lines):
                if i == available_lines - 1:
                    line = line[:-3] + "..."
                self.ui.text((int(30 + panel_width // 2), changelog_y + i * 25), line, font=16,
                             color=self.cfg.COLOR_TEXT_SECONDARY)

        # Install button
        button_y = self.ui.y_size - 60
        button_width = 200
        button_x = (self.ui.x_size - button_width) // 2
        app_x = button_x + 180
        back_x = self.ui.x_size - button_width + 20

        if software.installed:
            uninstall_dir = os.path.join(self.cfg.uninstall_path, software.category, software.id)
            uninstall_script = os.path.join(uninstall_dir, "uninstall.sh")
            if software.update_available:
                self.ui.button([button_x, button_y, button_x + button_width, button_y + 40],
                               self.t.t('Update'), "A", True)
            elif not os.path.exists(uninstall_script):
                self.ui.button([button_x, button_y, button_x + button_width, button_y + 40],
                               self.t.t("Reinstall"), "A", False)
            else:
                # Uninstall button
                self.ui.button([button_x, button_y, button_x + button_width, button_y + 40],
                               self.t.t("Uninstall"), "Y", False)
        else:
            self.ui.button([button_x, button_y, button_x + button_width, button_y + 40],
                           f"{self.t.t('Install')} ({size_mb}{unit})", "A", True, type=2)

        # Back button
        self.ui.button([back_x, button_y, back_x + 120, button_y + 40],
                       self.t.t("Back"), "B", False)

        self.ui.paint()

        LOGGER.info(f"Displayed software detail: {software.name}")

    def wrap_text(self, text: str, font_size: int, max_width: int) -> List[str]:
        try:
            font = ImageFont.truetype(self.cfg.font_file, font_size)
        except:
            font = ImageFont.load_default()

        paragraphs = text.split('\n')
        lines = []

        for para in paragraphs:
            if not para:
                lines.append('')
                continue

            words = para.split()
            if not words:
                lines.append('')
                continue

            current_line = []
            for word in words:
                test_word = word
                while True:
                    bbox = self.ui.active_draw.textbbox((0, 0), test_word, font=font)
                    word_width = bbox[2] - bbox[0]
                    if word_width <= max_width or len(test_word) <= 1:
                        break
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = []
                    low, high = 1, len(test_word)
                    while low < high:
                        mid = (low + high + 1) // 2
                        part = test_word[:mid]
                        bbox = self.ui.active_draw.textbbox((0, 0), part, font=font)
                        part_width = bbox[2] - bbox[0]
                        if part_width <= max_width:
                            low = mid
                        else:
                            high = mid - 1
                    lines.append(test_word[:low])
                    test_word = test_word[low:].lstrip()

                test_line = ' '.join(current_line + [test_word]) if current_line else test_word
                bbox = self.ui.active_draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
                if line_width <= max_width:
                    current_line.append(test_word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [test_word]
            if current_line:
                lines.append(' '.join(current_line))
        return lines

    def draw_search_interface(self) -> None:
        """Draw search interface"""
        self.ui.clear()
        self.ui.info_header(self.t.t("Search Software"), self.t.t("Enter software name"))

        # Search box
        search_box = [50, 120, self.ui.x_size - 50, 170]
        self.ui.panel(search_box, shadow=True)
        self.ui.text((60, 145), f"{self.t.t('Search')}: {self.manager.search_query}",
                     font=20, anchor="lm")

        # Search results
        if self.manager.search_query:
            results = self.manager.search_software(self.manager.search_query)
            results = results[
                self.current_page * self.software_per_page:(self.current_page + 1) * self.software_per_page]
            self.draw_software_grid(results)

        # Bottom actions
        button_y = self.ui.y_size - 50
        button_width = 140
        button_height = 36

        clear_x = 20
        self.ui.button([clear_x, button_y, clear_x + button_width, button_y + button_height],
                       self.t.t("Clear"), "Y", False)

        back_x = self.ui.x_size - button_width - 20
        self.ui.button([back_x, button_y, back_x + button_width, button_y + button_height],
                       self.t.t("Back"), "B", False)

    def draw_message(self, title: str, message: str, message_type: str = "info", button: bool = True) -> None:
        """Draw message dialog"""
        self.ui.clear()

        # Determine icon and color based on message type
        icons = {
            "info": "♥",
            "success": "♠",
            "warning": "♣",
            "error": "♦"
        }

        colors = {
            "info": self.cfg.COLOR_PRIMARY,
            "success": self.cfg.COLOR_SUCCESS,
            "warning": self.cfg.COLOR_WARNING,
            "error": self.cfg.COLOR_DANGER
        }

        icon = icons.get(message_type, "♥")
        color = colors.get(message_type, self.cfg.COLOR_PRIMARY)

        # Message panel
        panel_width = min(self.ui.x_size - 100, 500)
        panel_height = 200
        panel_x = (self.ui.x_size - panel_width) // 2
        panel_y = (self.ui.y_size - panel_height) // 2

        self.ui.panel([panel_x, panel_y, panel_x + panel_width, panel_y + panel_height],
                      shadow=True, accent=True)

        # Icon and text
        self.ui.text((self.ui.x_size // 2, panel_y + 40), icon, font=48, anchor="mm")
        self.ui.text((self.ui.x_size // 2, panel_y + 90), title, font=24,
                     anchor="mm", bold=True)
        self.ui.text((self.ui.x_size // 2, panel_y + 120), message, font=18,
                     anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)

        # OK button
        if button:
            button_width = 120
            button_x = (self.ui.x_size - button_width) // 2
            button_y = panel_y + panel_height - 50

            self.ui.button([button_x, button_y, button_x + button_width, button_y + 40],
                       self.t.t("OK"), "A", True)

        self.ui.paint()

    def show_instruction_view(self, name: str, content: str) -> None:
        """Display installation instructions with scroll support"""
        lines = self.wrap_text(content, 16, self.ui.x_size - 80)
        scroll_offset = 0

        start_y = 120
        line_height = 25
        bottom_hint = 70
        max_lines = (self.ui.y_size - start_y - bottom_hint) // line_height
        max_scroll = max(0, len(lines) - max_lines)

        while True:
            self.ui.clear()

            self.ui.info_header(name, self.t.t("Prompt message"))

            visible = lines[scroll_offset:scroll_offset + max_lines]
            y = start_y
            for line in visible:
                self.ui.text((40, y), line, font=16, color=self.cfg.COLOR_TEXT_SECONDARY)
                y += line_height

            hint_text = f"{self.t.t('Up/Down: Scroll')}  |  B: {self.t.t('Back')}"
            self.ui.text((self.ui.x_size // 2, self.ui.y_size - 15), hint_text,
                         font=18, anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)
            self.ui.paint()

            self.input.poll()
            if self.input.is_key("B"):
                break
            elif self.input.is_key("DY"):
                direction = int(self.input.value)
                new_offset = scroll_offset + (1 if direction == 1 else -1)
                scroll_offset = max(0, min(max_scroll, new_offset))
            elif self.input.is_key("L1"):
                scroll_offset = max(0, scroll_offset - max_lines)
            elif self.input.is_key("R1"):
                scroll_offset = min(max_scroll, scroll_offset + max_lines)

            self.input.reset()
            time.sleep(0.05)

# =========================
# Main Software Center Application
# =========================
class SoftwareCenterApp:
    def __init__(self):
        self.cfg = Config()

        # Detect hardware and language
        try:
            board_info = Path(self.cfg.root_path + "/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
            LOGGER.info("Detected board: %s", board_info)
        except (FileNotFoundError, IndexError) as e:
            LOGGER.warning("Board detection failed: %s, using default RG35xxH", e)
            board_info = "RG35xxH"
        self.board_info = board_info

        try:
            lang_index_raw = Path(self.cfg.root_path + "/mnt/vendor/oem/language.ini").read_text().splitlines()[0]
            lang_index = int(lang_index_raw)
            LOGGER.info("Detected language index: %s", lang_index)
        except (FileNotFoundError, IndexError, ValueError) as e:
            LOGGER.warning("Language detection failed: %s, using default index 2", e)
            lang_index = 2

        self.hw_info = self.cfg.board_mapping.get(self.board_info, 5)
        self.system_lang = self.cfg.system_list[lang_index if 0 <= lang_index < len(self.cfg.system_list) else 2]
        LOGGER.info("Hardware info: %s, System language: %s", self.hw_info, self.system_lang)

        self.t = Translator(self.system_lang)
        self.ui = UIRenderer(self.cfg, self.t, self.hw_info)
        self.input = InputHandler(self.cfg)
        self.manager = SoftwareManager(self.cfg, self.ui, self.t)
        self.ui_helper = SoftwareCenterUI(self.manager, self.input)
        self.manager.ui_helper = self.ui_helper

        self.skip_first_input = True
        self.running = True

    def run(self) -> None:
        """Main application loop"""
        self.ui.draw_loading_screen(
            self.t.t("Software Center"),
            self.t.t("Loading software catalog...")
        )

        if not self.check_network():
            self.ui_helper.draw_message(
                self.t.t("No Internet Connection"),
                self.t.t("Please check your network settings and try again"),
                "error"
            )
            self.wait_for_input()
            self.cleanup()
            return

        self.update_assets()

        self.ui.draw_loading_screen(
            self.t.t("Loading Software"),
            self.t.t("Fetching software catalog from repositories...")
        )

        if not self.manager.fetch_software_list():
            self.ui_helper.draw_message(
                self.t.t("Connection Error"),
                self.t.t("Failed to load software catalog"),
                "error"
            )
            self.wait_for_input()
            self.cleanup()
            return

        while self.running:
            try:
                if self.manager.selected_software:
                    self.show_software_detail()
                else:
                    self.show_main_interface()

                time.sleep(0.05)

            except Exception as e:
                LOGGER.error("Error in main loop: %s", e)
                self.ui_helper.draw_message(
                    self.t.t("Error"),
                    self.t.t("An unexpected error occurred"),
                    "error"
                )
                self.wait_for_input()
                break

        self.cleanup()

    def check_network(self) -> bool:
        """Check network connectivity"""
        test_servers = [
            ("8.8.8.8", 53),
            ("1.1.1.1", 53),
            ("223.5.5.5", 53),
        ]
        try:
            socket.gethostbyname("github.com")
            LOGGER.info("DNS resolution successful")
            return True
        except socket.gaierror:
            LOGGER.warning("DNS resolution failed")

        for host, port in test_servers:
            try:
                socket.setdefaulttimeout(3)
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((host, port))
                s.close()
                LOGGER.info("Network connection test passed with %s:%s", host, port)
                return True
            except (socket.timeout, socket.error) as e:
                LOGGER.warning("Connection test failed for %s:%s: %s", host, port, e)
                continue

        LOGGER.error("All network connection tests failed")
        return False

    def update_assets(self) -> None:
        try:
            base_url = self.cfg.server_url
            remote_ver_url = base_url + "assets_version.txt"
            remote_zip_url = base_url + "assets.zip"

            local_ver_file = self.cfg.root_path + "/mnt/mod/ctrl/configs/software_center/assets_version.txt"
            target_dir = self.cfg.root_path + "/mnt/mod/ctrl/configs/software_center"

            local_ver = assets_date
            if os.path.exists(local_ver_file):
                with open(local_ver_file, 'r', encoding='utf-8') as f:
                    stored_ver = f.read().strip()
                    if stored_ver:
                        local_ver = stored_ver
            LOGGER.info(f"Local assets version: {local_ver}")

            try:
                resp = requests.get(remote_ver_url, timeout=5)
                if resp.status_code != 200:
                    LOGGER.warning(f"Failed to fetch remote assets version: HTTP {resp.status_code}")
                    return
                remote_ver = resp.text.strip()
                LOGGER.info(f"Remote assets version: {remote_ver}")
            except Exception as e:
                LOGGER.error(f"Error fetching remote assets version: {e}")
                return

            if remote_ver == local_ver:
                LOGGER.info("Assets are up to date")
                return

            LOGGER.info(f"New assets version available: {remote_ver}, downloading...")

            os.makedirs(self.cfg.cache_path, exist_ok=True)
            zip_path = os.path.join(self.cfg.cache_path, "assets.zip")
            try:
                resp = requests.get(remote_zip_url, stream=True, timeout=30)
                resp.raise_for_status()
                total_size = int(resp.headers.get('content-length', 0))
                downloaded = 0
                with open(zip_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        downloaded += len(chunk)
                        f.write(chunk)
                        if total_size:
                            percent = downloaded * 100 // total_size
                            LOGGER.debug(f"Downloading assets: {percent}%")
                LOGGER.info("Assets.zip downloaded successfully")
            except Exception as e:
                LOGGER.error(f"Failed to download assets.zip: {e}")
                return

            try:
                os.makedirs(target_dir, exist_ok=True)
                with zipfile.ZipFile(zip_path, 'r') as zf:
                    zf.extractall(target_dir)
                LOGGER.info(f"Assets extracted to {target_dir}")
            except Exception as e:
                LOGGER.error(f"Failed to extract assets.zip: {e}")
                return
            finally:
                if os.path.exists(zip_path):
                    os.remove(zip_path)

            try:
                with open(local_ver_file, 'w', encoding='utf-8') as f:
                    f.write(remote_ver)
                LOGGER.info(f"Local assets version updated to {remote_ver}")
            except Exception as e:
                LOGGER.error(f"Failed to write local version file: {e}")

        except Exception as e:
            LOGGER.error(f"Unexpected error in update_assets: {e}")

    def show_main_interface(self) -> None:
        """Show main software center interface"""
        self.ui_helper.draw_main_interface()
        self.handle_main_input()

    def handle_main_input(self) -> None:
        """Handle input on main interface"""
        if self.skip_first_input:
            self.input.reset()
            self.skip_first_input = False
            return

        self.input.poll()

        if self.input.code_name:
            LOGGER.info(f"Main interface - Key: {self.input.code_name}, Value: {self.input.value}")

        if self.input.is_key("SELECT"):
            self.running = False
            return

        elif self.input.is_key("L1"):
            # Previous page
            software_list = self.manager.get_software_by_category(self.manager.current_category)
            total_pages = max(1, (
                        len(software_list) + self.ui_helper.software_per_page - 1) // self.ui_helper.software_per_page)
            if self.ui_helper.current_page > 0:
                self.ui_helper.current_page -= 1
            else:
                self.ui_helper.current_page = total_pages
            self.ui_helper.selected_index = 0

        elif self.input.is_key("R1"):
            # Next page
            software_list = self.manager.get_software_by_category(self.manager.current_category)
            total_pages = max(1, (
                        len(software_list) + self.ui_helper.software_per_page - 1) // self.ui_helper.software_per_page)
            if self.ui_helper.current_page < total_pages - 1:
                self.ui_helper.current_page += 1
            else:
                self.ui_helper.current_page = 0
            self.ui_helper.selected_index = 0

        # Category navigation
        elif self.input.is_key("L2"):
            categories = list(self.cfg.categories)
            current_index = categories.index(self.manager.current_category)
            if current_index > 0:
                self.manager.current_category = categories[current_index - 1]
            else:
                self.manager.current_category = categories[-1]
            self.ui_helper.current_page = 0
            self.ui_helper.selected_index = 0

        elif self.input.is_key("R2"):
            categories = list(self.cfg.categories)
            current_index = categories.index(self.manager.current_category)
            if current_index < len(categories) - 1:
                self.manager.current_category = categories[current_index + 1]
            else:
                self.manager.current_category = categories[0]
            self.ui_helper.current_page = 0
            self.ui_helper.selected_index = 0

        # Software selection
        elif self.input.is_key("DY"):
            software_list = self.get_current_software_list()
            if software_list:
                direction = int(self.input.value)
                self.ui_helper.selected_index = (self.ui_helper.selected_index + 2 * direction) % len(software_list)

        elif self.input.is_key("DX"):
            software_list = self.get_current_software_list()
            if software_list:
                direction = int(self.input.value)
                if self.ui_helper.selected_index % 2 == 1:
                    new_index = self.ui_helper.selected_index - 1
                    if new_index >= 0:
                        self.ui_helper.selected_index = new_index
                else:
                    new_index = self.ui_helper.selected_index + 1
                    if new_index < len(software_list):
                        self.ui_helper.selected_index = new_index

        # Install/View details
        elif self.input.is_key("A"):
            software_list = self.get_current_software_list()
            if self.ui_helper.selected_index < len(software_list):
                software = software_list[self.ui_helper.selected_index]
                self.manager.selected_software = software

        # Show installed software info
        elif self.input.is_key("Y"):
            software_list = self.get_current_software_list()
            if self.ui_helper.selected_index < len(software_list):
                software = software_list[self.ui_helper.selected_index]
                if software.installed:
                    self.show_software_detail()

        self.input.reset()

    def get_current_software_list(self) -> List[SoftwarePackage]:
        """Get current page software list"""
        if self.manager.search_query:
            software_list = self.manager.search_software(self.manager.search_query)
        else:
            software_list = self.manager.get_software_by_category(self.manager.current_category)

        start_idx = self.ui_helper.current_page * self.ui_helper.software_per_page
        end_idx = start_idx + self.ui_helper.software_per_page

        start_idx = int(start_idx)
        end_idx = int(end_idx)

        return software_list[start_idx:end_idx]

    def show_software_detail(self) -> None:
        """Show software detail view"""
        if not self.manager.selected_software:
            LOGGER.warning("No software selected for detail view")
            return

        LOGGER.info(f"Showing detail for: {self.manager.selected_software.name}")

        self.input.reset()
        self.skip_first_input = True

        while self.manager.selected_software and self.running:
            self.ui_helper.draw_software_detail(self.manager.selected_software)
            self.handle_detail_input()
            time.sleep(0.05)

        LOGGER.info("Exited detail view")

    def handle_detail_input(self) -> None:
        """Handle input on detail view"""
        if self.skip_first_input:
            self.input.reset()
            self.skip_first_input = False
            return

        self.input.poll()

        if not self.input.code_name:
            return

        software = self.manager.selected_software
        if not software:
            LOGGER.warning("No software selected in detail view")
            return

        LOGGER.info(f"Detail view - Key: {self.input.code_name}, Value: {self.input.value}")

        try:
            if self.input.is_key("B"):
                LOGGER.info("Exiting detail view - B button pressed")
                self.manager.selected_software = None
                return

            elif self.input.is_key("A"):
                LOGGER.info(f"A button pressed for {software.name}")
                if software.installed:
                    if software.update_available:
                        self.perform_software_update(software)
                    else:
                        self.install_software_from_detail(software)
                else:
                    self.install_software_from_detail(software)

            elif self.input.is_key("Y") and software.installed and not software.update_available:
                LOGGER.info(f"Y button pressed for uninstalling {software.name}")
                self.uninstall_software_from_detail(software)

        except Exception as e:
            LOGGER.error(f"Error handling detail input: {e}")
        finally:
            self.input.reset()

    def perform_software_update(self, software: SoftwarePackage) -> None:
        """Perform software update from detail view"""
        self.ui_helper.draw_message(
            self.t.t("Updating"),
            f"{self.t.t('Updating')} {software.name}...",
            "info"
        )
        self.ui.paint()

        if self.manager.install_software(software):
            self.ui_helper.draw_message(
                self.t.t("Update Complete"),
                f"{software.name} {self.t.t('has been updated to version')} {software.version}",
                "success"
            )
        else:
            self.ui_helper.draw_message(
                self.t.t("Update Failed"),
                f"{self.t.t('Failed to update')} {software.name}",
                "error"
            )
        self.wait_for_input()
        self.ui_helper.draw_software_detail(software)

    def install_software_from_detail(self, software: SoftwarePackage) -> None:
        """Install software from detail view"""
        self.ui_helper.draw_message(
            self.t.t("Installing"),
            f"{self.t.t('Installing')} {software.name}...",
            "info", button=False
        )
        self.ui.paint()

        if self.manager.install_software(software):
            self.ui_helper.draw_message(
                self.t.t("Installation Complete"),
                f"{software.name} {self.t.t('has been installed successfully')}",
                "success"
            )
        else:
            self.ui_helper.draw_message(
                self.t.t("Installation Failed"),
                f"{self.t.t('Failed to install')} {software.name}",
                "error"
            )
        self.wait_for_input()
        self.ui_helper.draw_software_detail(software)

    def uninstall_software_from_detail(self, software: SoftwarePackage) -> None:
        """Uninstall software from detail view"""
        self.ui_helper.draw_message(
            self.t.t("Uninstalling"),
            f"{self.t.t('Uninstalling')} {software.name}...",
            "warning"
        )
        self.ui.paint()

        if self.manager.uninstall_software(software):
            self.ui_helper.draw_message(
                self.t.t("Uninstallation Complete"),
                f"{software.name} {self.t.t('has been uninstalled')}",
                "success"
            )
        else:
            self.ui_helper.draw_message(
                self.t.t("Uninstallation Failed"),
                f"{self.t.t('Failed to uninstall')} {software.name}",
                "error"
            )
        self.wait_for_input()
        self.ui_helper.draw_software_detail(software)

    def launch_software(self, software: SoftwarePackage) -> None:
        """Launch software application"""
        self.ui_helper.draw_message(
            self.t.t("Launching"),
            f"{self.t.t('Launching')} {software.name}...",
            "info"
        )
        self.wait_for_input()

    def wait_for_input(self) -> None:
        """Wait for any input"""
        LOGGER.info("Waiting for input...")
        self.input.reset()
        start_time = time.time()

        while True:
            self.input.poll()
            if self.input.code_name and self.input.value == 1:
                LOGGER.info(f"Input received: {self.input.code_name}")
                break

            if time.time() - start_time > 30:  # 30秒超时
                LOGGER.warning("Input wait timeout")
                break

            time.sleep(0.05)

    def cleanup(self, code=0) -> None:
        """Cleanup resources"""
        LOGGER.info(f"Cleaning up resources, Exiting whout {code}")
        try:
            import sdl2
            sdl2.SDL_Quit()
        except Exception as e:
            LOGGER.warning("Error cleaning up SDL: %s", e)
        try:
            self.ui.draw_end()
            delete_path = {
                self.cfg.cache_path,
                self.cfg.cache_dir
            }
            for path in delete_path:
                if os.path.isfile(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)

            sys.exit(code)
        except Exception as e:
            LOGGER.error("Error during cleanup: %s", e)


# =========================
# Entrypoint
# =========================
if __name__ == "__main__":
    try:
        SoftwareCenterApp().run()
    except KeyboardInterrupt:
        LOGGER.info("Program interrupted by user")
    except Exception as e:
        LOGGER.error("Unexpected error: %s", e)
