import glob
import os
import struct

from app import hw_info

code = 0
codeName = ""
value = 0

def find_anbernic_device():
    keyword = "ANBERNIC"
    for event_path in glob.glob("/dev/input/event*"):
        dev_name = os.path.basename(event_path)
        sys_path = f"/sys/class/input/{dev_name}/device/name"
        try:
            with open(sys_path, 'r') as f:
                name = f.read().strip()
                if keyword in name:
                    return event_path
        except Exception:
            continue

    fallback = f"/dev/input/event{hw_info}"
    if os.path.exists(fallback):
        return fallback
    raise RuntimeError("No ANBERNIC input device found")

device_path = find_anbernic_device()

mapping = {
    304: "A",
    305: "B",
    306: "Y",
    307: "X",
    308: "L1",
    309: "R1",
    314: "L2",
    315: "R2",
    17: "DY",
    16: "DX",
    310: "SELECT",
    311: "START",
    312: "MENUF",
    114: "V+",
    115: "V-",
}

def check():
    global type, code, codeName, codeDown, value, valueDown
    with open(device_path, "rb") as f:
        while True:
            event = f.read(24)
            
            if event:
                (tv_sec, tv_usec, type, kcode, kvalue) = struct.unpack('llHHI', event)
                if kvalue != 0:
                    if kvalue != 1:
                        kvalue = -1
                    code = kcode
                    codeName = mapping.get(code, str(code))
                    value = kvalue
                    return

def key(keyCodeName, keyValue = 99):
    global code, codeName, value
    if codeName == keyCodeName:
        if keyValue != 99: 
            return value == keyValue
        return True

def slide_key():
    global codeName
    if codeName:
        return True

def reset_input():
    global codeName, value
    codeName = ""
    value = 0