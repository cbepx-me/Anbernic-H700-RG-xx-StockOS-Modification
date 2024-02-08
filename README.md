# RG35xx P &amp; RG35xx H Stock OS Modification

RG35xx P& RG35xx H Stock OS Modification is a project built on the official systems of Anbernic RG35xx PLUS and RG35xx H, which is enhanced through modifications to achieve a better user experience.

Include content
---------------
1. Modified OS images that support automatic partition expansion
2. Package files that support lossless upgrades
3. As a template package for customizing system themes
4. Other additional tools

Instructions for use
--------------------
# 1. OS_Image

Function：
Based on stock os improvement, modify partition arrangement, and support automatic expansion of partitions. 
Supports TF cards with a capacity of 16GB or more. 
Excluding games, you need to copy and add games yourself.

Installation instructions：
1.1 After downloading the. 7z compressed file, you need to decompress and obtain the. img image file
1.2 Burn the included .img to a MicroSD (>= 16GB) using your tool of choice (Rufus, Balena Etcher, dd, etc)
1.3 After completing the card swiping, there is no need for any other operation. Please insert the card directly and start up. 
    The first startup will automatically complete the expansion of the game partition, create directory, and install script files,
    During this period, it will automatically restart. Please be patient and wait for the operation to complete
1.4 After successfully starting the system, you can connect to the computer through a card reader and copy game files to the
    corresponding folder in the "ROMS" partition
1.5 Use partitioning tools to hide all partitions except for the ROMS partition, so that they do not pop up like windows that need to be formatted every time

# 2. Update_Package

Function Description:
This lossless upgrade patch is based on the official released new version of the system image production, adding some personal production functions, which can upgrade the original official system without affecting the original game and game save (lossless upgrade).

Usage:
2.1 After downloading the patch pack, unzip it to obtain the "APPS" folder
2.2 Copy the "APPS" folder to the "Roms" folder in the TF 1 or TF 2 card game partition
2.3 After booting up, enter "RA Game", find the corresponding "APPS" simulator, and run "RG35xxX_Upgrade_202xxxxx" inside it
2.4 Follow the prompts to complete the system upgrade
2.5 The first restart may take a longer time, please be patient and wait

# 3. Theme_Customization_Tool

function:
3.1.1 This template provides the necessary material resources for customized themes
3.1.2 Can serve as a template for customized themes
3.1.3 Can be used to restore the official default theme

Customized methods:

File and folder description：

3.2.1 Theme-TCT. sh - Theme installation script

This file is the theme installation script, which is used to install the theme.
Important reminder: To ensure successful installation of the theme, the content of the file should not be changed. 
The file name can be changed freely, but it must be consistent with the theme resource folder name! Stay consistent! Stay consistent!
For example, the theme installation script file name is "Theme-ABC. sh", and the theme resource folder name is "Theme-ABC" (pay attention to capitalization).

3.2.2 Theme-TCT - Theme Resource Folder

Contains all resource files corresponding to the theme, and the folder name can be modified freely, but it must be consistent with the theme installation script file name! Stay consistent! Stay consistent!

Internal folder description:

Boot: The second screen logo image displayed when the host starts
Charge_ Mode: Animated image displayed during shutdown and charging
Desktop_ Res: Game hall interface material images (where the HDMI folder corresponds to the images displayed when connecting to an external TV, and the LCD folder corresponds to the images displayed on the host screen, the same below)
Game_ Menu: Front end main interface material image
Game_ Overlay: Picture of the border of some emulators in the game hall
Loading: The logo image displayed during game loading and exiting
Retro: RA game interface icon image
Setjoy: Key setting image
Setkey: Button setting image
Shutdown: shutdown display image and warning image when low battery
Sound: Key sound effect file
Test: Key test material image
Theme: Front end main interface icon image
Wallpapers: Front end background image
WiFi: WiFi prompt material image

Important reminder:

(1) When making modifications, please follow the file format, resolution, transparency effect, file name, and other parameters of the original material images to avoid display errors!

(2) The main interface icon and background image contain ten resource folders numbered "0-9". After modification, please select the corresponding number in the host settings.

3.2.3 Imgs - Preview image folder

There is only one PNG format image file in this folder, which is a preview image of the corresponding theme installation script. It can be used as a preview theme effect in the console game list.
Important note: The image file name must be exactly the same as the theme installation script file name. For example, if the script file name is "Theme ABC. sh", the preview image file name should be "Theme ABC. png".

Installation method:

After completing the customization, please copy the "Theme-TCT. sh", "Theme-TCT", and "Imgs" script files and two folders together to the "Roms/APPS" folder in the game partition of Card 1 or Card 2. After booting up, enter "RA Games - APPS" to see the "Theme-TCT" function. After running, complete the theme installation.

# 4. Custom themes

The themes comes from the internet. Please let me know if there is any infringement.

1. Unplug the TF 1 or TF 2 and insert it into the computer. Copy the entire APPS folder into the Roms folder of TF 1 or TF 2.
2. Insert the TF and start it up. In the RA game, select APPS and find various themes to run.

Development Plan
----------------
1. Add LED control function script √ 
2. Add Backup and restore system data function script √ 
3. Add change  retroarch hotkey enable key function script √ 
4. Fix the issue of "QUICK_SHUTDOWN" √ 
5. Fix installation errors in the previous version √ 
6. Add Custom themes √ 
7. Add Install SSH √ 
8. Add Install mpv √ 
9. ...

About download quota exceeded
-----------------------------
Go up a directory and download the folder. Google Drive will make a zip of this folder and allow you to download that instead.

Enjoy it!
