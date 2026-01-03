#!/usr/bin/env python3

"""
Stock OS Mod Updater - Professional Edition
Enhanced UI Version
"""

from __future__ import annotations

# =========================
# Standard Library Imports
# =========================
import ctypes
import hashlib
import json
import logging
import math
import os
import shutil
import socket
import struct
import sys
import time
import zipfile
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.error import ContentTooShortError, URLError

# =========================
# Third-Party Imports
# =========================
from PIL import Image, ImageDraw, ImageFont

cur_app_ver = "2.0.0"
base_ver = "3.8.0"
base_date = "20250211"
source = "source/"

# =========================
# Logging Setup
# =========================
APP_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_PATH, "update.log")
log_delete = 1
if log_delete and os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
LOGGER = logging.getLogger("upgrade")
LOGGER.info(f">>>")
LOGGER.info(f"=== Start Log ===")

def read_current_os_version() -> str:
    try:
        os_ver_cfg_path: str = "/mnt/vendor/oem/version.ini"
        ver_file = Path(os_ver_cfg_path)
        if ver_file.exists():
            ver = ver_file.read_text().splitlines()[0]
            LOGGER.info("Current OS Date version: %s", ver)
            return ver
        LOGGER.warning(f"OS Date version file not found: {ver_file}")
    except Exception as e:
        LOGGER.error("Error reading OS Date version file: %s", e)
    return "Unknown"

