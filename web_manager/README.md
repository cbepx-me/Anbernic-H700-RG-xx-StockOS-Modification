# Web Game Manager – User Guide

This guide explains how to install, run, and use the **Web Game Manager** on your Anbernic handheld console.

---

## 1. Overview

The Web Game Manager turns your Anbernic device into a **web‑based ROM management center**.  
You can browse, upload, delete, and preview games from any computer, phone, or tablet on the same Wi‑Fi network – no need to eject the SD card.

### Key features at a glance
- 📂 Browse ROMs by console folder (e.g., NES, SNES, PS, GBA)  
- 🖼️ Show/hide preview images from the `Imgs/` folder  
- 📤 Upload single or multiple ROM files + previews in one go  
- 🗑️ Delete games and their associated preview images  
- 🔄 Switch between SD1 and SD2 instantly  
- 🔍 Search games by name or platform  
- 🌍 Interface in 10 languages (auto‑detected from system settings)  
- 🎮 Exit gracefully by pressing the **SELECT** button on the device  

---

## 2. Installation

1. Copy the entire program folder (e.g., `web_manager/`) to your device.  
   A typical location is `/mnt/mmc/Roms/APPS/`.

2. Make sure the following files are present:
   ```
   main.py, app.py, anbernic.py, input.py, language.py, systems.py, graphic.py
   lang/          (contains JSON translation files)
   web/           (contains template.html)
   ```

3. Install required Python packages (if not already installed):
   ```bash
   pip3 install flask Pillow
   ```
   > If `pip` is unavailable, the program will attempt to extract dependencies from `module.zip` (if present).

4. (Optional) Make the startup script executable:
   ```bash
   chmod +x web_manager.sh
   ```

---

## 3. Starting the Server

On the device, open a terminal (via SSH or the built‑in console) and navigate to the program folder:

```bash
cd /mnt/mmc/Roms/APPS/web_manager
python3 main.py
```

Or, if you have the script:

```bash
./web_manager.sh
```

The device screen will show a splash message with the IP address and port (usually `http://<IP>:5000`).  
The server is now running.

---

## 4. Accessing the Web Interface

- Connect your computer/phone to the **same Wi‑Fi** as the Anbernic device.  
- Open a web browser and enter the IP address shown on the device screen, for example:
  ```
  http://192.168.1.100:5000
  ```
- The main interface will load in your browser.

---

## 5. Using the Interface

### Left sidebar
- **SD selector** – switch between SD1 and SD2.  
- **Refresh** – reload the current folder list.  
- **Upload Game** – open the upload dialog.  
- **Search bar** – filter games by name or platform in real time.  
- **Game list** – click a console folder to enter; click a game to view its details.

### Main area (right)
- **Preview** – shows the game’s preview image (if available).  
- **Details** – displays game name, console, file size, modification time, and file path.  
- **Delete Game** – removes the ROM file and its preview(s).  
- **Update Preview** – upload a new preview image for the selected game (auto‑renamed to match the ROM name).

### Uploading games
1. Click **Upload Game**.  
2. Enter the target directory (e.g., `NES`, `SNES`, `PS`). This is the console folder where the ROM(s) will be saved.  
3. Select one or more ROM files (hold Ctrl/Cmd to select multiple).  
4. Optionally, select one or more preview images (`.png`, `.jpg`, etc.).  
   - If you upload **one ROM + one preview**, the preview will be renamed to match the ROM and placed in the `Imgs/` folder.  
   - If you upload **multiple ROMs + multiple previews**, the previews keep their original names and are stored in `Imgs/`.  
5. Click **Upload** and wait for completion. The list will refresh automatically.

### Deleting a game
- Select a game from the list, then click the **Delete** button in the details panel.  
- Confirm the deletion – both the ROM file and its matching preview will be removed.

### Updating a preview
- Select a game, click **Update Preview**, choose an image file, and upload.  
- The new preview will replace the old one (if any) and keep the same file name as the ROM.

---

## 6. Stopping the Server

- In the web interface, click the **Shutdown Server** button.  
- Or, press the **SELECT** physical button on the Anbernic device.  
- You can also press `Ctrl+C` in the terminal where the server is running.

---

## 7. Troubleshooting

| Issue | Solution |
|-------|----------|
| **No games appear** | Check that your ROM folders are in `/mnt/mmc/Roms/` or `/mnt/sdcard/Roms/`. |
| **Upload fails** | Ensure the target directory exists and there is enough free space. Also check file permissions. |
| **Preview not showing** | Verify that a preview image exists in `Imgs/` with the same base name as the ROM (e.g., `Super Mario.nes` → `Super Mario.png`). |
| **Language not correct** | The system language is read from `/mnt/vendor/oem/language.ini`. You can override it by adding `?lang=zh_CN` to the URL. |
| **Splash screen missing** | SDL2 may not be installed; the server will still start normally. |
| **Cannot access web page** | Check that the device IP is correct and both devices are on the same network. Also ensure firewall (if any) allows port 5000. |

---

## 8. Customization

- **Default SD card**: Change `current_sd = 1` or `2` in `app.py` (line ~90).  
- **Upload size limit**: Adjust `MAX_CONTENT_LENGTH` in `app.py` (default 1 GB).  
- **Port**: Modify `port=5000` in `app.run()` inside `main()`.

---

## 9. Support

For questions, suggestions, or bug reports, please refer to the Anbernic community forums or open an issue on the project repository (if available).

---

**Enjoy managing your game collection wirelessly! 🎮**