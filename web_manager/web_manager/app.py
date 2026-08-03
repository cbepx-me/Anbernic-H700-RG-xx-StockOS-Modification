#!/usr/bin/env python3
import os
from pathlib import Path
import socket
import threading
import time
from flask import Flask, request, jsonify, send_file, render_template_string
import sys

# 导入你的已有模块
from systems import systems, get_system_extension
from anbernic import Anbernic
from language import Translator

# 版本
ver = "1.0.0"

# 全局设备信息
board_info = "Unknown"
system_version = "Unknown"

try:
    import sdl2
    import sdl2.ext
    from PIL import Image, ImageDraw, ImageFont
    SDL_AVAILABLE = True
except ImportError:
    SDL_AVAILABLE = False

try:
    board_info = Path("/mnt/vendor/oem/board.ini").read_text().splitlines()[0]
    board_mapping = {
        'RGcubexx': 1,
        'RG34xx': 2,
        'RG34xxSP': 2,
        'RGSP': 2,
        'RG28xx': 3,
        'RG35xx+_P': 4,
        'RG35xxH': 5,
        'RG35xxSP': 6,
        'RG40xxH': 7,
        'RG40xxV': 8,
        'RG35xxPRO': 9
    }
    hw_info = board_mapping.get(board_info, 5)  # 默认 5
except:
    hw_info = 5

import input

try:
    lang_info = Path("/mnt/vendor/oem/language.ini").read_text().splitlines()[0]
    system_list = ['zh_CN', 'zh_TW', 'en_US', 'ja_JP', 'ko_KR', 'es_LA', 'ru_RU', 'de_DE', 'fr_FR', 'pt_BR']
    system_lang = system_list[int(lang_info)]
except (FileNotFoundError, IndexError):
    system_lang = 'en_US'


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
        return True
    except socket.gaierror:
        print("DNS resolution failed")
    for host, port in test_servers:
        try:
            socket.setdefaulttimeout(3)
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
            s.close()
            print("Network connection test passed with %s:%s", host, port)
            return True
        except (socket.timeout, socket.error) as e:
            print("Connection test failed for %s:%s: %s", host, port, e)
            continue
    print("All network connection tests failed")
    return False

