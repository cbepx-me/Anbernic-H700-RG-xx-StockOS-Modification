import os
import time
import graphic as gr
import subprocess
import textwrap
import sys
from systems import systems
from anbernic import Anbernic
from main import hw_info
from pathlib import Path

mod_tools = Path(__file__).parent / 'mod_tools'
an = Anbernic()

hw_config = {
    5: ("RG35XXH", "RG35XXH-kernel.modded"),
    7: ("RG40xx", "RG40xx-kernel.modded"),
    8: ("RG40xx", "RG40xx-kernel.modded")
}

class Set:
    def __init__(self):
        self.user = ""

    def execute_command(self, command, storage_path):
        if command.startswith('back:'):
            code = command[5:]
            if code == "sys":
                backup_file = f"{storage_path}/system.tar.gz"
                output = "System settings backup to:"
                files = [
                    "/mnt/data/.wifi",
                    "/mnt/data/dmenu/",
                    "/mnt/data/misc/",
                    "/root/.local/state/syncthing/",
                    "/mnt/mod/ctrl/configs/*.cfg",
                    "/mnt/mod/ctrl/configs/*.txt",
                    "/mnt/vendor/bin/arcade-plus.csv",
                    "/mnt/vendor/bin/default.ttf"
                ]
            elif code == "emu":
                backup_file = f"{storage_path}/emulator.tar.gz"
                output = "Emulator settings backup to:"
                files = [
                    "/.config/retroarch/retroarch.cfg",
                    "/mnt/mmc/Roms/OPENBOR/Saves/",
                    "/mnt/sdcard/Roms/OPENBOR/Saves/",
                    "/mnt/mmc/anbernic/autocores/",
                    "/mnt/mmc/anbernic/custom/",
                    "/mnt/mmc/openbor/Saves/",
                    "/mnt/sdcard/openbor/Saves/",
                    "/mnt/vendor/deep/drastic-modify/res/config/",
                    "/mnt/vendor/deep/drastic-modify/res/resources/settings.json",
                    "/mnt/vendor/deep/drastic/config/",
                    "/mnt/vendor/deep/ppsspp/PSP/SYSTEM/",
                    "/mnt/vendor/deep/retro/config/",
                    "/mnt/vendor/deep/retro/remaps/"
                ]
            elif code == "save":
                backup_file = f"{storage_path}/save.tar.gz"
                output = "Save files backup to:"
                files = [
                    "/mnt/mmc/.config/ppsspp/PSP/PPSSPP_STATE/",
                    "/mnt/mmc/.config/ppsspp/PSP/SAVEDATA/",
                    "/mnt/mmc/.pcsx/memcards/",
                    "/mnt/mmc/.pcsx/sstates/",
                    "/mnt/mmc/.pixel_reader_store/",
                    "/mnt/mmc/openbor/Saves/",
                    "/mnt/mmc/save/",
                    "/mnt/mmc/save_nds/",
                    "/mnt/mmc/saves_RA/",
                    "/mnt/mmc/states_RA/",
                    "/mnt/sdcard/.config/ppsspp/PSP/PPSSPP_STATE/",
                    "/mnt/sdcard/.config/ppsspp/PSP/SAVEDATA/",
                    "/mnt/sdcard/.pcsx/memcards/",
                    "/mnt/sdcard/.pcsx/sstates/",
                    "/mnt/sdcard/.pixel_reader_store/",
                    "/mnt/sdcard/openbor/Saves/",
                    "/mnt/sdcard/save/",
                    "/mnt/sdcard/save_nds/",
                    "/mnt/sdcard/saves_RA/",
                    "/mnt/sdcard/states_RA/",
                    "/mnt/vendor/deep/drastic-modify/res/backup/",
                    "/mnt/vendor/deep/drastic-modify/res/savestates/",
                    "/mnt/vendor/deep/retro/system/dc/vmu_save_A1.bin",
                    "/mnt/vendor/deep/retro/system/dc/vmu_save_B1.bin",
                    "/mnt/vendor/deep/retro/system/dc/vmu_save_C1.bin",
                    "/mnt/vendor/deep/retro/system/dc/vmu_save_D1.bin"
                ]
            elif code == "theme":
                backup_file = f"{storage_path}/theme.tar.gz"
                output = "Theme files backup to:"
                files = [
                    "/mnt/vendor/res1/",
                    "/mnt/vendor/res2/",
                    "/mnt/vendor/res3/",
                    "/mnt/vendor/res4/"
                ]
            backup_dir = os.path.dirname(backup_file)
            os.makedirs(backup_dir, exist_ok=True)
            files_to_compress = []
            for file in files:
                if os.path.exists(file):
                    files_to_compress.append(file)
            run_command = f"tar -zcvf {backup_file} {' '.join(files_to_compress)}"
        elif command.startswith('restore:'):
            code = command[8:]
            if code == "sys":
                backup_file = f"{storage_path}/system.tar.gz"
                output = "Recovered System settings backup file:"
            elif code == "emu":
                backup_file = f"{storage_path}/emulator.tar.gz"
                output = "Backup file for restored Emulator settings:"
            elif code == "save":
                backup_file = f"{storage_path}/save.tar.gz"
                output = "Recovered Saved files:"
            elif code == "theme":
                backup_file = f"{storage_path}/theme.tar.gz"
                output = "Recovered theme files:"
            if os.path.exists(backup_file):
                run_command = f"tar -zxvf {backup_file} -C /"
            else:
                return False, "No backup files exist!", backup_file
        elif command.startswith('tools:'):
            code = command[6:]
            run_command = f"{mod_tools} {code}"
            backup_file=code
            output = "Successful operation:"
        elif command.startswith('random:'):
            code = command[7:]
            if code == "add" or code == "del":
                run_command = f"{mod_tools} {code}"
                backup_file=code
                output = "Successful operation:"
            else:
                current_file_path = os.path.abspath(__file__)
                current_dir = os.path.dirname(current_file_path)
                file_path=f"{current_dir}/random.cfg"
                with open(file_path, 'w') as file:
                    file.write(code)
                gr.draw_end()
                print("Exiting Modify System Tools...")
                sys.exit()
        elif command.startswith('gamma:'):
            code = command[6:]
            hw, kernel_file = hw_config.get(hw_info, (None, None))
            if not hw:
                return False, "Unsupported hardware models:", hw_info
            current_dir = Path(__file__).parent.resolve()
            back_file = current_dir / f"{hw}-kernel.bak"
            if code == "gamma":
                if back_file.exists():
                    return False, "Already a gamma kernel!", hw
                else:
                    os.chdir(current_dir)
                    self.run_comm("dd if=/dev/mmcblk0p4 of=tmp_file skip=4 count=33969")
                    self.run_comm(f"tar --format=gnu -czf {back_file} tmp_file")
                    (current_dir / "tmp_file").unlink()
                    dep_file = current_dir / f"{hw}-kernel.dep"
                    if not dep_file.exists():
                        return False, "Gamma kernel file not found!", hw
                    self.run_comm(f"tar --no-same-owner -zxmf {dep_file} -C {current_dir}")
                    kernel_path = current_dir / kernel_file
                    if not kernel_path.exists():
                        return False, "Gamma kernel file not found!", hw
                    self.run_comm(f"dd if={kernel_path} of=/dev/mmcblk0p4 seek=4")
                    kernel_path.unlink()
                    gr.draw_end()
                    print("Exiting Modify System Tools...")
                    os.system('sync')
                    os.system('reboot')
                    time.sleep(100)
            elif code == "stock":
                if not back_file.exists():
                    return False, "Already a stock kernel!", hw
                else:
                    os.chdir(current_dir)
                    self.run_comm(f"tar --no-same-owner -zxmf {back_file} -C {current_dir}")
                    back_file.unlink()
                    tmp_file = current_dir / "tmp_file"
                    self.run_comm(f"dd if={tmp_file} of=/dev/mmcblk0p4 seek=4")
                    tmp_file.unlink()
                    gr.draw_end()
                    print("Exiting Modify System Tools...")
                    os.system('sync')
                    os.system('reboot')
                    time.sleep(100)

        try:
            result = subprocess.run(
                run_command,
                shell=True,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                timeout=6000
            )
            return True, output, backup_file
        except subprocess.CalledProcessError as e:
            return False, e.stdout.decode('utf-8'), backup_file
        except Exception as e:
            return False, str(e), backup_file

    def run_comm(self, cmd, check=True):
        result = subprocess.run(
            cmd, 
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"Error: {result.stderr}")
        return result

    def get_all_menus(self) -> list[str]:
        all_menu = [system["menu"] for system in systems]
        return all_menu

    def get_menu_help(self, menu_name: str) -> list[str]:
        for system in systems:
            if system["menu"] == menu_name:
                return system["menu_help"]

    def get_menu_option(self, menu_name: str) -> list[str]:
        for system in systems:
            if system["menu"] == menu_name:
                return system["options"]
        return []

    def get_opt_help(self, opt_select, menu_name: str) -> list[str]:
        for system in systems:
            if system["menu"] == menu_name:
                help_list=system["opt_help"]
                return help_list[opt_select]
        return []

    def get_menu_operation(self, opt_select, menu_name: str) -> list[str]:
        for system in systems:
            if system["menu"] == menu_name:
                operation_list=system["operations"]
                return operation_list[opt_select]
        return []
