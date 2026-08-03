from main import hw_info, system_lang
from graphic import screen_resolutions, UserInterface
from language import Translator
import input
import sys
from weather import weather
import threading
import datetime
import time
import subprocess
import os
import calendar

ver = "v1.3"
translator = Translator(system_lang)
gr = UserInterface()
skip_input_check = True
current_window = "console"
selected_index = 0

x_size, y_size, max_elem = screen_resolutions.get(hw_info, (640, 480, 11))

button_x = x_size - 120
button_y = y_size - 30
ratio = y_size / x_size

script_dir = os.path.dirname(os.path.abspath(__file__))
clock_sound_file = os.path.join(script_dir, 'sound', 'sound.wav')


def start():
    print("[INFO]Starting Time...")
    gr.draw_log(
        f"{translator.translate('welcome')}", fill=gr.colorBlue, outline=gr.colorBlueD1
    )
    gr.draw_paint()
    time.sleep(2)
    handle_console_input()


def update() -> None:
    global current_window, skip_input_check

    if skip_input_check:
        input.reset_input()
        skip_input_check = False
    else:
        input.check()

    if input.key("B"):
        gr.draw_log(
            f"{translator.translate('Exiting...')}", fill=gr.colorBlue, outline=gr.colorBlueD1
        )
        gr.draw_paint()
        time.sleep(2)
        gr.draw_end()
        print("[INFO]Exiting Time...")
        sys.exit()

    if current_window == "console":
        handle_console_input()
    elif current_window == "CLOCK":
        handle_clock_input()
    elif current_window == "TIMER":
        handle_timer_input()
    elif current_window == "STOPWATCH":
        handle_stopwatch_input()
    elif current_window == "SETTIME":
        handle_settime_input()
    else:
        handle_console_input()


def handle_console_input() -> None:
    global current_window, selected_index, skip_input_check

    file_list = ["CLOCK", "TIMER", "STOPWATCH", "SETTIME"]

    if input.key("DY"):
        selected_index = (selected_index + input.value) % len(file_list)
    elif input.key("A"):
        current_window = file_list[selected_index]
        skip_input_check = True
        return

    gr.draw_clear()
    gr.draw_rectangle_r([10, 40, x_size - 10, y_size - 40], 15, fill=gr.colorGrayD2, outline=None)
    gr.draw_text((x_size / 2, 20), f"{translator.translate('CLOCK')} {ver}", font=23, anchor="mm")

    if selected_index >= len(file_list):
        selected_index = 0
    start_idx = int(selected_index / max_elem) * max_elem
    end_idx = start_idx + max_elem

    for i, entry in enumerate(file_list[start_idx:end_idx]):
        gr.row_list(
            f"{translator.translate(entry)}",
            (20, 50 + (i * 35)),
            x_size - 40,
            i == (selected_index % max_elem),
        )

    gr.button_circle((30, button_y), "A", f"{translator.translate('Open')}")
    gr.button_circle((button_x, button_y), "B", f"{translator.translate('Exit')}")

    gr.draw_paint()


def handle_clock_input() -> None:
    global current_window, skip_input_check

    x_pos = x_size // 2
    y_pos = y_size // 2
    time_text_width = gr.get_text_width("00:00:00", font=100)
    x_time_pos = (x_size - time_text_width) // 2
    
    input.reset_input()
    thread = threading.Thread(target=input.check)
    thread.start()
    
    weather_font = 18 if hw_info in [2,3] else 20
    info_spacing = 28
    
    while True:
        now = datetime.datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        current_time = now.strftime("%H:%M:%S")
        weather_data, city = weather.get_weather()
        gr.draw_clear()
        gr.draw_text((x_pos, y_pos - 60), current_date, clock=1, font=46, color=gr.colorGreen, anchor="mm")
        gr.draw_text((x_time_pos, y_pos + 20), current_time, clock=1, font=100, color=gr.colorGreen, anchor="lm")
        
        weather_x = 20
        weather_y = 50
        if weather_data:
            cond_info = weather_data['condition']
            info_lines1 = [
                f"{translator.translate('TEMP')}: {weather_data['temp']}",
                f"{translator.translate('HUMIDITY')}: {weather_data['humidity']}%",
                f"{translator.translate('CONDITION')}: {translator.translate(cond_info)}"
            ]
            info_lines2 = f"({city} @ {weather_data['updated']})"
        else:
            info_lines1 = [translator.translate("FETCHING")]
            info_lines2 = translator.translate("Unknown")
        
        for idx, line in enumerate(info_lines1):
            color = gr.colorYellow if idx < 3 else gr.colorGrayL2
            gr.draw_text(
                (weather_x, weather_y + idx*info_spacing),
                line,
                font=weather_font,
                color=color,
                anchor="lm"
            )
        gr.draw_text(
                (weather_x, y_size - 60),
                info_lines2,
                font=weather_font,
                color=gr.colorGrayL2,
                anchor="lm"
            )
        gr.draw_paint()
        
        if input.slide_key():
            current_window = "console"
            skip_input_check = True
            gr.draw_clear()
            return