def show_splash_screen(ip):
    """使用 graphic.py 中的 UserInterface 显示启动画面"""
    print("[DEBUG] show_splash_screen called")
    try:
        from graphic import UserInterface
        ui = UserInterface()
        print("[DEBUG] UI instance created")
        ui.draw_clear()
        box_width = 600
        box_height = 260
        box_x = (ui.screen_width - box_width) // 2
        box_y = (ui.screen_height - box_height) // 2 - 20
        ui.draw_rectangle_r(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            radius=15,
            fill="#1a1a2e",
            outline="#0072bb"
        )
        title = f'★ {translator.translate("Anbernic game management")} ★'
        ui.draw_text((ui.screen_width // 2, box_y + 45), title, font=32, color="#ffffff", anchor="mm")
        url_text = f"http://{ip}:5000"
        ui.draw_text((ui.screen_width // 2, box_y + 105), url_text, font=32, color="#00d7ff", anchor="mm")
        open_text = translator.translate("Accessing the above address through a browser")
        ui.draw_text((ui.screen_width // 2, box_y + 165), open_text, font=25, color="#ffd700", anchor="mm")
        hint = translator.translate("Press SELECT to exit")
        ui.draw_text((ui.screen_width // 2, box_y + box_height - 35), hint, font=23, color="#888888", anchor="mm")
        ui.draw_text((box_x + box_width - 50, box_y + box_height - 35), f"v{ver}", font=23, color="#888888", anchor="mm")
        ui.draw_paint()
        print("[DEBUG] splash screen finished")
    except Exception as e:
        print(f"屏幕显示异常: {e}")
        import traceback
        traceback.print_exc()

def show_error_screen():
    try:
        from graphic import UserInterface
        ui = UserInterface()
        ui.draw_clear()
        box_width = 600
        box_height = 260
        box_x = (ui.screen_width - box_width) // 2
        box_y = (ui.screen_height - box_height) // 2 - 20
        ui.draw_rectangle_r(
            [box_x, box_y, box_x + box_width, box_y + box_height],
            radius=15,
            fill="#1a1a2e",
            outline="#0072bb"
        )
        title = f'✘ {translator.translate("No Internet Connection")} ✘'
        ui.draw_text((ui.screen_width // 2, box_y + 45), title, font=32, color="#cb0202", anchor="mm")
        open_text = translator.translate("Please check your network settings")
        ui.draw_text((ui.screen_width // 2, box_y + 135), open_text, font=29, color="#ffd700", anchor="mm")
        ui.draw_paint()
    except Exception as e:
        print(f"屏幕显示异常: {e}")
        import traceback
        traceback.print_exc()

# ---------- 获取本机 IP ----------
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return '127.0.0.1'

# ---------- Flask 应用 ----------
app = Flask(__name__)

# 设置上传文件大小限制（1GB）
app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024 * 1024

# 配置
ALLOWED_IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}
PREVIEW_DIR_NAME = "Imgs"

device = Anbernic()
translator = Translator(system_lang)
current_sd = 1  # 默认使用 SD1

def safe_filename(filename):
    """
    安全处理文件名：保留 Unicode（中文等），仅移除路径分隔符和 '..'，
    防止目录遍历攻击。
    """
    # 替换路径分隔符
    filename = filename.replace('/', '_').replace('\\', '_')
    # 移除 '..' 防止目录遍历
    while '..' in filename:
        filename = filename.replace('..', '_')
    # 移除控制字符（ASCII < 32）
    filename = ''.join(c for c in filename if ord(c) >= 32)
    # 去除首尾空白
    filename = filename.strip()
    # 如果文件名为空，给一个默认名
    if not filename:
        filename = 'unnamed'
    return filename

def get_rom_root():
    if current_sd == 1:
        path = device.get_sd1_storage_path()
    else:
        path = device.get_sd2_storage_path()
    print(f"[DEBUG] get_rom_root -> {path}, exists: {os.path.exists(path)}")
    return path

def get_preview_path(game_full_path):
    game_dir = os.path.dirname(game_full_path)
    game_basename = os.path.basename(game_full_path)
    name_without_ext = os.path.splitext(game_basename)[0]
    preview_dir = os.path.join(game_dir, PREVIEW_DIR_NAME)
    if not os.path.isdir(preview_dir):
        return None
    for ext in ALLOWED_IMAGE_EXT:
        candidate = os.path.join(preview_dir, name_without_ext + ext)
        if os.path.exists(candidate):
            return candidate
    return None

def detect_system_from_ext(filename):
    ext = os.path.splitext(filename)[1].lower().lstrip('.')
    for sys in systems:
        if ext in sys["extensions"]:
            return sys["name"]
    return "Unknown"

def get_subdirs():
    rom_root = get_rom_root()
    if not os.path.isdir(rom_root):
        print(f"[DEBUG] ROM root {rom_root} is not a directory")
        return []
    dirs = []
    for item in os.listdir(rom_root):
        full = os.path.join(rom_root, item)
        if os.path.isdir(full) and not item.startswith('.') and item != PREVIEW_DIR_NAME:
            has_games = False
            for root, _, files in os.walk(full):
                if PREVIEW_DIR_NAME in root.split(os.sep):
                    continue
                for f in files:
                    if not f.startswith('.'):
                        has_games = True
                        break
                if has_games:
                    break
            dirs.append({
                'name': item,
                'path': item,
                'has_games': has_games
            })
    dirs.sort(key=lambda x: x['name'].lower())
    print(f"[DEBUG] get_subdirs found {len(dirs)} directories: {[d['name'] for d in dirs]}")
    return dirs

def get_files_in_dir(subdir):
    """
    返回指定目录下的子目录和文件（不递归）。
    subdir 可以是 ''（根目录）、'NES' 或 'NES/子目录' 等。
    """
    rom_root = get_rom_root()
    target_dir = os.path.join(rom_root, subdir)
    if not os.path.isdir(target_dir):
        return []
    items = []
    for item in os.listdir(target_dir):
        full_path = os.path.join(target_dir, item)
        rel_path = os.path.relpath(full_path, rom_root)
        if os.path.isdir(full_path):
            # 忽略 Imgs 目录
            if item == PREVIEW_DIR_NAME:
                continue
            items.append({
                'name': item,
                'path': rel_path,
                'is_dir': True,
                'size': 0,
                'console': os.path.basename(subdir) if subdir else '',
                'preview': None,
                'modified': os.path.getmtime(full_path)
            })
        else:
            ext = os.path.splitext(item)[1].lower()
            # 仅识别支持的游戏扩展名
            if detect_system_from_ext(item) == "Unknown" and ext != '.zip':
                continue
            console = detect_system_from_ext(item)
            if console == "Unknown":
                console = os.path.basename(subdir) if subdir else "Unknown"
            if ext == '.zip':
                console = os.path.basename(subdir) if subdir else "Unknown"
            size = os.path.getsize(full_path)
            preview = get_preview_path(full_path)
            items.append({
                'name': os.path.splitext(item)[0],
                'path': rel_path,
                'is_dir': False,
                'size': size,
                'console': console,
                'preview': preview,
                'modified': os.path.getmtime(full_path)
            })
    # 目录在前，文件在后，各自按名称排序
    dirs = [i for i in items if i['is_dir']]
    files = [i for i in items if not i['is_dir']]
    dirs.sort(key=lambda x: x['name'].lower())
    files.sort(key=lambda x: x['name'].lower())
    return dirs + files

def delete_game(game_rel_path):
    rom_root = get_rom_root()
    full_path = os.path.join(rom_root, game_rel_path)
    if not os.path.exists(full_path):
        return False
    os.remove(full_path)
    preview = get_preview_path(full_path)
    if preview and os.path.exists(preview):
        os.remove(preview)
    return True

def get_system_version():
    """尝试从常见文件读取系统版本"""
    version_files = [
        '/mnt/vendor/oem/version.ini',
        '/etc/version',
        '/etc/os-release'
    ]
    for f in version_files:
        if os.path.exists(f):
            try:
                with open(f, 'r') as file:
                    content = file.read().strip()
                    lines = content.split('\n')
                    for line in lines:
                        if 'version' in line.lower() or 'VERSION' in line:
                            return line.split('=')[-1].strip()
                    return lines[0] if lines else 'Unknown'
            except:
                pass
    return 'Unknown'

# ---------- API 路由 ----------
@app.route('/api/device_info')
def device_info():
    return jsonify({
        'board': board_info,
        'system_version': get_system_version(),
        'ver': ver
    })

from flask import render_template_string
@app.route('/')
def index():
    lang = request.args.get('lang') or system_lang
    translator = Translator(lang)
    return render_template_string(HTML_TEMPLATE, _=translator.translate)

@app.route('/api/sd', methods=['GET', 'POST'])
def handle_sd():
    global current_sd
    if request.method == 'POST':
        data = request.get_json()
        new_sd = data.get('sd')
        if new_sd in (1, 2):
            current_sd = new_sd
            device.set_sd_storage(new_sd)
            return jsonify({'status': 'ok', 'sd': current_sd})
        return jsonify({'error': 'Invalid SD'}), 400
    else:
        return jsonify({'sd': current_sd})

@app.route('/api/dirs')
def api_dirs():
    dirs = get_subdirs()
    print(f"[DEBUG] api_dirs returning {len(dirs)} directories")
    return jsonify(dirs)

@app.route('/api/files')
def api_files():
    subdir = request.args.get('dir', '')
    if not subdir:
        return jsonify([])
    return jsonify(get_files_in_dir(subdir))

@app.route('/api/preview')
def get_preview():
    path = request.args.get('path')
    if not path:
        return '', 400
    rom_root = get_rom_root()
    full = os.path.join(rom_root, path)
    if not os.path.exists(full):
        return '', 404
    preview = get_preview_path(full)
    if preview and os.path.exists(preview):
        return send_file(preview, mimetype='image/jpeg')
    else:
        return '', 404

@app.route('/api/storage')
def get_storage():
    """获取当前 SD 卡的存储空间信息"""
    import shutil
    rom_root = get_rom_root()
    try:
        total, used, free = shutil.disk_usage(rom_root)
        return jsonify({
            'total': total,
            'used': used,
            'free': free,
            'path': rom_root
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_game():
    console = request.form.get('console', '').strip()
    if not console:
        return jsonify({'error': 'Missing console directory'}), 400

    rom_files = request.files.getlist('game_files')
    preview_files = request.files.getlist('preview_file')  # 多个预览图

    if not rom_files:
        return jsonify({'error': 'No ROM files uploaded'}), 400

    rom_root = get_rom_root()
    base_dir = os.path.join(rom_root, console)
    os.makedirs(base_dir, exist_ok=True)

    saved_roms = []
    preview_map = {}  # 用于单文件匹配

    # 判断是否只有单个 ROM
    single_rom = (len(rom_files) == 1)

    if single_rom:
        # 单文件模式：收集预览图，按主名建立映射
        for pf in preview_files:
            if pf.filename == '':
                continue
            base_name = os.path.splitext(pf.filename)[0]
            ext = os.path.splitext(pf.filename)[1].lower()
            if ext in ALLOWED_IMAGE_EXT:
                preview_map[base_name] = pf

    # 处理所有 ROM 文件
    for rf in rom_files:
        if rf.filename == '':
            continue
        safe_name = safe_filename(rf.filename)
        target_path = os.path.join(base_dir, safe_name)
        # 防止路径穿越
        if not os.path.abspath(target_path).startswith(os.path.abspath(rom_root)):
            return jsonify({'error': 'Invalid path'}), 400
        rf.save(target_path)
        saved_roms.append(target_path)

        # 如果是单文件模式，检查是否有匹配的预览图
        if single_rom:
            rom_base = os.path.splitext(safe_name)[0]
            if rom_base in preview_map:
                pf = preview_map[rom_base]
                ext = os.path.splitext(pf.filename)[1].lower()
                preview_dir = os.path.join(base_dir, PREVIEW_DIR_NAME)
                os.makedirs(preview_dir, exist_ok=True)
                preview_path = os.path.join(preview_dir, rom_base + ext)
                pf.save(preview_path)

    # 如果是多文件模式，将所有预览图原样保存到 Imgs 目录
    if not single_rom and preview_files:
        preview_dir = os.path.join(base_dir, PREVIEW_DIR_NAME)
        os.makedirs(preview_dir, exist_ok=True)
        for pf in preview_files:
            if pf.filename == '':
                continue
            # 直接保存原始文件名（安全处理）
            safe_preview_name = safe_filename(pf.filename)
            preview_path = os.path.join(preview_dir, safe_preview_name)
            pf.save(preview_path)

    return jsonify({
        'success': True,
        'count': len(saved_roms),
        'paths': [os.path.relpath(p, rom_root) for p in saved_roms]
    })

@app.route('/api/game', methods=['DELETE'])
def api_delete_game():
    path = request.args.get('path')
    if not path:
        return jsonify({'error': 'Missing path'}), 400
    if delete_game(path):
        return jsonify({'success': True})
    else:
        return jsonify({'error': 'Delete failed'}), 500

@app.route('/api/update_preview', methods=['POST'])
def update_preview():
    """更新预览图：自动重命名并覆盖已有文件"""
    path = request.form.get('path')
    if not path:
        return jsonify({'error': 'Missing game path'}), 400
    if 'image' not in request.files:
        return jsonify({'error': 'No image file'}), 400
    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'Empty filename'}), 400

    ext = os.path.splitext(image_file.filename)[1].lower()
    if ext not in ALLOWED_IMAGE_EXT:
        return jsonify({'error': 'Unsupported image format'}), 400

    rom_root = get_rom_root()
    game_full_path = os.path.join(rom_root, path)
    if not os.path.exists(game_full_path):
        return jsonify({'error': 'Game file not found'}), 404

    # 生成预览图文件名（与游戏主名相同）
    base_name = os.path.splitext(os.path.basename(game_full_path))[0]
    target_dir = os.path.join(os.path.dirname(game_full_path), PREVIEW_DIR_NAME)
    os.makedirs(target_dir, exist_ok=True)

    preview_filename = base_name + ext
    preview_path = os.path.join(target_dir, preview_filename)

    # 保存文件（直接覆盖）
    image_file.save(preview_path)

    return jsonify({
        'success': True,
        'preview_path': os.path.relpath(preview_path, rom_root)
    })

@app.route('/shutdown', methods=['GET'])
def shutdown():
    import threading
    import time
    import os

    def force_exit():
        # 等待 0.3 秒，确保 HTTP 响应已经发送到客户端
        time.sleep(0.3)
        # 强制退出进程，不执行任何清理（在嵌入式设备上安全）
        os._exit(0)

    # 启动后台线程执行退出
    threading.Thread(target=force_exit).start()
    return "服务器正在关闭...", 200

# ---------- 前端 HTML ----------
base_path = os.path.dirname(os.path.abspath(__file__))
html_path = os.path.join(base_path, "web", "template.html")
if os.path.exists(html_path):
    with open(html_path, 'r') as f:
        HTML_TEMPLATE = f.read()
else:
    print(f'缺少文件: template.html，正在退出...')
    os._exit(0)

def exit_on_key():
    """后台线程：监听任意物理按键，按下即退出程序"""
    print("[DEBUG] 按键监听线程已启动，按 SELECT 退出")
    while True:
        input.check()  # 阻塞等待按键事件
        if input.key("SELECT"):
            print(f"[DEBUG] 检测到按键: {input.codeName}，正在退出...")
            os._exit(0)  # 直接退出，避免调用路由

def main():
    if not is_connected():
        show_error_screen()
        time.sleep(3)
        sys.exit(1)

    ip = get_local_ip()
    print("\n" + "="*50)
    print("  🎮 Anbernic 游戏管理器已启动")
    print("="*50)
    print(f"  访问地址: http://{ip}:5000")
    print(f"  本机地址: http://127.0.0.1:5000")
    print("  关闭服务: 按 Ctrl+C 或访问 /shutdown")
    print("="*50 + "\n")
    show_splash_screen(ip)

    rom_root = get_rom_root()
    print(f"[DEBUG] ROM root path: {rom_root}")
    if os.path.exists(rom_root):
        print(f"[DEBUG] Content of ROM root: {os.listdir(rom_root)}")
    else:
        print(f"[DEBUG] ROM root does not exist!")

    threading.Thread(target=exit_on_key, daemon=True).start()

    # 启动 Flask
    app.run(host='0.0.0.0', port=5000, debug=False)

# ---------- 启动 ----------
if __name__ == '__main__':
    main()