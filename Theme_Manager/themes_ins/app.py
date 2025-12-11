from pathlib import Path
from main import hw_info, system_lang
from graphic import screen_resolutions, UserInterface
from language import Translator
import subprocess
import os
import config as cf
import input
import sys
import time
from anbernic import Anbernic
from themes import Themes

ver="v1.2"
translator = Translator(system_lang)
gr = UserInterface()
selected_position = 0
theme_selected_position = 0
logo_selected_position = 0
selected_system = ""
current_window = "console"
an = Anbernic()
themes = Themes()
skip_input_check = False

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 9))

button_x = x_size - 120
button_y = y_size - 30
ratio = y_size / x_size

help_info = {
    0: 'theme_help',
    1: 'logo_help',
    2: 'back.theme_help',
    3: 'restore.theme_help',
    4: 'restore.stock_help'
}

def start():
    print("[INFO]Starting Themes Manager...")
    gr.draw_log(
        f"{translator.translate('Welcome')}", fill=gr.colorBlue, outline=gr.colorBlueD1
    )
    gr.draw_paint()
    time.sleep(2)
    load_console_menu()


def update() -> None:
    global current_window, selected_position, skip_input_check

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
        print("[INFO]Exiting Themes Manager...")
        sys.exit()

    if current_window == "console":
        load_console_menu()
    elif current_window == "theme":
        load_theme_menu()
    elif current_window == "logo":
        load_logo_menu()
    elif current_window == "help":
        load_help_menu()
    else:
        load_console_menu()


