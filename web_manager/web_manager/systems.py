systems = [
    {"name": "A2600", "id": 0, "extensions": ["zip", "a26", "bin"]},
    {"name": "A5200", "id": 40, "extensions": ["a52", "zip"]},
    {"name": "A7800", "id": 0, "extensions": ["zip", "a78", "bin"]},
    {"name": "A800", "id": 0, "extensions": ["zip", "atr", "rom"]},
    {"name": "AMIGA","id": 64,"extensions": ["zip", "adf", "uae", "ipf", "dms", "adz", "lha", "m3u", "hdf", "hdz", "iso", "cue", "chd"]},
    {"name": "ATARIST","id": 42,"extensions": ["st", "stx", "msa", "dim", "ipf", "m3u", "zip"],},
    {"name": "ATOMISWAVE", "id": 53, "extensions": ["chd", "bin", "gdi", "zip"]},
    {"name": "C64","id": 66,"extensions": ["zip", "d64", "d71", "d80", "d81", "d82", "g64", "g41", "x64", "t64", "tap", "prg", "p00", "crt", "bin", "d6z", "d7z", "d8z", "g6z", "g4z", "x6z", "cmd", "m3u", "vsf", "nib", "nbz"]},
    {"name": "CPS1", "id": 6, "extensions": ["zip"]},
    {"name": "CPS2", "id": 7, "extensions": ["zip"]},
    {"name": "CPS3", "id": 8, "extensions": ["zip"]},
    {"name": "DOS","id": 135,"extensions": ["dosz", "com", "bat", "exe", "zip"]},
    {"name": "DREAMCAST", "id": 23, "extensions": ["chd", "cdi", "gdi", "cue", "iso", "bin", "zip",  "m3u"]},
    {"name": "EASYRPG", "id": 0, "extensions": ["ldb", "sh"]},
    {"name": "FBNEO", "id": 142, "extensions": ["zip"]},
    {"name": "FC","id": 3,"extensions": ["nes", "zip"]},
    {"name": "FDS", "id": 0, "extensions": ["zip", "fds"]},
    {"name": "GB", "id": 9, "extensions": ["gb", "zip"]},
    {"name": "GBA", "id": 12, "extensions": ["gba", "zip"]},
    {"name": "GBC", "id": 10, "extensions": ["gb", "gbc", "zip"]},
    {"name": "GG", "id": 21, "extensions": ["gg", "zip"]},
    {"name": "GW", "id": 52, "extensions": ["mgw"]},
    {"name": "HBMAME", "id": 0, "extensions": ["zip"]},
    {"name": "LYNX", "id": 28, "extensions": ["lnx", "zip"]},
    {"name": "MAME", "id": 75, "extensions": ["zip"]},
    {"name": "MD", "id": 1, "extensions": ["gen", "md", "smd", "bin", "zip"]},
    {"name": "MDCD","id": 20,"extensions": ["zip", "cue", "iso", "chd", "m3u", "sg"]},
    {"name": "MSX","id": 113,"extensions": ["zip", "rom", "ri", "mx1", "mx2", "col", "dsk", "cas", "sg", "sc", "m3u"]},
    {"name": "N64", "id": 14, "extensions": ["n64", "v64", "z64", "bin", "zip"]},
    {"name": "NAOMI", "id": 56, "extensions": ["zip"]},
    {"name": "NEOGEO", "id": 0, "extensions": ["zip"]},
    {"name": "NEOCD", "id": 0, "extensions": ["zip", "cue", "chd", "iso"]},
    {"name": "NGP", "id": 82, "extensions": ["ngp", "ngc", "zip"]},
    {"name": "PCE", "id": 105, "extensions": ["pce", "cue", "ccd", "zip"]},
    {"name": "PCECD","id": 114,"extensions": ["cue", "ccd", "chd", "toc", "m3u"]},
    {"name": "PGM2", "id": 0, "extensions": ["zip"]},
    {"name": "PICO", "id": 234, "extensions": ["p8", "png"]},
    {"name": "POKE", "id": 211, "extensions": ["min", "zip"]},
    {"name": "PS","id": 57,"extensions": ["bin", "img", "mdf", "iso", "cue", "ccd", "pbp", "chd", "m3u", "toc", "cbn", "sub", "zip"]},
    {"name": "PSP","id": 61,"extensions": ["cso", "pbp", "chd", "iso"],},
    {"name": "SATURN","id": 22,"extensions": ["bin", "cue", "iso", "mds", "ccd", "chd", "rar"],},
    {"name": "SCUMMVM", "id": 123, "extensions": ["zip", "scummvm"]},
    {"name": "SEGA32X","id": 19,"extensions": ["32x", "smd", "md", "bin", "ccd", "cue", "img", "iso", "sub", "wav", "zip"]},
    {"name": "SFC", "id": 4, "extensions": ["zip", "smc", "sfc"]},
    {"name": "SMS", "id": 2, "extensions": ["sms", "zip"]},
    {"name": "VARCADE", "id": 0, "extensions": ["zip"]},
    {"name": "VB", "id": 11, "extensions": ["vb", "zip"]},
    {"name": "VIC20", "id": 0, "extensions": ["zip", "a0", "20", "b0", "d6", "d7", "d8", "g4", "g6", "gz", "x6", "t64", "tap", "prg", "p00", "crt", "bin", "cmd", "m3u", "vsf", "nib", "nbz"]},
    {"name": "WS", "id": 45, "extensions": ["ws", "wsc", "zip"]},
    {"name": "NDS", "id": 15, "extensions": ["nds", "zip"]},
]


def get_system_id(system_name: str) -> int:
    for system in systems:
        if system["name"] == system_name:
            return system["id"]
    return -1


def get_system_extension(system_name: str) -> list[str]:
    for system in systems:
        if system["name"] == system_name:
            return system["extensions"]
    return []
