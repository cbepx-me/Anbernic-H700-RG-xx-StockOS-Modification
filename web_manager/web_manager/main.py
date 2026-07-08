#!/usr/bin/env python3
# make by G.R.H

from pathlib import Path
import zipfile
import os

def ensure_requests():
    try:
        import sdl2
        from PIL import Image, ImageDraw, ImageFont
        from flask import Flask, request, jsonify, send_file, render_template_string
        return True
    except ImportError:
        try:
            program = os.path.dirname(os.path.abspath(__file__))
            module_file = os.path.join(program, "module.zip")
            with zipfile.ZipFile(module_file, 'r') as zip_ref:
                zip_ref.extractall("/")
            print("Successfully installed sdl2 and PIL and flask")
            return True
        except Exception as e:
            print(f"Failed to install: {e}")
            return False

def main():

    if ensure_requests():
        import app
        app.main()

if __name__ == "__main__":
    main()