def handle_timer_input() -> None:
    global current_window, skip_input_check

    x_pos = x_size // 2
    y_pos = y_size // 2

    timer_duration = 0
    hours = 0
    minutes = 0
    seconds = 0
    end_time = "Sound"
    setting_index = 0
    set_list= ["Seconds", "Minutes", "Hours", "At the end"]
    current_set = set_list[setting_index]
    start_time = None
    countdown_finished = False
    gr.draw_clear()
    gr.draw_text((x_pos, y_pos - 100), f"{translator.translate('Set')}: {translator.translate(current_set)}", font=36, anchor="mm")
    gr.draw_text((x_pos, y_pos - 25), f"{hours:02d}:{minutes:02d}:{seconds:02d}", font=60, anchor="mm")
    gr.draw_text((x_pos, y_pos + 50), f"{translator.translate('At the end')}: {translator.translate(end_time)}", font=36, anchor="mm")
    gr.draw_text((x_pos, y_pos + 100), f"{translator.translate('Press DY to adjust, DX to switch setting')}", font=21, anchor="mm")
    gr.draw_text((x_pos, y_pos + 150), f"{translator.translate('Press START to start, B to Back')}", font=21, anchor="mm")
    gr.draw_paint()
    
    while start_time is None:
        input.check()
        if input.key("DY"):
            if setting_index == 3:
                if end_time == "Sound":
                    end_time = "Vibrate"
                else:
                    end_time = "Sound"
            elif setting_index == 2:
                if input.value == -1:
                    hours = min(99, hours - input.value)
                elif input.value == 1:
                    hours = max(0, hours - 1)
                    if hours == 0 and minutes > 0:
                        minutes = 59
                        seconds = 59
            elif setting_index == 1:
                if input.value == -1:
                    minutes = (minutes - input.value) % 60
                    if minutes == 0:
                        hours = min(99, hours + 1)
                elif input.value == 1:
                    if minutes > 0:
                        minutes = max(0, minutes - 1)
                    elif hours > 0:
                        hours -= 1
                        minutes = 59
                        seconds = 59
            elif setting_index == 0:
                if input.value == -1:
                    seconds = (seconds - input.value) % 60
                    if seconds == 0:
                        minutes = (minutes + 1) % 60
                        if minutes == 0:
                            hours = min(99, hours + 1)
                elif input.value == 1:
                    if seconds > 0:
                        seconds = max(0, seconds - 1)
                    elif minutes > 0:
                        minutes -= 1
                        seconds = 59
                    elif hours > 0:
                        hours -= 1
                        minutes = 59
                        seconds = 59
        elif input.key("DX"):
            setting_index = (setting_index - input.value) % 4
            current_set = set_list[setting_index]
        elif input.key("START"):
            timer_duration = hours * 3600 + minutes * 60 + seconds + 1
            if timer_duration > 1:
                start_time = time.time()
        elif input.key("B"):
            current_window = "console"
            skip_input_check = True
            gr.draw_clear()
            return

        gr.draw_clear()
        gr.draw_text((x_pos, y_pos - 100), f"{translator.translate('Set')}: {translator.translate(current_set)}", font=36, anchor="mm")
        gr.draw_text((x_pos, y_pos - 25), f"{hours:02d}:{minutes:02d}:{seconds:02d}", font=60, anchor="mm")
        gr.draw_text((x_pos, y_pos + 50), f"{translator.translate('At the end')}: {translator.translate(end_time)}", font=36, anchor="mm")
        gr.draw_text((x_pos, y_pos + 100), f"{translator.translate('Press DY to adjust, DX to switch setting')}", font=21, anchor="mm")
        gr.draw_text((x_pos, y_pos + 150), f"{translator.translate('Press START to start, B to Back')}", font=21, anchor="mm")
        gr.draw_paint()

    time_text_width = gr.get_text_width("00:00:00", font=100)
    x_time_pos = (x_size - time_text_width) // 2

    input.reset_input()
    thread = threading.Thread(target=input.check)
    thread.start()

    while True:
        elapsed_time = time.time() - start_time
        remaining_time = max(0, timer_duration - elapsed_time)
        if remaining_time > 0:
            remaining_minutes = int(remaining_time // 60)
            remaining_seconds = int(remaining_time % 60)
            remaining_hours = int(remaining_minutes // 60)
            remaining_minutes = remaining_minutes % 60
            time_str = f"{remaining_hours:02d}:{remaining_minutes:02d}:{remaining_seconds:02d}"
        
            gr.draw_clear()
            gr.draw_text((x_pos, y_pos-100), f"{translator.translate('TIMER')}", font=36, anchor="mm")
            gr.draw_text((x_time_pos, y_pos), time_str, clock=1, font=100, color=gr.colorBlue, anchor="lm")
            gr.draw_paint()
        
        if remaining_time == 0 and not countdown_finished:
            countdown_finished = True
            gr.draw_text((x_pos, y_pos+100), f"{translator.translate('Timer finished!')}", font=36, anchor="mm")
            gr.draw_paint()
        elif input.slide_key():
            current_window = "console"
            skip_input_check = True
            gr.draw_clear()
            return
        elif countdown_finished:
            try:
                if end_time == "Vibrate":
                    subprocess.run("echo 1 > /sys/class/power_supply/axp2202-battery/moto && sleep 0.3 && echo 0 > /sys/class/power_supply/axp2202-battery/moto && sleep 0.1", shell=True, check=True)
                else:
                    subprocess.run(["aplay", clock_sound_file], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error: {e}")


def handle_stopwatch_input() -> None:
    global current_window, skip_input_check

    x_pos = x_size // 2
    y_pos = y_size // 2
    time_text_width = gr.get_text_width("00:00:00", font=100)
    time_text_width2 = gr.get_text_width(".00", font=56)
    x_time_pos = (x_size - time_text_width) // 2

    start_time = 0
    elapsed_time = 0
    running = False
    
    input.reset_input()
    thread = threading.Thread(target=input.check)
    thread.start()

    while True:

        if input.key("START"):
            if running:
                elapsed_time += time.time() - start_time
                running = False
                input.reset_input()
                thread = threading.Thread(target=input.check)
                thread.start()

            else:
                start_time = time.time()
                running = True
                input.reset_input()
                thread = threading.Thread(target=input.check)
                thread.start()

        elif input.key("SELECT"):
            elapsed_time = 0
            start_time = None
            running = False
            input.reset_input()
            thread = threading.Thread(target=input.check)
            thread.start()

        elif input.key("B"):
            if running:
                elapsed_time += time.time() - start_time
                running = False
                input.reset_input()
                thread = threading.Thread(target=input.check)
                thread.start()
            else:
                current_window = "console"
                skip_input_check = True
                gr.draw_clear()
                return

        elif input.slide_key():
            input.reset_input()
            thread = threading.Thread(target=input.check)
            thread.start()

        if running:
            total_elapsed = elapsed_time + (time.time() - start_time)
        else:
            total_elapsed = elapsed_time

        hours = int(total_elapsed // 3600)
        minutes = int((total_elapsed % 3600) // 60)
        seconds = int(total_elapsed % 60)
        milliseconds = int((total_elapsed - int(total_elapsed)) * 100)
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

        gr.draw_clear()
        gr.draw_text((x_pos, y_pos - 150), f"{translator.translate('STOPWATCH')}", font=36, anchor="mm")
        gr.draw_text((x_time_pos, y_pos-50), time_str, clock=1, font=100, color=gr.colorRed, anchor="lm")
        gr.draw_text((x_time_pos+time_text_width - time_text_width2, y_pos+50), f"{milliseconds:02d}", clock=1, font=56, color=gr.colorRed, anchor="lm")

        gr.draw_text((x_pos, y_pos + 100), f"{translator.translate('Press START to start/stop, SELECT to reset')}", font=21, anchor="mm")
        gr.draw_text((x_pos, y_pos + 150), f"{translator.translate('Press B to Back')}", font=21, anchor="mm")

        gr.draw_paint()


def handle_settime_input() -> None:
    global current_window, skip_input_check

    input.reset_input()

    now = datetime.datetime.now()
    time_components = {
        "year": now.year,
        "month": now.month,
        "day": now.day,
        "hour": now.hour,
        "minute": now.minute,
        "second": now.second,
        "mode": 2  # 0:AM, 1:PM, 2:24h
    }

    # 顺序：年、月、日、时、分、秒、模式
    setting_keys = ["year", "month", "day", "hour", "minute", "second", "mode"]
    separators = ["/", "/", " ", ": ", ": ", "", " "]  # 模式前加空格
    setting_index = 0

    def get_hour_limits(mode):
        if mode == 2:  # 24h
            return 0, 23
        else:  # AM(0) or PM(1)
            return 1, 12

    def get_max_day(year, month):
        return calendar.monthrange(year, month)[1]

    def get_min_val(key):
        if key in ["year", "month", "day"]:
            return 1
        return 0  # hour, minute, second

    def get_max_val(key, components):
        if key == "year":
            return 2100
        elif key == "month":
            return 12
        elif key == "day":
            return get_max_day(components["year"], components["month"])
        elif key == "hour":
            return get_hour_limits(components["mode"])[1]
        elif key == "minute":
            return 59
        elif key == "second":
            return 59
        elif key == "mode":
            return 2
        return 0

    # 调整函数：处理进位/借位
    def adjust(idx, delta):
        if idx < 0 or idx >= len(setting_keys):
            return
        key = setting_keys[idx]
        if key == "mode":
            # 模式单独循环
            new_val = (time_components[key] + delta) % 3
            time_components[key] = new_val
            # 如果切换到12小时制，确保小时不超出
            if new_val != 2:
                h_min, h_max = get_hour_limits(new_val)
                if time_components["hour"] > h_max:
                    time_components["hour"] = h_max
                elif time_components["hour"] < h_min:
                    time_components["hour"] = h_min
            return

        # 获取当前值及范围
        cur = time_components[key]
        min_val = get_min_val(key)
        max_val = get_max_val(key, time_components)

        new_val = cur + delta

        if new_val < min_val:
            # 借位：当前值设为最大值，向上级借1
            time_components[key] = max_val
            if idx > 0:
                adjust(idx - 1, -1)  # 上级减1
        elif new_val > max_val:
            # 进位：当前值设为最小值，向上级进1
            time_components[key] = min_val
            if idx > 0:
                adjust(idx - 1, 1)   # 上级加1
        else:
            time_components[key] = new_val

        # 如果改变了月份或年份，需要修正日期
        if key in ["year", "month"]:
            max_day = get_max_day(time_components["year"], time_components["month"])
            if time_components["day"] > max_day:
                time_components["day"] = max_day

    font_size = 40 if x_size > 800 else 32

    while True:
        if input.key("DX"):
            direction = input.value
            setting_index = (setting_index + direction) % len(setting_keys)
        elif input.key("DY"):
            direction = input.value
            adjust(setting_index, -direction)  # 注意：input.value 为 -1（减小）或 1（增加）
        elif input.key("A"):
            try:
                # 根据模式转换小时
                hour = time_components["hour"]
                mode = time_components["mode"]
                if mode == 0:  # AM
                    if hour == 12:
                        hour = 0
                elif mode == 1:  # PM
                    if hour != 12:
                        hour += 12
                # mode==2 直接使用
                new_time = datetime.datetime(
                    year=time_components["year"],
                    month=time_components["month"],
                    day=time_components["day"],
                    hour=hour,
                    minute=time_components["minute"],
                    second=time_components["second"]
                )
                subprocess.run(f"date -s '{new_time.isoformat()}'", shell=True, check=True)
                subprocess.run("hwclock --systohc", shell=True, check=True)
                gr.draw_log(translator.translate("Time_Updated"), fill=gr.colorBlueD1, outline=gr.colorGray)
                gr.draw_paint()
                time.sleep(2)
                current_window = "console"
                skip_input_check = True
                return
            except Exception as e:
                gr.draw_log(f"Error: {e}", fill=gr.colorRed, outline=gr.colorGray)
                gr.draw_paint()
                time.sleep(2)
        elif input.key("B"):
            current_window = "console"
            skip_input_check = True
            return

        # 绘制界面
        gr.draw_clear()
        gr.draw_text((x_size / 2, 50), translator.translate("SETTIME"), font=36, anchor="mm")

        # 构建显示字符串，并计算起始x
        parts = []
        for i, key in enumerate(setting_keys):
            if key == "mode":
                mode_text = ["AM", "PM", "24h"][time_components[key]]
                parts.append(mode_text)
            elif key == "year":
                parts.append(f"{time_components[key]:04d}")
            else:
                parts.append(f"{time_components[key]:02d}")
            if i < len(separators) and separators[i]:
                parts.append(separators[i])
        full_str = "".join(parts)
        total_width = gr.get_text_width(full_str, font=font_size)
        start_x = (x_size - total_width) // 2
        y_center = y_size // 2

        x_pos = start_x
        y_pos = y_center
        for i, key in enumerate(setting_keys):
            if key == "mode":
                text = ["AM", "PM", "24h"][time_components[key]]
            elif key == "year":
                text = f"{time_components[key]:04d}"
            else:
                text = f"{time_components[key]:02d}"
            color = gr.colorYellow if i == setting_index else "white"
            gr.draw_text((x_pos, y_pos), text, font=font_size, color=color, anchor="lm")
            x_pos += gr.get_text_width(text, font=font_size)
            if i < len(separators) and separators[i]:
                gr.draw_text((x_pos, y_pos), separators[i], font=font_size, color="white", anchor="lm")
                x_pos += gr.get_text_width(separators[i], font=font_size)

        gr.button_circle((30, button_y), "A", f"{translator.translate('Set')}")
        gr.button_circle((button_x, button_y), "B", f"{translator.translate('Back')}")
        gr.draw_paint()
        input.check()