os_cur_ver = read_current_os_version()
if os_cur_ver >= "20251206":
    base_ver = "3.9.0"
    base_date = "20251206"
    source = "390/"

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
    import urllib3
    from urllib3.util import Retry
    from requests.adapters import HTTPAdapter
    import sdl2

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
    COLOR_PRIMARY: str = "#6366f1"  # Modern indigo
    COLOR_PRIMARY_LIGHT: str = "#818cf8"  # Light indigo
    COLOR_PRIMARY_DARK: str = "#4f46e5"  # Dark indigo
    COLOR_SECONDARY: str = "#f59e0b"  # Amber
    COLOR_ACCENT: str = "#10b981"  # Emerald
    COLOR_DANGER: str = "#ef4444"  # Red
    COLOR_SUCCESS: str = "#22c55e"  # Green
    COLOR_WARNING: str = "#f59e0b"  # Amber

    # Enhanced Background Colors
    COLOR_BG: str = "#0f172a"  # Dark blue-gray
    COLOR_BG_LIGHT: str = "#1e293b"  # Light blue-gray
    COLOR_BG_GRADIENT: str = "#1e1b4b"  # Gradient start

    # Enhanced Card Colors
    COLOR_CARD: str = "#1e293b"  # Card background
    COLOR_CARD_LIGHT: str = "#334155"  # Light card
    COLOR_CARD_HOVER: str = "#475569"  # Card hover state

    # Enhanced Text Colors
    COLOR_TEXT: str = "#f8fafc"  # Pure white
    COLOR_TEXT_SECONDARY: str = "#cbd5e1"  # Light gray
    COLOR_TEXT_TERTIARY: str = "#94a3b8"  # Medium gray

    # Enhanced Border and Effects
    COLOR_BORDER: str = "#334155"  # Border
    COLOR_BORDER_LIGHT: str = "#475569"  # Light border
    COLOR_SHADOW: str = "#020617"  # Deep shadow
    COLOR_OVERLAY: str = "#00000099"  # Semi-transparent overlay
    COLOR_GLOW: str = "#6366f155"  # Glow effect

    # Enhanced Button Colors
    COLOR_BUTTON_PRIMARY: str = "#4f46e5"  # Primary button
    COLOR_BUTTON_SECONDARY: str = "#475569"  # Secondary button
    COLOR_BUTTON_HOVER: str = "#6366f1"  # Button hover

    font_file: str = os.path.join(APP_PATH, "font", "font.ttf")
    if not os.path.exists(font_file):
        font_file: str = "/mnt/vendor/bin/default.ttf"

    ver_cfg_path: str = "/mnt/mod/ctrl/configs/ver.cfg"

    tmp_app_update: str = "/tmp/app.tar.gz"
    target_path: str = ""

    tmp_list = [
        "/dev/shm",
        "/tmp",
        "/mnt/mmc",
        "/mnt/sdcard"
    ]

    free_space = []
    for tmp in tmp_list:
        if os.path.exists(tmp):
            usage = shutil.disk_usage(tmp)
            free_num = usage.free + 1 if tmp == "/tmp" else usage.free
            free_space.append((free_num, tmp))
    free_space.sort(key=lambda x: x[0], reverse=True)
    tmp_path: str = free_space[0][1] if free_space[0][1] else "/tmp"
    LOGGER.info(f"Use the temporary download path: {tmp_path}")

    tmp_info: str = os.path.join(tmp_path, "info.json")
    tmp_update: str = os.path.join(tmp_path, "append.zip")

    bytes_per_pixel: int = 4
    keymap: Dict[int, str] = None

    retry_config = {
        'total': 3,
        'backoff_factor': 0.5,
        'status_forcelist': [500, 502, 503, 504],
        'allowed_methods': ['GET', 'HEAD']
    }

    mirrors = [
        {
            "name": "GitHub",
            "url": "https://github.com/cbepx-me/upgrade/releases/download/source/update_info.json",
            "region": "Global"
        },
        {
            "name": "GitCode (China)",
            "url": "https://gitcode.com/cbepx/upgrade/releases/download/source/update_info.json",
            "region": "CN"
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
            requests.head(mirror["url"], timeout=3, headers=headers)
            end = time.time() - start
        except:
            end = float('inf')
        speeds.append((end, mirror))
    speeds.sort(key=lambda x: x[0])
    info_url = speeds[0][1]["url"] if speeds[0][0] != float('inf') else fallback_mirror["url"]
    server_url = info_url[:-23] + source
    info_url = server_url + "update_info.json"
    LOGGER.info(f"Use the downloaded server: {server_url}")

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
            1: (720, 720, 18),
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
# Translator (mostly preserved)
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

    def poll(self) -> None:
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
# Enhanced UI Renderer
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

        self.button_y = self.y_size - 40
        self.button_x = self.x_size - 120

        if self._initialized:
            return
        self.window = self._create_window()
        self.renderer = self._create_renderer()
        self.opt_stretch = True
        self._initialized = True

        self._draw_start()
        self.screen_reset()
        self.set_active(self.create_image())

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
        window = sdl2.SDL_CreateWindow(
            "RomM".encode("utf-8"),
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

    def rect(self, xy, fill=None, outline=None, width: int = 1, radius: int = 0, shadow: bool = False) -> None:
        if shadow and radius > 0:
            shadow_xy = [xy[0] + 2, xy[1] + 2, xy[2] + 2, xy[3] + 2]
            self.active_draw.rounded_rectangle(shadow_xy, radius=radius,
                                               fill=self.cfg.COLOR_SHADOW, outline=None)

        if radius > 0:
            self.active_draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)
        else:
            self.active_draw.rectangle(xy, fill=fill, outline=outline, width=width)

    def circle(self, center: Tuple[int, int], radius: int, fill=None, outline=None, shadow: bool = False) -> None:
        x, y = center
        if shadow:
            shadow_radius = radius + 2
            self.active_draw.ellipse([x - shadow_radius, y - shadow_radius,
                                      x + shadow_radius, y + shadow_radius],
                                     fill=self.cfg.COLOR_SHADOW)
        self.active_draw.ellipse([x - radius, y - radius, x + radius, y + radius],
                                 fill=fill, outline=outline)

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

    def button(self, xy, label: str, icon: str = None, primary: bool = False, disabled: bool = False) -> None:
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

        font_size = 18
        if text_width > button_width * 0.7:
            font_size = max(12, int(18 * (button_width * 0.7) / text_width))
            try:
                fnt = ImageFont.truetype(font_path, font_size)
            except Exception:
                fnt = ImageFont.load_default()

        if icon:
            self.text((text_x - 40, text_y), icon, font=22, anchor="mm", color=text_color)
            self.text((text_x - 10, text_y), label, font=font_size, anchor="lm",
                      color=text_color, bold=primary and not disabled)
        else:
            self.text((text_x, text_y), label, font=font_size, anchor="mm",
                      color=text_color, bold=primary and not disabled)

    def info_header(self, title: str, subtitle: str = None) -> None:
        header_height = 120

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

        self.rect(badge_rect, fill=color, radius=text_height // 2, shadow=True)
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
    
        pct = max(0, min(100, percent)) / 100.0
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
                progress_text = f"{int(percent+1)}%"
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

    def draw_loading_screen(self, title: str, subtitle: str = None, progress: float = 0) -> None:
        self.clear()
    
        for i in range(self.y_size):
            ratio = i / self.y_size
            color = self._blend_colors(self.cfg.COLOR_BG_GRADIENT, self.cfg.COLOR_BG, ratio)
            self.rect([0, i, self.x_size, i + 1], fill=color)
    
        center_x, center_y = self.x_size // 2, self.y_size // 2 - 40
        radius = 40
        current_time = time.time()
        rotation = (current_time * 180) % 360
    
        outer_radius = radius
        inner_radius = radius - 8
        
        segments = 8
        for i in range(segments):
            start_angle = rotation + i * (360 / segments)
            end_angle = start_angle + (360 / segments) - 10
            
            start_rad = math.radians(start_angle)
            end_rad = math.radians(end_angle)
            
            angle = rotation + i * 45
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

# =========================
# Updater (network + verify + unzip) - UI enhancements only
# =========================
class Updater:
    def __init__(self, cfg: Config, ui: UIRenderer, translator: Translator):
        self.cfg = Config()
        self.input = InputHandler(self.cfg)
        self.skip_first_input = True
        self.cfg = cfg
        self.ui = ui
        self.t = translator
        self.update_info_dict: dict = {}
        self.session = requests.Session()
        self.session.headers.update(self.cfg.headers)
        self._active_threads = []
        self._shutdown_flag = False

        retry = Retry(
            total=self.cfg.retry_config['total'],
            backoff_factor=self.cfg.retry_config['backoff_factor'],
            status_forcelist=self.cfg.retry_config['status_forcelist'],
            allowed_methods=self.cfg.retry_config['allowed_methods']
        )

        adapter = HTTPAdapter(max_retries=retry)
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
        self.session.headers.update(self.cfg.headers)

    def _download_file(self, url, local_path, progress_hook=None, num_file=None):
        try:
            file_size = 0
            if os.path.exists(local_path):
                file_size = os.path.getsize(local_path)

            headers = self.cfg.headers.copy()
            if file_size > 0:
                headers['Range'] = f'bytes={file_size}-'
                LOGGER.info("Resuming download from byte %s", file_size)

            response = self.session.get(url, stream=True, timeout=(60, 300), headers=headers)

            if file_size > 0 and response.status_code == 416:
                content_range = response.headers.get('content-range', '')
                if content_range.startswith('bytes */'):
                    try:
                        total_size_from_server = int(content_range.split('/')[1])
                        if file_size >= total_size_from_server:
                            LOGGER.info("File already fully downloaded (416 due to complete file)")
                            return True
                    except (ValueError, IndexError):
                        pass

                LOGGER.warning("Server doesn't support range requests or range invalid, restarting download")
                os.remove(local_path)
                file_size = 0
                headers.pop('Range', None)
                response = self.session.get(url, stream=True, timeout=(60, 300), headers=headers)

            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            if 'content-range' in response.headers:
                content_range = response.headers['content-range']
                if '/' in content_range:
                    total_size = int(content_range.split('/')[-1])

            if file_size > 0 and total_size > file_size:
                total_size = total_size - file_size
            elif file_size > 0:
                total_size = total_size

            block_size = 512 * 1024  # 512KB block
            downloaded = file_size
            retry_count = 0
            max_retries = 3

            mode = 'ab' if file_size > 0 else 'wb'
            self._stop_all_threads()
            self._shutdown_flag = False
            thread = threading.Thread(target=self._input_poll_worker, name="input_poll")
            thread.daemon = True
            self._active_threads.append(thread)
            thread.start()

            with open(local_path, mode) as f:
                while retry_count <= max_retries:
                    try:
                        for data in response.iter_content(block_size):
                            if self.input.slide_key():
                                LOGGER.info("Download cancelled by user")
                                return "cancelled"

                            downloaded += len(data)
                            f.write(data)
                            f.flush()

                            if progress_hook and total_size > 0:
                                percent = (downloaded / (file_size + total_size)) * 100
                                progress_hook(
                                    (downloaded - file_size) // block_size,
                                    block_size,
                                    total_size,
                                    num_file
                                )
                        break
                    except (requests.exceptions.ChunkedEncodingError,
                            requests.exceptions.ConnectionError) as e:
                        retry_count += 1
                        if retry_count > max_retries:
                            raise e
                        LOGGER.warning("Download interrupted, retrying (%s/%s): %s",
                                       retry_count, max_retries, e)

                        current_size = os.path.getsize(local_path)
                        headers['Range'] = f'bytes={current_size}-'

                        time.sleep(2 * retry_count)

                        response = self.session.get(url, stream=True, timeout=(60, 300), headers=headers)
                        response.raise_for_status()
                        continue

            return True
        except requests.exceptions.Timeout:
            LOGGER.error("Timeout error downloading file: %s", url)
            return False
        except requests.exceptions.HTTPError as e:
            LOGGER.error("HTTP error downloading file: %s - %s", url, e)
            return False
        except requests.exceptions.RequestException as e:
            LOGGER.error("Error downloading file: %s - %s", url, e)
            return False
        except Exception as e:
            LOGGER.error("Unexpected error downloading file: %s - %s", url, e)
            return False
        finally:
            # 确保线程被停止
            self._stop_all_threads()

    def _input_poll_worker(self):
        """专门的输入监听工作线程"""
        while not self._shutdown_flag:
            try:
                self.input.poll()
                time.sleep(0.01)  # 小延迟避免过度占用CPU
            except Exception as e:
                if not self._shutdown_flag:
                    LOGGER.error("Error in input poll worker: %s", e)
                break

    def _stop_all_threads(self):
        """停止所有活动线程"""
        self._shutdown_flag = True
        time.sleep(0.1)  # 给线程时间响应

        for thread in self._active_threads[:]:
            if thread.is_alive():
                thread.join(timeout=0.5)
                if thread.is_alive():
                    LOGGER.warning(f"Thread {thread.name} failed to terminate gracefully")
            self._active_threads.remove(thread)

        # 重置输入状态
        self.input.reset()

    @staticmethod
    def is_connected() -> bool:
        test_servers = [
            ("8.8.8.8", 53),
            ("1.1.1.1", 53),
            ("223.5.5.5", 53),
            ("220.181.38.148", 80),
            ("114.114.114.114", 53),
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

    def read_current_version(self) -> str:
        try:
            ver_file = Path(self.cfg.ver_cfg_path)
            if ver_file.exists():
                ver = ver_file.read_text().splitlines()[0]
                LOGGER.info("Current MOD version: %s", ver)
                return ver
            LOGGER.warning(f"Version file not found: {ver_file}")
        except Exception as e:
            LOGGER.error("Error reading version file: %s", e)
        return "Unknown"

    def fetch_remote_info(self) -> dict:
        dit = {}
        max_retries = 3
        retry_count = 0

        while retry_count <= max_retries:
            try:
                LOGGER.info("Downloading update info from %s (attempt %s/%s)",
                            self.cfg.info_url, retry_count + 1, max_retries + 1)
                response = self.session.get(self.cfg.info_url, timeout=10)
                response.raise_for_status()

                with open(self.cfg.tmp_info, "w", encoding="utf-8") as f:
                    f.write(response.text)

                if os.path.exists(self.cfg.tmp_info):
                    with open(self.cfg.tmp_info, "r", encoding="utf-8") as f:
                        dit = json.load(f)

                info_filename = "info_zh_CN.txt" if self.t.lang_code in ["zh_CN", "zh_TW"] else "info_en_US.txt"
                info_url = f"{self.cfg.info_url.rsplit('/', 1)[0]}/{info_filename}"

                LOGGER.info("Downloading update info from %s (attempt %s/%s)",
                            info_url, retry_count + 1, max_retries + 1)
                response = self.session.get(info_url, timeout=10)
                response.raise_for_status()

                with open(self.cfg.tmp_info, "wb") as f:
                    f.write(response.content)

                if os.path.exists(self.cfg.tmp_info):
                    with open(self.cfg.tmp_info, "r", encoding="utf-8") as f:
                        update_info = f.read()
                        dit['update_info'] = update_info
                break

            except (ContentTooShortError, URLError) as e:
                retry_count += 1
                if retry_count > max_retries:
                    LOGGER.error("Error downloading update info after %s attempts: %s", max_retries + 1, e)
                    break
                LOGGER.warning("Attempt %s failed, retrying in %s seconds: %s",
                               retry_count, retry_count * 2, e)
                time.sleep(retry_count * 2)

            except Exception as e:
                LOGGER.error("Unexpected error processing update info: %s", e)
                break

        return dit

    def draw_home(self, model: str, cur_ver: str, new_ver: str, os_cur_ver: str,
                  actions_enabled: bool, append_enabled: bool) -> None:
        ui = self.ui
        t = self.t

        ui.clear()
        ui.info_header(f"{t.t('Stock OS Mod Updater')} v{cur_app_ver}",
                       t.t("Professional Edition - Enhanced UI"))

        content_top = 100
        content_height = ui.y_size - content_top - 60

        panel_padding = 25
        panel_width = ui.x_size - panel_padding * 2
        panel_height = content_height - 70

        ui.panel([panel_padding, content_top, panel_padding + panel_width, content_top + panel_height],
                 title=t.t("System Information"), accent=True)

        info_x = ui.x_size // 2
        y_start = content_top + 80
        line_height = 35

        info_items = [
            (f"{t.t('Device Model')}: {model}", 0),
            (f"{t.t('Current Version')}: {cur_ver}", 1),
            (f"{t.t('Available Version')}: {new_ver}", 2),
            (f"{t.t('OS date')}: {os_cur_ver}", 3)
        ]

        for text, offset in info_items:
            if 'Unknown' in text:
                text = f'  {text}'
            else:
                text = f'☑ {text}'
            y_pos = y_start + line_height * offset
            ui.text((info_x, y_pos), text, font=21, anchor="mm", shadow=True)

        status_y = y_start + line_height * 4 + 20
        if append_enabled:
            status_text = t.t("UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y),  f"{status_text} +", "success")
        elif actions_enabled:
            status_text = t.t("UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y), status_text, "success")
        else:
            status_text = t.t("NO UPDATE AVAILABLE")
            ui.status_badge((info_x, status_y), status_text, "info")

        button_y = ui.y_size - 55
        button_width = 150
        button_height = 40
        button_spacing = 20

        total_button_width = button_width * 3 + button_spacing * 2
        start_x = (ui.x_size - total_button_width) // 2

        if actions_enabled:
            ui.button([start_x, button_y, start_x + button_width, button_y + button_height],
                      t.t("Update"), "A", True)
            start_x += button_width + button_spacing

        ui.button([start_x, button_y, start_x + button_width, button_y + button_height],
                  t.t("Info"), "Y", False)
        start_x += button_width + button_spacing

        ui.button([start_x, button_y, start_x + button_width, button_y + button_height],
                  t.t("Exit"), "B", False)

        tip_y = status_y + 50
        if actions_enabled:
            tip_text = t.t("Tip: Press A to start update • Y for info • B to exit")
        else:
            tip_text = t.t("Tip: Y for update info • B to exit")

        ui.text((ui.x_size // 2, tip_y), tip_text, font=18, anchor="mm",
                color=ui.cfg.COLOR_TEXT_TERTIARY)

        ui.paint()

    def draw_message_center(self, title: str, subtitle: Optional[str] = None,
                            icon: Optional[str] = None, status: str = "info") -> None:
        ui = self.ui
        ui.clear()

        max_panel_width = min(ui.x_size - 100, 650)
        padding = 30

        title_font_size = 24
        subtitle_font_size = 20

        title_lines = self._wrap_text(ui, title, title_font_size, max_panel_width - 2 * padding - (60 if icon else 0))
        title_height = len(title_lines) * 35

        subtitle_height = 0
        if subtitle:
            subtitle_lines = self._wrap_text(ui, subtitle, subtitle_font_size,
                                             max_panel_width - 2 * padding - (60 if icon else 0))
            subtitle_height = len(subtitle_lines) * 28

        panel_height = 60 + title_height + subtitle_height + 30

        panel_height = min(panel_height, ui.y_size - 120)

        panel_width = max_panel_width
        panel_x = (ui.x_size - panel_width) // 2
        panel_y = (ui.y_size - panel_height) // 2 - 30

        accent = status in ["success", "warning", "error"]
        ui.panel([panel_x, panel_y, panel_x + panel_width, panel_y + panel_height],
                 title=None, shadow=True, accent=accent)

        icon_x = panel_x + 40
        icon_y = panel_y + panel_height // 2

        if icon:
            icon_size = 50
            icon_bg_size = icon_size + 10
            ui.circle((icon_x, icon_y), icon_bg_size // 2,
                      fill=ui.cfg.COLOR_PRIMARY_DARK, shadow=True)
            ui.text((icon_x, icon_y), icon, font=32, anchor="mm",
                    color=ui.cfg.COLOR_TEXT, shadow=True)

            text_x = icon_x + icon_bg_size + 25
            text_start_y = panel_y + 40
        else:
            text_x = panel_x + panel_width // 2
            text_start_y = panel_y + 40

        for i, line in enumerate(title_lines):
            y_pos = text_start_y + i * 35
            ui.text((text_x, y_pos), line, font=title_font_size,
                    anchor="lm" if icon else "mm", bold=True, shadow=True)

        if subtitle:
            subtitle_start_y = text_start_y + title_height + 15
            subtitle_lines = self._wrap_text(ui, subtitle, subtitle_font_size,
                                             max_panel_width - 2 * padding - (60 if icon else 0))

            if icon:
                subtitle_x = text_x
                anchor = "lm"
            else:
                subtitle_x = panel_x + panel_width // 2
                anchor = "mm"

            for i, line in enumerate(subtitle_lines):
                y_pos = subtitle_start_y + i * 28
                ui.text((subtitle_x, y_pos), line, font=subtitle_font_size,
                        anchor=anchor, color=ui.cfg.COLOR_TEXT_SECONDARY)

        if status != "info":
            status_colors = {
                "success": ui.cfg.COLOR_SUCCESS,
                "warning": ui.cfg.COLOR_WARNING,
                "error": ui.cfg.COLOR_DANGER
            }
            status_color = status_colors.get(status, ui.cfg.COLOR_PRIMARY)
            indicator_x = panel_x + panel_width - 25
            indicator_y = panel_y + 25
            ui.circle((indicator_x, indicator_y), 12, fill=status_color, shadow=True)

        if status == "error":
            button_y = ui.y_size - 60
            button_width = 160
            button_height = 40

            if os.path.exists(LOG_FILE):
                log_x = 30
                ui.button([log_x, button_y, log_x + button_width, button_y + button_height],
                          self.t.t("Show Log"), "Y", True)

            exit_x = ui.x_size - button_width - 30
            ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                      self.t.t("Exit"), "B", False)

        ui.paint()

        while status == "error":
            if self.skip_first_input:
                self.input.reset()
                self.skip_first_input = False
            else:
                self.input.poll()

            if self.input.is_key("B"):
                break
            elif os.path.exists(LOG_FILE) and self.input.is_key("Y"):
                with open(LOG_FILE, "r") as log_file:
                    log_content = log_file.read()
                    self.show_info(log_content)
                break

    def _wrap_text(self, ui: UIRenderer, text: str, font_size: int, max_width: int) -> list:
        if not text:
            return []

        try:
            font = ImageFont.truetype(ui.cfg.font_file, font_size)
        except:
            font = ImageFont.load_default()

        words = text.split()
        lines = []
        current_line = []

        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = ui.active_draw.textbbox((0, 0), test_line, font=font)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                if ui.active_draw.textbbox((0, 0), word, font=font)[2] > max_width:
                    chars = list(word)
                    split_word = []
                    current_chars = []

                    for char in chars:
                        test_chars = ''.join(current_chars + [char])
                        char_width = ui.active_draw.textbbox((0, 0), test_chars, font=font)[2]

                        if char_width <= max_width:
                            current_chars.append(char)
                        else:
                            if current_chars:
                                split_word.append(''.join(current_chars))
                            current_chars = [char]

                    if current_chars:
                        split_word.append(''.join(current_chars))

                    lines.extend(split_word)
                else:
                    current_line = [word]

        if current_line:
            lines.append(' '.join(current_line))

        return lines

    def _calculate_speed(self, downloaded: int) -> float | int | str:
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

    def show_info(self, info: str) -> None:
        ui = self.ui
        t = self.t

        current_page = 0

        def prepare_lines():
            ui.clear()
            content_top = 0
            content_height = ui.y_size - content_top

            panel_padding = 0
            panel_width = ui.x_size - panel_padding * 2
            panel_height = content_height - 60

            text_padding = 15
            text_width = panel_width - text_padding * 2
            text_x = panel_padding + text_padding

            font_size = 22
            try:
                font = ImageFont.truetype(ui.cfg.font_file, font_size)
            except:
                font = ImageFont.load_default()

            lines = []

            paragraphs = info.split('\n')

            for paragraph in paragraphs:
                if not paragraph.strip():
                    lines.append('')
                    continue

                words = paragraph.split()
                current_line = []

                for word in words:
                    test_line = ' '.join(current_line + [word]) if current_line else word
                    bbox = ui.active_draw.textbbox((0, 0), test_line, font=font)
                    line_width = bbox[2] - bbox[0]

                    if line_width <= text_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))

                        word_bbox = ui.active_draw.textbbox((0, 0), word, font=font)
                        word_width = word_bbox[2] - word_bbox[0]

                        if word_width > text_width:
                            chars = list(word)
                            current_chars = []

                            for char in chars:
                                test_chars = ''.join(current_chars + [char])
                                char_bbox = ui.active_draw.textbbox((0, 0), test_chars, font=font)
                                char_width = char_bbox[2] - char_bbox[0]

                                if char_width <= text_width:
                                    current_chars.append(char)
                                else:
                                    if current_chars:
                                        lines.append(''.join(current_chars))
                                    current_chars = [char]

                            if current_chars:
                                current_line = [''.join(current_chars)]
                            else:
                                current_line = []
                        else:
                            current_line = [word]

                if current_line:
                    lines.append(' '.join(current_line))

            return lines, text_x, panel_height, text_width, font

        def render_page(lines, text_x, panel_height, text_width, font, page):
            ui.clear()
            content_top = 0
            content_height = ui.y_size - content_top

            panel_padding = 0
            panel_width = ui.x_size - panel_padding * 2
            panel_height_val = content_height - 60

            ui.panel([panel_padding, content_top, panel_padding + panel_width, content_top + panel_height_val],
                     title=t.t("Update Information"))

            text_y = content_top + 60

            line_height = 30
            max_lines_per_page = (panel_height_val - 80) // line_height
            total_pages = (len(lines) + max_lines_per_page - 1) // max_lines_per_page

            page = max(0, min(page, total_pages - 1))

            start_line = page * max_lines_per_page
            end_line = min(start_line + max_lines_per_page, len(lines))

            for i, line in enumerate(lines[start_line:end_line]):
                y_pos = text_y + i * line_height

                if line:
                    bbox = ui.active_draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    if line_width > text_width:
                        truncated_line = line
                        while truncated_line and ui.active_draw.textbbox((0, 0), truncated_line + "...", font=font)[
                            2] > text_width:
                            truncated_line = truncated_line[:-1]
                        line = truncated_line + "..."

                ui.text((text_x, y_pos), line, font=19, anchor="lm")

            if total_pages > 1:
                page_info = f"{page + 1}/{total_pages}"
                page_x = ui.x_size - 20
                ui.text((page_x, text_y - 15), page_info, font=19,
                        color=ui.cfg.COLOR_TEXT_SECONDARY, anchor="rm")

            for i in range(30):
                reflect_ratio = i / 30
                reflect_color = ui._blend_colors(ui.cfg.COLOR_GLOW, ui.cfg.COLOR_BG, 1 - reflect_ratio)
                ui.rect([0, ui.y_size - i, ui.x_size, ui.y_size - i + 1], fill=reflect_color)

            button_y = ui.y_size - 50
            button_width = 140
            button_height = 36

            if total_pages > 1:
                prev_x = 20
                ui.button([prev_x, button_y, prev_x + button_width, button_y + button_height],
                          t.t("Previous"), "L1", False)

                next_x = ui.x_size // 2 - button_width
                ui.button([next_x, button_y, next_x + button_width, button_y + button_height],
                          t.t("Next"), "R1", False)
                exit_x = ui.x_size - button_width - 20
                ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                          t.t("Exit"), "B", False)
            else:
                exit_x = ui.x_size - button_width - 20
                ui.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                          t.t("Exit"), "B", False)

            ui.paint()
            return max_lines_per_page, total_pages, page

        lines, text_x, panel_height, text_width, font = prepare_lines()
        lines_per_page, total_pages, current_page = render_page(
            lines, text_x, panel_height, text_width, font, current_page
        )

        while True:
            if self.skip_first_input:
                self.input.reset()
                self.skip_first_input = False
            else:
                self.input.poll()

            if self.input.is_key("B"):
                return
            elif total_pages > 1:
                if self.input.is_key("L1") and current_page > 0:
                    current_page -= 1
                    lines_per_page, total_pages, current_page = render_page(
                        lines, text_x, panel_height, text_width, font, current_page
                    )
                elif self.input.is_key("R1") and current_page < total_pages - 1:
                    current_page += 1
                    lines_per_page, total_pages, current_page = render_page(
                        lines, text_x, panel_height, text_width, font, current_page
                    )

    def update_app(self, new_ver: str, update_url: str, update_md5: str) -> None:
        ui = self.ui
        t = self.t

        ui.clear()
        self.ui.text((self.ui.x_size // 2, self.ui.y_size // 2),
                     f"{t.t('Update the application')} v{cur_app_ver} -> v{new_ver}", font=26, anchor="mm", bold=True)
        ui.paint()
        time.sleep(3)

        def progress_hook(block_num: int, block_size: int, total_size: int, num_file=None):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 // total_size)
                    label_top = t.t("Downloading App Files...") + num_file
                    if total_size >= 1024 * 1024:
                        unit_num = 1024 * 1024
                        unit = "MB"
                    else:
                        unit_num = 1024
                        unit = "KB"
                    speed_display = self._calculate_speed(downloaded)
                    label_bottom = f"{(downloaded / unit_num):.1f}{unit} / {(total_size / unit_num):.2f}{unit} | {speed_display}"
                    ui.clear()
                    ui.info_header(t.t("Update application"), t.t("Downloading update package"))
                    ui.text((ui.x_size // 2, ui.y_size - 120),
                            t.t("Tip: Press any key to cancel the download and return to the main menu"),
                            font=22, anchor="mm", color=ui.cfg.COLOR_SECONDARY)
                    ui.progress_bar(ui.y_size // 2 + 20, percent, label_top=label_top, label_bottom=label_bottom)
                    ui.paint()
            except Exception as e:
                LOGGER.error("Error updating progress: %s", e)

        LOGGER.info("Starting upgrade app process")
        self.draw_message_center(t.t("Downloading"), t.t("Fetching verification data..."), "㊙", "info")

        download_result = self._download_file(update_url, self.cfg.tmp_app_update, progress_hook, '(1/1)')

        if download_result == "cancelled":
            LOGGER.info("App update cancelled by user")
            self.draw_message_center(t.t("Download Cancelled"), t.t("Returning to main menu..."), "☹", "info")
            time.sleep(2)
            return

        if not download_result:
            LOGGER.error(f"Error downloading update file: {update_url}")
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download update file."), "✘", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        LOGGER.info(f"Verifying downloaded files: {self.cfg.tmp_app_update}")
        self.draw_message_center(t.t("Verifying"), t.t("Checking file integrity..."), "✪", "info")

        down_md5 = ""

        if os.path.exists(self.cfg.tmp_app_update):
            try:
                md5_hash = hashlib.md5()
                with open(self.cfg.tmp_app_update, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                down_md5 = md5_hash.hexdigest().lower()
                LOGGER.info("Calculated MD5 of update file: %s", down_md5)
            except Exception as e:
                LOGGER.error("Error calculating MD5: %s", e)
                down_md5 = ""

        if down_md5 and update_md5 and down_md5.upper() == update_md5.upper():
            LOGGER.info("MD5 verification successful")
            LOGGER.info("Application restart")
            self.draw_message_center(t.t("Prompt message"), t.t("Updating, restart later..."), "㊙", "info")
            time.sleep(2)
            LOGGER.info("Restarting application for update...")
            self._cleanup_before_restart()
            MainApp.exit_not_cleanup(36)
        else:
            LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", update_md5, down_md5)
            self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "✘", "error")
            MainApp.exit_cleanup(3, self.ui, self.cfg)

    def _cleanup_before_restart(self):
        """重启前的彻底清理"""
        # 1. 停止所有线程
        self._stop_all_threads()

        # 2. 重置输入系统
        self.input.reset()

        # 3. 清理SDL资源
        self.ui.draw_end()

        # 4. 强制垃圾回收
        import gc
        gc.collect()

        # 5. 小延迟确保资源释放
        time.sleep(0.5)

    def start_update(self, update_file_list: list) -> None:
        ui = self.ui
        t = self.t

        def progress_hook(block_num: int, block_size: int, total_size: int, num_file=None):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 // total_size)
                    label_top = t.t("Downloading Update Files...") + num_file
                    if total_size >= 1024 * 1024:
                        unit_num = 1024 * 1024
                        unit = "MB"
                    else:
                        unit_num = 1024
                        unit = "KB"
                    speed_display = self._calculate_speed(downloaded)
                    label_bottom = f"{(downloaded / unit_num):.1f}{unit} / {(total_size / unit_num):.2f}{unit} | {speed_display}"
                    ui.clear()
                    ui.info_header(t.t("System Update"), t.t("Downloading update package"))
                    ui.text((ui.x_size // 2, ui.y_size - 120),
                            t.t("Tip: Press any key to cancel the download and return to the main menu"),
                            font=22, anchor="mm", color=ui.cfg.COLOR_SECONDARY)
                    ui.progress_bar(ui.y_size // 2 + 20, percent, label_top=label_top, label_bottom=label_bottom)
                    ui.paint()
            except Exception as e:
                LOGGER.error("Error updating progress: %s", e)

        LOGGER.info("Starting MOD OS update process")
        self.draw_message_center(t.t("Downloading"), t.t("Fetching verification data..."), "㊙", "info")

        tmp_space = shutil.disk_usage("/tmp").free
        mmc_space = shutil.disk_usage("/mnt/mmc").free
        sdcard_space = shutil.disk_usage("/mnt/sdcard").free
        if tmp_space == sdcard_space:
            self.cfg.target_path = "/mnt/mmc/tmp" if mmc_space > tmp_space else "/tmp/tmp"
        else:
            self.cfg.target_path = "/mnt/mmc/tmp" if mmc_space > sdcard_space else "/mnt/sdcard/tmp"
        LOGGER.info("Starting update from path %s", self.cfg.target_path)

        total_size = 1024 * 1024 * 1024
        if max(tmp_space, mmc_space, sdcard_space) < total_size:
            LOGGER.info("There is not enough free space on %s", self.cfg.target_path)
            self.draw_message_center(t.t("Insufficient TF card space"), t.t("Please reserve 1GB of free space on TF1 or TF2"), "✘", "error")
            shutil.rmtree(self.cfg.target_path)
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        if not os.path.exists(self.cfg.target_path):
            os.makedirs(self.cfg.target_path, exist_ok=True)

        file_num = 1
        for item in update_file_list:
            down_url = self.cfg.server_url + item['filename']
            target_file = os.path.join(self.cfg.target_path, item['filename'])
            download_result = self._download_file(down_url, target_file, progress_hook,
                                                  str(f'({file_num}/{len(update_file_list)})'))

            if download_result == "cancelled":
                LOGGER.info("System update cancelled by user")
                self.draw_message_center(t.t("Download Cancelled"), t.t("Returning to main menu..."), "☹", "info")
                time.sleep(2)
                return

            if not download_result:
                LOGGER.error(f"Error downloading update file: {down_url}")
                self.draw_message_center(t.t("Download Error"), t.t("Failed to download update file."), "✘", "error")
                shutil.rmtree(self.cfg.target_path)
                MainApp.exit_cleanup(2, self.ui, self.cfg)
            file_num += 1

        LOGGER.info(f"Verifying downloaded files: {self.cfg.target_path}")
        self.draw_message_center(t.t("Verifying"), t.t("Checking file integrity..."), "✪", "info")
        for item in update_file_list:
            target_file = os.path.join(self.cfg.target_path, item['filename'])
            down_md5 = ""
            check_md5 = item['md5']
            if os.path.exists(target_file):
                try:
                    md5_hash = hashlib.md5()
                    with open(target_file, "rb") as f:
                        for chunk in iter(lambda: f.read(4096), b""):
                            md5_hash.update(chunk)
                    down_md5 = md5_hash.hexdigest().lower()
                    LOGGER.info("Calculated MD5 of update file: %s", down_md5)
                except Exception as e:
                    LOGGER.error("Error calculating MD5: %s", e)
                    down_md5 = ""

            if down_md5 and check_md5 and down_md5.upper() == check_md5.upper():
                LOGGER.info(f"{item['filename']}: MD5 verification successful")
            else:
                LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", check_md5, down_md5)
                self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "✘", "error")
                shutil.rmtree(self.cfg.target_path)
                MainApp.exit_cleanup(3, self.ui, self.cfg)

        LOGGER.info("Starting install process")
        mod_path = "/mnt/mod"
        update_path = os.path.join(mod_path, 'update')
        data_path = os.path.join(update_path, 'mod', 'data')
        if not os.path.exists(data_path):
            os.makedirs(data_path, exist_ok=True)
        if os.path.isdir(update_path):
            shutil.rmtree(update_path)
        os.makedirs(update_path, exist_ok=True)

        for item in update_file_list:
            source_file = os.path.join(self.cfg.target_path, item['filename'])
            target_file = os.path.join(data_path, item['filename'])
            if item['filename'] == 'update.zip':
                if self.unpack_zip(source_file, mod_path) == 0:
                    LOGGER.info(f"{item['filename']}: installation completed")
                else:
                    LOGGER.error(f"Error unpacking update file: {item['filename']}")
                    self.draw_message_center(t.t("Extraction Error"), t.t("Failed to extract update files."), "✘",
                                             "error")
                    shutil.rmtree(self.cfg.target_path)
                    MainApp.exit_cleanup(4, self.ui, self.cfg)
            else:
                try:
                    self.draw_message_center(t.t("System Update"), t.t("Extracting files..."), "✪", "info")
                    shutil.copy(source_file, target_file)
                    LOGGER.info(f"{item['filename']}: installation completed")
                except Exception as e:
                    LOGGER.error(f"Error copy update file: {item['filename']}")
                    self.draw_message_center(t.t("Extraction Error"), t.t("Failed to extract update files."), "✘",
                                             "error")
                    shutil.rmtree(self.cfg.target_path)
                    MainApp.exit_cleanup(4, self.ui, self.cfg)

        self.draw_message_center(t.t("System Update"), t.t("Ready, start upgrading..."), "✔", "success")
        time.sleep(3)
        autostart = True
        shutil.rmtree(self.cfg.target_path)
        MainApp.reboot(self.ui, self.cfg, autostart)

    def start_append(self, update_url, md5) -> None:
        ui = self.ui
        t = self.t

        def progress_hook(block_num: int, block_size: int, total_size: int, num_file=None):
            try:
                downloaded = block_num * block_size
                if total_size > 0:
                    percent = min(100, downloaded * 100 // total_size)
                    label_top = t.t("Downloading Update Files...") + num_file
                    if total_size >= 1024 * 1024:
                        unit_num = 1024 * 1024
                        unit = "MB"
                    else:
                        unit_num = 1024
                        unit = "KB"
                    speed_display = self._calculate_speed(downloaded)
                    label_bottom = f"{(downloaded / unit_num):.1f}{unit} / {(total_size / unit_num):.2f}{unit} | {speed_display}"
                    ui.clear()
                    ui.info_header(t.t("System Update"), t.t("Downloading update package"))
                    ui.text((ui.x_size // 2, ui.y_size - 120),
                            t.t("Tip: Press any key to cancel the download and return to the main menu"),
                            font=22, anchor="mm", color=ui.cfg.COLOR_SECONDARY)
                    ui.progress_bar(ui.y_size // 2 + 20, percent, label_top=label_top, label_bottom=label_bottom)
                    ui.paint()
            except Exception as e:
                LOGGER.error("Error updating progress: %s", e)

        LOGGER.info("Starting OS append update process")
        self.draw_message_center(t.t("Downloading"), t.t("Fetching verification data..."), "㊙", "info")

        download_result = self._download_file(update_url, self.cfg.tmp_update, progress_hook, '(1/1)')

        if download_result == "cancelled":
            LOGGER.info("Append update cancelled by user")
            self.draw_message_center(t.t("Download Cancelled"), t.t("Returning to main menu..."), "☹", "info")
            time.sleep(2)
            return

        if not download_result:
            LOGGER.error(f"Error downloading update file: {update_url}")
            self.draw_message_center(t.t("Download Error"), t.t("Failed to download update file."), "✘", "error")
            MainApp.exit_cleanup(2, self.ui, self.cfg)

        LOGGER.info(f"Verifying downloaded files: {self.cfg.tmp_update}")
        self.draw_message_center(t.t("Verifying"), t.t("Checking file integrity..."), "✪", "info")

        down_md5 = ""

        if os.path.exists(self.cfg.tmp_update):
            try:
                md5_hash = hashlib.md5()
                with open(self.cfg.tmp_update, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        md5_hash.update(chunk)
                down_md5 = md5_hash.hexdigest().lower()
                LOGGER.info("Calculated MD5 of update file: %s", down_md5)
            except Exception as e:
                LOGGER.error("Error calculating MD5: %s", e)
                down_md5 = ""

        if down_md5 and md5 and down_md5.upper() == md5.upper():
            LOGGER.info("MD5 verification successful")
            tmp_space = shutil.disk_usage("/tmp")
            mmc_space = shutil.disk_usage("/mnt/mmc")
            sdcard_space = shutil.disk_usage("/mnt/sdcard")
            if tmp_space == sdcard_space:
                target_path = "/mnt/mmc"
            else:
                target_path = "/mnt/mmc" if mmc_space > sdcard_space else "/mnt/sdcard"
            LOGGER.info("Starting append update from path %s", target_path)

            if self.unpack_zip(self.cfg.tmp_update, target_path) == 0:
                self.draw_message_center(t.t("System Update"), t.t("Ready, start upgrading..."), "✔", "success")
                time.sleep(3)
                MainApp.reboot(self.ui, self.cfg)
            else:
                LOGGER.error("Error unpacking update file")
                self.draw_message_center(t.t("Extraction Error"), t.t("Failed to extract update files."), "✘", "error")
                MainApp.exit_cleanup(4, self.ui, self.cfg)
        else:
            LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", md5, down_md5)
            self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "✘", "error")
            MainApp.exit_cleanup(3, self.ui, self.cfg)

    def unpack_zip(self, dep_path: str, target_path: str) -> int:
        if not os.path.exists(dep_path):
            LOGGER.error("Update file not found: %s", dep_path)
            return 1
        try:
            with zipfile.ZipFile(dep_path, "r") as zip_ref:
                namelist = zip_ref.namelist()
                total_files = len(namelist)
                last_percent = -1
                LOGGER.info("Unpacking %s files from %s", total_files, dep_path)
                for i, file in enumerate(namelist):
                    zip_ref.extract(file, target_path)
                    percent = (i + 1) * 100 / max(1, total_files)

                    if percent != last_percent:
                        last_percent = percent
                        ui = self.ui
                        ui.clear()
                        ui.info_header(self.t.t("System Update"), self.t.t("Extracting files..."))

                        file_name = os.path.basename(file)
                        if len(file_name) > 30:
                            file_name = file_name[:27] + "..."

                        ui.text((ui.x_size // 2, ui.y_size // 2 - 20), f"{self.t.t('File')}: {file_name}", font=18,
                                anchor="mm")

                        progress_text = f"{i + 1} / {total_files} {self.t.t('files')}"
                        ui.text((ui.x_size // 2, ui.y_size // 2 + 40), progress_text,
                                font=16, anchor="mm", color=ui.cfg.COLOR_TEXT_SECONDARY)

                        ui.progress_bar(ui.y_size // 2 + 10, percent)
                        ui.paint()

            LOGGER.info("Unpacking completed successfully")
            return 0
        except zipfile.BadZipFile:
            LOGGER.error("Invalid zip file: %s", dep_path)
            return 1
        except Exception as e:
            LOGGER.error("Error unpacking zip file: %s", e)
            return 1

# =========================
# Enhanced Main Application
# =========================
class MainApp:
    def __init__(self):
        self.cfg = Config()

        try:
            board_info = Path("/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
            LOGGER.info("Detected board: %s", board_info)
        except (FileNotFoundError, IndexError) as e:
            LOGGER.warning("Board detection failed: %s, using default RG35xxH", e)
            board_info = "RG35xxH"
        self.board_info = board_info

        try:
            lang_index_raw = Path("/mnt/vendor/oem/language.ini").read_text().splitlines()[0]
            lang_index = int(lang_index_raw)
            LOGGER.info("Detected language index: %s", lang_index)
        except (FileNotFoundError, IndexError, ValueError) as e:
            LOGGER.warning("Language detection failed: %s, using default index 2", e)
            lang_index = 2

        self.hw_info = self.cfg.board_mapping.get(self.board_info, 0)
        self.system_lang = self.cfg.system_list[lang_index if 0 <= lang_index < len(self.cfg.system_list) else 2]
        LOGGER.info("Hardware info: %s, System language: %s", self.hw_info, self.system_lang)

        self.t = Translator(self.system_lang)
        self.ui = UIRenderer(self.cfg, self.t, self.hw_info)
        self.input = InputHandler(self.cfg)
        self.updater = Updater(self.cfg, self.ui, self.t)

        self.skip_first_input = True

    @staticmethod
    def exit_not_cleanup(code: int) -> None:
        LOGGER.info("Exiting with code %s", code)
        try:
            import sdl2
            sdl2.SDL_Quit()
        except Exception as e:
            LOGGER.warning("Error cleaning up SDL: %s", e)
        sys.exit(code)

    @staticmethod
    def exit_cleanup(code: int, ui: UIRenderer, cfg: Config) -> None:
        LOGGER.info("Exiting with code %s", code)
        try:
            for p in (cfg.tmp_info, cfg.tmp_update, cfg.target_path):
                if os.path.isfile(p):
                    os.remove(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p)
        except Exception as e:
            LOGGER.error("Error during exit cleanup: %s", e)
        finally:
            ui.draw_end()
            sys.exit(code)

    @staticmethod
    def reboot(ui: UIRenderer, cfg: Config, auto=False) -> None:
        LOGGER.info("Rebooting system")
        try:
            for p in (cfg.tmp_info, cfg.tmp_update, "/mnt/mod/update.dep"):
                if os.path.exists(p):
                    os.remove(p)
            if auto:
                update_dir = "/mnt/mod/ctrl"
                os.makedirs(update_dir, exist_ok=True)
                update_script_path = os.path.join(update_dir, "autostart")
                update_script_content = """#!/bin/bash

if [ -f /mnt/mod/update/update.sh ]; then
  chmod +x /mnt/mod/update/update.sh
  /mnt/mod/update/update.sh
fi
"""
                with open(update_script_path, "w") as f:
                    f.write(update_script_content)

            ui.draw_end()
            os.sync()
            os.system("reboot")
            sys.exit(0)
        except Exception as e:
            LOGGER.error("Error during reboot: %s", e)
            MainApp.exit_cleanup(1, ui, cfg)

    def run(self) -> None:
        self.ui.draw_loading_screen(
            self.t.t("Stock OS Mod Updater"),
            self.t.t("Professional Edition - Starting..."),
            progress=10
        )
        time.sleep(1)

        for i in range(20, 80, 10):
            self.ui.draw_loading_screen(
                self.t.t("Stock OS Mod Updater"),
                self.t.t("Initializing system..."),
                progress=i
            )
            time.sleep(0.1)

        cur_ver = self.updater.read_current_version()

        if not self.updater.is_connected():
            self.updater.draw_message_center(
                self.t.t("No Internet Connection"),
                self.t.t("Please check your network settings"),
                "✈", "error"
            )
            MainApp.exit_cleanup(1, self.ui, self.cfg)

        self.ui.draw_loading_screen(
            self.t.t("Checking for updates..."),
            self.t.t("Connecting to update servers"),
            progress=90
        )

        app_ver = app_update_url = app_md5 = update_ver = data_ver = data_update_url = data_md5 = ""
        update_file_list = []

        self.updater.update_info_dict = self.updater.fetch_remote_info()

        if self.updater.update_info_dict.get('app'):
            app_ver = self.updater.update_info_dict.get('app').get('version', 'Unknown')
            app_update_url = self.cfg.server_url + self.updater.update_info_dict.get('app').get('filename')
            app_md5 = self.updater.update_info_dict.get('app').get('md5')
            LOGGER.info(f"app: v{app_ver}")

        if self.updater.update_info_dict.get('update'):
            update_file_dict = self.updater.update_info_dict.get('update')
            if update_file_dict.get(self.board_info):
                update_file_list = update_file_dict.get('default') + update_file_dict.get(self.board_info)
            else:
                update_file_list = update_file_dict.get('default') + update_file_dict.get('RG35xxSP')

            update_ver = update_file_dict.get('version', 'Unknown')
            LOGGER.info(f'update: v{update_ver}')

        if self.updater.update_info_dict.get('data'):
            data_ver = self.updater.update_info_dict.get('data').get('version', 'Unknown')
            data_update_url = self.cfg.server_url + self.updater.update_info_dict.get('data').get('filename')
            data_md5 = self.updater.update_info_dict.get('data').get('md5')
            LOGGER.info(f"data: v{data_ver}")

        update_info = self.updater.update_info_dict.get('update_info', 'Unknown')

        if app_ver != "Unknown" and cur_app_ver < app_ver and bool(app_update_url):
            self.updater.update_app(app_ver, app_update_url, app_md5)

        update_active = False
        append_active = False

        if (
                cur_ver != "Unknown" and update_ver != "Unknown" and cur_ver < base_ver and bool(update_file_list)
        ) or (
                cur_ver == "Unknown" and os_cur_ver >= base_date and update_ver != "Unknown" and bool(update_file_list)
        ):
            update_active = True
            new_ver = update_ver
        elif cur_ver != "Unknown" and data_ver != "Unknown" and cur_ver < data_ver and bool(data_update_url):
            update_active = True
            append_active = True
            new_ver = data_ver
        else:
            new_ver = data_ver
        self.skip_first_input = False

        while True:
            try:
                self.updater.draw_home(self.board_info, cur_ver, new_ver, os_cur_ver,
                                       actions_enabled=update_active, append_enabled=append_active)

                if self.skip_first_input:
                    self.input.reset()
                    self.skip_first_input = False
                else:
                    self.input.poll()

                if self.input.is_key("B"):
                    MainApp.exit_cleanup(0, self.ui, self.cfg)

                elif update_active and self.input.is_key("A"):
                    if append_active:
                        self.updater.start_append(data_update_url, data_md5)
                    else:
                        self.updater.start_update(update_file_list)

                elif self.input.is_key("Y"):
                    self.updater.show_info(update_info)

                time.sleep(0.1)

            except Exception as e:
                LOGGER.error("Unexpected error in main loop: %s", e)
                self.updater.draw_message_center(
                    self.t.t("An error occurred"),
                    self.t.t("Please rerun the application"),
                    "☠", "error"
                )
                self.ui.draw_end()
                sys.exit(1)

# =========================
# Entrypoint
# =========================
if __name__ == "__main__":
    try:
        MainApp().run()
    except KeyboardInterrupt:
        LOGGER.info("Program interrupted by user")
        sys.exit(0)
    except Exception as e:
        LOGGER.error("Unexpected error: %s", e)
        sys.exit(1)
