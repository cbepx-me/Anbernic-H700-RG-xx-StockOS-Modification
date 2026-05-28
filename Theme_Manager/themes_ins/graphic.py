import ctypes
import os
from main import hw_info
from typing import Optional

import sdl2
from PIL import Image, ImageDraw, ImageFont

script_dir = os.path.dirname(os.path.abspath(__file__))
local_font_list = os.path.join(script_dir, "font/font.ttf")
sys_font_file = os.path.join("/mnt/vendor/bin/default.ttf")
font_file = local_font_list if os.path.exists(local_font_list) else sys_font_file

color_text = "#ffffff"

screen_resolutions = {
    1: (720, 720, 16),
    2: (720, 480, 9)
}

class UserInterface:
    _instance: Optional["UserInterface"] = None
    _initialized: bool = False

    screen_width, screen_height, max_elem = screen_resolutions.get(hw_info, (640, 480, 9))
    colorBlue = "#0072bb"
    colorBlueD1 = "#004f7f"
    colorGray = "#292929"
    colorGrayL1 = "#383838"
    colorGrayD2 = "#141414"
    colorGreen = "#00ff00"
    colorRed = "#cb0202"
    colorYellow = "#ffd700"
    colorGrayL2 = "#00d7ff"

    active_image: Image.Image
    active_draw: ImageDraw.ImageDraw

    def __init__(self):
        if self._initialized:
            return
        self.window = self._create_window()
        self.renderer = self._create_renderer()
        self.draw_start()
        self.opt_stretch = True
        self._initialized = True

    def __new__(cls):
        if not cls._instance:
            cls._instance = super(UserInterface, cls).__new__(cls)
        return cls._instance

    ###
    # WINDOW MANAGEMENT
    ###

    def create_image(self):
        """Create a new blank RGBA image for drawing."""
        return Image.new("RGBA", (self.screen_width, self.screen_height), color="black")

    def draw_start(self):
        """Initialize drawing for a new frame."""
        # Render directly to the screen
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
            0,  # Size ignored in fullscreen mode
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
            renderer = sdl2.render.SDL_CreateRenderer(
                self.window, -1, sdl2.render.SDL_RENDERER_SOFTWARE
            )
            if not renderer:
                print(f"Failed to create renderer: {sdl2.SDL_GetError()}")
                raise RuntimeError("Failed to create renderer")

        sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b"0")
        return renderer

    def draw_paint(self):
        # Convert PIL image to SDL2 texture at base resolution
        if hw_info == 3:
            rotated_image = self.active_image.rotate(90, expand=True)
            rgba_data = rotated_image.tobytes()
            temp_width, temp_height = rotated_image.size
        else:
            rgba_data = self.active_image.tobytes()
            temp_width, temp_height = self.screen_width, self.screen_height

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

        # Get current window size
        window_width = ctypes.c_int()
        window_height = ctypes.c_int()
        sdl2.SDL_GetWindowSize(
            self.window, ctypes.byref(window_width), ctypes.byref(window_height)
        )
        window_width, window_height = window_width.value, window_height.value

        # Let the user decide whether to stretch to fit or preserve aspect ratio
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

    def draw_end(self):
        sdl2.SDL_DestroyRenderer(self.renderer)
        sdl2.SDL_DestroyWindow(self.window)
        sdl2.SDL_Quit()

    ###
    # DRAWING FUNCTIONS
    ###

    def draw_clear(self):
        self.active_draw.rectangle(
            [0, 0, self.screen_width, self.screen_height], fill="black"
        )

    def draw_text(
        self,
        position: tuple[float, float],
        text: str,
        font: int = 21,
        color: str = color_text,
        **kwargs,
    ):
        self.active_draw.text(
            position, text, font=ImageFont.truetype(font_file, font), fill=color, **kwargs
        )

    def draw_rectangle(
        self,
        position,
        fill: str | None = None,
        outline: str | None = None,
        width: int = 1,
    ):
        self.active_draw.rectangle(position, fill=fill, outline=outline, width=width)

    def draw_rectangle_r(
        self,
        position,
        radius: float,
        fill: str | None = None,
        outline: str | None = None,
    ):
        self.active_draw.rounded_rectangle(position, radius, fill=fill, outline=outline)

    def row_list(self, text: str, pos: tuple[int, int], width: int, selected: bool) -> None:
        self.draw_rectangle_r(
            [pos[0], pos[1], pos[0] + width, pos[1] + 32],
            5,
            fill=(self.colorBlue if selected else self.colorGrayL1),
        )
        self.draw_text((pos[0] + 5, pos[1] + 5), text)

    def draw_circle(
        self,
        position,
        radius: int,
        fill: str | None = None,
        outline: str | None = color_text,
    ):
        self.active_draw.ellipse(
            [
                position[0],
                position[1],
                position[0] + radius,
                position[1] + radius,
            ],
            fill=fill,
            outline=outline,
        )

    def draw_log(self, text, fill="Black", outline="black", width=500, font=21):
        x = (self.screen_width - width) / 2
        y = (self.screen_height - 80) / 2
        rect_height = 80
        self.draw_rectangle_r([x, y, x + width, y + 80], 5, fill=fill, outline=outline)
    
        font_obj = ImageFont.truetype(font_file, font)
        padding = 10
        max_width = width - 2 * padding
    
        lines = []
        current_line = ""
        for word in text.split():
            test_line = f"{current_line} {word}".strip() if current_line else word
            bbox = font_obj.getbbox(test_line)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                
                bbox = font_obj.getbbox(word)
                word_width = bbox[2] - bbox[0]
                if word_width <= max_width:
                    current_line = word
                else:
                    remaining = word
                    while remaining:
                        substring = ""
                        for char in remaining:
                            temp_sub = substring + char
                            bbox = font_obj.getbbox(temp_sub)
                            temp_width = bbox[2] - bbox[0]
                            if temp_width <= max_width:
                                substring = temp_sub
                            else:
                                break
                        if substring:
                            lines.append(substring)
                            remaining = remaining[len(substring):]
                        else:
                            break
        if current_line:
            lines.append(current_line)
    
        ascent, descent = font_obj.getmetrics()
        line_height = int((ascent + descent) * 1.2)
        total_height = len(lines) * line_height
        start_y = y + (rect_height - total_height) // 2
    
        for i, line in enumerate(lines):
            text_x = x + width / 2
            text_y = start_y + i * line_height + ascent - 5
            self.draw_text((text_x, text_y), line, font, anchor="mm")
    
    
    def draw_help(self, text, fill="Black", outline="black", font=21):
        x = 20
        y = (self.screen_height - 110)
        rect_width = self.screen_width - 40
        rect_height = 75
        self.draw_rectangle_r([x, y, self.screen_width - 20, y + rect_height], 5, fill=fill, outline=outline)
    
        font_obj = ImageFont.truetype(font_file, font)
        padding = 10
        max_width = rect_width - 2 * padding
    
        lines = []
        current_line = ""
        for word in text.split():
            test_line = f"{current_line} {word}".strip() if current_line else word
            bbox = font_obj.getbbox(test_line)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                
                bbox = font_obj.getbbox(word)
                word_width = bbox[2] - bbox[0]
                if word_width <= max_width:
                    current_line = word
                else:
                    remaining = word
                    while remaining:
                        substring = ""
                        for char in remaining:
                            temp_sub = substring + char
                            bbox = font_obj.getbbox(temp_sub)
                            temp_width = bbox[2] - bbox[0]
                            if temp_width <= max_width:
                                substring = temp_sub
                            else:
                                break
                        if substring:
                            lines.append(substring)
                            remaining = remaining[len(substring):]
                        else:
                            break
        if current_line:
            lines.append(current_line)
    
        ascent, descent = font_obj.getmetrics()
        line_height = int((ascent + descent) * 1)
        total_height = len(lines) * line_height
        start_y = y + (rect_height - total_height) // 2

        for i, line in enumerate(lines):
            text_x = self.screen_width // 2
            text_y = start_y + i * line_height +10
            self.draw_text((text_x, text_y), line, font, anchor="mm")


    def draw_help2(self, text, font=21):
        rect_width = self.screen_width - 40
        rect_height = 30
        font_obj = ImageFont.truetype(font_file, font)
        padding = 10
        max_width = rect_width - 2 * padding
    
        lines = []
        current_line = ""
        for word in text.split():
            test_line = f"{current_line} {word}".strip() if current_line else word
            bbox = font_obj.getbbox(test_line)
            test_width = bbox[2] - bbox[0]
            
            if test_width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                    current_line = ""
                
                bbox = font_obj.getbbox(word)
                word_width = bbox[2] - bbox[0]
                if word_width <= max_width:
                    current_line = word
                else:
                    remaining = word
                    while remaining:
                        substring = ""
                        for char in remaining:
                            temp_sub = substring + char
                            bbox = font_obj.getbbox(temp_sub)
                            temp_width = bbox[2] - bbox[0]
                            if temp_width <= max_width:
                                substring = temp_sub
                            else:
                                break
                        if substring:
                            lines.append(substring)
                            remaining = remaining[len(substring):]
                        else:
                            break
        if current_line:
            lines.append(current_line)
    
        ascent, descent = font_obj.getmetrics()
        line_height = int((ascent + descent) * 1)
        total_height = len(lines) * line_height
        start_y = (total_height + rect_height) // 2
    
        for i, line in enumerate(lines):
            text_x = self.screen_width // 2
            text_y = start_y + i * line_height +10
            self.draw_text((text_x, text_y), line, font, anchor="mm")

    def get_text_width(self, text, font):
        image = Image.new('RGB', (1, 1))
        draw = ImageDraw.Draw(image)
        font_obj = ImageFont.truetype(font_file, font)
        bbox = draw.textbbox((0, 0), text, font=font_obj)
        width = bbox[2] - bbox[0]
        return width

    def button_circle(self, pos: tuple[int, int], button: str, text: str) -> None:
        self.draw_circle(pos, 25, fill=self.colorBlueD1)
        self.draw_text((pos[0] + 12, pos[1] + 12), button, anchor="mm")
        self.draw_text((pos[0] + 30, pos[1] + 12), text, font=19, anchor="lm")
    
    
    def button_rectangle(self, pos: tuple[int, int], button: str, text: str) -> None:
        self.draw_rectangle_r(
            (pos[0], pos[1], pos[0] + 60, pos[1] + 25), 5, fill=self.colorGrayL1
        )
        self.draw_text((pos[0] + 30, pos[1] + 12), button, anchor="mm")
        self.draw_text((pos[0] + 65, pos[1] + 12), text, font=19, anchor="lm")

    def display_image(self, image_path, target_x=0, target_y=0, target_width=None, target_height=None, rota=1):
        if target_width is None:
            target_width = self.screen_width - target_x
        if target_height is None:
            target_height = self.screen_height - target_y
        img = Image.open(image_path)
        img.thumbnail((target_width, target_height))
        paste_x = target_x + (target_width - img.width) // 2
        paste_y = target_y + (target_height - img.height) // 2
        if hw_info == 3 and rota == 1:
            img = img.rotate(-90, expand=True)
        self.active_image.paste(img, (paste_x, paste_y))
        self.draw_paint()
