#!/bin/bash

# DD Image Flashing Script
# Author: cbepx-me
# Version: 1.2 - Added GPT repair function

set -e  # Exit immediately on error

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

version=1.2

# Log functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Show available image files in current directory
show_available_images() {
    log_info "Available image files in current directory:"
    local images=($(find . -maxdepth 1 -type f -iname "*.img" -exec basename {} \; 2>/dev/null | sort))
    
    if [ ${#images[@]} -eq 0 ]; then
        log_error "No .img files found"
        exit 1
    fi
    
    for i in "${!images[@]}"; do
        local file="${images[$i]}"
        echo "  $((i+1)). $file ($(du -h "$file" | cut -f1))"
    done
    echo
}

# Select image file
select_image() {
    local images=($(find . -maxdepth 1 -type f -iname "*.img" -exec basename {} \; 2>/dev/null | sort))
    
    if [ ${#images[@]} -eq 1 ]; then
        SELECTED_IMAGE="${images[0]}"
        log_info "Auto-selected the only image file: $SELECTED_IMAGE"
        return
    fi
    
    while true; do
        read -p "Select image number (1-${#images[@]}): " choice
        
        if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le ${#images[@]} ]; then
            SELECTED_IMAGE="${images[$((choice-1))]}"
            break
        else
            log_error "Invalid selection, please try again"
        fi
    done
}

# Show available devices
show_available_devices() {
    log_info "Available storage devices:"
    echo "System disks (DO NOT SELECT!):"
    lsblk -o NAME,SIZE,TYPE,MOUNTPOINT,MODEL | grep -E "^(NAME|sd[a-z]|nvme|mmcblk)" | grep -v loop
    
    echo
    log_warn "Please identify your USB device/SD card by size and model"
    echo "USB devices are usually: /dev/sdX (X is a letter)"
    echo "SD cards are usually: /dev/mmcblkX"
    echo
}

# Select target device
select_device() {
    while true; do
        read -p "Enter target device path (e.g., /dev/sdb): " device
        
        # Basic validation
        if [[ ! "$device" =~ ^/dev/(sd[a-z]|mmcblk[0-9]+|nvme[0-9]+n[0-9]+)$ ]]; then
            log_error "Invalid device path format"
            continue
        fi
        
        if [ ! -b "$device" ]; then
            log_error "Device $device does not exist or is not a block device"
            continue
        fi
        
        # Check if it's a critical system device
        local system_devices=($(lsblk -n -o NAME | grep -E "^(sda|nvme0n1|mmcblk0)"))
        for sys_dev in "${system_devices[@]}"; do
            if [[ "$device" =~ "$sys_dev" ]]; then
                log_error "WARNING: $device might be a system disk!"
                read -p "Are you sure you want to continue? (Enter 'YES' to confirm): " confirm
                if [ "$confirm" != "YES" ]; then
                    continue 2
                fi
            fi
        done
        
        # Final confirmation
        local device_info=$(lsblk -o SIZE,MODEL,MOUNTPOINT "$device" | sed -n '2p')
        log_warn "You selected: $device"
        log_warn "Device info: $device_info"
        
        read -p "Confirm using this device? All data will be destroyed! (y/n): " final_confirm
        if [[ "$final_confirm" =~ ^[Yy]$ ]]; then
            SELECTED_DEVICE="$device"
            break
        fi
    done
}

# Unmount device partitions
unmount_device() {
    log_info "Checking and unmounting device partitions..."
    
    # Get all mounted partitions of the device
    local mounts=($(lsblk -n -o MOUNTPOINT "$SELECTED_DEVICE" 2>/dev/null | grep -v "^$" | grep -v "\[SWAP\]"))
    
    for mount in "${mounts[@]}"; do
        if [ -n "$mount" ] && mountpoint -q "$mount" 2>/dev/null; then
            log_warn "Unmounting partition: $mount"
            $ESUDO umount "$mount" 2>/dev/null || true
        fi
    done
    
    # Additional attempt to unmount common partitions
    for part in "${SELECTED_DEVICE}"*; do
        if [ -b "$part" ]; then
            mountpoint=$(lsblk -n -o MOUNTPOINT "$part" 2>/dev/null)
            if [ -n "$mountpoint" ] && mountpoint -q "$mountpoint" 2>/dev/null; then
                log_warn "Unmounting partition: $part -> $mountpoint"
                $ESUDO umount "$part" 2>/dev/null || true
            fi
        fi
    done
    
    sleep 2
}

# Execute flashing
flash_image() {
    log_info "Starting image flash..."
    log_info "Image: $SELECTED_IMAGE"
    log_info "Device: $SELECTED_DEVICE"
    log_info "This may take some time, please be patient..."
    echo
    
    # Check if image file exists
    if [ ! -f "$SELECTED_IMAGE" ]; then
        log_error "Image file does not exist: $SELECTED_IMAGE"
        exit 1
    fi
    
    # Calculate image size
    local image_size=$(du -h "$SELECTED_IMAGE" | cut -f1)
    log_info "Image size: $image_size"
    
    # Execute dd command
    local start_time=$(date +%s)
    
    $ESUDO dd if="$SELECTED_IMAGE" of="$SELECTED_DEVICE" \
        bs=4M status=progress \
        oflag=sync conv=fsync
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    log_success "Flash completed!"
    log_info "Total time: $duration seconds"
    
    # Sync disk
    log_info "Syncing disk..."
    sync
}

# Verify flash (optional)
verify_flash() {
    read -p "Do you want to verify the flash result? (y/n): " verify_choice
    if [[ "$verify_choice" =~ ^[Yy]$ ]]; then
        log_info "Starting verification..."
        
        # Create temporary files for verification
        local temp_hash=$(mktemp)
        local device_hash=$(mktemp)
        
        # Calculate hash of image file
        log_info "Calculating image file hash..."
        sha256sum "$SELECTED_IMAGE" | cut -d' ' -f1 > "$temp_hash"
        
        # Calculate hash of device (only the image size portion)
        log_info "Calculating device hash..."
        local image_size=$(stat -c%s "$SELECTED_IMAGE")
        $ESUDO dd if="$SELECTED_DEVICE" bs=4M count=$((image_size/4194304)) 2>/dev/null | \
            sha256sum | cut -d' ' -f1 > "$device_hash"
        
        # Compare hashes
        if cmp -s "$temp_hash" "$device_hash"; then
            log_success "Verification successful! Flash is correct."
        else
            log_error "Verification failed! There might be an issue with the flash."
        fi
        
        # Clean up temporary files
        rm -f "$temp_hash" "$device_hash"
    fi
}

# GPT partition table repair
fix_gpt_table() {
    log_info "Starting GPT partition table repair..."
    
    # Check if gdisk is available
    if ! command -v gdisk &> /dev/null; then
        log_error "gdisk is not installed, cannot repair GPT partition table"
        log_info "Please install gdisk: sudo apt install gdisk"
        return 1
    fi
    
    log_info "Running GPT partition table repair commands..."
    log_info "Executing: sudo gdisk $SELECTED_DEVICE"
    
    # Use echo to pipe commands to gdisk
    log_info "Executing GPT repair steps: p -> x -> e -> w -> y"
    
    # Method: Use echo to pipe commands
    echo -e "p\nx\ne\nw\ny" | $ESUDO gdisk "$SELECTED_DEVICE"
    
    local gdisk_result=$?
    
    if [ $gdisk_result -eq 0 ]; then
        log_success "GPT partition table repair completed"
        
        # Show repaired partition information
        log_info "Repaired partition table:"
        $ESUDO gdisk -l "$SELECTED_DEVICE" | head -20
    else
        log_error "GPT partition table repair failed, error code: $gdisk_result"
        return $gdisk_result
    fi
    
    # Sync again
    sync
}

# Final device information display
show_final_info() {
    log_info "Final device status:"
    echo "========================================"
    $ESUDO fdisk -l "$SELECTED_DEVICE" | head -20
    echo "----------------------------------------"
    lsblk "$SELECTED_DEVICE"
    echo "========================================"
    
    log_success "All operations completed!"
    log_info "Device is ready and can be safely removed"
}

# Main function
main() {
    clear
    echo "=============================================="
    echo "DD Image Flashing Script v$version(with GPT Repair)"
    echo "=============================================="
    echo 
    
    # Check root privileges
    if [ "$EUID" -eq 0 ]; then
        log_warn "It's not recommended to run this script directly as root"
        read -p "Continue anyway? (y/n): " root_continue
        if [[ ! "$root_continue" =~ ^[Yy]$ ]]; then
            exit 1
        fi
        ESUDO=""
    else
        ESUDO="sudo"
    fi
    
    # Check dependencies
    if ! command -v lsblk &> /dev/null; then
        log_error "Missing required tool: lsblk"
        exit 1
    fi
    
    # Select image
    show_available_images
    select_image
    
    echo
    # Select device
    show_available_devices
    select_device
    
    echo
    # Final warning
    log_error "!!! WARNING !!!"
    log_error "This will completely erase device: $SELECTED_DEVICE"
    log_error "All data will be permanently lost!"
    echo
    
    read -p "Enter 'YES, FLASH IT' to confirm flashing: " ultimate_confirm
    if [ "$ultimate_confirm" != "YES, FLASH IT" ]; then
        log_error "Operation cancelled"
        exit 0
    fi
    
    # Execute flashing process
    unmount_device
    flash_image
    verify_flash
    
    # GPT repair
    echo
    read -p "Do you want to repair GPT partition table? (Recommended) (y/n): " fix_gpt_choice
    if [[ "${fix_gpt_choice:-Y}" =~ ^[Yy]$ ]]; then
        fix_gpt_table
    else
        log_info "Skipping GPT partition table repair"
    fi
    
    # Show final information
    show_final_info
}

# Run main function
main "$@"