def load_console_menu() -> None:
    global selected_position, selected_system, current_window, skip_input_check

    #available_systems = themes.get_available_systems(an.get_sd_storage_path())
    available_systems = ["themes", "bootlogo", "back.theme", "restore.theme", "restore.stock"]
    selected_system = available_systems[selected_position]

    if available_systems:
        if input.key("DY"):
            selected_position = (selected_position + input.value) % len(available_systems)
        elif input.key("A"):
            selected_system = available_systems[selected_position]
            if selected_system == "themes":
                current_window = "theme"
            elif selected_system == "bootlogo":
                current_window = "logo"
            elif selected_system == "back.theme":
                gr.draw_log(f"{translator.translate('Backing up in progress...')}", fill=gr.colorBlue,
                            outline=gr.colorBlueD1)
                gr.draw_paint()
                back_path = "/mnt/mmc/anbernic/backup"
                if not os.path.exists(back_path):
                    os.mkdir(back_path)
                back_file = f"{back_path}/Theme_bak.zip"
                files = [
                    "/mnt/vendor/res1/",
                    "/mnt/vendor/res2/",
                    "/mnt/vendor/res3/",
                    "/mnt/vendor/bin/default.ttf"
                ]
                files_to_compress = []
                for file in files:
                    if os.path.exists(file):
                        files_to_compress.append(file)
                back_command = f"zip -qr {back_file} {' '.join(files_to_compress)}"
                subprocess.run(back_command, shell=True, check=True)
                gr.draw_log(
                    f"{translator.translate('Theme backup successful!')} {back_file}", fill=gr.colorBlue, outline=gr.colorBlueD1
                )
                gr.draw_paint()
                time.sleep(2)
            elif selected_system == "restore.theme":
                back_path = "/mnt/mmc/anbernic/backup"
                if not os.path.exists(back_path):
                    os.mkdir(back_path)
                back_file = f"{back_path}/Theme_bak.zip"
                if not os.path.exists(back_file):
                    gr.draw_log(f"{translator.translate('No backup files found.')} {back_file}", fill=gr.colorBlue,
                                outline=gr.colorBlueD1)
                    gr.draw_paint()
                    time.sleep(2)
                else:
                    gr.draw_log(f"{translator.translate('Restoring...')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
                    gr.draw_paint()
                    re_command = f"unzip -oq {back_file} -d /"
                    subprocess.run(re_command, shell=True, check=True)
                    gr.draw_log(
                        f"{translator.translate('Theme restoration successful!')}", fill=gr.colorBlue,
                        outline=gr.colorBlueD1
                    )
                    gr.draw_paint()
                    time.sleep(2)
            elif selected_system == "restore.stock":
                back_path = "/mnt/mmc/anbernic/backup"
                if not os.path.exists(back_path):
                    os.mkdir(back_path)
                back_file = f"{back_path}/Stock_theme_bak.zip"
                if not os.path.exists(back_file):
                    gr.draw_log(f"{translator.translate('No backup files found.')} {back_file}", fill=gr.colorBlue,
                                outline=gr.colorBlueD1)
                    gr.draw_paint()
                    time.sleep(2)
                else:
                    gr.draw_log(f"{translator.translate('Restoring...')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
                    gr.draw_paint()
                    re_command = f"unzip -oq {back_file} -d /"
                    subprocess.run(re_command, shell=True, check=True)
                    gr.draw_log(
                        f"{translator.translate('Theme restoration successful!')}", fill=gr.colorBlue,
                        outline=gr.colorBlueD1
                    )
                    gr.draw_paint()
                    time.sleep(2)
            gr.draw_log(
                f"{translator.translate('Checking file...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
            )
            gr.draw_paint()
            skip_input_check = True
            return
        elif input.key("X"):
            current_window = "help"
            skip_input_check = True
            return
        elif input.key("Y"):
            an.switch_sd_storage()
            selected_position = 0
            skip_input_check = True
            return

    help_console = help_info.get(selected_position)
    gr.draw_clear()
    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 110], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text((x_size / 2, 20), f"{translator.translate('Themes Manager')} {ver}", font=23, anchor="mm")
    gr.draw_help(
        f"{translator.translate(help_console)}", fill=None, outline=gr.colorBlueD1
    )

    if len(available_systems) > 0:
        start_idx = int(selected_position / max_elem) * max_elem
        end_idx = start_idx + max_elem
        for i, system in enumerate(available_systems[start_idx:end_idx]):
            menu_list(
                f"{translator.translate(system)}", (20, 50 + (i * 35)), x_size - 40, i == (selected_position % max_elem)
            )
        gr.button_circle((20, button_y), "A", f"{translator.translate('Select')}")
    else:
        gr.draw_text(
            (x_size / 2, y_size / 2), f"{translator.translate('No file found.')}", anchor="mm"
        )

    gr.button_circle((button_x - 300, button_y), "X", f"{translator.translate('Help')}")
    gr.button_circle((button_x - 170, button_y), "Y", f"{translator.translate('Switch')} TF: {an.get_sd_storage()}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

    gr.draw_paint()


def load_theme_menu() -> None:
    global \
        selected_position, \
        current_window, \
        theme_selected_position, \
        skip_input_check, \
        selected_system

    exit_menu = False
    theme_list = themes.get_themes(an.get_sd_storage_path(), selected_system)
    system_path: Path = Path(an.get_sd_storage_path()) / selected_system

    if len(theme_list) < 1:
        current_window = "console"
        selected_system = ""
        gr.draw_log(
            f"{translator.translate('No Theme .zip file found.')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(2)
        gr.draw_clear()
        exit_menu = True

    if input.key("B"):
        exit_menu = True
    elif input.key("DY"):
        theme_selected_position = (theme_selected_position + input.value) % len(theme_list)
    elif input.key("L1"):
        if theme_selected_position > 0:
            theme_selected_position = max(0, theme_selected_position - max_elem)
    elif input.key("R1"):
        if theme_selected_position < len(theme_list) - 1:
            theme_selected_position = min(
                len(theme_list) - 1, theme_selected_position + max_elem
            )
    elif input.key("L2"):
        if theme_selected_position > 0:
            theme_selected_position = max(0, theme_selected_position - 100)
    elif input.key("R2"):
        if theme_selected_position < len(theme_list) - 1:
            theme_selected_position = min(
                len(theme_list) - 1, theme_selected_position + 100
            )

    elif input.key("A"):
        rom = theme_list[theme_selected_position]
        theme_file=f"{system_path}/{rom.filename}"
        if os.path.exists(theme_file):
            gr.draw_log(f"{translator.translate('Installing...')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
            gr.draw_paint()
            themes.install_theme(system_path, theme_file)
            gr.draw_log(
                f"{translator.translate('Theme installation successful!')}", fill=gr.colorBlue, outline=gr.colorBlueD1
            )
            gr.draw_paint()
            time.sleep(2)

    elif input.key("Y"):
        an.switch_sd_storage()
        new_theme_list = themes.get_themes(an.get_sd_storage_path(), selected_system)
        if len(new_theme_list) < 1:
            an.switch_sd_storage()
            gr.draw_log(
            f"{translator.translate('No Theme .zip file found.')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
            gr.draw_paint()
            time.sleep(2)
        else:
            selected_position = 0
            skip_input_check = True
            return

    if exit_menu:
        current_window = "console"
        selected_system = ""
        gr.draw_clear()
        theme_selected_position = 0
        skip_input_check = True
        return

    gr.draw_clear()
    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 110], 15, fill=gr.colorGray, outline=None)
    gr.draw_text(
        (x_size / 2, 20),
        f"{translator.translate(selected_system)} : {theme_selected_position + 1} {translator.translate('of')} {len(theme_list)}",
        font=21,
        anchor="mm",
    )
    gr.draw_help(
        f"{translator.translate('help_theme')}", fill=None, outline=gr.colorBlueD1
    )

    start_idx = int(theme_selected_position / max_elem) * max_elem
    end_idx = start_idx + max_elem
    for i, rom in enumerate(theme_list[start_idx:end_idx]):
        menu_list(
            rom.name[:48] + "..." if len(rom.name) > 50 else rom.name,
            (20, 50 + (i * 35)),
            x_size -40,
            i == (theme_selected_position % max_elem),
        )

    theme = theme_list[theme_selected_position]
    img_file = f"{system_path}/{theme.name}.png"
    if not os.path.exists(img_file):
        img_file = f"{system_path}/{theme.name}.jpg"
    if os.path.exists(img_file):
        gr.display_image(img_file, target_x = int(x_size / 2 + 10), target_y = int(y_size / 4), target_width = int(x_size / 2 - 30), target_height = int((x_size / 2 - 30) * ratio), rota=0)

    gr.button_circle((20, button_y), "A", f"{translator.translate('Install')}")
    gr.button_circle((120, button_y), "B", f"{translator.translate('Back')}")
    gr.button_circle((button_x - 170, button_y), "Y", f"{translator.translate('Switch')} TF: {an.get_sd_storage()}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

    gr.draw_paint()

def load_logo_menu() -> None:
    global  current_window, \
        logo_selected_position, \
        skip_input_check, \
        selected_system

    logo_list = themes.get_logos(an.get_sd_storage_path(), selected_system)
    system_path = Path(an.get_sd_storage_path()) / selected_system

    if len(logo_list) < 1:
        current_window = "console"
        selected_system = ""
        gr.draw_log(
            f"{translator.translate('No Boot logo .bmp file found.')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(2)
        gr.draw_clear()
        skip_input_check = True
        return

    if input.key("B"):
        current_window = "console"
        skip_input_check = True
        return
    elif input.key("DY"):
        logo_selected_position = (logo_selected_position + input.value) % len(logo_list)
    elif input.key("L1"):
        if logo_selected_position > 0:
            logo_selected_position = max(0, logo_selected_position - max_elem)
    elif input.key("R1"):
        if logo_selected_position < len(logo_list) - 1:
            logo_selected_position = min(
                len(logo_list) - 1, logo_selected_position + max_elem
            )
    elif input.key("L2"):
        if logo_selected_position > 0:
            logo_selected_position = max(0, logo_selected_position - 100)
    elif input.key("R2"):
        if logo_selected_position < len(logo_list) - 1:
            logo_selected_position = min(
                len(logo_list) - 1, logo_selected_position + 100
            )

    elif input.key("A"):
        gr.draw_log(f"{translator.translate('Setting...')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
        gr.draw_paint()
        logo = logo_list[logo_selected_position]
        logo_file = f"{system_path}/{logo.filename}"
        themes.set_bootlogo(logo_file)
        cf.set_config("boot.logo", 0)
        gr.draw_log(f"{translator.translate('Boot Logo setting successful!')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
        gr.draw_paint()
        time.sleep(2)

    elif input.key("X"):
        cf.switch_config("boot.logo", 2)
        cur = cf.get_config('boot.logo')
        if cur == "OFF":
            gr.draw_log(f"{translator.translate('Random display Boot Logo DISABLED')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
        elif cur == "ON":
            gr.draw_log(f"{translator.translate('Random display Boot Logo ENABLED')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
        gr.draw_paint()
        time.sleep(2)

    gr.draw_clear()
    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 110], 15, fill=gr.colorGray, outline=None)
    gr.draw_text(
        (x_size / 2, 20),
        f"{translator.translate(selected_system)} : {logo_selected_position + 1} {translator.translate('of')} {len(logo_list)}",
        font=21,
        anchor="mm",
    )
    gr.draw_help(
        f"{translator.translate('help_logo')}", fill=None, outline=gr.colorBlueD1
    )

    start_idx = int(logo_selected_position / max_elem) * max_elem
    end_idx = start_idx + max_elem
    for i, rom in enumerate(logo_list[start_idx:end_idx]):
        menu_list(
            rom.name[:48] + "..." if len(rom.name) > 50 else rom.name,
            (20, 50 + (i * 35)),
            x_size -40,
            i == (logo_selected_position % max_elem),
        )

    logo = logo_list[logo_selected_position]
    img_file = f"{system_path}/{logo.filename}"
    if os.path.exists(img_file):
        gr.display_image(img_file, target_x = int(x_size / 2 + 10), target_y = int(y_size / 4), target_width = int(x_size / 2 - 30), target_height = int((x_size / 2 - 30) * ratio))

    gr.button_circle((20, button_y), "A", f"{translator.translate('Set')}")
    gr.button_circle((140, button_y), "B", f"{translator.translate('Back')}")
    gr.button_circle((260, button_y), "X", f"{translator.translate('Ran. disp')}: {translator.translate(cf.get_config('boot.logo'))}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

    gr.draw_paint()


def load_help_menu() -> None:
    global current_window, skip_input_check

    if input.key("B"):
        current_window = "console"
        skip_input_check = True
        return

    gr.draw_clear()

    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 40], 15, fill=gr.colorGrayL1, outline=None)
    gr.draw_text((x_size / 2, 20), f"{translator.translate('-Help-')}", anchor="mm")

    gr.draw_help2(
        f"{translator.translate('message_02-1')}\n{translator.translate('message_02-2')}\n{translator.translate('message_02-3')}", font=19
    )

    gr.button_circle((20, button_y), "B", f"{translator.translate('Back')}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

    gr.draw_paint()

def menu_list(text: str, pos: tuple[int, int], width: int, selected: bool) -> None:
    gr.draw_rectangle_r(
        [pos[0], pos[1], pos[0] + width, pos[1] + 32],
        5,
        fill=(gr.colorBlue if selected else gr.colorGrayL1),
    )
    gr.draw_text((pos[0] + 5, pos[1] + 5), text)
