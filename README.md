# Anbernic H700 Stock OS Modification

Stock OS Modification is a project built on the StockOS of Anbernic, which is enhanced through modifications to achieve a better user experience.

## Supported handheld models
- RG35xx Plus (RGG35xx 2024)
- RG35xx H
- RG35xxSP
- RG28xx
- RG40xx H
- RG40xx V
- RGcube XX
- RG34xx
- RG34xx SP
- RG35xx PRO

## Include content
1. Modified Stock OS images that support automatic partition expansion
2. Package files that support lossless upgrades
3. As a template package for customizing system themes
4. Open source resources
5. Other additional tools

## Important tips
1. It is recommended to use rufus flash TF under windows.
   - Windows recommends using: [Rufus](https://rufus.ie/)
   - Linux compatible: [flash_dd_with_gpt.sh](https://github.com/cbepx-me/Anbernic-H700-RG-xx-StockOS-Modification/releases/download/20260106/flash_dd_with_gpt.sh)
   - Mac OS compatible: [flash_dd_with_gpt (MacOS).sh](https://github.com/cbepx-me/Anbernic-H700-RG-xx-StockOS-Modification/releases/download/20260106/flash_dd_with_gpt.MacOS.sh)

2. When using programs such as BalenaEtcher and DD flash TF on MacOS or Linux systems, automatic partitioning will fail.
   - Solution: https://github.com/cbepx-me/Anbernic-H700-RG-xx-StockOS-Modification/issues/68
  
   You can use the script I provided to complete the flashing process. Please place the image file and script file in the same path, run the script, and follow the prompts to complete the subsequent operations. Please ensure that gdisk is installed before use:
   - Solution: https://github.com/cbepx-me/Anbernic-H700-RG-xx-StockOS-Modification/blob/main/flash_dd_with_gpt.sh

## Troubleshooting
### No partitions after flashing with script - Linux
If the storage medium seems to have no partitions in place, you should zero the device and manually format to `FAT32`, then try burning the image again.

```bash
$ sudo dd if=/dev/zero of=/path/to/device bs=32M status=progress conv=fdata
$ sync
$ sudo mkfs.fat -F 32 /path/to/device           
$ ./flash_dd_with_gpt.sh
```


## PortMaster related issues should be raised here:
https://github.com/kai4man/PortMaster-for-StockOS-MOD

### Compatible Games:
[**📋 Check the Working Ports List**](https://docs.google.com/spreadsheets/d/1UlxRCSIfNkZIiCMAgo8eFqKhsIbrLA_1d3lFdVyS4q8/edit?gid=0) - regularly updated spreadsheet with tested games.

## For more information, please visit
https://github.com/cbepx-me/RG35xx-P-RG35xx-H-Modification/wiki

## Download
### 1. 64-bit Stock OS Mod image:
- RG28xx, RG34xx, RG34xx SP, RGcubexx, RG35xx PRO:

https://drive.google.com/drive/folders/1zTtl8n5zpaRsxwIX7ncG-7sgwzf5Aym-?usp=sharing

- RG35xx PLUS (RG35xx 2024), RG35xx H, RG35xx SP, RG40xx H, RG40xx V:

https://drive.google.com/drive/folders/1ilDbBQP8XB4IVQfhnxde8Diu0fQdDPI9?usp=sharing

### 2. 64-bit Stock OS Mod Upgrade Package & other:

https://drive.google.com/drive/folders/1uwCkGX3H-K09pj0VbB6hkS8I0_qhzrGY?usp=sharing

### 3. RG28xx and RG35xx 2024 offline installation of PortMaster:

https://drive.google.com/drive/folders/1JP4g8DuRsBq1LgPPKWBKh6Zt2VMt1EJn?usp=sharing
