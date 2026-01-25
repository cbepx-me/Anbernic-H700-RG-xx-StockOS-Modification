#!/usr/bin/env python3
# make by G.R.H

from main import hw_info, system_lang
from graphic import screen_resolutions, UserInterface
from language import Translator
import input
import os
import sys
import re
import shutil
import subprocess
import time
import tarfile
import zipfile
import concurrent.futures
from pathlib import Path
import threading
from functools import lru_cache

ver = "3.9.2"
base_data = "20251206"
translator = Translator(system_lang)
gr = UserInterface()
selected_position = 0
menu_selected_position = 0
opt_selected_position = 0
selected_menu = ""
current_window = "menu"
skip_input_check = True
shdir = os.path.dirname(os.path.abspath(__file__))
sou_dir = os.path.dirname(shdir)
sound_file = os.path.join(shdir, 'res', 'sound.wav')
image_file = f"{hw_info}.png"
if hw_info > 2:
    image_file = "install.png"
image_path = os.path.join(shdir, 'res', image_file)

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 11))
button_x = x_size - 120
button_y = y_size - 30
ratio = y_size / x_size
n = 1

class ResourceCache:
    def __init__(self):
        self.config_cache = {}
        self.font_cache = {}
        self.image_cache = {}
    
    def get_config(self, path):
        if path not in self.config_cache:
            if os.path.exists(path):
                with open(path, 'r') as f:
                    self.config_cache[path] = f.read()
            else:
                self.config_cache[path] = ""
        return self.config_cache[path]
    
    def update_config_cache(self, path, content):
        self.config_cache[path] = content

cache = ResourceCache()

def start() -> None:
    gr.draw_clear()
    gr.draw_log(
        f"{translator.translate('Stock OS Modification Installer')} v{ver}", fill=gr.colorBlue, outline=gr.colorBlueD1
    )
    gr.draw_paint()
    subprocess.run(["aplay", sound_file], check=False)
    
    preload_resources()
    
    old_ver = read_current_os_version()
    if old_ver == "Unknown" or old_ver < base_data:
        gr.draw_log(
                f"{translator.translate('The system version does not meet the requirements')}: >= {base_data}",
                fill=gr.colorRed, outline=gr.colorRed
                    )
        gr.draw_paint()
        time.sleep(5)
        gr.draw_end()
        sys.exit(1)

    load_menu_menu()

def preload_resources():
    """预加载常用资源，减少运行时延迟"""
    # 预加载字体
    font_sizes = [12, 15, 17, 19, 21]
    for size in font_sizes:
        try:
            from PIL import ImageFont
            font_file_local = os.path.join(shdir, "font/font.ttf")
            font_file_sys = "/usr/share/fonts/TTF/DejaVuSansMono.ttf"
            font_path = font_file_local if os.path.exists(font_file_local) else font_file_sys
            ImageFont.truetype(font_path, size)
        except:
            pass
    
    # 预读取常用配置
    common_configs = [
        "/mnt/vendor/oem/board.ini",
        "/mnt/vendor/oem/language.ini",
        "/mnt/vendor/oem/version.ini",
        "/mnt/mod/lang.flg"
    ]
    for config in common_configs:
        cache.get_config(config)

def update() -> None:
    global current_window, \
            selected_position, \
            skip_input_check

    if skip_input_check:
        input.reset_input()
        skip_input_check = False
    else:
        input.check()

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

    all_menu = ["language", "Start"]

    if all_menu:
        if input.key("DY"):
            menu_selected_position = (menu_selected_position + input.value) % len(all_menu)
        elif input.key("A"):
            selected_menu = all_menu[menu_selected_position]
            if selected_menu == "language":
                current_window = "options"
                skip_input_check = True
                return
            else:
                mod_update()
        elif input.key("MENUF"):
            gr.draw_log(
                f"{translator.translate('User cancels installation...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
            )
            gr.draw_paint()
            time.sleep(1.5)
            gr.draw_end()
            sys.exit(0)

    gr.draw_clear()
    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 40], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text((x_size / 2, 20), f"{translator.translate('Stock OS Modification Installer')} v{ver}", font=17, anchor="mm")

    start_idx = int(menu_selected_position / max_elem) * max_elem
    end_idx = start_idx + max_elem
    for i, system in enumerate(all_menu[start_idx:end_idx]):
        gr.row_list(
            translator.translate(system), (20, 50 + (i * 35)), x_size - 40, i == (menu_selected_position % max_elem)
        )

    gr.button_circle((30, button_y), "A", f"{translator.translate('Select')}")
    gr.button_circle((button_x, button_y), "M", f"{translator.translate('Exit')}")
    gr.draw_paint()


