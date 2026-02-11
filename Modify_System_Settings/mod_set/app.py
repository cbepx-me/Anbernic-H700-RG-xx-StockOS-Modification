from main import hw_info, system_lang
from graphic import screen_resolutions, UserInterface
from language import Translator
from pathlib import Path
import subprocess
import input
import re
import os
import sys
import time
import math
import socket
from set import Set, get_setting

translator = Translator(system_lang)
selected_position = 0
menu_selected_position = 0
opt_selected_position = 0
selected_menu = ""
current_window = "menu"
help_txt = ""
skip_input_check = True
set = Set()
gr = UserInterface()

try:
    ver = Path("/mnt/mod/ctrl/configs/ver.cfg").read_text().splitlines()[0]
except (FileNotFoundError, IndexError):
    ver = 'Unknown'

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 7))

button_x = x_size - 110
button_y = y_size - 30
ratio = y_size / x_size

if hw_info in (1, 6):
    remove_lists = [ 'menu.varc' ]
elif hw_info == 3:
    remove_lists = [ 'menu.varc', 'menu.samba', 'menu.ssh', 'menu.syn' ]
else:
    remove_lists = []

mode_lists = ['menu.ra_hot', 'menu.ra_turbo', 'menu.ra_com', 'menu.shader', 'menu.bezel', 'menu.dark', 'menu.varc', 'menu.aca', 'menu.als']

def is_connected():
    test_servers = [
        ("8.8.8.8", 53),  # google
        ("1.1.1.1", 53),       # NTP DNS
        ("223.5.5.5", 53),       # ali DNS
        ("220.181.38.148", 80)   # baidu
    ]
    for host, port in test_servers:
        try:
            sock = socket.create_connection((host, port), timeout=3)
            sock.close()
            return True
        except (socket.timeout, socket.error):
            continue
    return False


def start() -> None:
    print("Starting Modify System Settings...")
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

    if input.key("MENUF"):
        gr.draw_log(
            f"{translator.translate('Exiting...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(1)
        gr.draw_end()
        print("Exiting Modify System Settings...")
        sys.exit()

    if current_window == "menu":
        load_menu_menu()
    elif current_window == "options":
        load_options_menu()
    else:
        load_menu_menu()


def get_wlan0_ip():
    try:
        output = subprocess.check_output(
            ["ip", "-4", "addr", "show", "wlan0"],
            stderr=subprocess.STDOUT,
            universal_newlines=True
        )
        
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)/\d+', output)
        if match:
            return match.group(1)
        return "None"
        
    except subprocess.CalledProcessError as e:
        return f"Command failed: {e.output.strip()}"
    except FileNotFoundError:
        return "ip command not found (this script requires iproute2 tools)"
    except Exception as e:
        return f"Error: {str(e)}"


