#!/usr/bin/env python3
import glob
import hashlib
import shutil
import socket
import subprocess
import threading
import time
from urllib.error import URLError, ContentTooShortError
import requests
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import ctypes
import json
import zipfile
import struct
from dataclasses import dataclass

# =========================
# Third-Party Imports
# =========================
from PIL import Image, ImageDraw, ImageFont

cur_app_ver = "1.0.6"

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
    import sdl2

APP_PATH = os.path.dirname(os.path.abspath(__file__))
LOG_FILE = os.path.join(APP_PATH, "launcher.log")
log_delete = 1
if log_delete and os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler(sys.stdout)],
)
LOGGER = logging.getLogger("launcher")
LOGGER.info(f"=== Launch Start ===")

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

    # 主色调（深蓝色系）
    COLOR_PRIMARY: str = "#1E90FF"  # 主按钮、标题等
    COLOR_PRIMARY_DARK: str = "#1B75D0"  # 深色主色调
    COLOR_ACCENT: str = "#00BFFF"  # 辅助色（如高亮）
    COLOR_SUCCESS: str = "#2ECC71"  # 成功状态
    COLOR_WARNING: str = "#F1C40F"  # 警告状态
    COLOR_DANGER: str = "#E74C3C"  # 错误状态

    # 背景色
    COLOR_BG: str = "#121212"  # 主背景色（深灰）
    COLOR_BG_LIGHT: str = "#1E1E1E"  # 浅色背景
    COLOR_BG_GRADIENT: str = "#2C2C2C"  # 渐变背景

    # 卡片和边框
    COLOR_CARD: str = "#0f1322"  # 卡片背景
    COLOR_CARD_LIGHT: str = "#2A2A2A"  # 浅色卡片
    COLOR_CARD_HOVER: str = "#333333"  # 卡片悬停效果
    COLOR_NEON_BORDER: str = "#1E90FF"  # 边框颜色

    # 文字颜色
    COLOR_TEXT: str = "#E0E0E0"  # 主文字颜色（浅灰）
    COLOR_TEXT_SECONDARY: str = "#B0B0B0"  # 次要文字颜色
    COLOR_TEXT_TERTIARY: str = "#808080"  # 辅助文字颜色

    # 阴影和光效
    COLOR_SHADOW: str = "#00000080"  # 阴影（透明黑）
    COLOR_GLOW: str = "#1E90FF33"  # 光效（透明蓝）

    # 按钮颜色
    COLOR_BUTTON_PRIMARY: str = "#1E90FF"  # 主按钮颜色
    COLOR_BORDER_LIGHT: str = "#3A3A3A"  # 边框颜色

    if os.name == "nt":
        root_path = APP_PATH + "/sys"
    else:
        root_path = ""
    font_file: str = os.path.join(APP_PATH, "font", "font.ttf")
    if not os.path.exists(font_file):
        font_file: str = root_path + "/mnt/vendor/bin/default.ttf"

    tmp_path: str = APP_PATH + "/tmp" if os.name == "nt" else "/tmp"
    tmp_info: str = os.path.join(tmp_path, "info.json")
    tmp_app_update: str =  os.path.join(tmp_path, "app.tar.gz")

    bytes_per_pixel: int = 4
    keymap: Dict[int, str] = None

    mirrors = [
        {
            "name": "GitHub",
            "url": "https://raw.githubusercontent.com/cbepx-me/Online_installation/refs/heads/main/app_ver.json",
            "down_url": "https://github.com/cbepx-me/Online_installation/releases/download/download/",
            "region": "Global"
        },
        {
            "name": "GitCode (China)",
            "url": "https://raw.gitcode.com/cbepx/install/raw/main/app_ver.json",
            "down_url": "https://gitcode.com/cbepx/install/releases/download/download/",
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
            response = requests.get(mirror["url"], timeout=3, headers=headers, stream=True)
            response.close()
            end = time.time() - start
            if response.status_code == 404:
                LOGGER.error(f"Mirror {mirror['name']} accessible but file update_info.json not found (404)")
                end = float('inf')
            elif response.status_code != 200:
                LOGGER.error(f"Mirror {mirror['name']} returned error code: {response.status_code}")
                end = float('inf')
        except:
            end = float('inf')
        speeds.append((end, mirror))
    speeds.sort(key=lambda x: x[0])
    server_url = speeds[0][1]["down_url"] if speeds[0][0] != float('inf') else fallback_mirror["down_url"]
    info_url = speeds[0][1]["url"] if speeds[0][0] != float('inf') else fallback_mirror["url"]
    LOGGER.info(f"Use the downloaded server: {server_url}")

    def __post_init__(self):
        if self.board_mapping is None:
            self.board_mapping = {
                "RGcubexx": 1,
                "RG34xx": 2,
                "RG34xxSP": 2,
                "RGSP": 2,
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

class InputHandler:
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self.code_name: str = ""
        self.value: int = 0
        self.board_info = Path(self.cfg.root_path + "/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
        self.device_path = self._find_anbernic_device()

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

    def _find_anbernic_device(self):
        keyword = "ANBERNIC"
        for event_path in glob.glob("/dev/input/event*"):
            dev_name = os.path.basename(event_path)
            sys_path = f"/sys/class/input/{dev_name}/device/name"
            try:
                with open(sys_path, 'r') as f:
                    name = f.read().strip()
                    if keyword in name:
                        return event_path
            except Exception:
                continue

        fallback = f"/dev/input/event{self.cfg.board_mapping.get(self.board_info, 5)}"
        if os.path.exists(fallback):
            return fallback
        raise RuntimeError("No ANBERNIC input device found")

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
                with open(self.device_path, "rb") as f:
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

class UIRenderer:
    _instance: Optional["UIRenderer"] = None
    _initialized: bool = False

    def __init__(self, cfg: Config, translator: Translator, hw_info: int):
        self.cfg = cfg
        self.t = translator
        self.input = InputHandler(self.cfg)
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

        self.skip_first_input = True

        try:
            self.hdmi_info = Path("/sys/class/extcon/hdmi/state").read_text().splitlines()[0]
        except (FileNotFoundError, IndexError):
            self.hdmi_info = 'HDMI=0'

    def screen_reset(self) -> None:
        for i in range(self.y_size):
            ratio = i / self.y_size
            color = self.blend_colors(self.cfg.COLOR_BG_GRADIENT, self.cfg.COLOR_BG, ratio)
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
        img = Image.open(image_path)
        img.thumbnail((target_width, target_height))
        paste_x = target_x + (target_width - img.width) // 2
        paste_y = target_y + (target_height - img.height) // 2
        if self.hw_info == 3 and rota == 1 and self.hdmi_info != "HDMI=1":
            img = img.rotate(-90, expand=True)
        self.active_image.paste(img, (paste_x, paste_y))

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
        panel_color = self.cfg.COLOR_CARD if not accent else self.cfg.COLOR_PRIMARY_DARK

        if shadow:
            for offset in range(3, 0, -1):
                alpha = 50 - offset * 10
                glow_color = self.cfg.COLOR_PRIMARY + f"{alpha:02x}"
                glow_xy = [xy[0] + offset, xy[1] + offset, xy[2] + offset, xy[3] + offset]
                self.rect(glow_xy, fill=glow_color, radius=16)

        self.rect(xy, fill=panel_color, outline=self.cfg.COLOR_NEON_BORDER, width=2, radius=16)

        if title:
            bar_rect = [xy[0] + 20, xy[1] - 2, xy[2] - 20, xy[1] + 4]
            self.rect(bar_rect, fill=self.cfg.COLOR_PRIMARY, radius=4)
            self.text((self.x_size // 2, xy[1] + 20), title, font=22,
                      anchor="mm", bold=True, shadow=True, color=self.cfg.COLOR_PRIMARY)

    def button(self, xy, label: str, icon: str = None, primary: bool = False, disabled: bool = False, type=0) -> None:
        if disabled:
            fill_color = self.cfg.COLOR_CARD_LIGHT
            text_color = self.cfg.COLOR_TEXT_TERTIARY
        else:
            fill_color = self.cfg.COLOR_BUTTON_PRIMARY if primary else self.cfg.COLOR_CARD_LIGHT
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
                self.text((text_x - 20, text_y), label, font=font_size, anchor="lm",
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

    def info_header(self, title: str, subtitle: str = None, ver: str = cur_app_ver) -> None:
        header_height = 100

        for i in range(header_height):
            ratio = i / header_height
            color = self.blend_colors(self.cfg.COLOR_PRIMARY_DARK, self.cfg.COLOR_BG_GRADIENT, ratio)
            self.rect([0, i, self.x_size, i + 1], fill=color)

        light_rect = [0, header_height - 2, self.x_size, header_height]
        self.rect(light_rect, fill=self.cfg.COLOR_BG_LIGHT + "40", radius=0)

        self.text((self.x_size // 2, 35), title, font=32, anchor="mm",
                bold=True, shadow=True, color=self.cfg.COLOR_TEXT)

        if subtitle:
            self.text((self.x_size // 2, 65), subtitle, font=18, anchor="mm",
                    color=self.cfg.COLOR_TEXT_SECONDARY, shadow=True)

        self.text((self.x_size - 50, 65), f'v{ver}', font=18, anchor="mm",
                bold=True, color=self.cfg.COLOR_TEXT_SECONDARY)

    def blend_colors(self, color1: str, color2: str, ratio: float) -> str:
        r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
        r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)

        r = max(0, min(255, int(r1 + (r2 - r1) * ratio)))
        g = max(0, min(255, int(g1 + (g2 - g1) * ratio)))
        b = max(0, min(255, int(b1 + (b2 - b1) * ratio)))

        return f"#{r:02x}{g:02x}{b:02x}"

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
            self.text((self.x_size // 2, self.y_size // 2), info_txt, anchor="mm", )
            self.paint()

    def draw_message_center(self, title: str, subtitle: Optional[str] = None,
                            icon: Optional[str] = None, status: str = "info") -> None:
        self.clear()

        max_panel_width = min(self.x_size - 100, 650)
        padding = 30

        title_font_size = 24
        subtitle_font_size = 20

        title_lines = self.wrap_text(self, title, title_font_size, max_panel_width - 2 * padding - (60 if icon else 0))
        title_height = len(title_lines) * 35

        subtitle_height = 0
        if subtitle:
            subtitle_lines = self.wrap_text(self, subtitle, subtitle_font_size,
                                            max_panel_width - 2 * padding - (60 if icon else 0))
            subtitle_height = len(subtitle_lines) * 28

        panel_height = 60 + title_height + subtitle_height + 30

        panel_height = min(panel_height, self.y_size - 120)

        panel_width = max_panel_width
        panel_x = (self.x_size - panel_width) // 2
        panel_y = (self.y_size - panel_height) // 2 - 30

        accent = status in ["success", "warning", "error"]
        self.panel([panel_x, panel_y, panel_x + panel_width, panel_y + panel_height],
                 title=None, shadow=True, accent=accent)

        icon_x = panel_x + 40
        icon_y = panel_y + panel_height // 2

        if icon:
            icon_size = 50
            icon_bg_size = icon_size + 10
            self.circle((icon_x, icon_y), icon_bg_size // 2,
                      fill=self.cfg.COLOR_PRIMARY_DARK, shadow=True)
            self.text((icon_x, icon_y), icon, font=32, anchor="mm",
                    color=self.cfg.COLOR_TEXT, shadow=True)

            text_x = icon_x + icon_bg_size + 25
            text_start_y = panel_y + 40
        else:
            text_x = panel_x + panel_width // 2
            text_start_y = panel_y + 40

        for i, line in enumerate(title_lines):
            y_pos = text_start_y + i * 35
            self.text((text_x, y_pos), line, font=title_font_size,
                    anchor="lm" if icon else "mm", bold=True, shadow=True)

        if subtitle:
            subtitle_start_y = text_start_y + title_height + 15
            subtitle_lines = self.wrap_text(self, subtitle, subtitle_font_size,
                                            max_panel_width - 2 * padding - (60 if icon else 0))

            if icon:
                subtitle_x = text_x
                anchor = "lm"
            else:
                subtitle_x = panel_x + panel_width // 2
                anchor = "mm"

            for i, line in enumerate(subtitle_lines):
                y_pos = subtitle_start_y + i * 28
                self.text((subtitle_x, y_pos), line, font=subtitle_font_size,
                        anchor=anchor, color=self.cfg.COLOR_TEXT_SECONDARY)

        if status != "info":
            status_colors = {
                "success": self.cfg.COLOR_SUCCESS,
                "warning": self.cfg.COLOR_WARNING,
                "error": self.cfg.COLOR_DANGER
            }
            status_color = status_colors.get(status, self.cfg.COLOR_PRIMARY)
            indicator_x = panel_x + panel_width - 25
            indicator_y = panel_y + 25
            self.circle((indicator_x, indicator_y), 12, fill=status_color, shadow=True)

        if status == "error":
            button_y = self.y_size - 60
            button_width = 160
            button_height = 40
            exit_x = self.x_size - button_width - 30
            self.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                      self.t.t("Exit"), "B", False)
        self.paint()

        while status == "error":
            if self.skip_first_input:
                self.input.reset()
                self.skip_first_input = False
            else:
                self.input.poll()

            if self.input.is_key("B"):
                break

    @staticmethod
    def wrap_text(ui: 'UIRenderer', text: str, font_size: int, max_width: int) -> list:
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

    def show_info(self, info: str) -> None:
        t = self.t

        current_page = 0

        def prepare_lines():
            self.clear()
            content_top = 0
            content_height = self.y_size - content_top

            panel_padding = 0
            panel_width = self.x_size - panel_padding * 2
            panel_height = content_height - 60

            text_padding = 15
            text_width = panel_width - text_padding * 2
            text_x = panel_padding + text_padding

            font_size = 22
            try:
                font = ImageFont.truetype(self.cfg.font_file, font_size)
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
                    bbox = self.active_draw.textbbox((0, 0), test_line, font=font)
                    line_width = bbox[2] - bbox[0]

                    if line_width <= text_width:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append(' '.join(current_line))

                        word_bbox = self.active_draw.textbbox((0, 0), word, font=font)
                        word_width = word_bbox[2] - word_bbox[0]

                        if word_width > text_width:
                            chars = list(word)
                            current_chars = []

                            for char in chars:
                                test_chars = ''.join(current_chars + [char])
                                char_bbox = self.active_draw.textbbox((0, 0), test_chars, font=font)
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
            self.clear()
            content_top = 0
            content_height = self.y_size - content_top

            panel_padding = 0
            panel_width = self.x_size - panel_padding * 2
            panel_height_val = content_height - 60

            self.panel([panel_padding, content_top, panel_padding + panel_width, content_top + panel_height_val],
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
                    bbox = self.active_draw.textbbox((0, 0), line, font=font)
                    line_width = bbox[2] - bbox[0]
                    if line_width > text_width:
                        truncated_line = line
                        while truncated_line and self.active_draw.textbbox((0, 0), truncated_line + "...", font=font)[
                            2] > text_width:
                            truncated_line = truncated_line[:-1]
                        line = truncated_line + "..."

                self.text((text_x, y_pos), line, font=19, anchor="lm")

            if total_pages > 1:
                page_info = f"{page + 1}/{total_pages}"
                page_x = self.x_size - 20
                self.text((page_x, text_y - 15), page_info, font=19,
                        color=self.cfg.COLOR_TEXT_SECONDARY, anchor="rm")

            for i in range(30):
                reflect_ratio = i / 30
                reflect_color = self.blend_colors(self.cfg.COLOR_GLOW, self.cfg.COLOR_BG, 1 - reflect_ratio)
                self.rect([0, self.y_size - i, self.x_size, self.y_size - i + 1], fill=reflect_color)

            button_y = self.y_size - 50
            button_width = 140
            button_height = 36

            if total_pages > 1:
                prev_x = 20
                self.button([prev_x, button_y, prev_x + button_width, button_y + button_height],
                          t.t("Previous"), "L1", False)

                next_x = self.x_size // 2 - button_width
                self.button([next_x, button_y, next_x + button_width, button_y + button_height],
                          t.t("Next"), "R1", False)
                exit_x = self.x_size - button_width - 20
                self.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                          t.t("Exit"), "B", False)
            else:
                exit_x = self.x_size - button_width - 20
                self.button([exit_x, button_y, exit_x + button_width, button_y + button_height],
                          t.t("Exit"), "B", False)

            self.paint()
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


# =========================
# Launcher main
# =========================
class LauncherApp:
    def __init__(self):
        self.cfg = Config()
        try:
            board_info = Path(self.cfg.root_path + "/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
        except:
            board_info = "RG35xxH"
        self.board_info = board_info

        try:
            lang_index = int(Path(self.cfg.root_path + "/mnt/vendor/oem/language.ini").read_text().splitlines()[0])
        except:
            lang_index = 2

        self.hw_info = self.cfg.board_mapping.get(self.board_info, 5)
        self.system_lang = self.cfg.system_list[lang_index if 0 <= lang_index < len(self.cfg.system_list) else 2]

        self.t = Translator(self.system_lang)
        self.ui = UIRenderer(self.cfg, self.t, self.hw_info)
        self.input = InputHandler(self.cfg)

        self.menu_items = [
            {
                "key": "system_updater",
                "name": self.t.t("System Updater"),
                "icon": "☑",
                "description": self.t.t("Stock OS Mod Updater")
            },
            {
                "key": "software_center",
                "name": self.t.t("Software Center"),
                "icon": "☆",
                "description": self.t.t("Install and manage software")
            },
            # {
            #     "key": "settings",
            #     "name": self.t.t("Settings"),
            #     "icon": "⚙️",
            #     "description": self.t.t("System settings")
            # },
        ]

        self.selected_index = 0
        self.skip_first_input = True

        self.card_width = self.ui.x_size - 240
        self.card_height = 100
        self.card_margin_top = 120
        self.card_margin_bottom = 80
        self.card_spacing_y = 15

        self.cards_per_page = self._calculate_cards_per_page()
        self.page_index = 0
        self.total_pages = max(1, (len(self.menu_items) + self.cards_per_page - 1) // self.cards_per_page)
        self.selected_index = 0

        self.update_info_dict: dict = {}
        self.session = requests.Session()
        self._active_threads = []

    def is_connected(self) -> bool:
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

    def _calculate_cards_per_page(self) -> int:
        available_height = self.ui.y_size - self.card_margin_top - self.card_margin_bottom
        card_with_spacing = self.card_height + self.card_spacing_y
        return max(1, available_height // card_with_spacing)

    def _calculate_rows_per_page(self) -> int:
        available_height = self.ui.y_size - self.card_margin_top - self.card_margin_bottom
        card_with_spacing = self.card_height + self.card_spacing_y
        return max(1, available_height // card_with_spacing)

    def draw_menu(self):
        self.ui.clear()
        self.ui.info_header(self.t.t("Launcher"), self.t.t("Choose an option"))

        start_idx = self.page_index * self.cards_per_page
        end_idx = min(start_idx + self.cards_per_page, len(self.menu_items))
        page_items = self.menu_items[start_idx:end_idx]

        total_height = len(page_items) * self.card_height + (len(page_items) - 1) * self.card_spacing_y
        start_y = self.card_margin_top + (self.ui.y_size - self.card_margin_top - self.card_margin_bottom - total_height) // 2

        for i, item in enumerate(page_items):
            y = start_y + i * (self.card_height + self.card_spacing_y)
            x = 120
            global_idx = start_idx + i
            is_selected = (global_idx == self.selected_index)
            self._draw_card(x, y, item, is_selected)

        if self.total_pages > 1:
            self._draw_page_indicator()

        button_y = self.ui.y_size - 60
        button_width = 160
        button_height = 40
        self.ui.button([20, button_y, 20 + button_width, button_y + button_height],
                       self.t.t("Select"), "A", primary=False)
        self.ui.button([self.ui.x_size - button_width - 20, button_y,
                        self.ui.x_size - 20, button_y + button_height],
                       self.t.t("Exit"), "B", primary=False)

        self.ui.paint()

    def _draw_card(self, x, y, item, is_selected):
        card_rect = [x, y, x + self.card_width, y + self.card_height]

        if is_selected:
            for offset in range(6, 0, -1):
                alpha = 80 - offset * 10
                glow_color = self.cfg.COLOR_PRIMARY + f"{alpha:02x}"
                glow_rect = [x - offset, y - offset, x + self.card_width + offset, y + self.card_height + offset]
                self.ui.rect(glow_rect, fill=glow_color, radius=16)
            fill_color = self.cfg.COLOR_PRIMARY_DARK
            border_color = self.cfg.COLOR_ACCENT
        else:
            fill_color = self.cfg.COLOR_CARD
            border_color = self.cfg.COLOR_BORDER_LIGHT

        self.ui.rect(card_rect, fill=fill_color, outline=border_color, width=2, radius=16, shadow=True)

        icon_radius = 32
        icon_center_x = x + 50
        icon_center_y = y + self.card_height // 2
        self.ui.circle((icon_center_x, icon_center_y), icon_radius, fill=self.cfg.COLOR_BG_LIGHT,
                    outline=self.cfg.COLOR_PRIMARY if is_selected else self.cfg.COLOR_BORDER_LIGHT)
        self.ui.text((icon_center_x, icon_center_y), item["icon"], font=32, anchor="mm",
                    color=self.cfg.COLOR_TEXT if is_selected else self.cfg.COLOR_TEXT_SECONDARY)

        name_x = x + 100
        name_y = y + 40
        self.ui.text((name_x, name_y), item["name"], font=20, anchor="lm",
                    bold=is_selected, color=self.cfg.COLOR_TEXT if is_selected else self.cfg.COLOR_TEXT_SECONDARY)

        desc_x = x + 100
        desc_y = y + 70
        desc = item.get("description", "")
        if len(desc) > 30:
            desc = desc[:27] + "..."
        self.ui.text((desc_x, desc_y), desc, font=14, anchor="lm",
                    color=self.cfg.COLOR_TEXT_TERTIARY if not is_selected else self.cfg.COLOR_TEXT)

    def _draw_page_indicator(self):
        dot_radius = 6
        dot_spacing = 15
        total_width = (self.total_pages - 1) * dot_spacing + 2 * dot_radius
        start_y = (self.ui.y_size - total_width) // 2 + 20
        x = self.ui.x_size - 80

        self.ui.text((self.ui.x_size - 40, self.ui.y_size // 2 + 20), f"{self.page_index + 1} / {self.total_pages}", font=18, anchor="mm",
                  color=self.cfg.COLOR_TEXT_SECONDARY, shadow=True)

        for i in range(self.total_pages):
            y = start_y + i * dot_spacing + dot_radius
            fill = self.cfg.COLOR_PRIMARY if i == self.page_index else self.cfg.COLOR_TEXT_TERTIARY
            self.ui.circle((x, y), dot_radius, fill=fill)

    def handle_input(self):
        if self.skip_first_input:
            self.input.reset()
            self.skip_first_input = False
            return

        self.input.poll()
        if not self.input.code_name:
            return

        if self.input.is_key("DY"):
            direction = self.input.value
            new_index = self.selected_index + direction
            if 0 <= new_index < len(self.menu_items):
                self.selected_index = new_index
                self._adjust_page_for_selected()
            elif direction == -1 and self.page_index > 0:
                self.page_index -= 1
                self.selected_index = min((self.page_index + 1) * self.cards_per_page - 1, len(self.menu_items) - 1)
            elif direction == 1 and self.page_index < self.total_pages - 1:
                self.page_index += 1
                self.selected_index = self.page_index * self.cards_per_page

        elif self.input.is_key("DX"):
            direction = self.input.value
            if direction == -1 and self.page_index > 0:
                self.page_index -= 1
                self.selected_index = min((self.page_index + 1) * self.cards_per_page - 1, len(self.menu_items) - 1)
            elif direction == 1 and self.page_index < self.total_pages - 1:
                self.page_index += 1
                self.selected_index = self.page_index * self.cards_per_page
            self._adjust_page_for_selected()

        elif self.input.is_key("A"):
            item = self.menu_items[self.selected_index]
            self.launch_application(item["key"], item["name"])
        elif self.input.is_key("B"):
            self.cleanup()
            sys.exit(0)

        self.input.reset()

    def _adjust_page_for_selected(self):
        page = self.selected_index // self.cards_per_page
        if page != self.page_index:
            self.page_index = page

    def launch_application(self, app_key, app_item):
        self.ui.tips_info(f'{self.t.t("Launching")}: {self.t.t(app_item)}')
        self.ui.draw_end()
        self.input = None

        script_map = {
            "system_updater": "upgrade.py",
            "software_center": "installer.py"
        }

        script = script_map.get(app_key)
        script = os.path.join(APP_PATH, script)
        if not script or not os.path.exists(script):
            print(f"Error: {script} not found")
            self.reinit_ui()
            return

        try:
            result = subprocess.run([sys.executable, script], check=False)
            if result.returncode != 0:
                print(f"Subprocess {script} exited with code {result.returncode}")
        except Exception as e:
            print(f"Failed to launch {script}: {e}")

        self.reinit_ui()

    def reinit_ui(self):
        self.cards_per_page = self._calculate_cards_per_page()
        self.total_pages = max(1, (len(self.menu_items) + self.cards_per_page - 1) // self.cards_per_page)
        self.selected_index = min(self.selected_index, len(self.menu_items) - 1)
        self.page_index = self.selected_index // self.cards_per_page

    def cleanup(self):
        try:
            self.ui.draw_end()
        except:
            pass

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
                    self.progress_bar(ui.y_size // 2 - 20, percent, label_top=label_top, label_bottom=label_bottom)
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
            self.exit_cleanup(2, self.ui, self.cfg)

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
            self.exit_not_cleanup(36)
        else:
            LOGGER.error("MD5 verification failed. Expected: %s, Got: %s", update_md5, down_md5)
            self.draw_message_center(t.t("Verification Failed"), t.t("File integrity check failed."), "✘", "error")
            self.exit_cleanup(3, self.ui, self.cfg)

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

            if total_size > file_size > 0:
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

    def progress_bar(self, y_center: int, percent: float, label_top: Optional[str] = None,
                     label_bottom: Optional[str] = None, show_percent: bool = True) -> None:
        bar_left = 50
        bar_right = self.ui.x_size - 50
        bar_top = y_center - 16
        bar_bottom = y_center + 16
        bar_height = bar_bottom - bar_top

        bar_left = int(bar_left)
        bar_right = int(bar_right)
        bar_top = int(bar_top)
        bar_bottom = int(bar_bottom)
        bar_height = int(bar_height)

        shadow_offset = 2
        self.ui.rect([bar_left - shadow_offset, bar_top - shadow_offset,
                   bar_right + shadow_offset, bar_bottom + shadow_offset],
                  fill=self.cfg.COLOR_SHADOW, radius=int(bar_height // 2))

        self.ui.rect([bar_left, bar_top, bar_right, bar_bottom],
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
                color = self.ui.blend_colors(self.cfg.COLOR_PRIMARY, self.cfg.COLOR_ACCENT, overall_ratio)

                self.ui.rect(gradient_rect, fill=color, radius=progress_radius)

            if show_percent:
                progress_text = f"{int(percent + 1)}%"
                text_x = (bar_left + bar_right) // 2
                text_y = y_center

                if percent < 50:
                    text_color = self.cfg.COLOR_TEXT
                else:
                    text_color = self.cfg.COLOR_BG

                self.ui.text((text_x, text_y), progress_text, font=20, anchor="mm",
                          color=text_color, shadow=percent >= 50)

        if label_top:
            self.ui.text((self.ui.x_size // 2, bar_top - 25), label_top,
                      font=22, anchor="mm", bold=True, shadow=True)
        if label_bottom:
            self.ui.text((self.ui.x_size // 2, bar_bottom + 25), label_bottom,
                      font=18, anchor="mm", color=self.cfg.COLOR_TEXT_SECONDARY)

    def draw_message_center(self, title: str, subtitle: Optional[str] = None,
                            icon: Optional[str] = None, status: str = "info") -> None:
        ui = self.ui
        ui.clear()

        max_panel_width = min(ui.x_size - 100, 650)
        padding = 30

        title_font_size = 24
        subtitle_font_size = 20

        title_lines = self.ui.wrap_text(ui, title, title_font_size, max_panel_width - 2 * padding - (60 if icon else 0))
        title_height = len(title_lines) * 35

        subtitle_height = 0
        if subtitle:
            subtitle_lines = self.ui.wrap_text(ui, subtitle, subtitle_font_size,
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
            subtitle_lines = self.ui.wrap_text(ui, subtitle, subtitle_font_size,
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
                    self.ui.show_info(log_content)
                break

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

    def _cleanup_before_restart(self):
        self._stop_all_threads()
        self.input.reset()
        self.ui.draw_end()

        import gc
        gc.collect()
        time.sleep(0.5)

    def _stop_all_threads(self):
        """停止所有活动线程"""
        self._shutdown_flag = True
        time.sleep(0.1)

        for thread in self._active_threads[:]:
            if thread.is_alive():
                thread.join(timeout=0.5)
                if thread.is_alive():
                    LOGGER.warning(f"Thread {thread.name} failed to terminate gracefully")
            self._active_threads.remove(thread)

        self.input.reset()

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
            for p in (cfg.tmp_info, cfg.tmp_app_update):
                if os.path.isfile(p):
                    os.remove(p)
                elif os.path.isdir(p):
                    shutil.rmtree(p)
        except Exception as e:
            LOGGER.error("Error during exit cleanup: %s", e)
        finally:
            ui.draw_end()
            sys.exit(code)

    def run(self):
        if not self.is_connected():
            self.ui.draw_message_center(
                self.t.t("No Internet Connection"),
                self.t.t("Please check your network settings"),
                "✈", "error"
            )
            self.cleanup()
            sys.exit(0)

        app_ver = app_update_url = app_md5 = ""

        self.update_info_dict = self.fetch_remote_info()
        if self.update_info_dict.get('app'):
            app_ver = self.update_info_dict.get('app').get('version', 'Unknown')
            app_update_url = self.cfg.server_url + self.update_info_dict.get('app').get('filename')
            app_md5 = self.update_info_dict.get('app').get('md5')
            LOGGER.info(f"app: v{app_ver}")

        if app_ver != "Unknown" and cur_app_ver < app_ver and bool(app_update_url):
            self.update_app(app_ver, app_update_url, app_md5)

        while True:
            self.draw_menu()
            self.handle_input()


if __name__ == "__main__":
    LauncherApp().run()