from main import hw_info, system_lang
from graphic import screen_resolutions, UserInterface
from language import Translator
from anbernic import Anbernic
from pathlib import Path
import os
import input
import sys
import time
import math
from set import Set

translator = Translator(system_lang)
selected_position = 0
menu_selected_position = 0
opt_selected_position = 0
selected_menu = ""
current_window = "menu"
help_txt = ""
skip_input_check = True
an = Anbernic()
set = Set()
gr = UserInterface()

try:
    ver = Path("/mnt/mod/ctrl/configs/ver.cfg").read_text().splitlines()[0]
except (FileNotFoundError, IndexError):
    ver = 'Unknown'

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 7))

button_x = x_size - 140
button_y = y_size - 30
ratio = y_size / x_size


def start() -> None:
    print("Starting Modify System Tools...")
    gr.draw_log(
        f"{translator.translate('welcome')}", fill=gr.colorBlue, outline=gr.colorBlueD1
    )
    gr.draw_paint()
    time.sleep(1)
    load_menu_menu()


def update() -> None:
    global current_window, \
            selected_position, \
            skip_input_check

    if skip_input_check:
        input.reset_input()
        skip_input_check = False
    else:
        input.check()

    if input.key("SELECT"):
        gr.draw_log(
            f"{translator.translate('Exiting...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(1)
        gr.draw_end()
        print("Exiting Modify System Tools...")
        sys.exit()

    if current_window == "menu":
        load_menu_menu()
    elif current_window == "options":
        load_options_menu()
    else:
        load_menu_menu()


def load_menu_menu() -> None:
    global \
        menu_selected_position, \
        selected_menu, \
        current_window, \
        skip_input_check

    all_menu = set.get_all_menus()

    if not all_menu:
        gr.draw_text((x_size/2, y_size/2), translator.translate('menu.empty'), font=23, anchor='mm')
        gr.draw_paint()
        time.sleep(2)
        current_window = "menu"
        return

    if all_menu:
        if input.key("DY"):
            menu_selected_position = (menu_selected_position + input.value) % len(all_menu)
        elif input.key("A"):
            current_window = "options"
            selected_menu = all_menu[menu_selected_position]
            skip_input_check = True
            return

    gr.draw_clear()

    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 40], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text((x_size / 2, 20), f"{translator.translate('Modify System Tools')} v{ver} - {math.ceil((menu_selected_position + 1) / max_elem)} / {math.ceil(len(all_menu) / max_elem)}", font=23, anchor="mm")

    start_idx = int(menu_selected_position / max_elem) * max_elem
    end_idx = start_idx + max_elem
    for i, system in enumerate(all_menu[start_idx:end_idx]):
        gr.row_list(
            translator.translate(system), (20, 50 + (i * 35)), x_size - 40, i == (menu_selected_position % max_elem)
        )

    help_txt = set.get_menu_help(all_menu[menu_selected_position])
    gr.draw_help(
        f"{translator.translate(help_txt)}", fill=gr.colorBlueD1, outline=gr.colorBlueD1
    )

    gr.button_circle((30, button_y), "A", f"{translator.translate('Select')}")
    gr.button_rectangle((button_x, button_y), "SEL", f"{translator.translate('Exit')}")

    gr.draw_paint()


def load_options_menu() -> None:
    global \
        current_window, \
        skip_input_check, \
        selected_menu, \
        opt_selected_position

    exit_menu = False

    opt_list = set.get_menu_option(selected_menu)

    if len(opt_list) < 1:
        current_window = "menu"
        gr.draw_log(
            f"{translator.translate('No available settings found.')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(2)
        exit_menu = True

    if input.key("B"):
        exit_menu = True
    elif input.key("A"):
        gr.draw_log(
            f"{translator.translate('Executing...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        #selected_operation = set.get_menu_operation(opt_selected_position, selected_menu)
        command = set.get_menu_operation(opt_selected_position, selected_menu)
        storage_path = an.get_sd_storage_path()
        success, output, file = set.execute_command(command, storage_path)
        if success:
            if command.startswith("tools:st"):
                gr.draw_clear()
                gr.draw_paint()
                os.system('sync')
                gr.draw_end()
                print("Exiting Modify System Tools...")
                sys.exit()
            status_msg = f"{translator.translate('Done')}. {translator.translate(output)}\n{file}"
            status_color = gr.colorBlue
        else:
            status_msg = f"{translator.translate('Error')}. {translator.translate(output)}\n{file}"
            status_color = gr.colorRed
        
        gr.draw_log(f"{status_msg}", fill=status_color, outline=status_color, font=19)
        gr.draw_paint()
        time.sleep(3)
        if command == "tools:apps":
            os.system('sync')
            gr.draw_log(f"{translator.translate('Rebooting...')}", fill=status_color, outline=status_color, font=19)
            gr.draw_paint()
            os.system('reboot')
            time.sleep(300)

    elif input.key("DY"):
        opt_selected_position = (opt_selected_position + input.value) % len(opt_list)

    elif input.key("Y") and menu_selected_position < 2:
        an.switch_sd_storage()

    if exit_menu:
        current_window = "menu"
        gr.draw_clear()
        opt_selected_position = 0
        skip_input_check = True
        return

    gr.draw_clear()

    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 40], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text(
        (x_size / 2, 20),
        f"{translator.translate(selected_menu)} - {translator.translate('options')} {opt_selected_position + 1} {translator.translate('of')} {len(opt_list)}",
        font=23, anchor="mm",
    )

    start_idx = int(opt_selected_position / max_elem) * max_elem
    end_idx = start_idx + max_elem
    for i, para in enumerate(opt_list[start_idx:end_idx]):
        gr.row_list(
            f"{translator.translate(para)}",
            (20, 50 + (i * 35)),
            x_size -40,
            i == (opt_selected_position % max_elem),
        )

    help_txt = set.get_opt_help(opt_selected_position, selected_menu)
    gr.draw_help(
        f"{translator.translate(help_txt)}",
        fill=None, outline=gr.colorBlueD1
    )

    gr.button_circle((30, button_y), "A", f"{translator.translate('Select')}")
    gr.button_circle((150, button_y), "B", f"{translator.translate('Back')}")
    if menu_selected_position < 2:
        gr.button_circle((270, button_y), "Y", f"{translator.translate('Save in')} TF: {an.get_sd_storage()}")
    gr.button_rectangle((button_x, button_y), "SEL", f"{translator.translate('Exit')}")

    gr.draw_paint()
