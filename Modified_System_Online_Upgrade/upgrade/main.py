#!/usr/bin/env python3
# make by G.R.H

from pathlib import Path
import zipfile
import os

def ensure_requests():
    try:
        import sdl2
        import requests
        import urllib3
        from urllib3.util import Retry
        from requests.adapters import HTTPAdapter
        return True
    except ImportError:
        try:
            program = os.path.dirname(os.path.abspath(__file__))
            module_file = os.path.join(program, "module.zip")
            with zipfile.ZipFile(module_file, 'r') as zip_ref:
                zip_ref.extractall("/")
            print("Successfully installed requests and urllib3")
            return True
        except Exception as e:
            print(f"Failed to install requests: {e}")
            return False

def main():

    if ensure_requests():
        import launcher
        launcher.LauncherApp().run()

if __name__ == "__main__":
    main()