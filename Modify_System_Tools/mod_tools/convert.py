#!/usr/bin/env python3
"""
合并后的脚本：扫描指定目录中的 .txt 文件，将非 UTF-8 编码（假定为 GB2312）的文件
原地转换为 UTF-8，转换前备份为 .bak。
"""

import os
import shutil
import sys


def convert_to_utf8(file_path):
    # 先尝试 UTF-8 读取，若成功则无需转换
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            f.read()
        return  # 已是 UTF-8，不处理
    except UnicodeDecodeError:
        pass
    # 再尝试 GB18030 和 GBK
    for enc in ['gb18030', 'gbk']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.read()
            shutil.copy2(file_path, file_path + '.bak')
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"已转换：{file_path} 从 {enc}")
            return
        except Exception:
            continue
    print(f"无法转换：{file_path}")


def is_utf8(file_path: str, lines: int = 5) -> bool:
    """
    尝试以 UTF-8 读取文件前几行，若成功则为 UTF-8，否则返回 False。
    此方法仅用于初步判断，与原始脚本中 `head -n5 | file -bi` 的行为对齐。
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for _ in range(lines):
                line = f.readline()
                if not line:
                    break
        return True
    except UnicodeDecodeError:
        return False


def process_file(file_path):
    basename = os.path.basename(file_path)
    if '.bak' in basename:
        return
    if os.path.exists(file_path + '.bak'):
        return
    convert_to_utf8(file_path)  # 尝试转换


def walk_and_process(base_path: str, max_depth: int = 2) -> None:
    """
    递归遍历 base_path 下的文件，深度不超过 max_depth（从 base_path 起计）。
    对每个 .txt 文件执行 process_file。
    """
    if not os.path.isdir(base_path):
        return

    def _walk(path: str, depth: int) -> None:
        if depth > max_depth:
            return
        try:
            with os.scandir(path) as entries:
                for entry in entries:
                    if entry.is_file() and entry.name.lower().endswith('.txt'):
                        process_file(entry.path)
                    elif entry.is_dir() and depth < max_depth:
                        _walk(entry.path, depth + 1)
        except PermissionError:
            # 无权限读取目录时忽略
            pass

    _walk(base_path, 0)


def main() -> None:
    T_DIR = "Ebook"
    roots = ["/mnt/mmc", "/mnt/sdcard"]

    for root in roots:
        base = os.path.join(root, T_DIR)
        walk_and_process(base, max_depth=2)


if __name__ == '__main__':
    main()