def load_menu_menu() -> None:
    global \
        menu_selected_position, \
        selected_menu, \
        current_window, \
        skip_input_check

    all_menu = set.get_all_menus()
    for remove_list in remove_lists:
        if all_menu.count(remove_list)>0:
            all_menu.remove(remove_list)

    if get_setting("ra.mode") == "1":
        for mode_list in mode_lists:
            if all_menu.count(mode_list)>0:
                all_menu.remove(mode_list)
    if system_lang != "zh_CN":
        all_menu.sort()
    if not all_menu:
        gr.draw_text((x_size/2, y_size/2), translator.translate('menu.empty'), font=23, anchor='mm')
        gr.draw_paint()
        time.sleep(2)
        current_window = "menu"
        return

    if all_menu:
        if input.key("DY"):
            menu_selected_position = (menu_selected_position + input.value) % len(all_menu)
        elif input.key("L1"):
            if menu_selected_position > 0:
                menu_selected_position = max(0, menu_selected_position - max_elem)
        elif input.key("R1"):
            if menu_selected_position < len(all_menu) - 1:
                menu_selected_position = min(
                    len(all_menu) - 1, menu_selected_position + max_elem
                )
        elif input.key("L2"):
            if menu_selected_position > 0:
                menu_selected_position = max(0, menu_selected_position - 100)
        elif input.key("R2"):
            if menu_selected_position < len(all_menu) - 1:
                menu_selected_position = min(
                    len(all_menu) - 1, menu_selected_position + 100
                )
        elif input.key("A"):
            current_window = "options"
            selected_menu = all_menu[menu_selected_position]
            skip_input_check = True
            return

    gr.draw_clear()

    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 40], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text((x_size / 2, 20), f"{translator.translate('Modify System Settings')} v{ver} - {math.ceil((menu_selected_position + 1) / max_elem)} / {math.ceil(len(all_menu) / max_elem)}", font=23, anchor="mm")

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
    
    ip_address = get_wlan0_ip()
    gr.draw_text((x_size / 2, button_y + 12), f"IP: {ip_address}", font=21,  color=gr.colorGreen, anchor="mm")
    gr.button_circle((30, button_y), "A", f"{translator.translate('Set')}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

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
        gr.draw_log(
            f"{translator.translate('No available settings found.')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(2)
        exit_menu = True

    if input.key("B"):
        exit_menu = True
    elif input.key("A"):
        gr.draw_log(f"{translator.translate('Executing...')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
        gr.draw_paint()
        command = set.get_menu_operation(opt_selected_position, selected_menu)
        if command.startswith('samba:2') or command.startswith('ssh:2') or command.startswith('syn:2'):
            if not is_connected():
                gr.draw_log(f"{translator.translate('No internet connection')}", fill=gr.colorBlue, outline=gr.colorBlueD1)
                gr.draw_paint()
                time.sleep(3)
                gr.draw_clear()
                current_window = "menu"
                opt_selected_position = 0
                skip_input_check = True
                return
        if command.startswith('lang:'):
            code = command[5:]
            translator.set_language(code)
        success, output = set.execute_command(command)
        if success:
            status_msg = f"{translator.translate('Done')}:\n< {translator.translate(selected_menu)} > {translator.translate(output)}"
            status_color = gr.colorBlue
            gr.draw_log(f"{status_msg}", fill=status_color, outline=status_color, font=19)
            gr.draw_paint()
            time.sleep(1)
        else:
            status_msg = f"{translator.translate('Error')}: < {translator.translate(selected_menu)} >\n{translator.translate(output)}"
            status_color = gr.colorRed
            gr.draw_log(f"{status_msg}", fill=status_color, outline=status_color, font=19)
            gr.draw_paint()
            time.sleep(5)

        exit_menu = True

    elif input.key("DY"):
        opt_selected_position = (opt_selected_position + input.value) % len(opt_list)
    elif input.key("L1"):
        if opt_selected_position > 0:
            opt_selected_position = max(0, opt_selected_position - max_elem)
    elif input.key("R1"):
        if opt_selected_position < len(opt_list) - 1:
            opt_selected_position = min(
                len(opt_list) - 1, opt_selected_position + max_elem
            )
    elif input.key("L2"):
        if opt_selected_position > 0:
            opt_selected_position = max(0, opt_selected_position - 100)
    elif input.key("R2"):
        if opt_selected_position < len(opt_list) - 1:
            opt_selected_position = min(
                len(opt_list) - 1, opt_selected_position + 100
            )

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
    if selected_menu == "menu.timezone":
        timezone_file = "/etc/timezone"
        if os.path.isfile(timezone_file):
            with open(timezone_file, 'r') as time_f:
                cur_time = time_f.readline().strip()
                if cur_time:
                    help_txt = f"{translator.translate('Current Time Zone:')} {cur_time}"
    gr.draw_help(
        f"{translator.translate(help_txt)}",
        fill=None, outline=gr.colorBlue
    )

    gr.button_circle((30, button_y), "A", f"{translator.translate('Select')}")
    gr.button_circle((200, button_y), "B", f"{translator.translate('Back')}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")

    gr.draw_paint()