def load_options_menu() -> None:
    global \
        current_window, \
        skip_input_check, \
        opt_selected_position

    exit_menu = False
    opt_list = [ "简体中文", "繁体中文", "English", "日本语", "한국어", "Español", "Русский", "Deutsch", "Français", "Português-BR" ]
    operations = [ "zh_CN", "zh_TW", "en_US", "ja_JP", "ko_KR", "es_LA", "ru_RU", "de_DE", "fr_FR", "pt_BR" ]

    if input.key("B"):
        exit_menu = True
    elif input.key("A"):
        gr.draw_log(
            f"{translator.translate('Executing...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        code = operations[opt_selected_position]
        translator.load_language(code)
        set_lang(code)
        exit_menu = True

    elif input.key("DY"):
        opt_selected_position = (opt_selected_position + input.value) % len(opt_list)

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
        font=17, anchor="mm",
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

    gr.button_circle((30, button_y), "A", f"{translator.translate('Select')}")
    gr.button_circle((200, button_y), "B", f"{translator.translate('Back')}")
    gr.draw_paint()


def mod_update():
    try:
        gr.draw_clear()
        gr.display_image(image_path)
        x = x_size // 2 - 177
        for i in list(range(30)):
            gr.draw_rectangle([x, y_size // 2 + 90, x + 6, y_size // 2 + 110], fill=gr.colorGrayL1)
            x += 12
        gr.draw_paint()
        
        # 初始化变量
        progress("Initializing ...", n)
        raconfig1 = "/.config/retroarch/retroarch.cfg"
        raconfig2 = "/mnt/vendor/deep/retro/retroarch.cfg"
        raconfig_files = [
            "/mnt/vendor/deep/retro/config/FinalBurn Neo/VARCADE.opt",
            "/mnt/vendor/deep/retro/config/MAME 2003/VARCADE.opt",
            "/mnt/vendor/deep/retro/config/MAME 2003-Plus/VARCADE.opt"
        ]
        keyrmp_files = [
            "/mnt/vendor/deep/retro/remaps/FinalBurn Neo/VARCADE.rmp",
            "/mnt/vendor/deep/retro/remaps/MAME 2003/VARCADE.rmp",
            "/mnt/vendor/deep/retro/remaps/MAME 2003-Plus/VARCADE.rmp"
        ]
    
        # 判断源目录
        progress("Initializing ...", n)
        kill_me = 0
        if sou_dir != "/mnt/mod/update":
            kill_me = 1
    
        # 获取语言设置
        progress("Initializing ...", n)
        lang_flg = "/mnt/mod/lang.flg"
        language_ini = "/mnt/vendor/oem/language.ini"
        if os.path.isfile(lang_flg):
            lang = cache.get_config(lang_flg).strip()
        else:
            lang = cache.get_config(language_ini).strip()
    
        # 硬件检测
        board_info = cache.get_config("/mnt/vendor/oem/board.ini").strip()
        if not board_info:
            board_info = ""
    
        # 解压并执行apps脚本 - 优化为并行处理
        progress("Initializing ...", n)
        data_dir = os.path.join(shdir, "data")
        apps_dep = os.path.join(data_dir, "apps.dep")
        if os.path.exists(apps_dep):
            unpack_zip(apps_dep, data_dir)
    
        apps_dir = os.path.join(data_dir, "apps")
        if os.path.isdir(apps_dir):
            entries = os.listdir(apps_dir)
            script_files = [script for script in entries if script.lower().endswith('.sh')]
            
            # 并行执行脚本（限制并发数）
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for script in script_files:
                    full_path = Path(os.path.join(apps_dir, script))
                    if not kill_me:
                        full_path.chmod(0o777)
                    show_info(f"{translator.translate('Running')}: {os.path.basename(script)} ...")
                    futures.append(executor.submit(subprocess.run, [str(full_path)], check=False, 
                                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
                
                # 等待所有脚本完成
                for future in concurrent.futures.as_completed(futures):
                    future.result()
                    
            shutil.rmtree(apps_dir)
    
        # 处理boot分区
        progress("Initializing ...", n)
        boot_device = "/dev/mmcblk0p2"
        boot_path = "/mnt/boot"
        os.makedirs(boot_path, exist_ok=True)
        subprocess.run(["umount", boot_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["mount", "-t", "vfat", "-o", "rw,utf8,noatime", boot_device, boot_path], 
                      check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logo_file = f"{hw_info}.bmp"
        if hw_info > 3:
            logo_file = "update.bmp"
        src_logo = os.path.join(shdir, "res", logo_file)
        shutil.copy(src_logo, os.path.join(boot_path, "bootlogo.bmp"))
        subprocess.run(["umount", boot_path], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        shutil.rmtree(boot_path)
    
        # 批量删除文件操作 - 优化为并行处理
        progress("Deleting files ...", n)
        files_to_delete = [
            "/.config/retroarch/tmp/*",
            "/.config/retroarch/dark.txt",
            "/mnt/mod/ctrl/configs/tk.cfg",
            "/mnt/mod/ctrl/configs/lr.cfg",
            "/mnt/mod/ctrl/configs/led_boot.cfg",
            "/mnt/mod/ctrl/configs/led_launch.cfg",
            "/mnt/mod/ctrl/configs/led_exit.cfg",
            "/mnt/vendor/deep/retro/info/core_info.cache",
            "/mnt/vendor/deep/retro/config/global.glslp",
            "/mnt/vendor/bin/ebook/resources/fonts/*",
            "/mnt/mmc/Roms/APPS/*"
        ]
        
        # 并行删除文件
        delete_tasks = []
        for file in files_to_delete:
            show_info(f"{translator.translate('Deleting')}: {os.path.basename(file)} ...")
            delete_tasks.append((file, "batch"))
        
        batch_delete_files(delete_tasks)
    
        # 清理无用文件
        progress("Deleting files ...", n)
        dep_files = {
            "RG28xx": ["34.dep", "34sp.dep", "35.dep", "cube.dep"],
            "RGcubexx": ["28.dep", "34.dep", "34sp.dep", "35.dep", "theme.dep"],
            "RG34xx": ["28.dep", "35.dep", "cube.dep", "theme.dep"],
            "RG34xxSP": ["28.dep", "35.dep", "cube.dep", "theme.dep"],
            "default": ["28.dep", "34.dep", "34sp.dep", "cube.dep"]
        }
    
        current_deps = dep_files.get(board_info, dep_files["default"])
        for dep in current_deps:
            dep_path = os.path.join(data_dir, dep)
            if os.path.exists(dep_path):
                show_info(f"{translator.translate('Deleting')}: {dep} ...")
                fast_delete(dep_path)
    
        # 并行清理着色器
        progress("Copying update files ...", n)
        shader_paths = list(Path("/mnt/vendor/deep/retro/shaders").glob("0-*"))
        if shader_paths:
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                futures = [executor.submit(shutil.rmtree, str(shader)) for shader in shader_paths]
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except:
                        pass
    
        # 分区调整
        progress("Copying update files ...", n)
        if os.path.exists("/dev/mmcblk0p8"):
            gdisk_input = "x\na\n1\n62\n63\n64\na\n2\n62\n63\n64\na\n3\n62\n63\n64\na\n4\n62\n63\n64\na\n5\n62\n63\n64\na\n6\n62\n63\n64\na\n7\n62\n63\n64\ne\nw\ny\n"
            subprocess.run(["gdisk", "/dev/mmcblk0"], input=gdisk_input.encode(), check=False,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
        # 硬件特定资源 - 并行解压
        progress("Installing specific files ...", n)
        hw_deps = {
            "RG28xx": ["28.dep", "theme.dep", "hdmi.dep"],
            "RGcubexx": ["cube.dep", "hdmi.dep"],
            "RG34xx": ["34.dep", "hdmi.dep"],
            "RG34xxSP": ["34.dep", "34sp.dep", "hdmi.dep"],
            "RG35xxSP": ["35.dep", "theme.dep", "hdmi.dep"],
        }
    
        current_hw = hw_deps.get(board_info, ["35.dep", "theme.dep", "hdmi.dep"])
        dep_paths = [(os.path.join(data_dir, dep), "/") for dep in current_hw if os.path.exists(os.path.join(data_dir, dep))]
        
        # 并行解压硬件特定文件
        parallel_unpack_files(dep_paths)
    
        progress("Installing specific files ...", n)
        dep_to_delete = [
            "28.dep",
            "hdmi.dep",
            "cube.dep",  # 修正了变量名
            "34.dep",
            "34sp.dep",
            "35.dep"
        ]
    
        for dep in dep_to_delete:
            dep_path = os.path.join(data_dir, dep)
            if os.path.exists(dep_path):
                fast_delete(dep_path)
    
        # 并行解压资源文件
        progress("Unzipping files ...", n)
        dep_files = [
            ("mnt.dep", "/"),
            ("psp.dep", "/mnt/mmc"),
            ("psp.dep", "/mnt/sdcard"),
            ("usr.dep", "/")
        ]
        
        dep_paths = [(os.path.join(data_dir, dep), target) for dep, target in dep_files 
                    if os.path.exists(os.path.join(data_dir, dep))]
        
        # 并行解压这些文件
        parallel_unpack_files(dep_paths)
    
        progress("Unzipping files ...", n)
        tar_files = [
            ("shader.dep", "/"),
            ("Roms.dep", "/mnt/mmc")
        ]
        
        tar_paths = [(os.path.join(data_dir, dep), target) for dep, target in tar_files 
                    if os.path.exists(os.path.join(data_dir, dep))]
        
        # 并行解压tar文件
        parallel_unpack_tars(tar_paths)
    
        progress("Installing specific files ...", n)
        # 并行更新配置
        show_info(f"{translator.translate('Processing')}: Retroarch ...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            futures = []
            for config in [raconfig1, raconfig2]:
                if os.path.exists(config):
                    futures.append(executor.submit(update_ra_config, config))
            
            for future in concurrent.futures.as_completed(futures):
                future.result()
    
        # 并行系统服务管理
        progress("Setting up the system ...", n)
        show_info(f"{translator.translate('Processing')}: System ...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = []
            futures.append(executor.submit(subprocess.run, ["systemctl", "stop", "ModemManager"], 
                                          check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            futures.append(executor.submit(subprocess.run, ["systemctl", "disable", "ModemManager"], 
                                          check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            futures.append(executor.submit(subprocess.run, ["apt", "-y", "remove", "unattended-upgrades"], 
                                          check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            futures.append(executor.submit(subprocess.run, ["apt", "-y", "purge", "unattended-upgrades"], 
                                          check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
            
            for future in concurrent.futures.as_completed(futures):
                future.result()
    
        # 并行配置文件修改
        progress("Setting up the system ...", n)
        config_patterns = [
            (r'savestate_auto_index\s*=\s*.*', 'savestate_auto_index = "false"'),
            (r'audio_fastforward_mute\s*=\s*.*', 'audio_fastforward_mute = "true"'),
            (r'quick_menu_show_close_content\s*=\s*.*', 'quick_menu_show_close_content = "false"'),
            (r'menu_show_load_content_animation\s*=\s*.*', 'menu_show_load_content_animation = "false"'),
            (r'settings_show_achievements\s*=\s*.*', 'settings_show_achievements = "true"')
        ]

        show_info(f"{translator.translate('Processing')}: System ...")
        config_tasks = []
        for config in [raconfig1, raconfig2]:
            if os.path.exists(config):
                config_tasks.append((config, config_patterns))
        
        # 并行处理配置文件
        parallel_update_configs(config_tasks)
    
        # 更多配置更新
        progress("Setting up the system ...", n)
        additional_settings = [
            ('menu_show_latency', 'true'),
            ('menu_show_overlays', 'true'),
            ('menu_show_rewind', 'true'),
            ('menu_show_video_layout', 'true'),
            ('quick_menu_show_reset_core_association', 'true'),
            ('quick_menu_show_save_core_overrides', 'true'),
            ('quick_menu_show_save_game_overrides', 'true'),
            ('quick_menu_show_set_core_association', 'true'),
            ('quick_menu_show_shaders', 'true')
        ]
        
        # 并行更新附加配置
        show_info(f"{translator.translate('Processing')}: Retroarch ...")
        config_tasks = []
        for config in [raconfig1, raconfig2]:
            if os.path.exists(config):
                config_tasks.append((config, additional_settings))
        
        parallel_update_additional_configs(config_tasks)
    
        # 其他配置操作
        progress("Setting up the system ...", n)
        setra_sh = "/mnt/vendor/ctrl/setRA.sh"
        if os.path.exists(setra_sh):
            with open(setra_sh, 'r') as f:
                lines = f.readlines()
            # 删除包含sw的行
            lines = [line for line in lines if 'sw' not in line]
        
            # 插入新内容
            for i, line in enumerate(lines):
                if 'set_ra_language $2' in line:
                    insert_pos = i + 1
                    lines.insert(insert_pos, '    /mnt/mod/ctrl/sw $2\n')
                    break
        
            with open(setra_sh, 'w') as f:
                f.writelines(lines)
    
        # RG28xx特定配置
        progress("Setting up the system ...", n)
        show_info(f"{translator.translate('Processing')}: Retroarch ...")
        if board_info == "RG28xx":
            config_tasks = []
            for config in [raconfig1, raconfig2]:
                if os.path.exists(config):

                    config_tasks.append(config)
            
            # 并行处理RG28xx配置
            parallel_update_rg28xx_configs(config_tasks)
    
        # 并行删除配置文件
        progress("Setting up the system ...", n)
        show_info(f"{translator.translate('Deleting')} ...")
        files_to_remove = raconfig_files + keyrmp_files
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for fpath in files_to_remove:
                if os.path.exists(fpath):
                    futures.append(executor.submit(os.remove, fpath))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except:
                    pass
    
        # NDS配置更新
        progress("Setting up the system ...", n)
        setnds_sh = "/mnt/vendor/ctrl/setNDS.sh"
        if os.path.exists(setnds_sh):
            result = subprocess.run(f"grep 'ndscheat' {setnds_sh}", shell=True, 
                                   capture_output=True, text=True)
            if result.returncode != 0:
                with open(setnds_sh, 'r') as f:
                    lines = f.readlines()
                for i, line in enumerate(lines):
                    if 'ndsCtrl.dge &' in line:
                        lines.insert(i, '\t\t\t/mnt/mod/ctrl/ndscheat\n')
                        break
            
                with open(setnds_sh, 'w') as f:
                    f.writelines(lines)
    
        # 批量文件权限设置
        progress("Setting up the system ...", n)
        bin_list = [
            "/usr/bin/zip",
            "/usr/bin/unzip"
        ]
        
        # 并行设置权限
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for bin_file in bin_list:
                if os.path.exists(bin_file):
                    show_info(f"{translator.translate('Processing')}: {bin_file} ...")
                    futures.append(executor.submit(os.chmod, bin_file, 0o777))
            
            # 设置ctrl目录下所有文件的权限
            ctrl_files = list(Path("/mnt/mod/ctrl").glob("*"))
            for p in ctrl_files:
                futures.append(executor.submit(p.chmod, 0o777))
            
            for future in concurrent.futures.as_completed(futures):
                future.result()
    
        progress("Setting up the system ...", n)
        core_files = [
            "/mnt/vendor/deep/retro/cores/prboom_libretro.so",
            "/mnt/vendor/deep/retro/cores/pcsx_rearmed_libretro.so",
            "/mnt/vendor/deep/retro/cores/mame2010_libretro.so",
            "/mnt/vendor/ctrl/dmenu_ln",
            "/mnt/vendor/ctrl/setRA.sh",
            "/usr/lib/aarch64-linux-gnu/libjpeg.so.62",
            "/usr/lib32/libatomic.so.1",
            "/usr/lib32/libcrypto.so.1.1",
            "/usr/lib32/libopenal.so.1",
            "/usr/lib32/libsndio.so.7.0",
            "/usr/lib32/libssl.so.1",
            "/usr/lib32/libzip.so.5",
            "/mnt/vendor/deep/drastic-modify/launch.sh",
            "/mnt/vendor/deep/emuJava/launch.sh"
        ]
        
        # 并行设置核心文件权限
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for core in core_files:
                if os.path.exists(core):
                    show_info(f"{translator.translate('Processing')}: {os.path.basename(core)} ...")
                    futures.append(executor.submit(os.chmod, core, 0o777))
            
            for future in concurrent.futures.as_completed(futures):
                future.result()
    
        # 语言配置
        progress("Setting up the system ...", n)
        if os.path.exists(language_ini):
            with open(language_ini, 'w') as f:
                f.write(lang)
            cache.update_config_cache(language_ini, lang)
    
        # RetroArch高级设置
        progress("Setting up the system ...", n)
        if os.path.exists("/mnt/vendor/ctrl/setRA.sh"):
            subprocess.run(["/mnt/vendor/ctrl/setRA.sh", "adv"], check=False,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
        # 帧缓冲配置
        progress("Recording frame buffer ...", n)
        if not os.path.exists("/mnt/mod/ctrl/configs/fb.cfg"):
            import fcntl
            fb_dev = os.open("/dev/fb0", os.O_RDWR)
            try:
                fb_info = bytearray(160)
                fcntl.ioctl(fb_dev, 0x4600, fb_info)
                with open('/mnt/mod/ctrl/configs/fb.cfg', 'wb') as f:
                    f.write(fb_info)
            finally:
                os.close(fb_dev)
    
        # 更新魔改包
        progress("Copying update files ...", n)
        if kill_me:
            paths_to_clean = ["/mnt/mod/update.log", "/mnt/mod/update.dep", "/mnt/mod/update"]
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = []
                for path in paths_to_clean:
                    if os.path.exists(path):
                        show_info(f"{translator.translate('Copying')}: {os.path.basename(path)} ...")
                        if os.path.isfile(path):
                            futures.append(executor.submit(os.remove, path))
                        elif os.path.isdir(path):
                            futures.append(executor.submit(shutil.rmtree, path))
                
                for future in concurrent.futures.as_completed(futures):
                    try:
                        future.result()
                    except:
                        pass
    
            if not os.path.exists("/mnt/mod/update"):
                os.makedirs("/mnt/mod/update", exist_ok=True)
            
            # 使用更快的目录复制
            fast_copy_tree(sou_dir, "/mnt/mod/update")
            
            update_sh = "/mnt/mod/update/update.sh"
            if os.path.exists(update_sh):
                os.chmod(update_sh, 0o777)
    
        # 备份主题
        progress("Backing up theme ...", n)
        backup_dir = "/mnt/mmc/anbernic/backup"
        if not os.path.exists(os.path.join(backup_dir, "Stock_theme_bak.zip")):
            os.makedirs(backup_dir, exist_ok=True)
            subprocess.run([
                "zip", "-qr", 
                os.path.join(backup_dir, "Stock_theme_bak.zip"),
                "/mnt/vendor/res1/",
                "/mnt/vendor/res2/",
                "/mnt/vendor/res3/",
                "/mnt/vendor/bin/default.ttf"
            ], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with open('/mnt/mod/ctrl/configs/ver.cfg', 'w') as f:
            f.write(ver)
        
        progress("Running the configuration program ...", n)
        subprocess.run(["aplay", sound_file], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        progress("Installation complete ...", n)
        subprocess.run(["/mnt/mod/ctrl/apps"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
        # 并行最终清理
        final_clean = [
            "/mnt/.create",
            "/mnt/.please_create",
            "/mnt/.update",
            "/mnt/.done",
            "/mnt/mod/lang.flg",
        ]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
            futures = []
            for path in final_clean:
                show_info(f"{translator.translate('Processing')}: {path} ...")
                if os.path.exists(path):
                    futures.append(executor.submit(os.remove, path))
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()
                except:
                    pass
    
        # 同步和退出
        progress("Rebooting ...", n)
        show_info(f"{translator.translate('Executing...')}")

        reboot_file = os.path.join(sou_dir, 'reboot.flg')
        with open(reboot_file, 'w') as f:
            f.write(ver)
        subprocess.run(["sync"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        gr.draw_end()
        sys.exit()
    except Exception as e:
        print(f"Upgrade failed to: {e}")
        gr.draw_end()
        sys.exit()

# RetroArch配置处理
def update_ra_config(config_path):
    dark_bak = "/.config/retroarch/dark.txt"
    if os.path.exists(dark_bak):
        with open(dark_bak, 'r') as dark_file:
            content_dark = dark_file.read()
        if "video_filter =" in content_dark:
            with open(config_path, 'r') as config_file:
                cfg = config_file.read()
            cfg = re.sub(r'video_filter =.*\n', '', cfg)
            cfg += content_dark
            with open(config_path, 'w') as config_file:
                config_file.write(cfg)
            os.remove(dark_bak)
    else:
        with open(config_path, 'r+') as config_file:
            cfg = config_file.read()
            cfg = re.sub(r'video_filter =.*', 'video_filter = ""', cfg)
            config_file.seek(0)
            config_file.write(cfg)
            config_file.truncate()


def progress(info, step, all=30, update_ui=True):
    """优化版的进度显示，减少UI更新频率"""
    global n
    n += 1
    
    # 减少UI更新频率：每3步或最后一步更新一次
    if not update_ui or (step % 3 != 0 and step != all):
        return
        
    inner_color1 = (19, 55, 87, 255)
    inner_color2 = (7, 211, 153, 255)
    tip_info = f"{translator.translate(info)}"
    print(tip_info)
    
    gr.draw_rectangle_r([x_size // 2 - 180, y_size // 2 - 120, x_size // 2 + 180, y_size // 2 - 90], 
                        17, fill=inner_color1, outline=None)
    
    # 缩短显示文本
    display_text = tip_info[:24] + '...' if len(tip_info) > 28 else tip_info
    gr.draw_text((x_size // 2, y_size // 2 - 100), display_text, 
                 font=15, color=inner_color2, anchor="mm")
    
    x1 = x_size // 2 - 177
    for i in list(range(step)):
        gr.draw_rectangle([x1, y_size // 2 + 90, x1 + 6, y_size // 2 + 110], fill=inner_color2)
        x1 += 12
    
    gr.draw_paint()

def unpack_tar(dep_path, target_path, show_progress=True):
    """优化版的tar解压，减少UI更新"""
    inner_color1 = (19, 55, 87, 255)
    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
    
    if os.path.exists(dep_path):
        with tarfile.open(dep_path, "r:gz") as tar_ref:
            total_files = len(tar_ref.getmembers())
            
            # 批量提取文件，每10个文件更新一次进度
            extracted_count = 0
            for i, file in enumerate(tar_ref.getmembers()):
                tar_ref.extract(file.name, target_path)
                extracted_count += 1
                
                # 减少UI更新频率
                if show_progress and (extracted_count % 10 == 0 or i == total_files - 1):
                    percent = (i + 1) * 100 / total_files
                    filled_width = int(320 * percent / 100)
                    tip_info1 = f"{translator.translate('Unpacking')} {os.path.basename(dep_path)}"
                    
                    # 简化UI更新
                    gr.draw_rectangle_r([x_size // 2 - 180, y_size // 2 - 80, x_size // 2 + 180, y_size // 2 + 80], 
                                        15, fill=inner_color1, outline=None)
                    gr.draw_text((x_size / 2, y_size / 2 - 60), tip_info1[:20], font=13, anchor="mm")
                    gr.draw_rectangle([x_size // 2 - 160, y_size // 2 + 10, x_size // 2 + 160, y_size // 2 + 30], 
                                      fill=gr.colorGrayL1)
                    gr.draw_rectangle([x_size // 2 - 160, y_size // 2 + 10, x_size // 2 - 160 + filled_width, y_size / 2 + 30], 
                                      fill=gr.colorBlue)
                    gr.draw_text((x_size / 2, y_size / 2 + 20), f"{int(percent)}%", font=13, anchor="mm")
                    gr.draw_paint()
    else:
        return 1

def unpack_zip(dep_path, target_path, show_progress=True):
    """优化版的ZIP解压，减少UI更新"""
    inner_color1 = (19, 55, 87, 255)
    if not os.path.exists(target_path):
        os.makedirs(target_path, exist_ok=True)
    
    if os.path.exists(dep_path):
        with zipfile.ZipFile(dep_path, "r") as zip_ref:
            total_files = len(zip_ref.namelist())
            
            # 批量提取文件，每10个文件更新一次进度
            extracted_count = 0
            for i, file in enumerate(zip_ref.namelist()):
                zip_ref.extract(file, target_path)
                extracted_count += 1
                
                # 减少UI更新频率
                if show_progress and (extracted_count % 10 == 0 or i == total_files - 1):
                    percent = (i + 1) * 100 / total_files
                    filled_width = int(320 * percent / 100)
                    tip_info1 = f"{translator.translate('Unpacking')} {os.path.basename(dep_path)}"
                    
                    # 简化UI更新
                    gr.draw_rectangle_r([x_size // 2 - 180, y_size // 2 - 80, x_size // 2 + 180, y_size // 2 + 80], 
                                        15, fill=inner_color1, outline=None)
                    gr.draw_text((x_size / 2, y_size / 2 - 60), tip_info1[:20], font=13, anchor="mm")
                    gr.draw_rectangle([x_size // 2 - 160, y_size // 2 + 10, x_size // 2 + 160, y_size // 2 + 30], 
                                      fill=gr.colorGrayL1)
                    gr.draw_rectangle([x_size // 2 - 160, y_size // 2 + 10, x_size // 2 - 160 + filled_width, y_size / 2 + 30], 
                                      fill=gr.colorBlue)
                    gr.draw_text((x_size / 2, y_size / 2 + 20), f"{int(percent)}%", font=13, anchor="mm")
                    gr.draw_paint()
    else:
        return 1

def show_info(info):
    """简化信息显示，减少UI开销"""
    inner_color = (19, 55, 87, 255)
    display_text = info[:24] + '...' if len(info) > 28 else info
    
    gr.draw_rectangle_r([x_size // 2 - 180, y_size // 2 - 80, x_size // 2 + 180, y_size // 2 + 80], 
                        15, fill=inner_color, outline=None)
    gr.draw_text((x_size / 2, y_size / 2), display_text, font=15, anchor="mm")
    gr.draw_paint()

def set_lang(value):
    ra_lang = [12, 11, 0, 1, 10, 3, 9, 4, 2, 7]
    psp_lang = ["zh_CN", "zh_TW", "en_US", "ja_JP", "ko_KR", "es_LA", "ru_RU", "de_DE", "fr_FR", "pt_BR"]

    lang_index = psp_lang.index(value)
    ra_value = ra_lang[lang_index]
    
    # 并行执行语言设置
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        futures = []
        futures.append(executor.submit(subprocess.run, ["/mnt/vendor/ctrl/setRA.sh", "language", str(ra_value)], 
                                      check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        futures.append(executor.submit(subprocess.run, ["/mnt/vendor/ctrl/setPSP.sh", "language", value], 
                                      check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
        
        for future in concurrent.futures.as_completed(futures):
            future.result()
    
    with open("/mnt/vendor/oem/language.ini", "w") as f:
        f.write(str(lang_index))
    
    src_file = os.path.join(shdir, 'res', str(lang_index))
    shutil.copy(src_file, "/mnt/data/dmenu/dmenu_attr.ini")

def read_current_os_version():
    try:
        ver_file = Path("/mnt/vendor/oem/version.ini")
        if ver_file.exists():
            ver = ver_file.read_text().splitlines()[0]
            return ver
    except Exception as e:
        print(f"Error reading OS Date version file: {e}")
    return "Unknown"

# ====================== 新增优化函数 ======================

def batch_delete_files(delete_tasks):
    """批量删除文件，减少系统调用"""
    for file_pattern, mode in delete_tasks:
        if "*" in file_pattern:
            dir_path = os.path.dirname(file_pattern)
            if os.path.exists(dir_path):
                for f in os.listdir(dir_path):
                    full_path = os.path.join(dir_path, f)
                    try:
                        if os.path.isfile(full_path):
                            os.unlink(full_path)  # 比os.remove更快
                        elif os.path.isdir(full_path):
                            shutil.rmtree(full_path)
                    except Exception as e:
                        print(f"Error deleting {full_path}: {e}")
        else:
            if os.path.exists(file_pattern):
                try:
                    if os.path.isfile(file_pattern):
                        os.unlink(file_pattern)
                    elif os.path.isdir(file_pattern):
                        shutil.rmtree(file_pattern)
                except Exception as e:
                    print(f"Error deleting {file_pattern}: {e}")

def fast_delete(file_path):
    """快速删除文件，不显示详细进度"""
    try:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
    except:
        pass

def parallel_unpack_files(file_list, max_workers=3):
    """并行解压多个文件"""
    if not file_list:
        return
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for dep_path, target_path in file_list:
            if os.path.exists(dep_path):
                show_info(f"{translator.translate('Unpacking')}: {dep_path} ...")
                if dep_path.endswith('.tar') or dep_path.endswith('.tar.gz'):
                    futures.append(executor.submit(unpack_tar, dep_path, target_path, False))
                else:
                    futures.append(executor.submit(unpack_zip, dep_path, target_path, False))
        
        # 等待所有任务完成
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error during unpacking: {e}")

def parallel_unpack_tars(file_list, max_workers=2):
    """并行解压多个tar文件"""
    if not file_list:
        return
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for dep_path, target_path in file_list:
            if os.path.exists(dep_path):
                futures.append(executor.submit(unpack_tar, dep_path, target_path, False))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error during tar unpacking: {e}")

def parallel_update_configs(config_tasks, max_workers=2):
    """并行更新多个配置文件"""
    if not config_tasks:
        return
    
    def update_single_config(config_path, patterns):
        if os.path.exists(config_path):
            content = cache.get_config(config_path)
            for pattern, replacement in patterns:
                content = re.sub(pattern, replacement, content)
            with open(config_path, 'w') as f:
                f.write(content)
            cache.update_config_cache(config_path, content)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for config_path, patterns in config_tasks:
            futures.append(executor.submit(update_single_config, config_path, patterns))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error updating config: {e}")

def parallel_update_additional_configs(config_tasks, max_workers=2):
    """并行更新多个附加配置"""
    if not config_tasks:
        return
    
    def update_additional_config(config_path, settings):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                for setting, value in settings:
                    if line.strip().startswith(setting):
                        line = f'{setting} = "{value}"\n'
                        break
                new_lines.append(line)
            with open(config_path, 'w') as f:
                f.writelines(lines)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for config_path, settings in config_tasks:
            futures.append(executor.submit(update_additional_config, config_path, settings))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error updating additional config: {e}")

def parallel_update_rg28xx_configs(config_paths, max_workers=2):
    """并行更新RG28xx配置"""
    def update_rg28xx_config(config_path):
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                content = f.read()
            content = re.sub(r'rgui_menu_color_theme\s*=\s*.*', 'rgui_menu_color_theme = "0"', content)
            content = re.sub(r'rgui_menu_theme_preset\s*=\s*.*', 'rgui_menu_theme_preset = ":/assets/rgui/Night Sky.cfg"', content)
            with open(config_path, 'w') as f:
                f.write(content)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for config_path in config_paths:
            futures.append(executor.submit(update_rg28xx_config, config_path))
        
        for future in concurrent.futures.as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error updating RG28xx config: {e}")

def fast_copy_tree(src, dst):
    """更快的目录复制"""
    if not os.path.exists(dst):
        os.makedirs(dst)
    
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True, copy_function=shutil.copy2)
        else:
            shutil.copy2(s, d)