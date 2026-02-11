from main import hw_info, system_lang
from graphic import screen_resolutions, UserInterface
from language import Translator
import os
import input
import sys
import threading
import time
from anbernic import Anbernic

ver="v1.2"
translator = Translator(system_lang)
an = Anbernic()
skip_input_check = True
current_window = "browser"
current_path = an.get_sd_storage_path()
file_list = []
menu_deep = [0] * 20
current_deep = 0
selected_index = menu_deep[current_deep]
gr = UserInterface()

slideshow_active = False
slideshow_index = 0
slideshow_interval = 3
last_slide_time = 0
slideshow_images = []

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 11))

button_x = x_size - 120
button_y = y_size - 30
ratio = y_size / x_size

def start():
    print("[INFO]Starting Image Browser...")
    gr.draw_log(
        f"{translator.translate('Image Browser')} {ver}", fill=gr.colorBlue, outline=gr.colorBlueD1
    )
    gr.draw_paint()
    time.sleep(2)
    handle_browser_input()


def update() -> None:
    global current_window, skip_input_check, slideshow_active

    if skip_input_check:
        input.reset_input()
        skip_input_check = False
    else:
        input.check()

    if input.key("MENUF"):
        gr.draw_log(
            f"{translator.translate('Exiting...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(2)
        gr.draw_end()
        print("[INFO]Exiting Image Browser...")
        sys.exit()

    if current_window == "browser":
        handle_browser_input()
    elif current_window == "image_viewer":
        handle_image_viewer_input()
    elif current_window == "slideshow":
        handle_slideshow_input()
    else:
        handle_browser_input()


def handle_browser_input() -> None:
    global current_window, selected_index, current_path, menu_deep, current_deep, skip_input_check, slideshow_active, slideshow_index, slideshow_images, last_slide_time

    update_file_list()

    if file_list:
        if input.key("DY"):
            selected_index = (selected_index + input.value) % len(file_list)
        elif input.key("DX"):
            selected_index = (selected_index + input.value * 5) % len(file_list)
        elif input.key("L1"):
            if selected_index > 0:
                selected_index = max(0, selected_index - max_elem)
        elif input.key("R1"):
            if selected_index < len(file_list) - 1:
                selected_index = min(
                    len(file_list) - 1, selected_index + max_elem
                )
        elif input.key("X") and file_list[selected_index][2] == "image":
            slideshow_images = [entry for entry in file_list if entry[2] == "image"]
            if len(slideshow_images) > 0:
                slideshow_active = True
                slideshow_index = slideshow_images.index(file_list[selected_index])
                last_slide_time = time.time()
                current_window = "slideshow"
                enter_fullscreen(slideshow_images[slideshow_index][1], is_slideshow=True)
                skip_input_check = True
                return

        elif input.key("A"):
            entry_type = file_list[selected_index][2]
            if entry_type == "dir":
                new_current_path = file_list[selected_index][1]
                new_file_list = an.get_current_path_files(new_current_path)
                if len(new_file_list) > 0:
                    menu_deep[current_deep] = selected_index
                    current_deep+=1
                    current_path = file_list[selected_index][1]
                    update_file_list()
                    selected_index = 0
                else:
                    menu_deep[current_deep] = selected_index
                    gr.draw_log(f"{translator.translate('No valid file found!')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
                    gr.draw_paint()
                    time.sleep(1)
            else:
                enter_fullscreen(file_list[selected_index][1])
                return
        elif input.key("B"):
            go_back_directory()
            if current_deep > 0:
                current_deep-=1
            selected_index = menu_deep[current_deep]
        elif input.key("Y"):
            an.switch_sd_storage()
            new_current_path = an.get_sd_storage_path()
            if not current_path == new_current_path:
                current_path = an.get_sd_storage_path()
                selected_index = 0
                current_deep = 0
                menu_deep = [0] * 20
                skip_input_check = True
                return

    menu_deep[current_deep] = selected_index
    gr.draw_clear()
    gr.draw_rectangle_r([10, 40, x_size-10, y_size-40], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text((50, 20), f"{translator.translate('Path')}: {current_path}", font=19, anchor="lm")
    gr.draw_text(
        (button_x + 50, 20),
        f"{selected_index + 1} / {len(file_list)}",
        anchor="mm",
    )

    if len(file_list) > 0:
        if selected_index >= len(file_list):
            selected_index = 0
        start_idx = int(selected_index / max_elem) * max_elem
        end_idx = start_idx + max_elem
    
        for i, entry in enumerate(file_list[start_idx:end_idx]):
            gr.row_list(
                entry[0][:48] + "..." if len(entry[0]) > 50 else entry[0],
                (20, 50 + (i * 35)),
                x_size -40,
                i == (selected_index % max_elem),
            )

        cur_file = file_list[selected_index][2]
        if cur_file == 'image':
            gr.preview_image(file_list[selected_index][1], target_x = int(x_size / 2 + 10), target_y = int(y_size / 4), target_width = int(x_size / 2 - 30), target_height = int((x_size / 2 - 30) * ratio))
            gr.button_circle((210, button_y), "X", f"{translator.translate('Slideshow')}")
        gr.button_circle((20, button_y), "A", f"{translator.translate('Open')}")
    else:
        gr.draw_text(
            (x_size / 2, y_size / 2), f"{translator.translate('No valid file found!')}", anchor="mm"
        )

    gr.button_circle((120, button_y), "B", f"{translator.translate('Back')}")
    gr.button_circle((button_x-170, button_y), "Y", f"{translator.translate('Switch')} TF: {an.get_sd_storage()}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

    gr.draw_paint()


def handle_image_viewer_input():
    global current_window, selected_index
    
    if input.key("DY"):
        selected_index = (selected_index + input.value) % len(file_list)
        enter_fullscreen(file_list[selected_index][1])
    elif input.key("DX"):
        selected_index = (selected_index + input.value * 5) % len(file_list)
        enter_fullscreen(file_list[selected_index][1])
    elif input.key("L1"):
        if selected_index > 0:
            selected_index = max(0, selected_index - max_elem)
        enter_fullscreen(file_list[selected_index][1])
    elif input.key("R1"):
        if selected_index < len(file_list) - 1:
            selected_index = min(
                len(file_list) - 1, selected_index + max_elem
            )
        enter_fullscreen(file_list[selected_index][1])
    elif input.key("B"):
        exit_fullscreen()


def handle_slideshow_input():
    global slideshow_active, slideshow_index, current_window, last_slide_time, selected_index, slideshow_images, slideshow_interval, skip_input_check
    input.reset_input()
    thread = threading.Thread(target=input.check)
    thread.start()
    
    while True:
        current_time = time.time()
        if current_time - last_slide_time >= slideshow_interval:
            slideshow_index = (slideshow_index + 1) % len(slideshow_images)
            last_slide_time = time.time()
            enter_fullscreen(slideshow_images[slideshow_index][1], is_slideshow=True)
        elif input.slide_key():
            slideshow_active = False
            current_window = "browser"
            if len(slideshow_images)>1:
                selected_index = slideshow_index
            skip_input_check = True
            return

def enter_fullscreen(image_path, is_slideshow=False):
    global current_window
    if not is_slideshow:
        current_window = "image_viewer"
    gr.draw_clear()
    gr.display_image(image_path)
    gr.draw_paint()

def exit_fullscreen():
    global current_window, skip_input_check
    current_window = "browser"
    skip_input_check = True

def update_file_list():
    global current_path, file_list
    gr.button_circle((20, 6), " ", " ", color=gr.colorRed)
    gr.draw_paint()
    file_list = an.get_current_path_files(current_path)

def go_back_directory():
    global current_path, current_deep
    if current_deep > 0:
        current_path = os.path.dirname(current_path)
        update_file_list()
