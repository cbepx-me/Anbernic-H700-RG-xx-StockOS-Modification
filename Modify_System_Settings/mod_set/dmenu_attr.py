#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
dmenu_attr.py - dmenu 属性文件读写（多固件自动识别）

文件结构
--------
    总共 BODY_SIZE + 4 字节
    前 BODY_SIZE 字节为数据区，末尾 4 字节为 CRC32(数据区) ^ CRC_XOR，小端

profile 识别优先级
------------------
    1. 环境变量 DMENU_ATTR_PROFILE
    2. dmenu_attr.ini 文件大小（与 body_size + 4 一一对应）
    3. board.ini 里的销售型号
    4. 默认 rgdsplus

扩展字段：在“字段定义区”追加 register_field(...)，
         offsets={profile: 偏移} 声明各 profile 的位置。
"""

import os
from pathlib import Path
import struct
import warnings
import zlib
from collections import OrderedDict

__all__ = [
    "ATTR_PATH", "BODY_SIZE", "TAIL_SIZE", "FILE_SIZE", "CRC_XOR",
    "PROFILES", "ACTIVE_PROFILE", "TBD",
    "AttrError", "FieldError", "Field",
    "register_field", "get_field", "list_fields",
    "AttrFile",
    "read_param", "write_param", "read_all", "write_all",
    "compute_tail", "dump_info", "dump_raw",
]


# =====================================================================
#  固件配置表
# =====================================================================
ATTR_PATH = "/mnt/data/dmenu/dmenu_attr.ini"

PROFILES = {
    "rgdsplus":     {"body_size": 180, "crc_xor": 0x35495BFE},  # 文件 184 字节
    "rgds": {"body_size": 172, "crc_xor": 0x5613D0B9},  # 文件 176 字节
    "h700":       {"body_size": 136, "crc_xor": 0x773333E6},  # 文件 140 字节
}

# 偏移未确定时使用的占位符
# register_field 里 offsets[profile] 为 TBD → 该 profile 下跳过该字段
TBD = None


def _detect_profile():
    """按优先级识别 profile。"""
    # 1) 环境变量
    env = os.environ.get("DMENU_ATTR_PROFILE", "").strip()
    if env:
        if env in PROFILES:
            return env
        warnings.warn(
            "未知 profile: %r（可选: %s），改为按文件大小识别"
            % (env, ", ".join(PROFILES)), stacklevel=2)

    # 2) 文件大小
    try:
        size = os.path.getsize(ATTR_PATH)
    except OSError:
        size = None
    if size is not None:
        for name, cfg in PROFILES.items():
            if cfg["body_size"] + 4 == size:
                return name

    # 3) 读取型号
    try:
        text = Path("/mnt/vendor/oem/board.ini").read_text(
            encoding="utf-8", errors="ignore")
        for line in text.splitlines():
            model = line.strip()
            if not model:
                continue
            if model == "RGdsplus":
                return "rgdsplus"
            if model == "RGds":
                return "rgds"
            return "h700"
    except Exception:
        pass

    # 4) 兜底
    return "rgdsplus"


ACTIVE_PROFILE = _detect_profile()
_PROF = PROFILES[ACTIVE_PROFILE]
BODY_SIZE = _PROF["body_size"]
CRC_XOR   = _PROF["crc_xor"]
TAIL_SIZE = 4
FILE_SIZE = BODY_SIZE + TAIL_SIZE


# =====================================================================
#  异常
# =====================================================================
class AttrError(Exception):
    """属性文件读写相关的错误。"""


class FieldError(AttrError):
    """字段定义或访问相关的错误。"""


# =====================================================================
#  字段描述
# =====================================================================
class Field(object):
    """描述数据区中的一个参数域。"""

    __slots__ = ("name", "offset", "fmt", "size", "scale", "bias",
                 "min_value", "max_value", "description")

    def __init__(self, name, offset, fmt="<i", scale=1, bias=0,
                 min_value=None, max_value=None, description=""):
        if not isinstance(name, str) or not name:
            raise FieldError("字段名必须是非空字符串")

        if fmt[:1] in ">=!@":
            raise FieldError("字段 %s 只支持小端格式（'<'），收到: %r" % (name, fmt))
        if not fmt.startswith("<"):
            fmt = "<" + fmt

        size = struct.calcsize(fmt)
        try:
            unpacked = struct.unpack(fmt, b"\x00" * size)
        except struct.error as exc:
            raise FieldError("字段 %s 的格式无效: %s (%s)" % (name, fmt, exc))
        if len(unpacked) != 1:
            raise FieldError("字段 %s 的格式必须只描述一个值: %s" % (name, fmt))

        offset = int(offset)
        if offset < 0 or offset + size > BODY_SIZE:
            raise FieldError(
                "字段 %s 越界: 偏移 0x%X 大小 %d，超出当前 profile(%s) 的数据区 %d 字节"
                % (name, offset, size, ACTIVE_PROFILE, BODY_SIZE))

        self.name = name
        self.offset = offset
        self.fmt = fmt
        self.size = size
        self.scale = scale
        self.bias = bias
        self.min_value = min_value
        self.max_value = max_value
        self.description = description

    @property
    def is_integer(self):
        return self.fmt[-1] in "bBhHiIlLqQ"

    def raw_to_value(self, raw):
        if self.scale == 1 and self.bias == 0:
            return raw
        return raw * self.scale + self.bias

    def value_to_raw(self, value):
        if self.scale == 1 and self.bias == 0:
            raw = value
        else:
            raw = (value - self.bias) / float(self.scale)
        if self.is_integer:
            raw = int(round(raw))
        return raw

    def validate(self, value):
        if self.min_value is not None and value < self.min_value:
            raise ValueError(
                "字段 %s 的值 %r 小于下限 %r" % (self.name, value, self.min_value))
        if self.max_value is not None and value > self.max_value:
            raise ValueError(
                "字段 %s 的值 %r 大于上限 %r" % (self.name, value, self.max_value))

    def __repr__(self):
        return ("<Field %s @0x%02X fmt=%r range=[%s, %s]>"
                % (self.name, self.offset, self.fmt,
                   self.min_value, self.max_value))


# =====================================================================
#  字段注册表
# =====================================================================
_FIELDS = OrderedDict()


def _register(field):
    if field.name in _FIELDS:
        raise FieldError("字段名重复: %s" % field.name)
    for other in _FIELDS.values():
        if (field.offset < other.offset + other.size
                and other.offset < field.offset + field.size):
            raise FieldError(
                "字段 %s(0x%02X..0x%02X) 与已注册的 %s(0x%02X..0x%02X) 区间重叠"
                % (field.name, field.offset, field.offset + field.size,
                   other.name, other.offset, other.offset + other.size))
    _FIELDS[field.name] = field
    return field


def register_field(name, offset=None, fmt="<i", scale=1, bias=0,
                   min_value=None, max_value=None,
                   offsets=None, description=""):
    """注册一个参数域。

    offset=0x38                          所有 profile 共用同一偏移
    offsets={"rgdsplus": 0x38, "h700": 0x2C}
                                         每个 profile 用各自偏移；
                                         当前 profile 不在字典里或值为 TBD
                                         → 该字段在当前 profile 下跳过
    """
    if offsets is not None:
        if offset is not None:
            raise FieldError(
                "register_field(%r): offset 与 offsets 只能给一个" % name)
        if ACTIVE_PROFILE not in offsets:
            return None
        offset = offsets[ACTIVE_PROFILE]
        if offset is TBD or offset is None:
            return None
    if offset is None:
        raise FieldError(
            "register_field(%r): 必须提供 offset 或 offsets" % name)

    return _register(Field(name, offset, fmt, scale, bias,
                           min_value, max_value, description))


def get_field(name):
    try:
        return _FIELDS[name]
    except KeyError:
        raise FieldError(
            "未注册的字段: %s（当前 profile=%s 已注册: %s）"
            % (name, ACTIVE_PROFILE, ", ".join(_FIELDS) or "无")) from None


def list_fields():
    return list(_FIELDS.values())


# =====================================================================
#  校验计算
# =====================================================================
def compute_tail(body):
    return (zlib.crc32(bytes(body)) & 0xFFFFFFFF) ^ CRC_XOR


# =====================================================================
#  文件对象
# =====================================================================
class AttrFile(object):
    """dmenu_attr.ini 的内存映像，修改后一次落盘。"""

    def __init__(self, path=ATTR_PATH, strict=True):
        self.path = path
        self.strict = strict
        self._data = None
        self._dirty = False

    def load(self, path=None):
        target = path or self.path
        with open(target, "rb") as fh:
            data = fh.read()
        if len(data) != FILE_SIZE:
            raise AttrError(
                "%s 大小异常: %d 字节，应为 %d 字节（profile=%s）"
                % (target, len(data), FILE_SIZE, ACTIVE_PROFILE))
        self.path = target
        self._data = bytearray(data)
        self._dirty = False
        if not self.verify():
            msg = "%s CRC 校验失败" % target
            if self.strict:
                raise AttrError(msg)
            warnings.warn(msg, stacklevel=2)
        return self

    def _ensure_loaded(self):
        if self._data is None:
            self.load()

    def verify(self):
        self._ensure_loaded()
        body = bytes(self._data[:BODY_SIZE])
        tail = struct.unpack_from("<I", self._data, BODY_SIZE)[0]
        return tail == compute_tail(body)

    def save(self, path=None):
        self._ensure_loaded()
        target = path or self.path
        body = bytes(self._data[:BODY_SIZE])
        struct.pack_into("<I", self._data, BODY_SIZE, compute_tail(body))

        tmp = target + ".tmp"
        with open(tmp, "wb") as fh:
            fh.write(self._data)
        os.replace(tmp, target)
        self._dirty = False
        return True

    @property
    def data(self):
        self._ensure_loaded()
        return bytes(self._data)

    def get(self, name, raw=False):
        self._ensure_loaded()
        f = get_field(name)
        value = struct.unpack_from(f.fmt, self._data, f.offset)[0]
        return value if raw else f.raw_to_value(value)

    def set(self, name, value, validate=True):
        self._ensure_loaded()
        f = get_field(name)
        if validate:
            f.validate(value)
        raw = f.value_to_raw(value)
        struct.pack_into(f.fmt, self._data, f.offset, raw)
        self._dirty = True
        return raw

    def as_dict(self, raw=False):
        self._ensure_loaded()
        return {f.name: self.get(f.name, raw=raw) for f in _FIELDS.values()}

    def update(self, mapping, validate=True):
        for name, value in mapping.items():
            self.set(name, value, validate=validate)
        return self

    def __getitem__(self, name):
        return self.get(name)

    def __setitem__(self, name, value):
        self.set(name, value)

    def __contains__(self, name):
        return name in _FIELDS

    def __iter__(self):
        return iter(_FIELDS)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None and self._dirty:
            self.save()
        return False

    def __repr__(self):
        return "<AttrFile %s [%s]%s>" % (
            self.path, ACTIVE_PROFILE, " (dirty)" if self._dirty else "")


# =====================================================================
#  便捷函数
# =====================================================================
def read_param(name, path=ATTR_PATH, raw=False):
    return AttrFile(path).get(name, raw=raw)


def write_param(name, value, path=ATTR_PATH):
    with AttrFile(path) as attr:
        attr.set(name, value)
    return True


def read_all(path=ATTR_PATH, raw=False):
    return AttrFile(path).as_dict(raw=raw)


def write_all(mapping, path=ATTR_PATH):
    with AttrFile(path) as attr:
        attr.update(mapping)
    return True


# =====================================================================
#  调试工具
# =====================================================================
def dump_info(path=ATTR_PATH):
    try:
        attr = AttrFile(path, strict=False)
        attr.load()
    except OSError as exc:
        print("无法打开 %s: %s" % (path, exc))
        return

    data = attr.data
    print("profile   : %s" % ACTIVE_PROFILE)
    print("文件路径  : %s" % path)
    print("文件大小  : %d 字节 (body=%d, tail=%d)"
          % (len(data), BODY_SIZE, TAIL_SIZE))
    print("校验通过  : %s" % attr.verify())
    print("-" * 68)
    for f in list_fields():
        try:
            value = attr.get(f.name)
            raw = attr.get(f.name, raw=True)
            print("0x%02X  %-22s = %-8s (raw=%-6s) %s"
                  % (f.offset, f.name, value, raw, f.description))
        except Exception as exc:
            print("0x%02X  %-22s <读取失败: %s>" % (f.offset, f.name, exc))
    body = data[:BODY_SIZE]
    tail = struct.unpack_from("<I", data, BODY_SIZE)[0]
    print("-" * 68)
    print("body crc32: 0x%08x" % (zlib.crc32(body) & 0xFFFFFFFF))
    print("tail 值   : 0x%08x" % tail)
    print("期望 tail : 0x%08x  (K=0x%08x)" % (compute_tail(body), CRC_XOR))


def dump_raw(path=ATTR_PATH):
    try:
        data = AttrFile(path, strict=False).data
    except OSError as exc:
        print("无法打开 %s: %s" % (path, exc))
        return
    body = data[:BODY_SIZE]
    print("profile : %s   body_size=%d" % (ACTIVE_PROFILE, BODY_SIZE))
    print("offset  bytes               int32        已注册字段")
    for off in range(0, BODY_SIZE, 4):
        chunk = body[off:off + 4]
        val = struct.unpack("<i", chunk)[0]
        names = [f.name for f in _FIELDS.values()
                 if off <= f.offset < off + 4]
        print("0x%02X    %s  %-12d %s" % (off, chunk.hex(" "), val, ",".join(names)))


# =====================================================================
#  字段定义区
# =====================================================================
# rgdsplus 与 rgds 偏移一致；h700 整体比 rgdsplus 小 0x0C。

register_field(
    "swap_screen",
    offsets={"rgdsplus": 0x00, "rgds": 0x00},
    fmt="<i", min_value=0, max_value=1,
    description="交换上下屏 (0关闭, 1开启)",
)
register_field(
    "single_screen",
    offsets={"rgdsplus": 0x04, "rgds": 0x04},
    fmt="<i", min_value=0, max_value=2,
    description="单屏显示 (0关闭, 1开启, 2开启同时交换屏幕)",
)
register_field(
    "brightness_bottom",
    offsets={"rgdsplus": 0x20, "rgds": 0x20},
    fmt="<i", bias=1, min_value=1, max_value=8,
    description="下屏亮度等级 (1~8)",
)
register_field(
    "brightness_top",
    offsets={"rgdsplus": 0x24, "rgds": 0x24, "h700": 0x18},
    fmt="<i", bias=1, min_value=1, max_value=8,
    description="上屏亮度等级 (1~8)",
)
register_field(
    "lock_screen",
    offsets={"rgdsplus": 0x28, "rgds": 0x28, "h700": 0x1C},
    fmt="<i", min_value=0, max_value=4,
    description="自动锁屏 (0一分钟, 1二分钟, 2五分钟, 3十分钟, 4永不)",
)
register_field(
    "volume",
    offsets={"rgdsplus": 0x30, "rgds": 0x30, "h700": 0x24},
    fmt="<i", min_value=0, max_value=10,
    description="系统音量 (0~10)",
)
register_field(
    "button_sound",
    offsets={"rgdsplus": 0x34, "rgds": 0x34, "h700": 0x28},
    fmt="<i", min_value=0, max_value=1,
    description="按键声音 (0关闭, 1开启)",
)
register_field(
    "language",
    offsets={"rgdsplus": 0x38, "rgds": 0x38, "h700": 0x2C},
    fmt="<i", min_value=0, max_value=9,
    description="系统语言 (0~9)",
)
register_field(
    "wifi",
    offsets={"rgdsplus": 0x44, "rgds": 0x44, "h700": 0x38},
    fmt="<i", min_value=0, max_value=1,
    description="WIFI开关 (0关闭, 1开启)",
)
register_field(
    "simple_menu",
    offsets={"rgdsplus": 0x8C, "rgds": 0x8C, "h700": 0x80},
    fmt="<i", min_value=0, max_value=1,
    description="简单菜单 (0开启, 1关闭)",
)


if __name__ == "__main__":
    dump_info()